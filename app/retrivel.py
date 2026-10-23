from embedding import embed_query
from db import search_similar_chunks

#get similar chunks to the query
def search_query(query: str):
    # Step 1: Convert query to embedding
    query_embedding = embed_query(query)

    # Step 2: Get top_k results (already sorted by similarity)
    results = search_similar_chunks(query_embedding)

    return results


# TEST RUN
if __name__ == "__main__":
    query = "what is sql"

    results = search_query(query)

    print("\nTop Results:\n")

    if not results:
        print("No results found.")
    else:
        for r in results:
            print(f"📄 {r['source_file']} (chunk {r['chunk_id']})")
            print(f"Distance: {r['distance']:.3f}")
            print(f"Content: {r['content']}...\n")