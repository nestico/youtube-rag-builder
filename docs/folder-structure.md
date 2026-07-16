# Folder Structure

```
youtube-rag-builder/
│
├── cache/                         # Generated at runtime
│   └── enrichment/
│       ├── {video_id}.json        # Cached Gemini response per YouTube video
│       └── linkedin/
│           └── {slug}.json        # Cached Gemini response per LinkedIn lesson
│
├── docs/
│   ├── architecture.md            # System architecture and design
│   ├── folder-structure.md        # This file
│   ├── linkedin-import.md         # LinkedIn Learning import workflow
│   ├── pipeline.md                # Detailed pipeline stage documentation
│   └── quickstart.md              # Step-by-step setup and usage guide
│
├── index/                         # Generated at runtime
│   ├── enriched_manifest.json           # YouTube enrichment manifest
│   ├── enriched_manifest_linkedin.json  # LinkedIn enrichment manifest
│   ├── markdown_manifest.json           # Generated markdown files list
│   ├── videos.csv                       # Transcript extraction results (CSV)
│   └── videos.json                      # Transcript extraction results (JSON)
│
├── markdown/                      # Generated at runtime
│   ├── index.md                   # Top-level knowledge base index
│   ├── playlists/
│   │   └── {slug}.md              # Plain playlist markdown (video list)
│   ├── videos/
│   │   └── {video_id}.md          # Plain video markdown (metadata + transcript)
│   ├── linkedin/
│   │   └── videos/
│   │       └── {slug}.md          # Plain LinkedIn lesson markdown
│   └── enriched/
│       ├── playlists/
│       │   └── {slug}.md          # AI-enriched playlist summary (YouTube)
│       ├── videos/
│       │   └── {video_id}.md      # AI-enriched video (YouTube)
│       └── linkedin/
│           ├── playlists/
│           │   └── {slug}.md      # AI-enriched course summary (LinkedIn)
│           └── videos/
│               └── {slug}.md      # AI-enriched lesson (LinkedIn)
│
├── metadata/
│   ├── command_bar_playlist.json  # Raw playlist metadata from yt-dlp (generated)
│   └── linkedin/
│       └── pl400_cert_prep.json   # LinkedIn course manifest (hand-authored)
│
├── transcripts/
│   ├── {video_id}.json            # Raw YouTube transcript segments (generated)
│   └── linkedin/
│       └── {slug}.txt             # Manually copied LinkedIn transcripts
│
├── scripts/
│   ├── extract_playlist.py        # Stage 1: Playlist metadata extraction
│   ├── extract_all_transcripts.py # Stage 2: Transcript download
│   ├── generate_markdown.py       # Stage 3: Markdown generation
│   ├── import_linkedin_course.py  # LinkedIn: manifest + transcripts → markdown
│   └── enrich_markdown.py         # Stage 4: AI enrichment (multi-source)
│
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── requirements.txt
```

> Directories marked "generated at runtime" are excluded from git and appear after running the pipeline. `metadata/linkedin/` and `transcripts/linkedin/` are hand-authored inputs you create as part of the LinkedIn workflow.

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

### `markdown/enriched/linkedin/` and related `linkedin/` subdirectories

The LinkedIn Learning source mirrors the YouTube layout one level deeper: hand-authored manifest in `metadata/linkedin/`, manually copied transcripts in `transcripts/linkedin/`, generated lesson markdown in `markdown/linkedin/videos/`, and enriched output in `markdown/enriched/linkedin/`. See [linkedin-import.md](linkedin-import.md).

### `scripts/`

All pipeline scripts. Each is independently runnable. See [docs/pipeline.md](pipeline.md) for per-script documentation.

---

## What Gets Committed to Git

By default, `.gitignore` excludes generated data directories (`transcripts/`, `metadata/`, `cache/`, `markdown/`, `index/`) since they are reproducible from source. Only the scripts, documentation, and configuration files are committed.

To share enriched output with collaborators, selectively remove exclusions from `.gitignore`.
