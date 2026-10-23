from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_OVERLAP, CHUNK_SIZE

#   Split loaded documents into smaller chunks and add metadata.
def chunk_process_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):

    if not documents:
        print("No documents to chunk!")
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n\n", "\n\n", "\n", ".", " ", ""]
    )

    chunked_documents = text_splitter.split_documents(documents)

    #  FIX: chunk_id per document (IMPORTANT)
    doc_chunk_map = {}

    for chunk in chunked_documents:
        source = chunk.metadata.get("source_file")

        if source not in doc_chunk_map:
            doc_chunk_map[source] = 0

        doc_chunk_map[source] += 1
        chunk.metadata["chunk_id"] = doc_chunk_map[source]

    print(f"Total chunks created: {len(chunked_documents)}")
    return chunked_documents


