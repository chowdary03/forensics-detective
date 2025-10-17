import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PyPDF2 import PdfReader
from tqdm import tqdm


@dataclass
class ConvertResult:
    total: int
    succeeded: int
    failed: int


def detect_soffice(custom_path: Optional[str]) -> Optional[str]:
    if custom_path and os.path.exists(custom_path):
        return custom_path
    # Common locations
    candidates = [
        shutil.which("soffice"),
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def run_soffice_convert(soffice: str, src_path: str, out_dir: str, filter_str: str, filter_data: Optional[str]) -> Tuple[str, bool, Optional[str]]:
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        soffice,
        "--headless",
        "--convert-to", filter_str,
        "--outdir", out_dir,
        src_path,
    ]
    env = os.environ.copy()
    if filter_data:
        env["UNITY_FILE_FILTER_DATA"] = filter_data
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False)
        ok = proc.returncode == 0
        err = proc.stderr.decode("utf-8", errors="ignore").strip() or None
        return (src_path, ok, err)
    except Exception as e:  # noqa: BLE001
        return (src_path, False, str(e))


def convert_all(
    workers: int,
    *,
    input_dir: Optional[str] = None,
    pdf_dir_override: Optional[str] = None,
) -> ConvertResult:
    soffice = detect_soffice(None)
    if not soffice:
        raise SystemExit("LibreOffice soffice not found. Install LibreOffice or set libreoffice.soffice_path in config.yaml")

    # Convert from ODT directory for deterministic pipeline (DOCX -> ODT -> PDF)
    odt_dir = input_dir or "lo_odt"
    pdf_dir = pdf_dir_override or "lo_pdfs"
    os.makedirs(pdf_dir, exist_ok=True)

    # Default LibreOffice PDF export filter
    filter_str = "pdf:writer_pdf_Export"
    filter_data = None

    odt_files = [os.path.join(odt_dir, f) for f in os.listdir(odt_dir) if f.lower().endswith(".odt")]
    odt_files.sort()
    total = len(odt_files)

    def job(path: str) -> Tuple[str, bool, Optional[str]]:
        return run_soffice_convert(soffice, path, pdf_dir, filter_str, filter_data)

    succeeded = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for src, ok, err in tqdm(pool.map(job, odt_files), total=total, desc="LibreOffice export"):
            if ok:
                succeeded += 1
            else:
                failed += 1

    # rename/move PDFs to match .docx basenames if needed
    produced = {f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")}
    for odt_path in odt_files:
        base = os.path.splitext(os.path.basename(odt_path))[0]
        candidate = os.path.join(pdf_dir, f"{base}.pdf")
        if os.path.exists(candidate):
            continue
        # Sometimes soffice uses different file names; attempt to find and rename first matching
        for p in list(produced):
            if p.lower().startswith(base.lower()):
                os.rename(os.path.join(pdf_dir, p), candidate)
                produced.remove(p)
                break

    return ConvertResult(total=total, succeeded=succeeded, failed=failed)


def count_pages_in_dir(pdf_dir: str) -> List[int]:
    counts = []
    for f in os.listdir(pdf_dir):
        if not f.lower().endswith(".pdf"):
            continue
        try:
            reader = PdfReader(os.path.join(pdf_dir, f))
            counts.append(len(reader.pages))
        except Exception:
            pass
    return counts


if __name__ == "__main__":
    # Zero-arg default runner
    workers = 6
    res = convert_all(workers)
    print(f"Converted: {res.succeeded}/{res.total}, failed: {res.failed}")


