import os, sys, csv, requests
from urllib.parse import quote

CSV_PATH = os.getenv("CSV_PATH", "content/sayings.csv")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME  = os.getenv("REPO_NAME")
BRANCH     = os.getenv("BRANCH", "main")

IG_USER_ID = os.getenv("IG_USER_ID")
PAGE_TOKEN = os.getenv("PAGE_TOKEN")

def raw_url(path_rel: str) -> str:
    # Use raw.githubusercontent.com (immediately public after push)
    return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{path_rel}"

def set_status(row_id: str, new_status: str):
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    changed = False
    for r in rows:
        if r.get("id") == row_id:
            r["status"] = new_status
            changed = True
            break
    if changed:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)

def main():
    image_rel_path = os.getenv("IMAGE_REL_PATH")
    caption = os.getenv("CAPTION", "").strip()
    row_id = os.getenv("ROW_ID")

    if not (image_rel_path and caption and row_id):
        print("Missing env IMAGE_REL_PATH / CAPTION / ROW_ID", file=sys.stderr)
        return 1

    img_url = raw_url(image_rel_path)
    # Step 1: create media container
    url1 = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    r1 = requests.post(url1, data={
        "image_url": img_url,
        "caption": caption,
        "access_token": PAGE_TOKEN
    }, timeout=30)
    if r1.status_code != 200:
        print(f"Create media failed: {r1.status_code} {r1.text}", file=sys.stderr)
        return 2
    creation_id = r1.json().get("id")
    if not creation_id:
        print(f"No creation_id in response: {r1.text}", file=sys.stderr)
        return 3

    # Step 2: publish
    url2 = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    r2 = requests.post(url2, data={
        "creation_id": creation_id,
        "access_token": PAGE_TOKEN
    }, timeout=30)
    if r2.status_code != 200:
        print(f"Publish failed: {r2.status_code} {r2.text}", file=sys.stderr)
        return 4

    # mark as published
    set_status(row_id, "published")
    print("published=true")
    return 0

if __name__ == "__main__":
    sys.exit(main())
