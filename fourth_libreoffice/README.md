### Fourth Source: LibreOffice Headless PDF Export

This pipeline converts the existing `.docx` files in `wikipedia_docs/` to PDF using LibreOffice's headless exporter (`soffice --headless`). No new content is generated; it strictly operates on the provided corpus.

#### Why LibreOffice
- Stable and scriptable PDF export
- Works directly from `.docx` (same input content as other sources)
- Control over output quality via `writer_pdf_Export`

---

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r fourth_libreoffice/requirements.txt

# Install LibreOffice (macOS example)
brew install --cask libreoffice
```

---

### Configure

No config file is required; defaults are baked in.

---

### Run (no flags needed)

```bash
source .venv/bin/activate
python fourth_libreoffice/convert_to_odt.py   # converts wikipedia_docs/*.docx -> lo_odt/
python fourth_libreoffice/convert_to_pdf.py   # converts wikipedia_docs/*.docx -> lo_pdfs/ and writes lo_logs/summary.json
```

Outputs:
- `lo_odt/` — ODT files converted from DOCX (LibreOffice-native storage)
- `lo_pdfs/` — PDFs exported from DOCX via LibreOffice

---

### Notes
- PDF export uses `soffice --headless --convert-to pdf:writer_pdf_Export`; filter options can be tuned in `config.yaml`.


