import os
from bs4 import BeautifulSoup
import mammoth
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

# Resolve paths relative to the repo root so this works from any CWD
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
HTML_DIR = os.path.join(ROOT, 'fifth_html')
PDF_DIR = os.path.join(ROOT, 'fifth_pdfs')
DOCX_DIR = os.path.join(ROOT, 'wikipedia_docs')
TEMPLATE_DIR = HERE  # base.html is stored alongside this script


def ensure_dirs() -> None:
    os.makedirs(HTML_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)


def render_template(title: str, content_html: str) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('base.html')
    return template.render(title=title, content=content_html)


def docx_to_html(docx_path: str, out_html: str) -> None:
    import base64

    def inline_image(image):
        with image.open() as img_bytes:
            data = img_bytes.read()
        b64 = base64.b64encode(data).decode('ascii')
        return {"src": f"data:{image.content_type};base64,{b64}"}

    with open(docx_path, 'rb') as f:
        result = mammoth.convert_to_html(f, convert_image=mammoth.images.inline(inline_image))
    soup = BeautifulSoup(result.value, 'html.parser')
    final_html = render_template(os.path.splitext(os.path.basename(docx_path))[0].replace('_', ' '), str(soup))
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(final_html)


def html_to_pdf(html_path: str, pdf_path: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_load_state('load')
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
        html_path = os.path.join(HTML_DIR, base + '.html')
        pdf_path = os.path.join(PDF_DIR, base + '.pdf')
        docx_to_html(docx_path, html_path)
        html_to_pdf(html_path, pdf_path)
    print(f"Saved HTML to {HTML_DIR} and PDFs to {PDF_DIR}")


if __name__ == '__main__':
    main()


