import json
import yt_dlp
from pathlib import Path

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL5xdZrvu1OhVx4c2YCgTJYbYUi9Uznxag"

output_dir = Path(__file__).parent.parent / "metadata" / "youtube"
output_dir.mkdir(exist_ok=True)

ydl_opts = {
    "extract_flat": True,
    "quiet": False,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    playlist_info = ydl.extract_info(PLAYLIST_URL, download=False)

output_file = output_dir / "command_bar_playlist.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(playlist_info, f, indent=2, ensure_ascii=False)

print(f"Saved playlist metadata to {output_file}")
print(f"Videos found: {len(playlist_info.get('entries', []))}")