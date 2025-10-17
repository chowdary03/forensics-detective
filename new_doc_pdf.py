import os
import glob
import subprocess
from pathlib import Path
import tempfile


def convert_all_docs(input_folder="wikipedia_docs", output_folder="word_pdfs"):
    """Convert all .docx files to PDF using one Microsoft Word session (macOS)."""
    input_path = Path(input_folder).resolve()
    output_path = Path(output_folder).resolve()
    os.makedirs(output_path, exist_ok=True)

    word_files = sorted(glob.glob(str(input_path / "*.docx")))
    if not word_files:
        print("n No Word files found.")
        return

    print(f"🔄 Converting {len(word_files)} Word documents to PDF...\n")

    # Skip already converted PDFs
    files_to_convert = []
    for f in word_files:
        pdf_path = output_path / (Path(f).stem + ".pdf")
        if not pdf_path.exists():
            files_to_convert.append(Path(f).as_posix())

    if not files_to_convert:
        print(" All PDFs already exist. Nothing to convert.")
        return

    # Create a temp file for AppleScript to log progress
    temp_log = Path(tempfile.gettempdir()) / "word_batch_convert_log.txt"
    if temp_log.exists():
        temp_log.unlink()

    file_list = ",".join([f'"{f}"' for f in files_to_convert])
    total_files = len(files_to_convert)

    # Build AppleScript
    applescript = f'''
    set fileList to {{{file_list}}}
    set totalFiles to {total_files}
    set logFile to POSIX file "{temp_log.as_posix()}"
    tell application "Microsoft Word"
        activate
        set i to 0
        repeat with f in fileList
            set i to i + 1
            try
                set docPath to f as text
                open POSIX file docPath
                delay 0.5
                set docName to name of active document
                set pdfName to text 1 thru ((offset of ".docx" in docName) - 1) of docName & ".pdf"
                set pdfPath to "{output_path.as_posix()}/" & pdfName
                save as active document file name pdfPath file format format PDF
                close active document saving no
                set logText to "[" & i & "/" & totalFiles & "] Converted: " & docName & return
            on error errMsg
                set logText to "[" & i & "/" & totalFiles & "] ❌ Error with " & f & " → " & errMsg & return
                try
                    close active document saving no
                end try
            end try
            do shell script "echo " & quoted form of logText & " >> " & quoted form of POSIX path of logFile
        end repeat
        quit
    end tell
    '''

    temp_script = Path("batch_convert.scpt")
    temp_script.write_text(applescript)

    # Run AppleScript in background
    process = subprocess.Popen(
        ["osascript", str(temp_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Stream progress from log file in real time
    try:
        last_size = 0
        while process.poll() is None:
            if temp_log.exists():
                with open(temp_log, "r") as logf:
                    logf.seek(last_size)
                    new_data = logf.read()
                    if new_data:
                        print(new_data, end="")
                        last_size = logf.tell()
            else:
                print("⏳ Waiting for Word to start...")
            # check every second
            import time
            time.sleep(1)

        # print any final lines
        if temp_log.exists():
            with open(temp_log, "r") as logf:
                logf.seek(last_size)
                print(logf.read(), end="")

        print("\n Conversion complete!")

    finally:
        if temp_script.exists():
            temp_script.unlink()
        if temp_log.exists():
            temp_log.unlink()


if __name__ == "__main__":
    convert_all_docs()
