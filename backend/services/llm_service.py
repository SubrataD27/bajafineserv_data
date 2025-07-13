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
        """Generate response using intelligent rule-based system"""
        try:
            # Extract key information from prompt with improved logic
            age_match = re.search(r'(\d+)[- ]?(?:year|yr|y)(?:ear)?[- ]?old|(\d+)[- ]?(?:M|F|male|female)', prompt, re.IGNORECASE)
            age = int(age_match.group(1) or age_match.group(2)) if age_match else None
            
            # Enhanced procedure/surgery detection
            surgery_keywords = {
                'knee': ['knee', 'joint', 'arthroscopy', 'meniscus', 'ligament'],
                'heart': ['heart', 'cardiac', 'bypass', 'angioplasty', 'stent', 'valve'],
                'cancer': ['cancer', 'tumor', 'oncology', 'chemotherapy', 'radiation', 'malignant'],
                'eye': ['eye', 'cataract', 'glaucoma', 'retina', 'cornea'],
                'brain': ['brain', 'neurosurgery', 'stroke', 'aneurysm'],
                'spine': ['spine', 'spinal', 'disc', 'vertebra'],
                'surgery': ['surgery', 'operation', 'procedure', 'treatment']
            }
            
            procedure = None
            procedure_type = None
            for proc_type, keywords in surgery_keywords.items():
                if any(keyword.lower() in prompt.lower() for keyword in keywords):
                    procedure = proc_type
                    procedure_type = proc_type
                    break
            
            # Extract location with enhanced detection
            location_patterns = [
                r'in ([A-Za-z]+)',
                r'at ([A-Za-z]+)',
                r'from ([A-Za-z]+)'
            ]
            location = None
            for pattern in location_patterns:
                location_match = re.search(pattern, prompt, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1).title()
                    break
            
            # Enhanced policy duration detection
            policy_duration_months = None
            duration_patterns = [
                (r'(\d+)[- ]?(?:month|mon)s?', 1),
                (r'(\d+)[- ]?(?:year|yr)s?', 12),
                (r'(\d+)[- ]?(?:day|d)s?', 1/30)
            ]
            
            for pattern, multiplier in duration_patterns:
                duration_match = re.search(pattern, prompt, re.IGNORECASE)
                if duration_match:
                    policy_duration_months = int(duration_match.group(1)) * multiplier
                    break
            
            # Intelligent decision making based on enhanced rules
            decision = "approved"
            base_amount = 100000.0  # Base coverage
            amount = base_amount
            justification_parts = []
            
            # Age-based rules with detailed logic
            if age:
                justification_parts.append(f"Patient age: {age} years")
                if age < 18:
                    amount *= 0.9
                    justification_parts.append("Minor patient - special considerations applied")
                elif age > 65:
                    if age > 75:
                        amount *= 0.7
                        justification_parts.append("Senior citizen (75+) - reduced coverage")
                    else:
                        amount *= 0.8
                        justification_parts.append("Senior citizen - age factor applied")
                elif age > 50:
                    amount *= 0.9
                    justification_parts.append("Middle-aged patient - slight adjustment")
            
            # Procedure-based intelligent rules
            procedure_amounts = {
                'knee': 150000,
                'heart': 500000,
                'cancer': 800000,
                'eye': 75000,
                'brain': 1000000,
                'spine': 300000,
                'surgery': 100000
            }
            
            if procedure:
                if procedure in procedure_amounts:
                    amount = procedure_amounts[procedure]
                    justification_parts.append(f"{procedure.title()} surgery approved - specialized coverage")
                    
                    # Additional procedure-specific rules
                    if procedure == 'cancer':
                        if age and age > 60:
                            amount *= 1.2
                            justification_parts.append("Cancer treatment for senior - premium coverage")
                    elif procedure == 'heart':
                        if age and age > 55:
                            amount *= 1.1
                            justification_parts.append("Cardiac procedure for senior - enhanced coverage")
                else:
                    justification_parts.append(f"General surgical procedure: {procedure}")
            
            # Policy duration rules with grace period
            if policy_duration_months is not None:
                justification_parts.append(f"Policy duration: {policy_duration_months:.1f} months")
                if policy_duration_months < 6:
                    decision = "rejected"
                    amount = 0.0
                    justification_parts.append("❌ REJECTION: Policy duration insufficient (minimum 6 months required)")
                elif policy_duration_months < 12:
                    amount *= 0.8
                    justification_parts.append("Partial coverage - policy duration less than 1 year")
                elif policy_duration_months >= 24:
                    amount *= 1.1
                    justification_parts.append("Premium coverage - long-term policy holder")
            
            # Location-based adjustments (city-specific costs)
            location_multipliers = {
                'mumbai': 1.2,
                'delhi': 1.15,
                'bangalore': 1.1,
                'chennai': 1.1,
                'pune': 1.05,
                'hyderabad': 1.05,
                'kolkata': 1.0,
                'ahmedabad': 0.95
            }
            
            if location and location.lower() in location_multipliers:
                multiplier = location_multipliers[location.lower()]
                amount *= multiplier
                justification_parts.append(f"Location-based adjustment for {location} (factor: {multiplier})")
            
            # Context-based adjustments from document analysis
            if context:
                context_lower = context.lower()
                if 'emergency' in context_lower:
                    amount *= 1.15
                    justification_parts.append("Emergency procedure - priority coverage")
                if 'specialist' in context_lower or 'consultant' in context_lower:
                    amount *= 1.1
                    justification_parts.append("Specialist consultation - enhanced coverage")
                if 'complications' in context_lower:
                    amount *= 1.2
                    justification_parts.append("Complications considered - extended coverage")
            
            # Final validations
            if decision == "approved" and amount > 0:
                # Ensure minimum coverage
                if amount < 25000:
                    amount = 25000
                    justification_parts.append("Minimum coverage threshold applied")
                
                # Round to nearest 1000
                amount = round(amount / 1000) * 1000
                
                # Final decision summary
                justification_parts.insert(0, f"✅ APPROVED: Coverage amount Rs. {amount:,.0f}")
            
            # Create comprehensive justification
            justification = "\n".join(justification_parts)
            
            # Create structured response with enhanced metadata
            response = {
                "decision": decision,
                "amount": amount,
                "justification": justification,
                "extracted_info": {
                    "age": age,
                    "procedure": procedure,
                    "procedure_type": procedure_type,
                    "location": location,
                    "policy_duration_months": policy_duration_months
                },
                "analysis_metadata": {
                    "processing_method": "intelligent_rule_based",
                    "confidence_factors": {
                        "age_detected": age is not None,
                        "procedure_detected": procedure is not None,
                        "location_detected": location is not None,
                        "policy_duration_detected": policy_duration_months is not None
                    }
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            print(f"Error in intelligent processing: {e}")
            return json.dumps({
                "decision": "requires_review",
                "amount": 0.0,
                "justification": "❌ Query requires manual review due to processing error",
                "extracted_info": {},
                "analysis_metadata": {"error": str(e)}
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