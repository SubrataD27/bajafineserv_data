"""
Query Processor for HackRx 6.0 - Main Query Processing Logic
Combines LLM and document processing for intelligent query handling
"""

import json
import re
from typing import Dict, Any, List
from datetime import datetime
import asyncio
from .llm_service import LLMService
from .document_processor import DocumentProcessor

class QueryProcessor:
    def __init__(self, llm_service: LLMService, document_processor: DocumentProcessor):
        self.llm_service = llm_service
        self.document_processor = document_processor
        
        # Decision rules and thresholds
        self.decision_rules = {
            "min_policy_duration_months": 6,
            "max_age_standard": 60,
            "max_age_premium": 75,
            "base_coverage_amount": 50000,
            "premium_multiplier": 1.5,
            "age_penalty_factor": 0.8
        }
        
        # Procedure mappings
        self.procedure_mappings = {
            "knee": {"covered": True, "category": "orthopedic", "base_amount": 75000},
            "heart": {"covered": True, "category": "cardiac", "base_amount": 200000},
            "surgery": {"covered": True, "category": "general", "base_amount": 50000},
            "cancer": {"covered": True, "category": "oncology", "base_amount": 500000},
            "dental": {"covered": False, "category": "dental", "base_amount": 0},
            "cosmetic": {"covered": False, "category": "cosmetic", "base_amount": 0}
        }
    
    async def process_query(self, query: str, session_id: str) -> Dict[str, Any]:
        """Main query processing pipeline"""
        try:
            # Step 1: Parse the query to extract structured information
            parsed_info = await self._parse_query_details(query)
            
            # Step 2: Search for relevant document chunks
            relevant_chunks = await self.document_processor.search_similar_chunks(query, top_k=5)
            
            # Step 3: Apply decision-making logic
            decision_result = await self._make_decision(parsed_info, relevant_chunks)
            
            # Step 4: Generate justification
            justification = await self._generate_justification(
                parsed_info, relevant_chunks, decision_result
            )
            
            # Step 5: Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                parsed_info, relevant_chunks, decision_result
            )
            
            # Step 6: Format response
            response = {
                "decision": decision_result["decision"],
                "amount": decision_result["amount"],
                "justification": justification,
                "confidence_score": confidence_score,
                "referenced_clauses": self._format_referenced_clauses(relevant_chunks),
                "parsed_info": parsed_info,
                "processing_metadata": {
                    "chunks_analyzed": len(relevant_chunks),
                    "decision_factors": decision_result.get("factors", []),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            return response
            
        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                "decision": "error",
                "amount": 0.0,
                "justification": f"Error processing query: {str(e)}",
                "confidence_score": 0.0,
                "referenced_clauses": [],
                "parsed_info": {},
                "processing_metadata": {}
            }
    
    async def _parse_query_details(self, query: str) -> Dict[str, Any]:
        """Parse query to extract structured information"""
        parsed_info = {
            "age": None,
            "gender": None,
            "procedure": None,
            "location": None,
            "policy_duration": None,
            "policy_duration_unit": None,
            "raw_query": query
        }
        
        # Extract age
        age_patterns = [
            r'(\d+)[- ]?(?:year|yr|y)(?:ear)?[- ]?old',
            r'(\d+)[- ]?(?:M|F|male|female)',
            r'(\d+)[yY]'
        ]
        
        for pattern in age_patterns:
            age_match = re.search(pattern, query, re.IGNORECASE)
            if age_match:
                parsed_info["age"] = int(age_match.group(1))
                break
        
        # Extract gender
        gender_match = re.search(r'(M|F|male|female)', query, re.IGNORECASE)
        if gender_match:
            gender = gender_match.group(1).lower()
            parsed_info["gender"] = "male" if gender in ["m", "male"] else "female"
        
        # Extract procedure/surgery
        procedure_keywords = list(self.procedure_mappings.keys())
        for keyword in procedure_keywords:
            if keyword.lower() in query.lower():
                parsed_info["procedure"] = keyword
                break
        
        # If no specific procedure found, look for general terms
        if not parsed_info["procedure"]:
            general_terms = ["surgery", "operation", "procedure", "treatment"]
            for term in general_terms:
                if term.lower() in query.lower():
                    parsed_info["procedure"] = "surgery"
                    break
        
        # Extract location
        location_match = re.search(r'in ([A-Za-z]+)', query, re.IGNORECASE)
        if location_match:
            parsed_info["location"] = location_match.group(1).title()
        
        # Extract policy duration
        duration_patterns = [
            r'(\d+)[- ]?(?:month|mon)[- ]?(?:old|policy)',
            r'(\d+)[- ]?(?:year|yr)[- ]?(?:old|policy)',
            r'(\d+)[- ]?(?:day|d)[- ]?(?:old|policy)'
        ]
        
        for pattern in duration_patterns:
            duration_match = re.search(pattern, query, re.IGNORECASE)
            if duration_match:
                parsed_info["policy_duration"] = int(duration_match.group(1))
                
                # Determine unit
                if "month" in pattern or "mon" in pattern:
                    parsed_info["policy_duration_unit"] = "months"
                elif "year" in pattern or "yr" in pattern:
                    parsed_info["policy_duration_unit"] = "years"
                    parsed_info["policy_duration"] *= 12  # Convert to months
                elif "day" in pattern or "d" in pattern:
                    parsed_info["policy_duration_unit"] = "days"
                    parsed_info["policy_duration"] = parsed_info["policy_duration"] / 30  # Convert to months
                break
        
        return parsed_info
    
    async def _make_decision(self, parsed_info: Dict[str, Any], relevant_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply decision-making logic based on parsed information and document context"""
        decision_factors = []
        decision = "approved"
        amount = self.decision_rules["base_coverage_amount"]
        
        # Check policy duration
        policy_duration = parsed_info.get("policy_duration", 0)
        if policy_duration and policy_duration < self.decision_rules["min_policy_duration_months"]:
            decision = "rejected"
            amount = 0.0
            decision_factors.append(f"Policy duration ({policy_duration} months) is less than minimum required ({self.decision_rules['min_policy_duration_months']} months)")
        
        # Check age factors
        age = parsed_info.get("age")
        if age and decision == "approved":
            if age > self.decision_rules["max_age_premium"]:
                decision = "rejected"
                amount = 0.0
                decision_factors.append(f"Age ({age}) exceeds maximum coverage age ({self.decision_rules['max_age_premium']})")
            elif age > self.decision_rules["max_age_standard"]:
                amount *= self.decision_rules["age_penalty_factor"]
                decision_factors.append(f"Age penalty applied for age {age}")
        
        # Check procedure coverage
        procedure = parsed_info.get("procedure")
        if procedure and decision == "approved":
            if procedure in self.procedure_mappings:
                procedure_info = self.procedure_mappings[procedure]
                if procedure_info["covered"]:
                    amount = procedure_info["base_amount"]
                    decision_factors.append(f"{procedure.title()} surgery is covered under {procedure_info['category']} category")
                else:
                    decision = "rejected"
                    amount = 0.0
                    decision_factors.append(f"{procedure.title()} is not covered under policy")
        
        # Apply document-based rules from relevant chunks
        for chunk in relevant_chunks:
            chunk_text = chunk["chunk"].lower()
            
            # Look for exclusions
            if "exclusion" in chunk_text or "not covered" in chunk_text:
                if procedure and procedure.lower() in chunk_text:
                    decision = "rejected"
                    amount = 0.0
                    decision_factors.append(f"Procedure found in exclusions: {chunk['document']}")
                    break
            
            # Look for specific coverage amounts
            coverage_match = re.search(r'coverage[^:]*:\s*(?:rs\.?\s*)?(\d+(?:,\d+)*)', chunk_text)
            if coverage_match and decision == "approved":
                coverage_amount = int(coverage_match.group(1).replace(',', ''))
                if coverage_amount > amount:
                    amount = coverage_amount
                    decision_factors.append(f"Coverage amount updated based on policy document: {chunk['document']}")
        
        return {
            "decision": decision,
            "amount": amount,
            "factors": decision_factors
        }
    
    async def _generate_justification(self, parsed_info: Dict[str, Any], relevant_chunks: List[Dict[str, Any]], decision_result: Dict[str, Any]) -> str:
        """Generate human-readable justification for the decision"""
        justification_parts = []
        
        # Add decision summary
        decision = decision_result["decision"]
        amount = decision_result["amount"]
        
        if decision == "approved":
            justification_parts.append(f"✅ Claim APPROVED for amount: Rs. {amount:,.2f}")
        elif decision == "rejected":
            justification_parts.append("❌ Claim REJECTED")
        else:
            justification_parts.append("⚠️ Claim requires manual review")
        
        # Add factors
        factors = decision_result.get("factors", [])
        if factors:
            justification_parts.append("\n📋 Decision Factors:")
            for i, factor in enumerate(factors, 1):
                justification_parts.append(f"{i}. {factor}")
        
        # Add parsed information summary
        if parsed_info:
            justification_parts.append("\n📝 Extracted Information:")
            
            if parsed_info.get("age"):
                justification_parts.append(f"• Age: {parsed_info['age']} years")
            if parsed_info.get("gender"):
                justification_parts.append(f"• Gender: {parsed_info['gender'].title()}")
            if parsed_info.get("procedure"):
                justification_parts.append(f"• Procedure: {parsed_info['procedure'].title()}")
            if parsed_info.get("location"):
                justification_parts.append(f"• Location: {parsed_info['location']}")
            if parsed_info.get("policy_duration"):
                unit = parsed_info.get("policy_duration_unit", "months")
                justification_parts.append(f"• Policy Duration: {parsed_info['policy_duration']} {unit}")
        
        # Add relevant document references
        if relevant_chunks:
            justification_parts.append(f"\n📄 Referenced Documents ({len(relevant_chunks)}):")
            for i, chunk in enumerate(relevant_chunks[:3], 1):  # Show top 3
                justification_parts.append(f"{i}. {chunk['document']} (relevance: {chunk['similarity']:.2f})")
        
        return "\n".join(justification_parts)
    
    def _calculate_confidence_score(self, parsed_info: Dict[str, Any], relevant_chunks: List[Dict[str, Any]], decision_result: Dict[str, Any]) -> float:
        """Calculate confidence score for the decision"""
        confidence_factors = []
        
        # Factor 1: Information completeness
        required_fields = ["age", "procedure", "policy_duration"]
        completed_fields = sum(1 for field in required_fields if parsed_info.get(field) is not None)
        info_completeness = completed_fields / len(required_fields)
        confidence_factors.append(info_completeness * 0.3)
        
        # Factor 2: Document relevance
        if relevant_chunks:
            avg_similarity = sum(chunk["similarity"] for chunk in relevant_chunks) / len(relevant_chunks)
            confidence_factors.append(avg_similarity * 0.4)
        else:
            confidence_factors.append(0.0)
        
        # Factor 3: Decision clarity
        factors = decision_result.get("factors", [])
        if factors:
            decision_clarity = min(len(factors) / 3, 1.0)  # More factors = more clarity
            confidence_factors.append(decision_clarity * 0.3)
        else:
            confidence_factors.append(0.1)
        
        # Calculate final confidence score
        confidence_score = sum(confidence_factors)
        return min(max(confidence_score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _format_referenced_clauses(self, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format referenced clauses for response"""
        formatted_clauses = []
        
        for chunk in relevant_chunks:
            clause = {
                "document": chunk["document"],
                "content": chunk["chunk"][:300] + "..." if len(chunk["chunk"]) > 300 else chunk["chunk"],
                "relevance_score": chunk["similarity"],
                "chunk_index": chunk["chunk_index"]
            }
            formatted_clauses.append(clause)
        
        return formatted_clauses
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get statistics about the query processor"""
        return {
            "llm_model_info": self.llm_service.get_model_info(),
            "document_summaries": self.document_processor.get_all_documents_summary(),
            "decision_rules": self.decision_rules,
            "procedure_mappings": self.procedure_mappings,
            "status": "active"
        }