import wikipedia
import os

# Folder to save articles
folder = "data/source_documents/wikipedia_docs"
os.makedirs(folder, exist_ok=True)

# List of topics to scrape
topics = [
    "Artificial Intelligence",
    "Python (programming language)",
    "Psychology",
    "History of Mathematics",
    "Quantum Mechanics",
    "Sociology",
    "Computer Science",
    "Philosophy"
]

for topic in topics:
    try:
        # Get the content
        text = wikipedia.page(topic).content
        filename = topic.replace(" ", "_") + ".txt"
        with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {filename}")
    except Exception as e:
        print(f"Error with {topic}: {e}")
