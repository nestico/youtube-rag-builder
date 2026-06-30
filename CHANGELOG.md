# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Supabase vector database integration
- Azure OpenAI, OpenAI, and Anthropic provider implementations
- Multi-playlist support
- Embedding generation pipeline
- Web UI for knowledge base browsing

---

## [0.3.0] — 2026-06-30

### Added
- Cache layer for Gemini enrichment responses (`cache/enrichment/{video_id}.json`)
- `CACHE HIT` / `CACHE MISS` logging to avoid redundant API calls
- Cache is checked before every Gemini call; responses saved on miss

---

## [0.2.0] — 2026-06-30

### Added
- `enrich_markdown.py` — AI enrichment pipeline using Google Gemini 2.5 Pro
- Provider architecture: abstract `LLMProvider` base class with `ClaudeProvider`, `GeminiProvider`, `AzureOpenAIProvider`, `OpenAIProvider` stubs
- `MarkdownParser` — parses existing video markdown files
- `EnrichmentEngine` — prompt templates for video and playlist enrichment
- `MarkdownWriter` — writes enriched markdown with YAML front-matter
- Enriched output fields: executive summary, key concepts, key learnings, technologies, keywords, suggested questions
- Playlist-level AI summary with major topics and recommended learning path
- `--limit N` CLI argument for testing on a subset of videos
- `TEST MODE ENABLED` logging when `--limit` is supplied
- `index/enriched_manifest.json` output
- Windows User Environment Variable support for `GEMINI_API_KEY_RAG_YOUTUBE` (reads directly from registry when IDE terminal doesn't inherit env vars)

---

## [0.1.0] — 2026-06-01

### Added
- `extract_playlist.py` — extracts YouTube playlist metadata via `yt-dlp`
- `extract_all_transcripts.py` — downloads transcripts via `youtube-transcript-api`
- `generate_markdown.py` — generates structured markdown per video and per playlist
- `index/videos.csv` and `index/videos.json` transcript index
- `index/markdown_manifest.json` markdown generation manifest
- `requirements.txt` with initial dependencies
