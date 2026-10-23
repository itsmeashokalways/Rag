import psycopg2
from psycopg2.extras import Json
from config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    TOP_K
)


# CONNECTION
def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


# VECTOR FORMAT (pgvector)
def vector_to_sql(vector):
    return "[" + ",".join(str(x) for x in vector) + "]"


# INSERT DOCUMENT
def insert_document(cursor, source_file, file_type, file_path=None):

    cursor.execute("""
        INSERT INTO rag.documents (source_file, file_type, file_path)
        VALUES (%s, %s, %s)
        ON CONFLICT (source_file, file_type)
        DO NOTHING
        RETURNING id;
    """, (source_file, file_type, file_path))

    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute("""
        SELECT id FROM rag.documents
        WHERE source_file = %s AND file_type = %s;
    """, (source_file, file_type))

    return cursor.fetchone()[0]


# INSERT CHUNK
def insert_chunk(cursor, document_id, chunk_id, content, metadata, embedding):

    chunk_label = f"{metadata.get('source_file', 'doc')}_chunk_{chunk_id}"
    embedding_str = vector_to_sql(embedding)

    cursor.execute("""
        INSERT INTO rag.chunks (
            document_id,
            chunk_id,
            chunk_label,
            content,
            metadata,
            embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s::vector)
        ON CONFLICT (document_id, chunk_id)
        DO UPDATE SET
            chunk_label = EXCLUDED.chunk_label,
            content = EXCLUDED.content,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding;
    """, (
        document_id,
        chunk_id,
        chunk_label,
        content,
        Json(metadata),
        embedding_str
    ))


# INSERT MULTIPLE RECORDS (SYNC + NO DUPLICATES)
def insert_records(records):

    if not records:
        print(" No records to insert.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        inserted_chunks = 0

        #  STEP 1: Collect active files
        active_files = set()

        for record in records:
            metadata = record.get("metadata", {})

            source_file = metadata.get("source_file")
            file_type = metadata.get("file_type")

            if not source_file or not file_type:
                raise ValueError("Missing source_file or file_type in metadata")

            active_files.add((source_file, file_type))

        #  STEP 2: Delete removed documents (SYNC)
        if active_files:
            values = ",".join(
                cursor.mogrify("(%s, %s)", item).decode("utf-8")
                for item in active_files
            )

            delete_query = f"""
                DELETE FROM rag.documents
                WHERE (source_file, file_type) NOT IN ({values});
            """

            cursor.execute(delete_query)

        #  STEP 3: Track processed documents (IMPORTANT FIX)
        processed_docs = set()

        #  STEP 4: Insert / Update
        for record in records:

            metadata = record.get("metadata", {})
            text = record.get("text", "")
            embedding = record.get("embedding", [])

            source_file = metadata.get("source_file")
            file_type = metadata.get("file_type")
            file_path = metadata.get("source")
            chunk_id = metadata.get("chunk_id", 0)

            # Insert document
            document_id = insert_document(
                cursor,
                source_file,
                file_type,
                file_path
            )

            #  DELETE OLD CHUNKS ONLY ONCE PER DOCUMENT
            if document_id not in processed_docs:
                cursor.execute("""
                    DELETE FROM rag.chunks
                    WHERE document_id = %s;
                """, (document_id,))
                processed_docs.add(document_id)

            # Insert chunk
            insert_chunk(
                cursor,
                document_id,
                chunk_id,
                text,
                metadata,
                embedding
            )

            inserted_chunks += 1

        #  Optimize pgvector performance
        cursor.execute("ANALYZE rag.chunks;")

        conn.commit()
        print(f" Inserted/updated {inserted_chunks} chunks")

    except Exception as e:
        conn.rollback()
        print(" Error inserting records:", e)

    finally:
        cursor.close()
        conn.close()


# SIMILARITY SEARCH
def search_similar_chunks(query_embedding):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        embedding_str = vector_to_sql(query_embedding)

        cursor.execute("""
            SELECT
                c.content,
                d.source_file,
                d.file_type,
                c.chunk_id,
                c.chunk_label,
                c.metadata,
                c.embedding <-> %s::vector AS distance
            FROM rag.chunks c
            JOIN rag.documents d ON c.document_id = d.id
            ORDER BY c.embedding <-> %s::vector
            LIMIT %s;
        """, (embedding_str, embedding_str, TOP_K))

        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "content": row[0],
                "source_file": row[1],
                "file_type": row[2],
                "chunk_id": row[3],
                "chunk_label": row[4],
                "metadata": row[5],
                "distance": row[6]
            })

        return results

    except Exception as e:
        print(" Search error:", e)
        return []

    finally:
        cursor.close()
        conn.close()
        
        
# GET ALL CHUNKS FOR FILE
def get_chunks_by_document(source_file):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                d.source_file,
                d.file_type,
                c.chunk_id,
                c.chunk_label,
                c.content,
                c.metadata
            FROM rag.chunks c
            JOIN rag.documents d ON c.document_id = d.id
            WHERE d.source_file = %s
            ORDER BY c.chunk_id;
        """, (source_file,))

        rows = cursor.fetchall()

        return [
            {
                "source_file": r[0],
                "file_type": r[1],
                "chunk_id": r[2],
                "chunk_label": r[3],
                "content": r[4],
                "metadata": r[5]
            }
            for r in rows
        ]

    except Exception as e:
        print("Error fetching chunks:", e)
        return []

    finally:
        cursor.close()
        conn.close()


# CHAT SESSION
def create_session(session_id, name="New Chat"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO rag.chat_sessions (id, name)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """, (session_id, name))

    conn.commit()
    cursor.close()
    conn.close()


# SAVE MESSAGE
def save_message(session_id, role, message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO rag.chat_messages (session_id, role, message)
        VALUES (%s, %s, %s);
    """, (session_id, role, message))

    conn.commit()
    cursor.close()
    conn.close()


# GET CHAT HISTORY
def get_chat_history(session_id, limit=6):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, message
        FROM rag.chat_messages
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (session_id, limit))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows[::-1]

def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM rag.chat_sessions
        ORDER BY created_at DESC;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"id": r[0], "name": r[1]} for r in rows]

def update_session_name(session_id, name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE rag.chat_sessions
        SET name = %s
        WHERE id = %s;
    """, (name[:50], session_id))

    conn.commit()
    cursor.close()
    conn.close()

def get_recent_chat_context(session_id, limit=6):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, message
        FROM rag.chat_messages
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (session_id, limit))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # Return in correct order (old → new)
    return rows[::-1]