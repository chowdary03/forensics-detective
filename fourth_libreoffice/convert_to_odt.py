import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional, Tuple

from tqdm import tqdm


@dataclass
class ConvertResult:
    total: int
    succeeded: int
    failed: int


def detect_soffice(custom_path: Optional[str]) -> Optional[str]:
    if custom_path and os.path.exists(custom_path):
        return custom_path
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


def run_soffice_convert(soffice: str, src_docx: str, out_dir: str) -> Tuple[str, bool, Optional[str]]:
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "odt",
        "--outdir", out_dir,
        src_docx,
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        ok = proc.returncode == 0
        err = proc.stderr.decode("utf-8", errors="ignore").strip() or None
        return (src_docx, ok, err)
    except Exception as e:  # noqa: BLE001
        return (src_docx, False, str(e))


def convert_docx_dir_to_odt(
    workers: int,
    *,
    input_dir: str = "wikipedia_docs",
    odt_dir_override: Optional[str] = None,
) -> ConvertResult:
    soffice = detect_soffice(None)
    if not soffice:
        raise SystemExit("LibreOffice soffice not found. Install LibreOffice or set libreoffice.soffice_path in config.yaml")

    docx_dir = input_dir
    odt_dir = odt_dir_override or "lo_odt"
    os.makedirs(odt_dir, exist_ok=True)

    docx_files = [os.path.join(docx_dir, f) for f in os.listdir(docx_dir) if f.lower().endswith(".docx")]
    docx_files.sort()
    total = len(docx_files)

    def job(path: str) -> Tuple[str, bool, Optional[str]]:
        return run_soffice_convert(soffice, path, odt_dir)

    # Parallel pass (may skip some files due to LibreOffice concurrency issues)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for _src, _ok, _err in tqdm(pool.map(job, docx_files), total=total, desc="DOCX → ODT"):
            pass

    # Verification pass: find missing ODTs and fill sequentially (robust)
    docx_bases = {os.path.splitext(os.path.basename(p))[0] for p in docx_files}
    odt_bases = {os.path.splitext(f)[0] for f in os.listdir(odt_dir) if f.lower().endswith('.odt')}
    missing = sorted(docx_bases - odt_bases)
    for name in missing:
        src = os.path.join(docx_dir, name + '.docx')
        _src, _ok, _err = run_soffice_convert(soffice, src, odt_dir)

    # Final counts
    odt_bases_final = {os.path.splitext(f)[0] for f in os.listdir(odt_dir) if f.lower().endswith('.odt')}
    succeeded = len(docx_bases & odt_bases_final)
    failed = total - succeeded
    return ConvertResult(total=total, succeeded=succeeded, failed=failed)


if __name__ == "__main__":
    # Zero-arg default runner (sequential for reliability)
    workers = 1
    res = convert_docx_dir_to_odt(workers)
    print(f"Converted: {res.succeeded}/{res.total}, failed: {res.failed}")


