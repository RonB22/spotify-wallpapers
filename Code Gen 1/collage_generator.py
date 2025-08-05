import os
import random
from PIL import Image
import shutil

# הגדרות גודל תמונת רקע לאייפון
WIDTH, HEIGHT = 1290, 2796
COVER_FOLDER = "album_covers"
OUTPUT_FOLDER = "wallpapers"
COVER_SIZE = 300

# מחיקת תיקיית wallpapers אם קיימת ויצירת חדשה
if os.path.exists(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)
os.makedirs(OUTPUT_FOLDER)

def load_album_covers():
    covers = []
    for file in os.listdir(COVER_FOLDER):
        if file.endswith(".jpg") or file.endswith(".png"):
            path = os.path.join(COVER_FOLDER, file)
            try:
                img = Image.open(path).resize((COVER_SIZE, COVER_SIZE))
                covers.append(img)
            except:
                pass
    return covers

def generate_collage(index=1):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    covers = load_album_covers()
    random.shuffle(covers)

    cols = WIDTH // COVER_SIZE
    rows = HEIGHT // COVER_SIZE
    max_covers = cols * rows

    # במידה ויש מעט עטיפות, שכפל אותן (אפשר להסיר אם אתה מוריד מספיק)
    if len(covers) < max_covers:
        multiplier = (max_covers // len(covers)) + 1
        covers *= multiplier

    random.shuffle(covers)

    for i in range(max_covers):
        x = (i % cols) * COVER_SIZE
        y = (i // cols) * COVER_SIZE
        canvas.paste(covers[i], (x, y))

    output_path = os.path.join(OUTPUT_FOLDER, f"wallpaper_{index}.jpg")
    canvas.save(output_path)
    print(f"[✓] נשמר בהצלחה: {output_path}")

for i in range(1, 6):
    generate_collage(i)
