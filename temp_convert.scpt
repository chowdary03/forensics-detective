
tell application "Microsoft Word"
    open POSIX file "/Users/shwetangisingh/work/ForensicsDetective/wikipedia_docs/wiki_doc_03966.docx"
    set theDoc to active document
    save as theDoc file name "/Users/shwetangisingh/work/ForensicsDetective/word_pdfs/wiki_doc_03966.pdf" file format PDF file format
    close theDoc
end tell
