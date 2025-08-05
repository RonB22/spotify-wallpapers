import os
import shutil
import time
import requests
import random
from PIL import Image
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# הגדרות
CLIENT_ID = "b67d81317a4649fda40a518583d83a20"
CLIENT_SECRET = "f29e05b65aed4f188de91acbda2b7a27"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-library-read"

ALBUM_FOLDER = "album_covers"
WALLPAPER_FOLDER = "wallpapers"

# גודל התמונות
WIDTH, HEIGHT = 1290, 2796
COVER_SIZE = 300  # גודל עטיפות באורך ורוחב

def clear_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def download_album_covers(sp):
    print("🔄 מוריד עטיפות אלבומים...")
    clear_folder(ALBUM_FOLDER)

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
            path = os.path.join(ALBUM_FOLDER, filename)

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

    print(f"✅ סה\"כ עטיפות שהורדו: {total_downloaded}")

def load_album_covers():
    covers = []
    for file in os.listdir(ALBUM_FOLDER):
        if file.endswith(".jpg") or file.endswith(".png"):
            path = os.path.join(ALBUM_FOLDER, file)
            try:
                img = Image.open(path).resize((COVER_SIZE, COVER_SIZE))
                covers.append(img)
            except:
                pass
    return covers

def generate_collages(number=5):
    print("🎨 יוצר קולאז'ים...")
    clear_folder(WALLPAPER_FOLDER)

    covers = load_album_covers()
    cols = WIDTH // COVER_SIZE
    rows = HEIGHT // COVER_SIZE
    max_covers = cols * rows

    if len(covers) == 0:
        print("[!] אין עטיפות להציג. הורד קודם את העטיפות.")
        return

    # שכפל אם יש מעט עטיפות
    if len(covers) < max_covers:
        multiplier = (max_covers // len(covers)) + 1
        covers *= multiplier

    for i in range(1, number + 1):
        canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        random.shuffle(covers)

        for idx in range(max_covers):
            x = (idx % cols) * COVER_SIZE
            y = (idx // cols) * COVER_SIZE
            canvas.paste(covers[idx], (x, y))

        output_path = os.path.join(WALLPAPER_FOLDER, f"wallpaper_{i}.jpg")
        canvas.save(output_path)
        print(f"[✓] קולאז' נשמר: {output_path}")

def main():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))

    download_album_covers(sp)
    generate_collages()

    print("\n🎉 כל התהליך הושלם! התמונות מוכנות בתיקיית 'wallpapers/'.")

if __name__ == "__main__":
    main()
