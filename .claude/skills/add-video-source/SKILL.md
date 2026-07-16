---
name: add-video-source
description: Add a new video content source (e.g., MS Teams, TikTok, Vimeo) to the RAG pipeline. Creates the source-symmetric directory layout, importer script, SOURCE_CONFIGS entry, and documentation updates. Use when the user wants to ingest videos from a new platform.
---

# Add a New Video Source

This project ingests video content from multiple sources into one RAG knowledge base. Every source follows the same source-symmetric layout and converges at `scripts/enrich_markdown.py`. Follow these steps in order.

## Step 0 — Classify the source first

Ask (or determine) two things before writing any code:

1. **How are transcripts obtained?**
   - *Automated* (public API/tool, like YouTube via `youtube-transcript-api`): write an extractor script.
   - *Manual* (no API, or ToS forbids scraping — LinkedIn Learning, most paid platforms): follow the manifest + copied-transcripts pattern of `scripts/import_linkedin_course.py`.
   - *No transcripts exist* (e.g., TikTok, raw video files): the source needs a transcription step (e.g., Whisper) before import — flag this and design that step first.

2. **Is the content licensed/private?** MS Teams recordings, LinkedIn Learning courses, and any corporate or paid content must NEVER be committed to git. The `.gitignore` already excludes all data dirs (`markdown/`, `transcripts/`, `metadata/`, `cache/`, `index/`) — verify the new source's files fall under those rules before the first commit, and check `git status` output after staging. Public YouTube/TikTok metadata is fine; transcripts of paid/private content are not.

## Step 1 — Create the directory layout

For a source named `{source}` (short lowercase identifier, e.g. `msteams`, `tiktok`):

```
metadata/{source}/          # manifest or extracted metadata JSON
transcripts/{source}/       # transcripts (.json if automated, .txt if manual)
markdown/{source}/videos/   # generated plain markdown (created by importer)
```

Enriched output, cache, and manifest dirs are created automatically by the enrichment script.

## Step 2 — Produce input markdown in the standard schema

Write either an extractor (`scripts/extract_{source}_*.py`) or an importer (`scripts/import_{source}_*.py`, modeled on `scripts/import_linkedin_course.py`) that emits one file per video at `markdown/{source}/videos/{id}.md` with EXACTLY this structure (the regex parser in `enrich_markdown.py` depends on it):

```
# {title}

## Metadata

Video ID: {id}

Video URL:
{url}

Duration (seconds):
{integer}

Playlist:
{playlist_or_course_title}

Channel:
{channel_or_author}

## Transcript

{transcript text}
```

The metadata JSON in `metadata/{source}/` must contain at least `title`, `channel`, and optionally `description` — the enrichment stage reads these for the playlist-level summary.

## Step 3 — Register the source in enrich_markdown.py

Add one entry to `SOURCE_CONFIGS` in `scripts/enrich_markdown.py`:

```python
"{source}": {
    "videos_dir": ROOT / "markdown" / "{source}" / "videos",
    "metadata_file": ROOT / "metadata" / "{source}" / "{manifest}.json",
    "enriched_videos_dir": ENRICHED_DIR / "{source}" / "videos",
    "enriched_playlists_dir": ENRICHED_DIR / "{source}" / "playlists",
    "manifest_file": INDEX_DIR / "enriched_manifest_{source}.json",
    "cache_dir": CACHE_DIR / "{source}",
},
```

The `--source` CLI flag picks up new entries automatically (choices are derived from `SOURCE_CONFIGS`).

## Step 4 — Test

```powershell
py -m py_compile scripts\enrich_markdown.py scripts\{new_script}.py
py scripts\{new_script}.py                          # import/extract
py scripts\enrich_markdown.py --source {source} --limit 1   # one cheap API call
py scripts\enrich_markdown.py --source {source}             # full run
```

Verify: YAML front-matter present in enriched output, `CACHE HIT` on a second run, per-lesson URLs clickable, and `[Enriched Notes]` links resolve.

## Step 5 — Update documentation

- `README.md` — features list, folder-structure tree, usage section
- `docs/architecture.md` — SOURCE_CONFIGS table, Mermaid diagram branch, data-flow table
- `docs/pipeline.md` — new source section (model on "Alternate Source — LinkedIn Learning")
- `docs/folder-structure.md` — tree
- `docs/quickstart.md` — optional step section
- `CHANGELOG.md` — new version entry
- New `docs/{source}-import.md` if the workflow has manual steps

## Step 6 — Commit

Stage, then check `git status` — confirm no transcript/markdown data files are staged (only `scripts/`, `docs/`, `.claude/`, and root config files should appear). Commit and push.

## Source-specific notes

- **MS Teams**: recordings live in OneDrive/SharePoint via Stream. Transcripts are downloadable as `.vtt` from the Stream player (Video settings → Transcript → Download) when the owner enabled transcription. Strip VTT timestamps on import. Corporate content — manual import pattern, never commit transcripts.
- **TikTok**: `yt-dlp` extracts metadata and can list auto-captions when present, but most TikToks have none — plan a Whisper transcription step. Public content, but keep generated transcripts out of git anyway (data dirs are ignored).
- **Vimeo**: API provides captions for videos that have them; availability varies per video.
