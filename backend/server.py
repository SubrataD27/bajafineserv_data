from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime
import asyncio

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="HackRx 6.0 - LLM Query Retrieval System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/hackrx_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client.hackrx_db

# Collections
documents_collection = db.documents
queries_collection = db.queries
sessions_collection = db.sessions

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    session_id: str
    query: str
    decision: str
    amount: Optional[float] = None
    justification: str
    confidence_score: float
    referenced_clauses: List[Dict[str, Any]]
    processing_time: float

class DocumentInfo(BaseModel):
    id: str
    name: str
    type: str
    upload_date: datetime
    processed: bool

# Global variables for models (will be loaded on startup)
llm_service = None
document_processor = None
query_processor = None

@app.on_event("startup")
async def startup_event():
    """Initialize models and services on startup"""
    global llm_service, document_processor, query_processor
    
    # Initialize services
    from services.llm_service import LLMService
    from services.document_processor import DocumentProcessor
    from services.query_processor import QueryProcessor
    
    llm_service = LLMService()
    document_processor = DocumentProcessor()
    query_processor = QueryProcessor(llm_service, document_processor)
    
    # Process existing documents if any
    await process_existing_documents()

async def process_existing_documents():
    """Process PDF documents on startup"""
    import glob
    pdf_files = glob.glob("/app/*.pdf")
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        
        # Check if already processed
        existing_doc = await documents_collection.find_one({"name": filename})
        if not existing_doc:
            print(f"Processing document: {filename}")
            doc_id = str(uuid.uuid4())
            
            # Process the document
            processed_content = await document_processor.process_document(pdf_file)
            
            # Store in database
            doc_data = {
                "id": doc_id,
                "name": filename,
                "type": "pdf",
                "upload_date": datetime.utcnow(),
                "processed": True,
                "content": processed_content
            }
            await documents_collection.insert_one(doc_data)
            print(f"Document {filename} processed and stored")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents():
    """Get all processed documents"""
    docs = []
    async for doc in documents_collection.find({}):
        docs.append(DocumentInfo(
            id=doc["id"],
            name=doc["name"],
            type=doc["type"],
            upload_date=doc["upload_date"],
            processed=doc["processed"]
        ))
    return docs

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural language query"""
    try:
        start_time = datetime.utcnow()
        
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process the query
        result = await query_processor.process_query(
            query=request.query,
            session_id=session_id
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Store query and result
        query_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "query": request.query,
            "result": result,
            "timestamp": datetime.utcnow(),
            "processing_time": processing_time
        }
        await queries_collection.insert_one(query_data)
        
        # Return response
        return QueryResponse(
            session_id=session_id,
            query=request.query,
            decision=result["decision"],
            amount=result.get("amount"),
            justification=result["justification"],
            confidence_score=result["confidence_score"],
            referenced_clauses=result["referenced_clauses"],
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get query history for a session"""
    queries = []
    async for query in queries_collection.find({"session_id": session_id}).sort("timestamp", 1):
        queries.append({
            "id": query["id"],
            "query": query["query"],
            "result": query["result"],
            "timestamp": query["timestamp"],
            "processing_time": query["processing_time"]
        })
    return queries

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    total_documents = await documents_collection.count_documents({})
    total_queries = await queries_collection.count_documents({})
    session_ids = await queries_collection.distinct("session_id")
    total_sessions = len(session_ids)
    
    return {
        "total_documents": total_documents,
        "total_queries": total_queries,
        "total_sessions": total_sessions,
        "system_status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)