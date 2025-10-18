import os
import glob
import time
import subprocess

def convert_single_file(word_file, output_folder):
    """Convert a single Word file to PDF using AppleScript"""
    filename = os.path.splitext(os.path.basename(word_file))[0]
    output_file = os.path.join(output_folder, f"{filename}.pdf")

    # Skip if already exists
    if os.path.exists(output_file):
        print(f"Skipping {filename} (already exists)")
        return True

    # Write AppleScript for this file
    with open('src/pdf_conversions/temp_convert.scpt', 'w') as f:
        f.write(f'''
tell application "Microsoft Word"
    try
        open POSIX file "{os.path.abspath(word_file)}"
        delay 0.5
        set theDoc to document 1
        save as theDoc file name "{os.path.abspath(output_file)}" file format format PDF
        close theDoc saving no
    on error errMsg
        display dialog "Error: " & errMsg
    end try
end tell
''')

    try:
        # Run AppleScript with timeout (30 seconds)
        result = subprocess.run(['osascript', 'temp_convert.scpt'],
                                timeout=30, check=True)
        print(f"✓ Converted {filename}")
        return True

    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout: {filename} took too long, skipped.")
        return False
    except subprocess.CalledProcessError:
        print(f"✗ Failed to convert {filename}")
        return False


# === Main Conversion ===
word_files = glob.glob("data/source_documents/wikipedia_docs/*.docx")
os.makedirs("data/converted_pdfs/word_pdfs", exist_ok=True)

print(f"Converting {len(word_files)} Word documents to PDF...")
success_count = 0
failed_files = []

for i, word_file in enumerate(word_files):
    print(f"[{i+1}/{len(word_files)}] Processing {os.path.basename(word_file)}")

    if convert_single_file(word_file, "data/word_pdfs"):
        success_count += 1
    else:
        failed_files.append(word_file)

    # Restart Word every 50 files to prevent freezing
    if (i + 1) % 50 == 0:
        print("🔁 Restarting Microsoft Word to refresh memory...")
        os.system('osascript -e \'tell application "Microsoft Word" to quit saving no\'')
        time.sleep(3)

print("\n✅ Conversion complete!")
print(f"Successfully converted: {success_count}/{len(word_files)}")
if failed_files:
    print(f"Failed files: {[os.path.basename(f) for f in failed_files]}")

# Cleanup temp file
if os.path.exists('temp_convert.scpt'):
    os.remove('temp_convert.scpt')