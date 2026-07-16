import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
MANIFEST_FILE = ROOT / "metadata" / "linkedin" / "pl400_cert_prep.json"
TRANSCRIPTS_DIR = ROOT / "transcripts" / "linkedin"
OUTPUT_DIR = ROOT / "markdown" / "linkedin" / "videos"


def load_manifest(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def create_lesson_markdown(
    entry: dict[str, Any],
    course_title: str,
    channel: str,
    course_url: str,
    transcript_text: str,
) -> str:
    slug: str = entry.get("slug", "")
    title: str = entry.get("title", "")
    module: str = entry.get("module", "")
    duration: int = int(entry.get("duration", 0))
    video_url: str = entry.get("url") or course_url

    lines = [
        f"# {title}",
        "",
        "## Metadata",
        "",
        f"Video ID: {slug}",
        "",
        "Video URL:",
        video_url,
        "",
        "Duration (seconds):",
        str(duration),
        "",
        "Playlist:",
        course_title,
        "",
        "Channel:",
        channel,
        "",
        "## Module",
        "",
        module,
        "",
        "## Transcript",
        "",
        transcript_text.strip(),
        "",
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{slug}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return f"markdown/linkedin/videos/{slug}.md"


def main() -> None:
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Course manifest not found: {MANIFEST_FILE}\n"
            "Fill in metadata/linkedin/pl400_cert_prep.json first."
        )

    manifest = load_manifest(MANIFEST_FILE)
    course_title: str = manifest.get("title", "LinkedIn Learning Course")
    channel: str = manifest.get("channel", "LinkedIn Learning")
    course_url: str = manifest.get("course_url", "")
    videos: list[dict[str, Any]] = manifest.get("videos", [])
    total = len(videos)

    imported = 0
    missing = 0

    for i, entry in enumerate(videos, start=1):
        slug = entry.get("slug", "")
        title = entry.get("title", "")
        log.info(f"[{i}/{total}] Importing: {title}")

        transcript_path = TRANSCRIPTS_DIR / f"{slug}.txt"
        if not transcript_path.exists():
            log.warning(f"  -> Transcript missing: transcripts/linkedin/{slug}.txt")
            missing += 1
            continue

        transcript_text = transcript_path.read_text(encoding="utf-8")
        if not transcript_text.strip():
            log.warning(f"  -> Transcript file is empty: transcripts/linkedin/{slug}.txt")
            missing += 1
            continue

        create_lesson_markdown(entry, course_title, channel, course_url, transcript_text)
        imported += 1

    print()
    print("=================================")
    print("LinkedIn Course Import Complete")
    print("=================================")
    print(f"Lessons in manifest   : {total}")
    print(f"Imported              : {imported}")
    print(f"Missing transcripts   : {missing}")
    if missing:
        print()
        print("Copy each missing transcript from the lesson's Transcript tab")
        print("and save it as transcripts/linkedin/{slug}.txt, then re-run.")


if __name__ == "__main__":
    main()
