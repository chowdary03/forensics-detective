import os
from docx2pdf import convert
from tqdm import tqdm

def batch_convert_docx_to_pdf(input_folder, output_folder):
    """
    Converts all .docx files in the input folder to PDF in the output folder.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Get all DOCX files
    docx_files = [f for f in os.listdir(input_folder) if f.endswith(".docx")]

    print(f"Found {len(docx_files)} DOCX files to convert.\n")

    for filename in tqdm(docx_files, desc="Converting files"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename.replace(".docx", ".pdf"))

        if os.path.exists(output_path):
            # Skip if PDF already exists
            continue

        try:
            convert(input_path, output_path)
        except Exception as e:
            print(f"\n✗ Error converting {filename}: {e}")

    print("\n Conversion complete!")

if __name__ == "__main__":
    INPUT_FOLDER = "/Users/shwetangisingh/work/ForensicsDetective/wikipedia_docs"
    OUTPUT_FOLDER = "/Users/shwetangisingh/work/ForensicsDetective/pdf_files"

    batch_convert_docx_to_pdf(INPUT_FOLDER, OUTPUT_FOLDER)
