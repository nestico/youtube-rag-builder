# Contributing

Thank you for your interest in contributing to youtube-rag-builder.

---

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/youtube-rag-builder.git
   cd youtube-rag-builder
   ```
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # macOS/Linux
   ```
4. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
5. Set your API key (see [README — Setup](README.md#setup--gemini-api-key))

---

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test with `--limit` to avoid burning API quota:
   ```bash
   py scripts/enrich_markdown.py --limit 3
   ```
4. Verify the script compiles cleanly:
   ```bash
   py -m py_compile scripts/enrich_markdown.py
   ```
5. Commit with a clear message:
   ```bash
   git commit -m "feat: add OpenAI provider implementation"
   ```
6. Push and open a pull request against `main`

---

## Adding a New LLM Provider

All providers implement the `LLMProvider` abstract base class in `scripts/enrich_markdown.py`:

```python
class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def complete(self, prompt: str) -> str: ...
```

To add a new provider:

1. Subclass `LLMProvider`
2. Implement `complete(self, prompt: str) -> str`
3. Update `build_provider()` to return your provider when appropriate
4. Document the required environment variable in the README

---

## Code Style

- Python 3.11+
- No external formatter required — keep style consistent with existing files
- No comments unless the reason is non-obvious
- Keep functions focused and small
- Prefer editing existing classes over introducing new abstractions

---

## Commit Message Format

```
type: short description

Types: feat, fix, refactor, docs, chore
```

---

## Reporting Issues

Open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual output
- Python version and OS
