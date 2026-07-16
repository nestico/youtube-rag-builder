# youtube-rag-builder

A pipeline that turns YouTube playlists and LinkedIn Learning courses into a fully enriched RAG knowledge base — extracting transcripts, generating structured markdown, and enriching content with AI-generated summaries, key concepts, keywords, and suggested questions ready for vector database ingestion.

---

## Overview

```
YouTube Playlist                     LinkedIn Learning Course
      │  (automated)                       │  (manual import,
      ▼                                    │   licensed seat)
 Metadata Extraction ──► metadata/youtube/ ▼
      │                              Course manifest + copied
      ▼                              transcripts
 Transcript Extraction ──►                 │
      │       transcripts/youtube/         ▼
      ▼                              import_linkedin_course.py
 Markdown Generation ──►                   │
      │       markdown/youtube/videos/     ▼
      │                     markdown/linkedin/videos/
      │                                    │
      └────────────────┬───────────────────┘
                       ▼
              AI Enrichment (Gemini 2.5 Pro)
                       │
       ├──► markdown/enriched/            (per-source outputs)
       ├──► cache/enrichment/             (JSON response cache)
       └──► index/                        (manifests & indexes)
```

---

## Features

- Extract YouTube playlist metadata via `yt-dlp`
- Download video transcripts via `youtube-transcript-api`
- Import LinkedIn Learning courses via manifest + manually copied transcripts (ToS-compliant, uses your licensed seat)
- Multi-source enrichment: `--source youtube | linkedin | all`
- Generate structured markdown files per video and per playlist
- Enrich markdown with AI using Google Gemini:
  - Executive summary
  - Key concepts
  - Key learnings
  - Technologies mentioned
  - Keywords for vector filtering
  - Suggested RAG questions
- Cache enrichment responses to avoid redundant API calls
- Generate playlist-level AI summaries with major topics and learning paths
- Build JSON manifests for downstream RAG pipeline integration
- Provider architecture supports future OpenAI / Azure / Anthropic integration

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     youtube-rag-builder                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  YouTube     │    │  Transcript  │    │  Markdown        │  │
│  │  Playlist    │───►│  Extraction  │───►│  Generation      │  │
│  │  (yt-dlp)    │    │  (yt api)    │    │  (structured)    │  │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘  │
│                                                   │             │
│                                                   ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  RAG Ready   │    │  JSON        │    │  AI Enrichment   │  │
│  │  Knowledge   │◄───│  Manifests   │◄───│  (Gemini 2.5)    │  │
│  │  Base        │    │  & Index     │    │  + Cache Layer   │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
youtube-rag-builder/
│
├── cache/
│   └── enrichment/
│       ├── youtube/         # Cached Gemini responses (YouTube videos)
│       └── linkedin/        # Cached Gemini responses (LinkedIn lessons)
│
├── docs/                    # Project documentation
│   ├── architecture.md
│   ├── folder-structure.md
│   ├── linkedin-import.md
│   ├── pipeline.md
│   └── quickstart.md
│
├── index/
│   ├── enriched_manifest_youtube.json   # YouTube enrichment manifest
│   └── enriched_manifest_linkedin.json  # LinkedIn enrichment manifest
│
├── markdown/                # Generated at pipeline runtime
│   ├── youtube/
│   │   ├── videos/          # Plain video markdown (YouTube)
│   │   └── playlists/       # Plain playlist markdown (YouTube)
│   ├── linkedin/
│   │   └── videos/          # Plain lesson markdown (LinkedIn)
│   └── enriched/
│       ├── youtube/
│       │   ├── playlists/   # AI-enriched playlist summaries (YouTube)
│       │   └── videos/      # AI-enriched video markdown (YouTube)
│       └── linkedin/
│           ├── playlists/   # AI-enriched course summary (LinkedIn)
│           └── videos/      # AI-enriched lesson markdown (LinkedIn)
│
├── metadata/
│   ├── youtube/             # Playlist metadata (generated by yt-dlp)
│   └── linkedin/            # LinkedIn course manifests (hand-authored)
│
├── transcripts/
│   ├── youtube/             # Raw video transcripts (generated JSON)
│   └── linkedin/            # Manually copied LinkedIn transcripts (.txt)
│
├── scripts/
│   ├── extract_playlist.py        # Step 1: Extract playlist metadata
│   ├── extract_all_transcripts.py # Step 2: Download transcripts
│   ├── generate_markdown.py       # Step 3: Generate markdown files
│   ├── import_linkedin_course.py  # LinkedIn: manifest + transcripts → markdown
│   └── enrich_markdown.py         # Step 4: AI enrichment (--source youtube|linkedin|all)
│
└── requirements.txt
```

> Data directories (`cache/`, `metadata/`, `transcripts/`, `markdown/`, `index/`) are generated at runtime and excluded from git — only scripts and docs are committed.

---

## Installation

**Requirements:** Python 3.11+

```powershell
git clone https://github.com/your-username/youtube-rag-builder.git
cd youtube-rag-builder
py -m pip install -r requirements.txt
```

---

## Setup — Gemini API Key

This project uses Google Gemini 2.5 Pro for AI enrichment.

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add it to your Windows User Environment Variables:
   - Variable name: `GEMINI_API_KEY_RAG_YOUTUBE`
   - Variable value: `AIzaSy...`

No code changes needed — the pipeline reads the key automatically.

---

## Usage

### YouTube pipeline

Run each step in sequence:

```powershell
# Step 1 — Extract playlist metadata
py scripts\extract_playlist.py

# Step 2 — Download transcripts
py scripts\extract_all_transcripts.py

# Step 3 — Generate markdown
py scripts\generate_markdown.py

# Step 4 — Enrich with AI (all videos)
py scripts\enrich_markdown.py

# Step 4 — Enrich with AI (limit for testing)
py scripts\enrich_markdown.py --limit 3
```

### LinkedIn Learning course

Fill in the course manifest, copy transcripts from each lesson's Transcript tab, then:

```powershell
py scripts\import_linkedin_course.py
py scripts\enrich_markdown.py --source linkedin
```

Or enrich everything at once:

```powershell
py scripts\enrich_markdown.py --source all
```

See [docs/quickstart.md](docs/quickstart.md) for a full walkthrough and [docs/linkedin-import.md](docs/linkedin-import.md) for the LinkedIn workflow.

---

## Sample Enriched Output

Each enriched video file includes a YAML front-matter block for vector DB filtering:

```yaml
---
video_id: abc123
playlist: Power Apps - Command Bar
channel: Microsoft Power Apps
keywords:
  - command bar
  - power apps
  - canvas app
technologies:
  - Power Apps
  - Microsoft 365
---
```

Followed by structured sections:

- Executive Summary
- Key Concepts
- Key Learnings
- Technologies
- Keywords
- Suggested Questions (ready for RAG retrieval)
- Full Transcript

---

## Future Roadmap

- [x] Multi-source support (YouTube + LinkedIn Learning)
- [x] Incremental enrichment via response cache (already-enriched videos are free)
- [ ] Supabase vector database integration
- [ ] Azure OpenAI provider implementation
- [ ] OpenAI provider implementation
- [ ] Anthropic Claude provider implementation
- [ ] Web UI for browsing the knowledge base
- [ ] Multi-playlist support
- [ ] Chunking strategy for large transcripts
- [ ] Embedding generation pipeline
- [ ] Cross-source "hub" summaries (e.g., mapping cert modules to tutorial videos)

---

## License

MIT — see [LICENSE](LICENSE)
