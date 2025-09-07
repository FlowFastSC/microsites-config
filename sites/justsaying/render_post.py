import csv, os, textwrap, sys, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PALETTE = {
    "bg": "#FFE5D4",      # warm sand
    "accent": "#694F5D",  # deep plum
    "ink": "#222222"      # near-black for text
}

W, H = 1000, 1500
M = 80  # margin
TITLE_FS = 72
SUB_FS = 40
CREDIT_FS = 28
LINE_SPACING = 1.18

FONT_SANS = "assets/fonts/NotoSans-Regular.ttf"
FONT_SERIF = "assets/fonts/NotoSerif-Regular.ttf"

CSV_PATH = os.getenv("CSV_PATH", "content/sayings.csv")
OUT_DIR = Path(os.getenv("OUT_DIR", "public/instagram"))

def wrap(draw, text, font, max_width):
    # simple greedy wrapper
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textlength(test, font=font) <= max_width:
            cur.append(w)
        else:
            if cur: lines.append(" ".join(cur))
            cur = [w]
    if cur: lines.append(" ".join(cur))
    return lines

def draw_text_block(draw, text, font, x, y, max_width, fill):
    lines = wrap(draw, text, font, max_width)
    line_h = font.size * LINE_SPACING
    for i, line in enumerate(lines):
        draw.text((x, y + i*line_h), line, font=font, fill=fill)
    return y + len(lines)*line_h

def pick_row(rows, today):
    # choose first queued with date <= today (YYYY-MM-DD)
    for r in rows:
        if (r.get("status","").strip().lower() == "queued" and
            r.get("date","") <= today):
            return r
    return None

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # load data
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).strftime("%Y-%m-%d")  # Europe/Amsterdam (+02:00 in summer)
    row = pick_row(rows, today)
    if not row:
        print("no_row=true", file=sys.stderr)
        print("::notice title=Instagram::No queued row for today")
        return 0

    text = row["text"].strip()
    translation = row.get("translation","").strip()
    hashtags = (row.get("hashtags","") or "").strip()
    pid = row["id"].strip()
    style = (row.get("image_style") or "classic").strip()

    # canvas
    im = Image.new("RGB", (W, H), PALETTE["bg"])
    draw = ImageDraw.Draw(im)

    # simple accent bar at top
    draw.rectangle([0,0,W,18], fill=PALETTE["accent"])

    # load fonts
    title_font = ImageFont.truetype(FONT_SERIF, TITLE_FS)
    sub_font   = ImageFont.truetype(FONT_SANS, SUB_FS)
    credit_font= ImageFont.truetype(FONT_SANS, CREDIT_FS)

    # layout
    x = M
    y = int(H*0.18)

    # headline (Dutch saying)
    y = draw_text_block(draw, text, title_font, x, y, W-2*M, fill=PALETTE["ink"])
    y += 24

    # translation (optional)
    if translation:
        y = draw_text_block(draw, translation, sub_font, x, y, W-2*M, fill=PALETTE["accent"])
        y += 16

    # small footer / brand (edit as you like)
    footer = "Spreekwoorden • @yourhandle"
    fw, fh = draw.textlength(footer, font=credit_font), credit_font.size
    draw.text((W-M-fw, H-M-fh), footer, font=credit_font, fill=PALETTE["ink"])

    # subtle frame
    draw.rectangle([M//2, M//2, W-M//2, H-M//2], outline=PALETTE["accent"], width=2)

    # save
    out_name = f"{today}-{pid}.png"
    out_path = OUT_DIR / out_name
    im.save(out_path, format="PNG")

    # caption
    caption_parts = [text]
    if translation: caption_parts.append(f"Vertaling: {translation}")
    if hashtags: caption_parts.append(hashtags)
    caption = "\n\n".join(caption_parts)

    # outputs for workflow
    print(f"image_rel_path={out_path.as_posix()}")
    print(f"caption<<EOF\n{caption}\nEOF")
    print(f"row_id={pid}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
