# youtube-rag-builder

A pipeline that turns a YouTube playlist into a fully enriched RAG knowledge base — extracting transcripts, generating structured markdown, and enriching content with AI-generated summaries, key concepts, keywords, and suggested questions ready for vector database ingestion.

---

## Overview

```
YouTube Playlist
      │
      ▼
 Metadata Extraction  ──► metadata/
      │
      ▼
 Transcript Extraction ──► transcripts/
      │
      ▼
 Markdown Generation  ──► markdown/videos/
      │                   markdown/playlists/
      ▼
 AI Enrichment        ──► markdown/enriched/videos/
  (Gemini 2.5 Pro)        markdown/enriched/playlists/
      │
      ├──► cache/enrichment/     (JSON response cache)
      │
      └──► index/                (manifests & indexes)
```

---

## Features

- Extract YouTube playlist metadata via `yt-dlp`
- Download video transcripts via `youtube-transcript-api`
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
│   └── enrichment/          # Cached Gemini responses (JSON per video)
│
├── docs/                    # Project documentation
│   ├── architecture.md
│   ├── folder-structure.md
│   ├── pipeline.md
│   └── quickstart.md
│
├── index/
│   └── enriched_manifest.json   # Enrichment manifest for RAG ingestion
│
├── markdown/
│   └── enriched/
│       ├── playlists/       # AI-enriched playlist summaries
│       └── videos/          # AI-enriched video markdown (YAML front-matter)
│
├── metadata/                # Raw playlist metadata JSON (yt-dlp output)
│
├── transcripts/             # Raw video transcripts (JSON per video)
│
├── scripts/
│   ├── extract_playlist.py        # Step 1: Extract playlist metadata
│   ├── extract_all_transcripts.py # Step 2: Download transcripts
│   ├── generate_markdown.py       # Step 3: Generate markdown files
│   └── enrich_markdown.py         # Step 4: AI enrichment pipeline
│
└── requirements.txt
```

---

## Installation

**Requirements:** Python 3.11+

```bash
git clone https://github.com/your-username/youtube-rag-builder.git
cd youtube-rag-builder
pip install -r requirements.txt
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

Run each step in sequence:

```bash
# Step 1 — Extract playlist metadata
py scripts/extract_playlist.py

# Step 2 — Download transcripts
py scripts/extract_all_transcripts.py

# Step 3 — Generate markdown
py scripts/generate_markdown.py

# Step 4 — Enrich with AI (all videos)
py scripts/enrich_markdown.py

# Step 4 — Enrich with AI (limit for testing)
py scripts/enrich_markdown.py --limit 3
```

See [docs/quickstart.md](docs/quickstart.md) for a full walkthrough.

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

- [ ] Supabase vector database integration
- [ ] Azure OpenAI provider implementation
- [ ] OpenAI provider implementation
- [ ] Anthropic Claude provider implementation
- [ ] Incremental enrichment (skip already-enriched videos)
- [ ] Web UI for browsing the knowledge base
- [ ] Multi-playlist support
- [ ] Chunking strategy for large transcripts
- [ ] Embedding generation pipeline

---

## License

MIT — see [LICENSE](LICENSE)
