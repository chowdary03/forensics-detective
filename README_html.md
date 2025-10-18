### Fifth Source: Browser-based PDF Generation (Headless Chromium)

This source converts existing `wikipedia_docs/*.docx` to HTML and renders them to PDF using a headless browser (Chromium) via Playwright's print-to-PDF. This ensures identical content with other sources and high reproducibility.

Run (no flags):
- python fifth_browser/generate_browser_pdfs.py

Outputs:
- fifth_html/ — intermediate HTML (saved per document)
- fifth_pdfs/ — final PDFs (printed via Chromium)

Install:
- python3 -m venv .venv && source .venv/bin/activate
- pip install -r fifth_browser/requirements.txt
- python -m playwright install chromium

Notes:
- Uses default Letter page size, 0.5in margins, background printing on.
- Content is only from `wikipedia_docs/`; no internet is required to run.
