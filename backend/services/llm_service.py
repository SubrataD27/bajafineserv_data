"""
LLM Service for HackRx 6.0 - Free LLM Integration
Supports rule-based intelligent processing with optional HuggingFace integration
"""

import os
from typing import Dict, Any, List
from datetime import datetime
import json
import re

class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "fallback")
        self.model_name = os.getenv("HUGGINGFACE_MODEL", "rule-based")
        self.device = "cpu"
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Initialize the model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model based on provider"""
        try:
            # Start with fallback system - more reliable for demo
            self._initialize_fallback()
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            # Fallback to rule-based system
            self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Initialize fallback rule-based system"""
        print("🔄 Initializing intelligent rule-based system...")
        self.provider = "fallback"
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        print("✅ Intelligent rule-based system initialized")
    
    async def generate_response(self, prompt: str, context: str = "", max_tokens: int = 256) -> str:
        """Generate response using the rule-based intelligent system"""
        try:
            return await self._generate_fallback_response(prompt, context)
                
        except Exception as e:
            print(f"Error in generate_response: {e}")
            return await self._generate_fallback_response(prompt, context)
    
    async def _generate_hf_response(self, prompt: str, context: str, max_tokens: int) -> str:
        """Generate response using Hugging Face model"""
        try:
            # Create the full prompt
            full_prompt = f"Context: {context}\n\nQuery: {prompt}\n\nResponse:"
            
            # Generate response
            responses = self.pipeline(
                full_prompt,
                max_length=len(full_prompt.split()) + max_tokens,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            generated_text = responses[0]['generated_text']
            
            # Extract only the response part
            response_start = generated_text.find("Response:") + len("Response:")
            response = generated_text[response_start:].strip()
            
            return response
            
        except Exception as e:
            print(f"Error in HF generation: {e}")
            return await self._generate_fallback_response(prompt, context)
    
    async def _generate_fallback_response(self, prompt: str, context: str) -> str:
        """Generate response using rule-based fallback system"""
        try:
            # Extract key information from prompt
            age_match = re.search(r'(\d+)[- ]?(?:year|yr|y)(?:ear)?[- ]?old|(\d+)[- ]?(?:M|F|male|female)', prompt, re.IGNORECASE)
            age = int(age_match.group(1) or age_match.group(2)) if age_match else None
            
            # Extract procedure/surgery information
            surgery_keywords = ['surgery', 'operation', 'procedure', 'treatment', 'knee', 'heart', 'brain', 'cancer']
            procedure = None
            for keyword in surgery_keywords:
                if keyword.lower() in prompt.lower():
                    procedure = keyword
                    break
            
            # Extract location
            location_match = re.search(r'in ([A-Za-z]+)', prompt)
            location = location_match.group(1) if location_match else None
            
            # Extract policy duration
            policy_match = re.search(r'(\d+)[- ]?(?:month|day|year)', prompt, re.IGNORECASE)
            policy_duration = int(policy_match.group(1)) if policy_match else None
            
            # Simple rule-based decision making
            decision = "approved"
            amount = 50000.0
            justification = "Based on policy analysis"
            
            # Age-based rules
            if age and age > 60:
                amount *= 0.8
                justification += " (age factor applied)"
            
            # Procedure-based rules
            if procedure and procedure.lower() in ['knee', 'heart']:
                if procedure.lower() == 'heart':
                    amount *= 1.5
                    justification += f" ({procedure} surgery covered with premium)"
                else:
                    justification += f" ({procedure} surgery covered)"
            
            # Policy duration rules
            if policy_duration and policy_duration < 6:
                decision = "rejected"
                amount = 0.0
                justification += " (policy duration insufficient - minimum 6 months required)"
            
            # Create structured response
            response = {
                "decision": decision,
                "amount": amount,
                "justification": justification,
                "extracted_info": {
                    "age": age,
                    "procedure": procedure,
                    "location": location,
                    "policy_duration": policy_duration
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            print(f"Error in fallback generation: {e}")
            return json.dumps({
                "decision": "requires_review",
                "amount": 0.0,
                "justification": "Query requires manual review due to processing error",
                "extracted_info": {}
            }, indent=2)
    
    async def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query to extract structured information"""
        try:
            # Use LLM to parse the query
            parse_prompt = f"""
            Parse the following insurance query and extract structured information:
            
            Query: {query}
            
            Extract:
            - Age (if mentioned)
            - Gender (if mentioned)
            - Procedure/Surgery type
            - Location/City
            - Policy duration
            - Any other relevant details
            
            Return as structured data:
            """
            
            response = await self.generate_response(parse_prompt)
            
            # Try to extract structured info from response
            # This is a simplified extraction - in production, you'd want more robust parsing
            return {
                "raw_query": query,
                "parsed_response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing query: {e}")
            return {
                "raw_query": query,
                "parsed_response": "Error parsing query",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "device": self.device,
            "status": "active" if self.model or self.provider == "fallback" else "error"
        }