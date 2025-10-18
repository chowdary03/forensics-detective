import os
from bs4 import BeautifulSoup
import mammoth
from playwright.sync_api import sync_playwright

# Resolve paths relative to the repo root so this works from any CWD
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
PDF_DIR = os.path.join(ROOT, 'data/html_pdfs')
DOCX_DIR = os.path.join(ROOT, 'data/source_documents/wikipedia_docs')


def ensure_dirs() -> None:
    os.makedirs(PDF_DIR, exist_ok=True)


BASE_HTML = """<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>{title}</title>
    <style>
      @page { size: auto; margin: 0; }
      html, body { margin: 0; padding: 0; }
      body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.4; padding: 0.6in; }
      h1, h2, h3 { margin: 0.6em 0 0.3em; }
      p { margin: 0.4em 0; }
      img { max-width: 100%; page-break-inside: avoid; }
      table { border-collapse: collapse; width: 100%; font-size: 10pt; }
      th, td { border: 1px solid #ccc; padding: 6px; }
      th { background: #f5f5f5; }
      * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      main { display: block; }
    </style>
  </head>
  <body>
    <h1>{title}</h1>
    <main>
      {content}
    </main>
  </body>
  </html>
"""


def build_full_html(title: str, content_html: str) -> str:
    # Avoid str.format to prevent CSS braces from being treated as placeholders
    return BASE_HTML.replace("{title}", title).replace("{content}", content_html)


def docx_to_html_string(docx_path: str) -> str:
    import base64

    def inline_image(image):
        with image.open() as img_bytes:
            data = img_bytes.read()
        b64 = base64.b64encode(data).decode('ascii')
        return {"src": f"data:{image.content_type};base64,{b64}"}

    with open(docx_path, 'rb') as f:
        result = mammoth.convert_to_html(f, convert_image=mammoth.images.inline(inline_image))
    # Use BeautifulSoup to normalize/clean the HTML snippet from mammoth
    soup = BeautifulSoup(result.value, 'html.parser')
    title = os.path.splitext(os.path.basename(docx_path))[0].replace('_', ' ')
    return build_full_html(title=title, content_html=str(soup))


def html_string_to_pdf(html_content: str, pdf_path: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.set_content(html_content, wait_until='load')
        page.wait_for_timeout(200)
        page.pdf(
            path=pdf_path,
            format='Letter',
            margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'},
            print_background=True,
            scale=1.0,
        )
        browser.close()


def main() -> None:
    ensure_dirs()
    docx_files = [f for f in os.listdir(DOCX_DIR) if f.lower().endswith('.docx')]
    docx_files.sort()
    for name in docx_files:
        base = os.path.splitext(name)[0]
        docx_path = os.path.join(DOCX_DIR, name)
        pdf_path = os.path.join(PDF_DIR, base + '.pdf')
        html_content = docx_to_html_string(docx_path)
        html_string_to_pdf(html_content, pdf_path)
        print(f"Saved PDF: {pdf_path}")
    print(f"Saved PDFs to {PDF_DIR}")


if __name__ == '__main__':
    main()


