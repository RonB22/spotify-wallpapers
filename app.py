
import os
import shutil
import time
import random
from flask import Flask, redirect, request, session, url_for, render_template, send_from_directory
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecretkey"

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
SCOPE = "user-library-read"

ALBUM_FOLDER = "album_covers"
WALLPAPER_FOLDER = "static/wallpapers"

WIDTH, HEIGHT = 1290, 2796
COVER_SIZE = 300

def clear_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def get_spotify_client():
    token_info = session.get("token_info", None)
    if not token_info:
        return None

    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=".cache")

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    return spotipy.Spotify(auth=token_info['access_token'])

def download_album_covers(sp):
    clear_folder(ALBUM_FOLDER)
    limit, offset, total_downloaded = 50, 0, 0

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
                total_downloaded += 1
                time.sleep(0.1)
            except Exception as e:
                print(f"[X] שגיאה: {filename} - {e}")

        offset += limit

    return total_downloaded

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
    clear_folder(WALLPAPER_FOLDER)
    covers = load_album_covers()
    cols = WIDTH // COVER_SIZE
    rows = HEIGHT // COVER_SIZE
    max_covers = cols * rows

    if not covers:
        return 0

    if len(covers) < max_covers:
        covers *= (max_covers // len(covers)) + 1

    for i in range(1, number + 1):
        canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        random.shuffle(covers)

        for idx in range(max_covers):
            x = (idx % cols) * COVER_SIZE
            y = (idx // cols) * COVER_SIZE
            canvas.paste(covers[idx], (x, y))

        canvas.save(os.path.join(WALLPAPER_FOLDER, f"wallpaper_{i}.jpg"))

    return number

def get_saved_albums(sp, limit=50):
    albums, offset = [], 0
    while True:
        results = sp.current_user_saved_albums(limit=limit, offset=offset)
        items = results['items']
        if not items:
            break
        for item in items:
            album = item['album']
            name = album['name']
            image_url = album['images'][0]['url']
            albums.append({"name": name, "image_url": image_url})
        offset += limit
    return albums

@app.route("/")
def index():
    return render_template("index.html", logged_in="token_info" in session)

@app.route("/login")
def login():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=".cache")
    return redirect(sp_oauth.get_authorize_url())

@app.route("/callback")
def callback():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=".cache")
    code = request.args.get('code')
    error = request.args.get('error')
    if error:
        return f"Error during authentication: {error}"
    if not code:
        return "Authorization code not found. Please try to login again."

    token_info = sp_oauth.get_access_token(code, check_cache=False)
    if not token_info:
        return "Failed to get access token. Please try again."
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route("/generate")
def generate():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('index'))

    total = download_album_covers(sp)
    if total == 0:
        return "לא נמצאו עטיפות אלבומים."
    if generate_collages() == 0:
        return "אירעה שגיאה ביצירת קולאז'ים."
    return redirect(url_for('show_wallpapers'))

@app.route("/wallpapers/<filename>")
def wallpapers(filename):
    return send_from_directory(WALLPAPER_FOLDER, filename)

@app.route("/show_wallpapers")
def show_wallpapers():
    if not os.path.exists(WALLPAPER_FOLDER):
        return "לא נוצרו רקעים עדיין."
    files = [f for f in os.listdir(WALLPAPER_FOLDER) if f.endswith((".jpg", ".png"))]
    return render_template("wallpapers.html", files=files)

@app.route("/select")
def select_albums():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for("index"))
    albums = get_saved_albums(sp)
    return render_template("select_albums.html", albums=albums)

@app.route("/generate_from_selection", methods=["POST"])
def generate_from_selection():
    selected_urls = request.form.getlist("selected_albums")
    if not selected_urls:
        return "לא נבחרו אלבומים."

    clear_folder(ALBUM_FOLDER)
    clear_folder(WALLPAPER_FOLDER)

    for idx, url in enumerate(selected_urls):
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).resize((COVER_SIZE, COVER_SIZE))
            image.save(os.path.join(ALBUM_FOLDER, f"album_{idx}.jpg"))
        except Exception as e:
            print(f"שגיאה בהורדת תמונה: {e}")

    generate_collages()
    return redirect(url_for("show_wallpapers"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
