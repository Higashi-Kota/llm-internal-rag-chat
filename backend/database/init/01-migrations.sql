-- RAG Chat Database Schema
-- Idempotent migration: DROP and recreate tables for clean slate

-- Drop tables in reverse order (respect foreign key dependencies)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS diagrams CASCADE;

-- Create diagrams table
CREATE TABLE diagrams (
    id UUID PRIMARY KEY,
    trace_id VARCHAR NOT NULL,
    prompt TEXT NOT NULL,
    language VARCHAR NOT NULL,
    diagram_type VARCHAR NOT NULL,
    mermaid_code TEXT,
    status VARCHAR NOT NULL,
    error_message TEXT,
    model VARCHAR,
    latency_ms INTEGER,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_diagrams_trace_id ON diagrams(trace_id);
CREATE INDEX idx_diagrams_created_at ON diagrams(created_at);

-- Create chat_sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);

-- Create chat_messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    sources_json TEXT,
    model VARCHAR(100),
    provider VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Migration complete: tables diagrams, chat_sessions, chat_messages created';
END $$;
