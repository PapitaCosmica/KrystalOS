from sqlmodel import Session, create_engine, text
from sentence_transformers import SentenceTransformer
import os
import uuid

# Load model (downloads on first run)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Use the same DB URL as docker-compose
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://krystal:krystal@localhost:5432/krystalos")
engine = create_engine(DATABASE_URL)

def init_vector_db():
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        session.exec(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                filename TEXT,
                content TEXT,
                embedding vector(384)
            );
        """))
        session.commit()

async def store_document_embedding(filename: str, content: str):
    # Vectorize text chunks (simplified: embedding whole text for now)
    embedding = model.encode(content).tolist()
    doc_id = str(uuid.uuid4())
    
    with Session(engine) as session:
        # Note: raw SQL interpolation for vector extension
        session.exec(text("""
            INSERT INTO documents (id, filename, content, embedding)
            VALUES (:id, :filename, :content, :embedding)
        """), {"id": doc_id, "filename": filename, "content": content, "embedding": str(embedding)})
        session.commit()
        
    return doc_id

async def search_documents(query: str, limit: int = 5):
    query_embedding = model.encode(query).tolist()
    
    with Session(engine) as session:
        # Cosine distance (<=>)
        results = session.exec(text("""
            SELECT filename, content, 1 - (embedding <=> :query_embedding) AS similarity
            FROM documents
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """), {"query_embedding": str(query_embedding), "limit": limit}).fetchall()
        
    return [{"filename": r[0], "content": r[1][:200] + "...", "similarity": float(r[2])} for r in results]
