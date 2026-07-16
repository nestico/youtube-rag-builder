# LinkedIn Learning Import

Import selected videos from a LinkedIn Learning course into the knowledge base, alongside the YouTube pipeline.

> **Access note:** This workflow uses your licensed LinkedIn Learning seat as intended — you copy transcripts manually from the course's Transcript tab. Automated downloading of LinkedIn Learning content violates LinkedIn's Terms of Service and is not supported by this project.

---

## Overview

```
Course contents (browser)          You                     Pipeline
─────────────────────────          ───                     ────────
1. Pick key video per module  ──►  Fill manifest JSON
2. Open video → Transcript tab ──► Copy text → save .txt
                                                     ──►   import_linkedin_course.py
                                                     ──►   enrich_markdown.py --source linkedin
```

---

## Step 1 — Fill in the course manifest

Edit [metadata/linkedin/pl400_cert_prep.json](../metadata/linkedin/pl400_cert_prep.json).

For each module of the course, pick the one video you consider most important and add an entry:

```json
{
  "slug": "m03-implement-plugins",
  "module": "Module 3: Extend the Platform",
  "title": "Implement plug-ins",
  "duration": 480,
  "url": "https://www.linkedin.com/learning/{course-slug}/{lesson-slug}"
}
```

- **slug** — your own short ID, kebab-case, prefixed with the module number (`m01-`, `m02-`, …). It becomes the file name everywhere — the transcript file must be named `{slug}.txt` exactly.
- **module** — module name as shown in the course contents sidebar.
- **title** — the exact lesson title.
- **duration** — length in seconds (optional; use `0` if unknown).
- **url** — optional lesson-specific URL. Copy it from your browser's address bar while watching the lesson. If omitted, links fall back to the course landing page.

---

## Step 2 — Copy each transcript

For each video in your manifest:

1. Open the video on LinkedIn Learning
2. Click the **Transcript** tab below the player
3. Select all the transcript text and copy it
4. Save it to a plain text file named after the slug:

```
transcripts/linkedin/m03-implement-plugins.txt
```

Plain text, UTF-8, no special formatting needed — timestamps and speaker labels are fine, they'll be treated as part of the text.

---

## Step 3 — Run the import

```powershell
py scripts\import_linkedin_course.py
```

This validates every manifest entry against `transcripts/linkedin/` and generates:

```
markdown/linkedin/videos/{slug}.md
```

Lessons with missing transcript files are reported and skipped — you can re-run the import any time as you add more transcripts.

---

## Step 4 — Enrich

```powershell
# LinkedIn course only
py scripts\enrich_markdown.py --source linkedin

# Or everything (YouTube + LinkedIn)
py scripts\enrich_markdown.py --source all
```

Outputs:

```
markdown/enriched/linkedin/videos/{slug}.md      # per-lesson enrichment
markdown/enriched/linkedin/playlists/{slug}.md   # course-level summary
cache/enrichment/linkedin/{slug}.json            # response cache
index/enriched_manifest_linkedin.json            # manifest
```

The `--limit N` flag works here too for test runs.

---

## Adding another course later

1. Create a new manifest JSON in `metadata/linkedin/`
2. Point `SOURCE_CONFIGS["linkedin"]["metadata_file"]` in `scripts/enrich_markdown.py` at it (or add a new source entry)
3. Repeat steps 2–4
