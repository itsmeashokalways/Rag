from ingestion import process_all_documents
from sentence_transformers import SentenceTransformer
from chunk import chunk_process_documents
from config import DOCS_PATH, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL


# LOAD MODEL 
model = SentenceTransformer(EMBEDDING_MODEL)


# Generate Embedding
def generate_embeddings():
    """
    Full pipeline:
    Load → Chunk → Embed → Return structured data
    """

    # Step 1: Load documents
    all_docs = process_all_documents(DOCS_PATH)

    if not all_docs:
        print("No documents found!")
        return []

    # Step 2: Chunk documents
    chunks = chunk_process_documents(all_docs, CHUNK_SIZE, CHUNK_OVERLAP)

    if not chunks:
        print("No chunks created!")
        return []

    print(f"Total chunks: {len(chunks)}")

    # Step 3: Extract text
    texts = [chunk.page_content for chunk in chunks]

    if not texts:
        print("No text found!")
        return []

    # Step 4: Generate embeddings
    print("\nGenerating embeddings...")
    embeddings = model.encode(texts, batch_size=32)

    print(f"Total embeddings: {len(embeddings)}")
    print(f"Embedding dimension: {len(embeddings[0])}")

    # Step 5: Prepare data
    data = [
        {
            "text": chunk.page_content,
            "embedding": embedding,
            "metadata": chunk.metadata
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    return data


# EMBED USER QUERY
def embed_query(query: str) -> list[float]:
    """
    Convert user query → embedding vector
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    return model.encode([query])[0]

# TEST RUN
if __name__ == "__main__":
    data = generate_embeddings()
    print(f"\nSample output:\n{data[:1]}")