import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
METADATA_FILE = ROOT / "metadata" / "command_bar_playlist.json"
TRANSCRIPTS_DIR = ROOT / "transcripts"
MARKDOWN_DIR = ROOT / "markdown"
VIDEOS_DIR = MARKDOWN_DIR / "videos"
PLAYLISTS_DIR = MARKDOWN_DIR / "playlists"
INDEX_DIR = ROOT / "index"
MANIFEST_FILE = INDEX_DIR / "markdown_manifest.json"


def load_playlist(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_transcript(video_id: str) -> list[dict[str, Any]]:
    path = TRANSCRIPTS_DIR / f"{video_id}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge_transcript(segments: list[dict[str, Any]]) -> str:
    texts: list[str] = []
    prev = ""
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        if text == prev:
            continue
        texts.append(text)
        prev = text
    merged = " ".join(texts)
    merged = re.sub(r" {2,}", " ", merged)
    return merged.strip()


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def create_video_markdown(
    entry: dict[str, Any],
    playlist_title: str,
    channel: str,
) -> tuple[str, bool]:
    video_id: str = entry.get("id", "")
    title: str = entry.get("title", "")
    url: str = entry.get("url", f"https://www.youtube.com/watch?v={video_id}")
    duration: float = entry.get("duration", 0.0)

    segments = load_transcript(video_id)
    transcript_text = merge_transcript(segments) if segments else "_Transcript not available._"

    lines = [
        f"# {title}",
        "",
        "## Metadata",
        "",
        f"Video ID: {video_id}",
        "",
        "Video URL:",
        url,
        "",
        "Duration (seconds):",
        str(int(duration)),
        "",
        "Playlist:",
        playlist_title,
        "",
        "Channel:",
        channel,
        "",
        "## Transcript",
        "",
        transcript_text,
        "",
    ]

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VIDEOS_DIR / f"{video_id}.md"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return f"videos/{video_id}.md", True
    except Exception as e:
        print(f"  -> Failed to write {video_id}.md: {e}")
        return f"videos/{video_id}.md", False


def create_playlist_markdown(
    playlist: dict[str, Any],
    entries: list[dict[str, Any]],
) -> str:
    title: str = playlist.get("title", "Playlist")
    channel: str = playlist.get("channel", "")
    description: str = playlist.get("description", "").strip()
    total = len(entries)

    lines = [
        f"# {title}",
        "",
        "## Playlist Information",
        "",
        "Channel:",
        channel,
        "",
        "Description:",
        description,
        "",
        "Total Videos:",
        str(total),
        "",
        "## Videos",
        "",
    ]

    for i, entry in enumerate(entries, start=1):
        video_id = entry.get("id", "")
        video_title = entry.get("title", "")
        url = entry.get("url", f"https://www.youtube.com/watch?v={video_id}")
        duration = entry.get("duration", 0.0)

        lines += [
            f"### Video {i}",
            "",
            "Title:",
            video_title,
            "",
            "URL:",
            url,
            "",
            "Video ID:",
            video_id,
            "",
            "Duration:",
            str(int(duration)),
            "",
            "Summary:",
            f"Transcript file available in videos/{video_id}.md",
            "",
        ]

    PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    file_name = f"{slug}.md"
    out_path = PLAYLISTS_DIR / file_name
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return f"playlists/{file_name}"


def create_index(
    playlist_title: str,
    playlist_file: str,
    video_files: list[str],
) -> None:
    lines = [
        "# Knowledge Base Index",
        "",
        "## Playlists",
        "",
        f"- {playlist_title}",
        "",
        "### Playlist File",
        "",
        playlist_file,
        "",
        "### Video Files",
        "",
    ]
    for vf in video_files:
        lines.append(f"- {vf}")
    lines.append("")

    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    with open(MARKDOWN_DIR / "index.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def create_manifest(
    playlist_title: str,
    channel: str,
    entries: list[dict[str, Any]],
    video_records: list[dict[str, str]],
) -> None:
    manifest = {
        "playlist": playlist_title,
        "total_videos": len(entries),
        "channel": channel,
        "video_files": video_records,
    }
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def main() -> None:
    playlist = load_playlist(METADATA_FILE)
    entries: list[dict[str, Any]] = playlist.get("entries", [])
    playlist_title: str = playlist.get("title", "Playlist")
    channel: str = playlist.get("channel", "")

    success = 0
    failed = 0
    video_files: list[str] = []
    video_records: list[dict[str, str]] = []

    for i, entry in enumerate(entries, start=1):
        video_id = entry.get("id", "")
        title = entry.get("title", "")
        print(f"[{i}/{len(entries)}] Generating markdown: {title}")

        md_file, ok = create_video_markdown(entry, playlist_title, channel)
        if ok:
            success += 1
        else:
            failed += 1

        video_files.append(md_file)
        video_records.append({
            "video_id": video_id,
            "title": title,
            "markdown_file": md_file,
        })

    playlist_file = create_playlist_markdown(playlist, entries)
    create_index(playlist_title, playlist_file, video_files)
    create_manifest(playlist_title, channel, entries, video_records)

    print()
    print("=================================")
    print("Markdown Generation Complete")
    print("=================================")
    print(f"Videos Processed : {success}")
    print(f"Videos Failed    : {failed}")
    print(f"Playlist Files   : 1")
    print(f"Index Created    : Yes")


if __name__ == "__main__":
    main()
