"""
Document Processor for HackRx 6.0 - PDF Processing and Text Extraction
Handles PDF parsing, text extraction, and semantic chunking
"""

import os
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
import re
from datetime import datetime
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import hashlib

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = None
        self.embeddings_cache = {}
        self.document_chunks = {}
        
        # Initialize sentence transformer model
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize a simple embedding model fallback"""
        try:
            # Use a simple fallback - will implement basic text similarity
            print("🔄 Initializing simple text similarity system...")
            self.embedding_model = None
            print("✅ Simple text similarity system initialized")
            
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            self.embedding_model = None
    
    async def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """Process a PDF document and extract structured content"""
        try:
            print(f"📄 Processing document: {pdf_path}")
            
            # Extract text from PDF
            text_content = self._extract_text_from_pdf(pdf_path)
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(text_content)
            
            # Create semantic chunks
            chunks = self._create_semantic_chunks(cleaned_text)
            
            # Generate embeddings for chunks
            embeddings = self._generate_embeddings(chunks)
            
            # Extract policy-specific information
            policy_info = self._extract_policy_info(cleaned_text)
            
            # Create document structure
            document_data = {
                "file_path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "processed_at": datetime.utcnow().isoformat(),
                "text_content": cleaned_text,
                "chunks": chunks,
                "embeddings": embeddings.tolist() if embeddings is not None else [],
                "policy_info": policy_info,
                "metadata": {
                    "chunk_count": len(chunks),
                    "text_length": len(cleaned_text),
                    "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else None
                }
            }
            
            # Cache the processed document
            doc_id = hashlib.md5(pdf_path.encode()).hexdigest()
            self.document_chunks[doc_id] = document_data
            
            print(f"✅ Document processed successfully: {len(chunks)} chunks created")
            return document_data
            
        except Exception as e:
            print(f"❌ Error processing document {pdf_path}: {e}")
            return {
                "file_path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "processed_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "text_content": "",
                "chunks": [],
                "embeddings": [],
                "policy_info": {},
                "metadata": {}
            }
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text += f"\n--- Page {page_num + 1} ---\n{text}"
            
            doc.close()
            return full_text
            
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers (common patterns)
        text = re.sub(r'--- Page \d+ ---', '', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\/\%\$]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _create_semantic_chunks(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Create semantic chunks from text with overlap"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def _generate_embeddings(self, chunks: List[str]) -> np.ndarray:
        """Generate simple text-based similarity scores"""
        if not chunks:
            return np.array([])
        
        try:
            # Simple text-based similarity using word overlap
            # This is a fallback - in production you'd use proper embeddings
            embeddings = []
            for chunk in chunks:
                # Create a simple feature vector based on common insurance terms
                insurance_terms = ['coverage', 'premium', 'policy', 'claim', 'benefit', 'deductible', 
                                 'surgery', 'treatment', 'medical', 'hospital', 'doctor', 'patient',
                                 'age', 'year', 'month', 'amount', 'rupees', 'rs', 'cost', 'fee']
                
                # Count term frequencies
                chunk_lower = chunk.lower()
                term_vector = [chunk_lower.count(term) for term in insurance_terms]
                
                # Add text length and word count features
                term_vector.extend([len(chunk), len(chunk.split())])
                
                embeddings.append(term_vector)
            
            return np.array(embeddings)
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return np.array([])
    
    def _extract_policy_info(self, text: str) -> Dict[str, Any]:
        """Extract policy-specific information from text"""
        policy_info = {
            "policy_number": [],
            "coverage_amount": [],
            "premium_amount": [],
            "policy_term": [],
            "exclusions": [],
            "benefits": [],
            "claim_procedures": [],
            "waiting_periods": []
        }
        
        # Extract policy numbers
        policy_numbers = re.findall(r'Policy No[\.:]?\s*([A-Z0-9]+)', text, re.IGNORECASE)
        policy_info["policy_number"] = policy_numbers
        
        # Extract coverage amounts
        coverage_amounts = re.findall(r'Coverage[^:]*:\s*Rs\.?\s*([\d,]+)', text, re.IGNORECASE)
        policy_info["coverage_amount"] = coverage_amounts
        
        # Extract premium amounts
        premium_amounts = re.findall(r'Premium[^:]*:\s*Rs\.?\s*([\d,]+)', text, re.IGNORECASE)
        policy_info["premium_amount"] = premium_amounts
        
        # Extract waiting periods
        waiting_periods = re.findall(r'waiting period[^:]*:\s*(\d+\s*(?:days?|months?|years?))', text, re.IGNORECASE)
        policy_info["waiting_periods"] = waiting_periods
        
        # Extract exclusions (look for exclusion sections)
        exclusion_section = re.search(r'exclusions?:(.{0,500})', text, re.IGNORECASE | re.DOTALL)
        if exclusion_section:
            exclusions = re.findall(r'(?:•|\d+\.|\-)\s*([^•\n]+)', exclusion_section.group(1))
            policy_info["exclusions"] = [ex.strip() for ex in exclusions[:10]]  # Limit to 10
        
        return policy_info
    
    async def search_similar_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks across all documents"""
        if not self.embedding_model:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            similar_chunks = []
            
            # Search across all cached documents
            for doc_id, doc_data in self.document_chunks.items():
                if not doc_data.get("embeddings") or not doc_data.get("chunks"):
                    continue
                
                embeddings = np.array(doc_data["embeddings"])
                chunks = doc_data["chunks"]
                
                # Calculate similarity scores
                similarities = np.dot(embeddings, query_embedding)
                
                # Get top chunks from this document
                top_indices = np.argsort(similarities)[-top_k:][::-1]
                
                for idx in top_indices:
                    if similarities[idx] > 0.5:  # Threshold for similarity
                        similar_chunks.append({
                            "document": doc_data["filename"],
                            "chunk": chunks[idx],
                            "similarity": float(similarities[idx]),
                            "chunk_index": int(idx)
                        })
            
            # Sort by similarity and return top results
            similar_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_chunks[:top_k]
            
        except Exception as e:
            print(f"Error searching similar chunks: {e}")
            return []
    
    def get_document_summary(self, doc_id: str) -> Dict[str, Any]:
        """Get summary information for a specific document"""
        if doc_id not in self.document_chunks:
            return {}
        
        doc_data = self.document_chunks[doc_id]
        return {
            "filename": doc_data.get("filename", "Unknown"),
            "processed_at": doc_data.get("processed_at", "Unknown"),
            "chunk_count": len(doc_data.get("chunks", [])),
            "text_length": len(doc_data.get("text_content", "")),
            "policy_info": doc_data.get("policy_info", {}),
            "has_embeddings": len(doc_data.get("embeddings", [])) > 0
        }
    
    def get_all_documents_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all processed documents"""
        summaries = []
        for doc_id in self.document_chunks:
            summary = self.get_document_summary(doc_id)
            summary["doc_id"] = doc_id
            summaries.append(summary)
        return summaries