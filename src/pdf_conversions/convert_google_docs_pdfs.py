#!/usr/bin/env python3
import os
import io
import time
import json
from pathlib import Path
from multiprocessing import Pool, cpu_count

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from tqdm import tqdm

SCOPES = ['https://www.googleapis.com/auth/drive.file']
BATCH_SIZE = 500  # Number of files per run (avoid macOS malloc crash)
NUM_WORKERS = min(4, cpu_count())  # Safe parallelism on macOS
MAX_RETRIES = 2

# Folders
DOCX_FOLDER = Path("data/source_documents/wikipedia_docs")
PDF_FOLDER = Path("data/google_docs_pdfs")
TOKEN_FILE = Path("src/utils/token.pkl")
CREDENTIALS_FILE = Path("src/utils/credentials_oauth.json")


def authenticate_oauth():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    return service


def convert_docx_to_pdf(args):
    docx_path, pdf_path = args
    service = authenticate_oauth()
    
    if pdf_path.exists():
        return f"Skipped: {pdf_path.name}"

    retries = 0
    while retries <= MAX_RETRIES:
        try:
            # Upload DOCX and convert to Google Docs
            file_metadata = {
                'name': docx_path.stem,
                'mimeType': 'application/vnd.google-apps.document'
            }
            media = MediaFileUpload(str(docx_path),
                                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                    resumable=True)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = file.get('id')

            # Export as PDF
            request = service.files().export_media(fileId=file_id,
                                                   mimeType='application/pdf')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            with open(pdf_path, 'wb') as f:
                f.write(fh.getvalue())

            # Delete Google Doc to save space
            service.files().delete(fileId=file_id).execute()
            return f"Success: {pdf_path.name}"

        except Exception as e:
            retries += 1
            time.sleep(2)
            if retries > MAX_RETRIES:
                return f"Failed: {pdf_path.name} | {str(e)}"


def run_batch(files_chunk):
    args_list = [(f, PDF_FOLDER / f"{f.stem}.pdf") for f in files_chunk]
    results = []
    with Pool(NUM_WORKERS) as pool:
        for res in tqdm(pool.imap_unordered(convert_docx_to_pdf, args_list), total=len(args_list)):
            results.append(res)
    return results


def main():
    PDF_FOLDER.mkdir(exist_ok=True)
    docx_files = list(DOCX_FOLDER.glob("*.docx"))
    total_files = len(docx_files)
    print(f"Found {total_files} DOCX files to convert.\n")

    # Process in batches
    for i in range(0, total_files, BATCH_SIZE):
        batch_files = docx_files[i:i+BATCH_SIZE]
        print(f"\nProcessing batch {i//BATCH_SIZE +1} ({len(batch_files)} files)...")
        results = run_batch(batch_files)
        for r in results:
            print(r)


if __name__ == "__main__":
    main()
