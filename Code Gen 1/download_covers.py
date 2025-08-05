import os
import shutil
import requests
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import time

# מחיקת תיקיית album_covers אם קיימת, ויצירת חדשה
if os.path.exists("album_covers"):
    shutil.rmtree("album_covers")
os.makedirs("album_covers")

# הגדרות חיבור ל-Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="b67d81317a4649fda40a518583d83a20",
    client_secret="f29e05b65aed4f188de91acbda2b7a27",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read"
))

limit = 50
offset = 0
total_downloaded = 0

while True:
    results = sp.current_user_saved_albums(limit=limit, offset=offset)
    items = results['items']
    if not items:
        break

    for item in items:
        album = item['album']
        name = album['name'].replace('/', '-')
        artist = album['artists'][0]['name'].replace('/', '-')
        image_url = album['images'][0]['url']

        filename = f"{artist} - {name}.jpg"
        path = os.path.join("album_covers", filename)

        try:
            response = requests.get(image_url)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"[+] נשמר: {filename}")
            total_downloaded += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"[X] שגיאה: {filename} - {e}")

    offset += limit

print(f"\nסה״כ עטיפות שנשמרו: {total_downloaded}")
