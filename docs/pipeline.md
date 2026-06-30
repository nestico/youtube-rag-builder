# Pipeline

## Stage 1 — Playlist Metadata Extraction

**Script:** `scripts/extract_playlist.py`  
**Input:** YouTube playlist URL (hardcoded in script)  
**Output:** `metadata/command_bar_playlist.json`

Uses `yt-dlp` with `extract_flat=True` to fetch playlist metadata without downloading videos. The output JSON includes the playlist title, channel name, description, and a list of video entries (id, title, url, duration).

```bash
py scripts/extract_playlist.py
```

**Key fields in output:**
```json
{
  "title": "Power Apps - Command Bar",
  "channel": "Microsoft Power Apps",
  "entries": [
    { "id": "abc123", "title": "...", "url": "...", "duration": 312 }
  ]
}
```

---

## Stage 2 — Transcript Extraction

**Script:** `scripts/extract_all_transcripts.py`  
**Input:** `metadata/command_bar_playlist.json`  
**Output:** `transcripts/{video_id}.json`, `index/videos.csv`, `index/videos.json`

Iterates every video in the playlist metadata and calls `YouTubeTranscriptApi` to fetch the auto-generated or manual transcript. Each transcript is saved as a JSON array of `{text, start, duration}` segments.

Videos without available transcripts are marked `FAILED` in the index but do not stop the pipeline.

```bash
py scripts/extract_all_transcripts.py
```

**Transcript segment format:**
```json
[
  { "text": "welcome to this tutorial", "start": 0.0, "duration": 3.2 },
  { "text": "today we'll look at...",   "start": 3.2, "duration": 2.8 }
]
```

---

## Stage 3 — Markdown Generation

**Script:** `scripts/generate_markdown.py`  
**Input:** `metadata/command_bar_playlist.json` + `transcripts/*.json`  
**Output:** `markdown/videos/{video_id}.md`, `markdown/playlists/{slug}.md`, `markdown/index.md`, `index/markdown_manifest.json`

Merges each transcript into a single continuous text, deduplicating consecutive repeated segments. Generates one markdown file per video and one playlist index file.

```bash
py scripts/generate_markdown.py
```

**Video markdown structure:**
```
# {title}

## Metadata
Video ID: ...
Video URL: ...
Duration (seconds): ...
Playlist: ...
Channel: ...

## Transcript
{merged transcript text}
```

---

## Stage 4 — AI Enrichment

**Script:** `scripts/enrich_markdown.py`  
**Input:** `markdown/videos/*.md`  
**Output:** `markdown/enriched/videos/*.md`, `markdown/enriched/playlists/*.md`, `cache/enrichment/*.json`, `index/enriched_manifest.json`

The most complex stage. For each video markdown file:

1. **Parse** — `MarkdownParser` extracts title, video_id, transcript, and metadata via regex
2. **Cache check** — looks for `cache/enrichment/{video_id}.json`; loads and skips API call on hit
3. **Enrich** — on cache miss, sends a structured prompt to Gemini 2.5 Pro requesting JSON output
4. **Save cache** — writes raw JSON response to `cache/enrichment/{video_id}.json`
5. **Write enriched markdown** — `MarkdownWriter` produces a fully structured file with YAML front-matter
6. **Playlist enrichment** — after all videos, sends a playlist-level prompt summarising all video summaries

```bash
# Full run
py scripts/enrich_markdown.py

# Test run (first N videos only)
py scripts/enrich_markdown.py --limit 3
```

### Enrichment Prompt — Video

The video prompt requests a JSON object with:

| Field | Description |
|---|---|
| `executive_summary` | Business-friendly paragraph summary |
| `key_concepts` | Core ideas or techniques demonstrated |
| `key_learnings` | Concrete skills a viewer gains |
| `technologies` | Tools, platforms, languages, services mentioned |
| `keywords` | Short terms for search and vector filtering |
| `suggested_questions` | Natural language questions a RAG system should answer |

### Enrichment Prompt — Playlist

The playlist prompt requests:

| Field | Description |
|---|---|
| `playlist_summary` | High-level description of what the playlist covers |
| `major_topics` | Top-level topics across all videos |
| `recommended_learning_path` | Ordered steps for working through the playlist |

### Cache Behaviour

```
enrich_video(parsed)
    │
    ├── cache hit?  ──YES──► return cached dict
    │
    └── NO ──► call Gemini ──► save to cache ──► return dict
```

Cached files persist across runs. Delete `cache/enrichment/` to force a full re-enrichment.
