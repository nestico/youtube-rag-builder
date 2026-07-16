# Architecture

## Overview

youtube-rag-builder is a sequential data pipeline. Each stage is an independent Python script that reads from one directory and writes to another. Stages can be re-run independently — for example, re-running enrichment on already-generated markdown without re-downloading transcripts.

The pipeline supports two content sources that converge at the enrichment stage:

- **YouTube** — fully automated (yt-dlp + youtube-transcript-api)
- **LinkedIn Learning** — manifest-driven manual import (transcripts copied from the Transcript tab under the subscriber's licensed seat; automated scraping is not supported as it violates LinkedIn's ToS)

---

## Pipeline Stages

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PIPELINE STAGES                              │
│                                                                      │
│  ┌─────────────┐                                                     │
│  │  YouTube    │                                                     │
│  │  Playlist   │  URL                                                │
│  │  (source)   │                                                     │
│  └──────┬──────┘                                                     │
│         │ yt-dlp                                                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │  Stage 1    │  extract_playlist.py                                │
│  │  Metadata   │──► metadata/youtube/command_bar_playlist.json               │
│  │  Extraction │                                                     │
│  └──────┬──────┘                                                     │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │  Stage 2    │  extract_all_transcripts.py                         │
│  │  Transcript │──► transcripts/youtube/{video_id}.json                      │
│  │  Extraction │──► index/videos.csv                                 │
│  └──────┬──────┘──► index/videos.json                               │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │  Stage 3    │  generate_markdown.py                               │
│  │  Markdown   │──► markdown/youtube/videos/{video_id}.md                   │
│  │  Generation │──► markdown/youtube/playlists/{slug}.md            │
│  └──────┬──────┘──► markdown/youtube/index.md                       │
│         │           index/markdown_manifest.json                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │  Stage 4    │  enrich_markdown.py                                 │
│  │  AI         │──► markdown/enriched/videos/{video_id}.md           │
│  │  Enrichment │──► markdown/enriched/playlists/{slug}.md            │
│  │  (Gemini)   │──► cache/enrichment/{video_id}.json                 │
│  └─────────────┘──► index/enriched_manifest_{source}.json           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Mermaid Diagram

```mermaid
flowchart TD
    YT([🎬 YouTube Playlist URL])

    subgraph S1["Stage 1 — extract_playlist.py"]
        direction TB
        A1[yt-dlp\nextract_flat]
    end

    subgraph S2["Stage 2 — extract_all_transcripts.py"]
        direction TB
        A2[youtube-transcript-api]
    end

    subgraph S3["Stage 3 — generate_markdown.py"]
        direction TB
        A3[Merge transcripts\nGenerate markdown]
    end

    subgraph S4["Stage 4 — enrich_markdown.py"]
        direction TB
        P[MarkdownParser]
        C{Cache hit?}
        G[Gemini 2.5 Pro]
        E[EnrichmentEngine]
        W[MarkdownWriter]

        P --> C
        C -->|YES — load JSON| W
        C -->|NO| G
        G --> E
        E -->|save JSON| CACHE[(cache/enrichment/\nvideo_id.json)]
        E --> W
    end

    LI([💼 LinkedIn Learning Course])
    subgraph SL["LinkedIn import — import_linkedin_course.py"]
        direction TB
        M[Course manifest JSON\n+ copied transcripts]
    end

    YT --> S1
    S1 -->|metadata/youtube/command_bar_playlist.json| S2
    S2 -->|transcripts/youtube/video_id.json| S3
    S3 -->|markdown/youtube/videos/video_id.md| S4
    LI -->|Transcript tab, manual copy| SL
    SL -->|markdown/linkedin/videos/slug.md| S4

    S4 --> R1[(markdown/enriched/\nsource/videos/)]
    S4 --> R2[(markdown/enriched/\nsource/playlists/)]
    S4 --> R3[(index/\nenriched manifests)]
```

---

## Component Design

### Scripts

Each script is self-contained and follows the same structural pattern:

- Path constants at the top (`ROOT`, `VIDEOS_DIR`, etc.)
- Pure functions or classes for data transformation
- A `main()` function as the entry point
- `if __name__ == "__main__": main()`

### Provider Pattern (`enrich_markdown.py`)

The enrichment script uses a provider abstraction to decouple the pipeline from any specific LLM vendor:

```
LLMProvider (abstract)
    │
    ├── GeminiProvider        ← active
    ├── ClaudeProvider        ← implemented, not wired
    ├── AzureOpenAIProvider   ← stub
    └── OpenAIProvider        ← stub
```

`build_provider()` is the single wiring point — swapping providers requires changing one function.

### Source Configuration (`enrich_markdown.py`)

`SOURCE_CONFIGS` maps each content source to its own set of paths:

| Path | youtube | linkedin |
|---|---|---|
| Input markdown | `markdown/youtube/videos/` | `markdown/linkedin/videos/` |
| Metadata | `metadata/youtube/command_bar_playlist.json` | `metadata/linkedin/pl400_cert_prep.json` |
| Enriched output | `markdown/enriched/youtube/` | `markdown/enriched/linkedin/` |
| Cache | `cache/enrichment/youtube/` | `cache/enrichment/linkedin/` |
| Manifest | `index/enriched_manifest_youtube.json` | `index/enriched_manifest_linkedin.json` |

The `--source` CLI flag selects which sources to process (`youtube` is the default; `all` runs both). Adding a new source is one new entry in `SOURCE_CONFIGS` plus a way to produce its input markdown.

### Cache Layer

Enrichment responses are cached as JSON files keyed by `video_id`:

```
cache/enrichment/{video_id}.json
```

On each run, `EnrichmentEngine.enrich_video()` checks for a cache hit before calling the LLM. This prevents redundant API calls when re-running the pipeline.

### YAML Front-matter

Enriched video files include a YAML front-matter block at the top, enabling metadata-based filtering in vector databases:

```yaml
---
video_id: abc123
playlist: Power Apps - Command Bar
channel: Microsoft Power Apps
keywords:
  - command bar
technologies:
  - Power Apps
---
```

---

## Data Flow Summary

| Stage | Input | Output |
|---|---|---|
| extract_playlist | YouTube URL | `metadata/*.json` |
| extract_all_transcripts | `metadata/*.json` | `transcripts/*.json`, `index/videos.*` |
| generate_markdown | `metadata/youtube/*.json` + `transcripts/youtube/*.json` | `markdown/youtube/**` |
| import_linkedin_course | `metadata/linkedin/*.json` + `transcripts/linkedin/*.txt` | `markdown/linkedin/videos/**` |
| enrich_markdown | per-source markdown dirs | per-source `markdown/enriched/**`, `cache/**`, manifests |

---

## Design Principles

- **Sequential, not coupled** — each stage reads files from disk; no in-memory passing between stages
- **Idempotent** — re-running any stage overwrites previous output safely
- **Cache-friendly** — enrichment is expensive; the cache layer makes re-runs free for already-processed videos
- **Provider-agnostic** — the enrichment engine works with any LLM via the `LLMProvider` interface
