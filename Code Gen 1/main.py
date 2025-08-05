import spotipy
from spotipy.oauth2 import SpotifyOAuth

# הגדרות הזדהות שלך
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="b67d81317a4649fda40a518583d83a20",
    client_secret="f29e05b65aed4f188de91acbda2b7a27",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read"
))

# בדיקה: שליפת 5 האלבומים הראשונים
results = sp.current_user_saved_albums(limit=5)

for idx, item in enumerate(results['items']):
    album = item['album']
    print(f"{idx + 1}. {album['name']} — {album['artists'][0]['name']}")
    print("עטיפה:", album['images'][0]['url'])
