import abc
import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
VIDEOS_DIR = ROOT / "markdown" / "videos"
METADATA_FILE = ROOT / "metadata" / "command_bar_playlist.json"
ENRICHED_DIR = ROOT / "markdown" / "enriched"
ENRICHED_VIDEOS_DIR = ENRICHED_DIR / "videos"
ENRICHED_PLAYLISTS_DIR = ENRICHED_DIR / "playlists"
INDEX_DIR = ROOT / "index"
MANIFEST_FILE = INDEX_DIR / "enriched_manifest.json"
CACHE_DIR = ROOT / "cache" / "enrichment"

SOURCE_CONFIGS: dict[str, dict[str, Path]] = {
    "youtube": {
        "videos_dir": VIDEOS_DIR,
        "metadata_file": METADATA_FILE,
        "enriched_videos_dir": ENRICHED_VIDEOS_DIR,
        "enriched_playlists_dir": ENRICHED_PLAYLISTS_DIR,
        "manifest_file": MANIFEST_FILE,
        "cache_dir": CACHE_DIR,
    },
    "linkedin": {
        "videos_dir": ROOT / "markdown" / "linkedin" / "videos",
        "metadata_file": ROOT / "metadata" / "linkedin" / "pl400_cert_prep.json",
        "enriched_videos_dir": ENRICHED_DIR / "linkedin" / "videos",
        "enriched_playlists_dir": ENRICHED_DIR / "linkedin" / "playlists",
        "manifest_file": INDEX_DIR / "enriched_manifest_linkedin.json",
        "cache_dir": CACHE_DIR / "linkedin",
    },
}


# ─── LLM Provider interface ───────────────────────────────────────────────────

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def complete(self, prompt: str) -> str: ...


class ClaudeProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-opus-4-8",
        max_tokens: int = 1024,
    ) -> None:
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install the Anthropic SDK: pip install anthropic")
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


class AzureOpenAIProvider(LLMProvider):
    """Stub — implement when Azure OpenAI credentials are available."""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError("AzureOpenAIProvider is not yet implemented.")


class OpenAIProvider(LLMProvider):
    """Stub — implement when OpenAI credentials are available."""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError("OpenAIProvider is not yet implemented.")


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-pro") -> None:
        try:
            from google import genai
        except ImportError:
            raise ImportError("Install the Google GenAI SDK: pip install google-genai")
        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY_RAG_YOUTUBE"])
        self.model = model

    def complete(self, prompt: str) -> str:
        response = self._client.models.generate_content(model=self.model, contents=prompt)
        return response.text


# ─── Markdown parser ──────────────────────────────────────────────────────────

class MarkdownParser:
    def parse_video(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8")
        result: dict[str, Any] = {
            "title": "",
            "video_id": "",
            "url": "",
            "duration": "",
            "playlist": "",
            "channel": "",
            "transcript": "",
        }

        m = re.search(r"^# (.+)$", text, re.MULTILINE)
        if m:
            result["title"] = m.group(1).strip()

        m = re.search(r"Video ID:\s*([^\n]+)", text)
        if m:
            result["video_id"] = m.group(1).strip()

        m = re.search(r"Video URL:\s*\n([^\n]+)", text)
        if m:
            raw = m.group(1).strip()
            link = re.search(r"\[.*?\]\((.*?)\)", raw)
            result["url"] = link.group(1) if link else raw

        m = re.search(r"Duration\s*(?:\(seconds\))?:\s*\n?(\d+)", text)
        if m:
            result["duration"] = m.group(1).strip()

        m = re.search(r"Playlist:\s*\n(.+)", text)
        if m:
            result["playlist"] = m.group(1).strip()

        m = re.search(r"Channel:\s*\n(.+)", text)
        if m:
            result["channel"] = m.group(1).strip()

        m = re.search(r"## Transcript\s*\n+([\s\S]+)", text)
        if m:
            result["transcript"] = m.group(1).strip()

        return result


# ─── Prompts ──────────────────────────────────────────────────────────────────

_VIDEO_PROMPT = """\
You are a knowledge engineer building a RAG knowledge base from a YouTube video transcript.

Analyze the transcript and return a JSON object with exactly these fields:

{{
  "executive_summary": "One concise business-friendly paragraph summarizing what this video teaches.",
  "key_concepts": ["concept 1", "concept 2", "concept 3", "concept 4", "concept 5"],
  "key_learnings": ["learning 1", "learning 2", "learning 3", "learning 4", "learning 5"],
  "technologies": ["technology 1", "technology 2"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "suggested_questions": [
    "Question a user might ask that this video answers?",
    "Another question?",
    "Another question?",
    "Another question?"
  ]
}}

Rules:
- Return ONLY valid JSON. No explanation, no markdown fences.
- key_concepts: core ideas or techniques demonstrated.
- key_learnings: concrete skills or takeaways a viewer gains.
- technologies: specific tools, platforms, languages, or services mentioned.
- keywords: short terms useful for search and vector filtering.
- suggested_questions: natural language questions a user might enter in a RAG system.

Video Title: {title}
Playlist: {playlist}
Channel: {channel}

Transcript:
{transcript}
"""

_PLAYLIST_PROMPT = """\
You are a knowledge engineer building a RAG knowledge base from a YouTube playlist.

Given the playlist title, channel, and a list of video titles with their summaries, return a JSON object:

{{
  "playlist_summary": "A high-level business-friendly paragraph describing what this playlist covers.",
  "major_topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"],
  "recommended_learning_path": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ...",
    "Step 4: ...",
    "Step 5: ..."
  ]
}}

Rules:
- Return ONLY valid JSON. No explanation, no markdown fences.

Playlist Title: {playlist_title}
Channel: {channel}

Videos:
{video_summaries}
"""


# ─── Enrichment engine ────────────────────────────────────────────────────────

class EnrichmentEngine:
    def __init__(self, provider: LLMProvider, cache_dir: Path = CACHE_DIR) -> None:
        self.provider = provider
        self.cache_dir = cache_dir

    def enrich_video(self, parsed: dict[str, Any]) -> dict[str, Any]:
        video_id = parsed.get("video_id", "")
        cache_path = self.cache_dir / f"{video_id}.json"

        if cache_path.exists():
            log.info("CACHE HIT")
            return json.loads(cache_path.read_text(encoding="utf-8"))

        log.info("CACHE MISS")
        transcript = parsed.get("transcript", "")
        if len(transcript) > 12000:
            transcript = transcript[:12000] + "... [truncated]"
        prompt = _VIDEO_PROMPT.format(
            title=parsed.get("title", ""),
            playlist=parsed.get("playlist", ""),
            channel=parsed.get("channel", ""),
            transcript=transcript,
        )
        enrichment = self._parse_json(self.provider.complete(prompt))

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(enrichment, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return enrichment

    def enrich_playlist(
        self,
        playlist_title: str,
        channel: str,
        video_enrichments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        summaries = "\n".join(
            f"- {e.get('title', '')}: {e.get('enrichment', {}).get('executive_summary', '')}"
            for e in video_enrichments
        )
        prompt = _PLAYLIST_PROMPT.format(
            playlist_title=playlist_title,
            channel=channel,
            video_summaries=summaries,
        )
        return self._parse_json(self.provider.complete(prompt))

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
        clean = re.sub(r"```\s*$", "", clean.strip(), flags=re.MULTILINE)
        try:
            return json.loads(clean.strip())
        except json.JSONDecodeError as exc:
            log.warning(f"  -> JSON parse error: {exc}")
            return {}


# ─── Markdown writer ──────────────────────────────────────────────────────────

class MarkdownWriter:
    def write_video(
        self,
        parsed: dict[str, Any],
        enrichment: dict[str, Any],
        out_path: Path,
    ) -> None:
        video_id = parsed.get("video_id", "")
        title = parsed.get("title", "")
        url = parsed.get("url", "")
        duration = parsed.get("duration", "")
        playlist = parsed.get("playlist", "")
        channel = parsed.get("channel", "")
        transcript = parsed.get("transcript", "")

        keywords = enrichment.get("keywords", [])
        technologies = enrichment.get("technologies", [])

        fm_keywords = "\n".join(f"  - {k}" for k in keywords)
        fm_technologies = "\n".join(f"  - {t}" for t in technologies)

        lines: list[str] = [
            "---",
            f"video_id: {video_id}",
            f"playlist: {playlist}",
            f"channel: {channel}",
            "keywords:",
            fm_keywords,
            "technologies:",
            fm_technologies,
            "---",
            "",
            f"# {title}",
            "",
            "## Metadata",
            "",
            "Video ID:",
            video_id,
            "",
            "Video URL:",
            f"[Watch video]({url})",
            "",
            "Duration:",
            f"{duration} seconds",
            "",
            "Playlist:",
            playlist,
            "",
            "Channel:",
            channel,
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            enrichment.get("executive_summary", "_Not available._"),
            "",
            "---",
            "",
            "## Key Concepts",
            "",
        ]
        for c in enrichment.get("key_concepts", []):
            lines.append(f"- {c}")
        lines += ["", "---", "", "## Key Learnings", ""]
        for learning in enrichment.get("key_learnings", []):
            lines.append(f"- {learning}")
        lines += ["", "---", "", "## Technologies", ""]
        for t in technologies:
            lines.append(f"- {t}")
        lines += [
            "",
            "---",
            "",
            "## Keywords",
            "",
            ", ".join(keywords),
            "",
            "---",
            "",
            "## Suggested Questions",
            "",
        ]
        for q in enrichment.get("suggested_questions", []):
            lines.append(f"- {q}")
        lines += ["", "---", "", "## Transcript", "", transcript, ""]

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")

    def write_playlist(
        self,
        playlist_title: str,
        channel: str,
        description: str,
        enrichment: dict[str, Any],
        video_enrichments: list[dict[str, Any]],
        out_path: Path,
    ) -> None:
        lines: list[str] = [
            f"# {playlist_title}",
            "",
            "## Playlist Summary",
            "",
            enrichment.get("playlist_summary", "_Not available._"),
            "",
            "## Major Topics",
            "",
        ]
        for topic in enrichment.get("major_topics", []):
            lines.append(f"- {topic}")
        lines += ["", "## Recommended Learning Path", ""]
        for step in enrichment.get("recommended_learning_path", []):
            lines.append(step)
        lines += [
            "",
            "---",
            "",
            "## Playlist Information",
            "",
            "Channel:",
            channel,
            "",
            "Description:",
            description,
            "",
            "---",
            "",
            "## Video Catalog",
            "",
        ]
        for i, ve in enumerate(video_enrichments, start=1):
            vid = ve.get("video_id", "")
            vt = ve.get("title", "")
            vurl = ve.get("url", "")
            lines += [
                f"### {i}. {vt}",
                "",
                f"[Watch video]({vurl})",
                "",
                f"[Enriched Notes](../videos/{vid}.md)",
                "",
            ]

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def save_manifest(
    playlist_title: str,
    records: list[dict[str, str]],
    manifest_file: Path = MANIFEST_FILE,
) -> None:
    manifest = {
        "playlist": playlist_title,
        "videos_processed": len(records),
        "enriched_files": records,
    }
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _read_windows_user_env(name: str) -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value or ""
    except Exception:
        return ""


def build_provider() -> LLMProvider:
    _ENV_VAR = "GEMINI_API_KEY_RAG_YOUTUBE"
    api_key = os.environ.get(_ENV_VAR, "") or _read_windows_user_env(_ENV_VAR)
    if not api_key:
        raise EnvironmentError(
            f"{_ENV_VAR} environment variable is not set.\n"
            "Add it to your Windows User Environment Variables."
        )
    return GeminiProvider(api_key=api_key)


# ─── Main ─────────────────────────────────────────────────────────────────────

def process_source(
    source: str,
    cfg: dict[str, Path],
    provider: LLMProvider,
    parser: MarkdownParser,
    writer: MarkdownWriter,
    limit: int | None,
) -> None:
    metadata_file = cfg["metadata_file"]
    if not metadata_file.exists():
        log.warning(f"Skipping {source}: metadata file not found: {metadata_file}")
        return

    video_files = sorted(cfg["videos_dir"].glob("*.md"))
    if not video_files:
        log.warning(f"Skipping {source}: no markdown files in {cfg['videos_dir']}")
        return

    engine = EnrichmentEngine(provider, cache_dir=cfg["cache_dir"])

    playlist_meta: dict[str, Any] = json.loads(
        metadata_file.read_text(encoding="utf-8")
    )
    playlist_title: str = playlist_meta.get("title", "Playlist")
    channel: str = playlist_meta.get("channel", "")
    description: str = (playlist_meta.get("description") or "").strip()

    if limit is not None:
        print("TEST MODE ENABLED")
        print(f"Processing first {limit} videos")
        video_files = video_files[:limit]
    total = len(video_files)

    success = 0
    failed = 0
    manifest_records: list[dict[str, str]] = []
    all_enrichments: list[dict[str, Any]] = []

    for i, md_path in enumerate(video_files, start=1):
        log.info(f"[{i}/{total}] Enriching: {md_path.name}")
        try:
            parsed = parser.parse_video(md_path)
            enrichment = engine.enrich_video(parsed)
            out_path = cfg["enriched_videos_dir"] / md_path.name
            writer.write_video(parsed, enrichment, out_path)

            video_id = parsed.get("video_id", md_path.stem)
            rel = str(out_path.relative_to(ROOT)).replace("\\", "/")
            manifest_records.append({"video_id": video_id, "file": rel})
            all_enrichments.append(
                {
                    "video_id": video_id,
                    "title": parsed.get("title", ""),
                    "url": parsed.get("url", ""),
                    "enrichment": enrichment,
                }
            )
            success += 1
        except Exception as exc:
            log.warning(f"  -> Failed: {exc}")
            failed += 1

    log.info("Generating playlist enrichment...")
    playlist_files = 0
    try:
        playlist_enrichment = engine.enrich_playlist(
            playlist_title, channel, all_enrichments
        )
        slug = slugify(playlist_title)
        playlist_out = cfg["enriched_playlists_dir"] / f"{slug}.md"
        writer.write_playlist(
            playlist_title,
            channel,
            description,
            playlist_enrichment,
            all_enrichments,
            playlist_out,
        )
        playlist_files = 1
    except Exception as exc:
        log.warning(f"Playlist enrichment failed: {exc}")

    save_manifest(playlist_title, manifest_records, cfg["manifest_file"])

    print()
    print("=================================")
    print(f"Enrichment Complete ({source})")
    print("=================================")
    print(f"Videos Processed : {success}")
    print(f"Videos Failed    : {failed}")
    print(f"Playlist Files   : {playlist_files}")
    print(f"Index Created    : Yes")


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Enrich video markdown with LLM metadata.")
    arg_parser.add_argument("--limit", type=int, default=None, metavar="N",
                            help="Process only the first N videos.")
    arg_parser.add_argument("--source", choices=["youtube", "linkedin", "all"],
                            default="youtube",
                            help="Content source to enrich (default: youtube).")
    args = arg_parser.parse_args()

    parser = MarkdownParser()
    provider = build_provider()
    log.info("Using provider: Gemini")
    log.info(f"Model: {provider.model}")
    writer = MarkdownWriter()

    sources = ["youtube", "linkedin"] if args.source == "all" else [args.source]
    for source in sources:
        log.info(f"--- Source: {source} ---")
        process_source(source, SOURCE_CONFIGS[source], provider, parser, writer, args.limit)


if __name__ == "__main__":
    main()
