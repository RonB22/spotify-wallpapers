import os
import shutil
import time
import random
from flask import Flask, redirect, request, session, url_for, render_template, send_from_directory
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image

app = Flask(__name__)
app.secret_key = "supersecretkey"  # תשנה למשהו חזק בפרודקשן!

# הגדרות Spotify OAuth
CLIENT_ID = "b67d81317a4649fda40a518583d83a20"
CLIENT_SECRET = "f29e05b65aed4f188de91acbda2b7a27"
REDIRECT_URI = "https://spotify-wallpapers-production.up.railway.app/callback"
# REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPE = "user-library-read"

ALBUM_FOLDER = "album_covers"
WALLPAPER_FOLDER = "static/wallpapers"

WIDTH, HEIGHT = 1290, 2796
COVER_SIZE = 300

# פונקציות עזר

def clear_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def download_album_covers(sp):
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

    if len(covers) == 0:
        return 0

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

    return number

# Flask routes

@app.route("/")
def index():
    if "token_info" in session:
        return render_template("index.html", logged_in=True)
    else:
        return render_template("index.html", logged_in=False)

@app.route("/login")
def login():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=".cache")
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=".cache")

    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route("/generate")
def generate():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('index'))

    sp = spotipy.Spotify(auth=token_info['access_token'])

    total = download_album_covers(sp)
    if total == 0:
        return "לא נמצאו עטיפות אלבומים."

    count = generate_collages()
    if count == 0:
        return "אירעה שגיאה ביצירת קולאז'ים."

    return redirect(url_for('show_wallpapers'))

@app.route("/wallpapers/<filename>")
def wallpapers(filename):
    return send_from_directory(WALLPAPER_FOLDER, filename)

@app.route("/show_wallpapers")
def show_wallpapers():
    if not os.path.exists(WALLPAPER_FOLDER):
        return "לא נוצרו רקעים עדיין."

    files = os.listdir(WALLPAPER_FOLDER)
    files = [f for f in files if f.endswith(".jpg") or f.endswith(".png")]

    return render_template("wallpapers.html", files=files)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
