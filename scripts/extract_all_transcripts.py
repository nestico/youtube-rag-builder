import json
import csv
from pathlib import Path
from typing import Any

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

ROOT = Path(__file__).parent.parent
METADATA_FILE = ROOT / "metadata" / "command_bar_playlist.json"
TRANSCRIPTS_DIR = ROOT / "transcripts"
INDEX_DIR = ROOT / "index"
CSV_FILE = INDEX_DIR / "videos.csv"
JSON_FILE = INDEX_DIR / "videos.json"

CSV_COLUMNS = ["video_id", "title", "url", "duration", "transcript_file", "status"]


def load_playlist(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entries", [])


def extract_transcript(video_id: str) -> list[dict[str, Any]] | None:
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
        return [
            {"text": item.text, "start": item.start, "duration": item.duration}
            for item in transcript
        ]
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
        print(f"  -> Skipped: {type(e).__name__}")
        return None
    except Exception as e:
        print(f"  -> Error: {e}")
        return None


def save_transcript(video_id: str, segments: list[dict[str, Any]]) -> str:
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    file_name = f"{video_id}.json"
    path = TRANSCRIPTS_DIR / file_name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)
    return file_name


def save_csv_index(records: list[dict[str, Any]]) -> None:
    INDEX_DIR.mkdir(exist_ok=True)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def save_json_index(records: list[dict[str, Any]]) -> None:
    INDEX_DIR.mkdir(exist_ok=True)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def main() -> None:
    entries = load_playlist(METADATA_FILE)
    total = len(entries)
    records: list[dict[str, Any]] = []
    success = 0
    failed = 0

    for i, entry in enumerate(entries, start=1):
        video_id = entry.get("id", "")
        title = entry.get("title", "")
        url = entry.get("url", "")
        duration = entry.get("duration", 0.0)

        print(f"[{i}/{total}] Downloading transcript: {title}")

        segments = extract_transcript(video_id)

        if segments is not None:
            transcript_file = save_transcript(video_id, segments)
            status = "SUCCESS"
            success += 1
        else:
            transcript_file = ""
            status = "FAILED"
            failed += 1

        records.append({
            "video_id": video_id,
            "title": title,
            "url": url,
            "duration": duration,
            "transcript_file": transcript_file,
            "status": status,
        })

    save_csv_index(records)
    save_json_index(records)

    print()
    print("=================================")
    print("Transcript Extraction Complete")
    print("=================================")
    print(f"Total Videos : {total}")
    print(f"Success      : {success}")
    print(f"Failed       : {failed}")


if __name__ == "__main__":
    main()
