# Quickstart

This guide walks you through running the full pipeline from a YouTube playlist URL to an enriched RAG-ready knowledge base.

---

## Prerequisites

- Python 3.11 or higher
- A Google Gemini API key ([get one free at Google AI Studio](https://aistudio.google.com/app/apikey))
- A YouTube playlist URL

---

## 1. Clone and Install

```powershell
git clone https://github.com/your-username/youtube-rag-builder.git
cd youtube-rag-builder
py -m pip install -r requirements.txt
```

---

## 2. Set Your API Key

Add `GEMINI_API_KEY_RAG_YOUTUBE` to your Windows User Environment Variables:

1. Press `Win + S` → search **Environment Variables**
2. Click **Edit the system environment variables** → **Environment Variables...**
3. Under **User variables** → click **New**
4. Variable name: `GEMINI_API_KEY_RAG_YOUTUBE`
5. Variable value: your API key (`AIzaSy...`)
6. Click OK → open a new terminal

Verify it's set:

```powershell
echo $env:GEMINI_API_KEY_RAG_YOUTUBE
```

---

## 3. Configure Your Playlist

Edit `scripts/extract_playlist.py` and set your playlist URL:

```python
PLAYLIST_URL = "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

---

## 4. Run the Pipeline

### Step 1 — Extract Playlist Metadata

```bash
py scripts/extract_playlist.py
```

Output: `metadata/youtube/command_bar_playlist.json`

```
Saved playlist metadata to metadata/youtube/command_bar_playlist.json
Videos found: 24
```

---

### Step 2 — Download Transcripts

```bash
py scripts/extract_all_transcripts.py
```

Output: `transcripts/youtube/{video_id}.json` for each video, plus `index/videos.csv` and `index/videos.json`

```
[1/24] Downloading transcript: Introduction to Command Bar
[2/24] Downloading transcript: Adding Custom Buttons
...
=================================
Transcript Extraction Complete
=================================
Total Videos : 24
Success      : 23
Failed       : 1
```

---

### Step 3 — Generate Markdown

```bash
py scripts/generate_markdown.py
```

Output: `markdown/youtube/videos/*.md`, `markdown/youtube/playlists/*.md`, `markdown/youtube/index.md`, `index/markdown_manifest.json`

```
[1/24] Generating markdown: Introduction to Command Bar
[2/24] Generating markdown: Adding Custom Buttons
...
=================================
Markdown Generation Complete
=================================
Videos Processed : 24
Videos Failed    : 0
Playlist Files   : 1
Index Created    : Yes
```

---

### Step 4 — Enrich with AI

**Test run (recommended first time — 3 videos only):**

```bash
py scripts/enrich_markdown.py --limit 3
```

**Full run (all videos):**

```bash
py scripts/enrich_markdown.py
```

Output: `markdown/enriched/youtube/videos/*.md`, `markdown/enriched/youtube/playlists/*.md`, `cache/enrichment/youtube/*.json`, `index/enriched_manifest_youtube.json`

```
Using provider: Gemini
Model: gemini-2.5-pro
[1/24] Enriching: abc123.md
CACHE MISS
[2/24] Enriching: def456.md
CACHE MISS
...
=================================
Enrichment Complete
=================================
Videos Processed : 24
Videos Failed    : 0
Playlist Files   : 1
Index Created    : Yes
```

On subsequent runs, cached videos are served instantly:

```
[1/24] Enriching: abc123.md
CACHE HIT
[2/24] Enriching: def456.md
CACHE HIT
```

---

## 5. Explore the Output

After a full run, your knowledge base is in `markdown/enriched/`:

```
markdown/enriched/youtube/
├── playlists/
│   └── Power-Apps---Command-Bar.md   # Playlist summary + learning path
└── videos/
    ├── abc123.md                      # Enriched video with YAML front-matter
    ├── def456.md
    └── ...
```

Each video file is ready for ingestion into a vector database such as Supabase, Pinecone, or Chroma.

---

## 6. Optional — Add a LinkedIn Learning Course

If you have a LinkedIn Learning subscription, you can add selected course videos to the same knowledge base:

```powershell
py scripts\import_linkedin_course.py
py scripts\enrich_markdown.py --source linkedin
```

This requires filling in a course manifest and copying transcripts manually — see [linkedin-import.md](linkedin-import.md) for the full workflow.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY_RAG_YOUTUBE is not set` | Open a new terminal after adding the env var, or verify the variable name is exact. The script also reads the Windows registry directly, so this normally works even in IDE terminals — verify the stored value with `[System.Environment]::GetEnvironmentVariable("GEMINI_API_KEY_RAG_YOUTUBE", "User")` |
| `API key not valid` | Check your key in Google AI Studio — ensure it has Gemini API access enabled |
| Transcript download failed for a video | The video may have transcripts disabled; it will be skipped automatically |
| `No module named 'yt_dlp'` | Run `pip install -r requirements.txt` |
| Cache returns stale results | Delete `cache/enrichment/` and re-run `enrich_markdown.py` |
