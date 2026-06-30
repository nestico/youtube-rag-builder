# Folder Structure

```
youtube-rag-builder/
│
├── cache/
│   └── enrichment/
│       └── {video_id}.json        # Cached Gemini enrichment response per video
│
├── docs/
│   ├── architecture.md            # System architecture and design
│   ├── folder-structure.md        # This file
│   ├── pipeline.md                # Detailed pipeline stage documentation
│   └── quickstart.md              # Step-by-step setup and usage guide
│
├── index/
│   ├── enriched_manifest.json     # List of all enriched files (RAG ingestion input)
│   ├── markdown_manifest.json     # List of all generated markdown files
│   ├── videos.csv                 # Transcript extraction results (CSV)
│   └── videos.json                # Transcript extraction results (JSON)
│
├── markdown/
│   ├── index.md                   # Top-level knowledge base index
│   ├── playlists/
│   │   └── {slug}.md              # Plain playlist markdown (video list)
│   ├── videos/
│   │   └── {video_id}.md          # Plain video markdown (metadata + transcript)
│   └── enriched/
│       ├── playlists/
│       │   └── {slug}.md          # AI-enriched playlist summary
│       └── videos/
│           └── {video_id}.md      # AI-enriched video (YAML front-matter + sections)
│
├── metadata/
│   └── command_bar_playlist.json  # Raw playlist metadata from yt-dlp
│
├── transcripts/
│   └── {video_id}.json            # Raw transcript segments from YouTube
│
├── scripts/
│   ├── extract_playlist.py        # Stage 1: Playlist metadata extraction
│   ├── extract_all_transcripts.py # Stage 2: Transcript download
│   ├── generate_markdown.py       # Stage 3: Markdown generation
│   └── enrich_markdown.py         # Stage 4: AI enrichment pipeline
│
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Directory Purposes

### `cache/enrichment/`

Stores the raw JSON response from Gemini for each video, keyed by `video_id`. Prevents redundant API calls on repeated runs. Safe to delete if you want to force re-enrichment.

### `docs/`

Project documentation. All files are written in Markdown and rendered automatically by GitHub.

### `index/`

Manifest and index files consumed by downstream systems (vector databases, search indexes, RAG pipelines). The most important file for integration is `enriched_manifest.json`.

### `markdown/videos/`

Plain markdown generated from transcripts. Input to the enrichment stage. Each file contains video metadata and the full merged transcript.

### `markdown/enriched/videos/`

The primary output of the pipeline. Each file has:
- YAML front-matter with `video_id`, `playlist`, `channel`, `keywords`, `technologies`
- AI-generated sections: executive summary, key concepts, key learnings, technologies, keywords, suggested questions
- Full original transcript appended at the bottom

These files are the intended input for vector database ingestion.

### `metadata/`

Raw JSON output from `yt-dlp`. Contains all playlist and video metadata. Not committed to git by default (see `.gitignore`).

### `transcripts/`

Raw transcript JSON from `youtube-transcript-api`. One file per video. Not committed to git by default.

### `scripts/`

All pipeline scripts. Each is independently runnable. See [docs/pipeline.md](pipeline.md) for per-script documentation.

---

## What Gets Committed to Git

By default, `.gitignore` excludes generated data directories (`transcripts/`, `metadata/`, `cache/`, `markdown/`, `index/`) since they are reproducible from source. Only the scripts, documentation, and configuration files are committed.

To share enriched output with collaborators, selectively remove exclusions from `.gitignore`.
