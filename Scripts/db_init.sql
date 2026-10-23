-- ENABLE PGVECTOR
CREATE EXTENSION IF NOT EXISTS vector;

-- CREATE SCHEMA
CREATE SCHEMA IF NOT EXISTS rag;

SET search_path TO rag, public;

-- DOCUMENTS (UNCHANGED)
CREATE TABLE IF NOT EXISTS rag.documents (
    id BIGSERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source_file, file_type)
);

-- CHUNKS (UNCHANGED)
DROP TABLE IF EXISTS rag.chunks;

CREATE TABLE rag.chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES rag.documents(id) ON DELETE CASCADE,
    chunk_id INT NOT NULL,
    chunk_label TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(384) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (document_id, chunk_id)
);

-- VECTOR INDEX
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
ON rag.chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- OTHER INDEXES
CREATE INDEX IF NOT EXISTS idx_documents_source_file
ON rag.documents(source_file);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON rag.chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_chunks_metadata
ON rag.chunks USING GIN(metadata);

-- CHAT SESSIONS (IMPROVED)
CREATE TABLE IF NOT EXISTS rag.chat_sessions (
    id VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_created
ON rag.chat_sessions (created_at DESC);

-- CHAT MESSAGES (IMPROVED)
CREATE TABLE IF NOT EXISTS rag.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES rag.chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- FAST RETRIEVAL INDEX
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time
ON rag.chat_messages (session_id, created_at ASC);