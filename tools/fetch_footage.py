# Runs INSIDE the Composio remote workbench (COMPOSIO_REMOTE_WORKBENCH), not locally.
# The workbench can reach Pixabay; the build workspace cannot, so the clip is
# committed to GitHub in <=2.5 MB chunks and reassembled after `git pull`:
#     cat footage/<name>.mp4.part* > assets/footage.mp4
#
# Before running, prepend these three lines (the key is NOT stored in this public repo):
#     KEY = "<pixabay api key from the scheduled task prompt>"
#     QUERIES = ["rain window night", "lonely road dusk"]   # 2-4 English queries for the mood
#     EXCLUDE_IDS = [154401]                                 # ids already used (log.json "footage_id")
import base64, os, subprocess, sys, requests

REPO = "saeedmalati/terapi-khone-reels"
CH = 2_500_000

def pick():
    seen = set(EXCLUDE_IDS)
    for q in QUERIES:
        r = requests.get("https://pixabay.com/api/videos/", params={"key": KEY, "q": q, "per_page": 50, "safesearch": "true"}, timeout=20).json()
        for h in r.get("hits", []):
            L = h["videos"]["large"]
            tags = h.get("tags", "").lower()
            if h["id"] in seen or "ai generated" in tags:
                continue
            if L["height"] >= 1920 and L["height"] > L["width"] and 12 <= h["duration"] <= 45 and L["size"] < 35e6:
                return q, h, L
    return None

found = pick()
if not found:
    print("NO_FOOTAGE")
else:
    q, h, L = found
    data = requests.get(L["url"], timeout=120, headers={"User-Agent": "Mozilla/5.0"}).content
    # compress (background is darkened anyway) so the repo stays small
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "imageio-ffmpeg"], capture_output=True)
        import imageio_ffmpeg
        open("/home/user/fg_in.mp4", "wb").write(data)
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-y", "-i", "/home/user/fg_in.mp4", "-an",
                        "-vf", "scale=1080:1920", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                        "-pix_fmt", "yuv420p", "/home/user/fg_out.mp4"], check=True, capture_output=True)
        small = open("/home/user/fg_out.mp4", "rb").read()
        if 0 < len(small) < len(data):
            data = small
    except Exception as e:
        print("compress skipped:", str(e)[:120])
    slug = "-".join(h["tags"].replace(",", " ").split()[:3]).lower()
    name = f"{h['id']}-{slug}.mp4"
    n = (len(data) + CH - 1) // CH
    errs = []
    for i in range(n):
        res, err = proxy_execute("PUT", f"/repos/{REPO}/contents/footage/{name}.part{i:02d}", "github",
                                 body={"message": f"footage {h['id']} part {i}", "content": base64.b64encode(data[i*CH:(i+1)*CH]).decode(),
                                       "committer": {"name": "Claude", "email": "noreply@anthropic.com"}})
        if err:
            errs.append((i, str(err)[:120]))
    print({"query": q, "footage_id": h["id"], "name": name, "parts": n, "duration": h["duration"],
           "size": len(data), "tags": h["tags"], "errors": errs})
