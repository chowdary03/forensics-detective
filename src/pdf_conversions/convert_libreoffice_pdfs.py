import os
import subprocess
from pathlib import Path
from tqdm import tqdm

input_folder = Path("wikipedia_docs")
output_folder = Path("libreoffice_pdfs")
output_folder.mkdir(exist_ok=True)

word_files = list(input_folder.glob("*.docx"))

success_count = 0
failed_files = []

for file in tqdm(word_files, desc="Converting DOCX to PDF"):
    output_file = output_folder / f"{file.stem}.pdf"
    
    if output_file.exists():
        continue

    try:
        subprocess.run([
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "--headless",
            "--convert-to", "pdf",
            str(file),
            "--outdir", str(output_folder)
        ], check=True)
        success_count += 1
    except subprocess.CalledProcessError:
        failed_files.append(file.name)

print("\nConversion complete!")
print(f"Successfully converted: {success_count}/{len(word_files)}")
if failed_files:
    print(f"Failed files ({len(failed_files)}): {failed_files}")
