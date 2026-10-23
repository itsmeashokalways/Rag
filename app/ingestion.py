from pathlib import Path
from langchain_community.document_loaders import TextLoader, Docx2txtLoader, PyMuPDFLoader

#process all doc , return as single documents
def process_all_documents(data_dir: str):

    all_documents = []
    base_path = Path(data_dir)

    loader_map = {
        ".pdf": PyMuPDFLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
        ".docx": Docx2txtLoader
    }

    for ext, loader_cls in loader_map.items():
        files = list(base_path.glob(f"**/*{ext}"))
        print(f"Found {len(files)} {ext} files")

        for file_path in files:
            try:
                loader_kwargs = {"encoding": "utf-8"} if ext in [".txt", ".md"] else {}
                loader = loader_cls(str(file_path), **loader_kwargs)

                docs = loader.load()

                for doc in docs:
                    doc.metadata["source_file"] = file_path.name
                    doc.metadata["file_type"] = ext[1:]

                all_documents.extend(docs)

            except Exception as e:
                print(f"Error: {file_path.name} -> {e}")

    print(f"Total documents loaded: {len(all_documents)}")
    return all_documents

process_all_documents("data")