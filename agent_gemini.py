# src/agent_gemini.py
import google.generativeai as genai
import os
import time
from typing import List, Tuple
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from models import (
    AgentResponse, 
    EscalationDecision, 
    RetrievedDocument, 
    ConfidenceLevel,
    QueryCategory
)
from vector_store import VectorStore

load_dotenv()

class FlowSupportAgent:
    """Gemini-powered customer support agent with RAG"""
    
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.0 Flash (best free model)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Initialize vector store
        print("🔧 Initializing agent...")
        self.vector_store = VectorStore()
        print("✅ Agent ready!\n")
    
    def build_context(self, query: str, n_docs: int = 5) -> Tuple[str, List[RetrievedDocument]]:
        """Retrieve relevant documents and build context"""
        search_results = self.vector_store.search(query, n_results=n_docs)
        
        context_parts = []
        retrieved_docs = []
        
        # SMART: If installation query, inject requirements first
        query_lower = query.lower()
        if any(word in query_lower for word in ["install", "won't install", "can't install", "download", "setup"]):
            requirements_header = """[CRITICAL - CHECK SYSTEM REQUIREMENTS FIRST]

System Requirements:
- Mac: macOS 12.0 or newer, 500MB free space, microphone, internet
- Windows: Windows 10 (64-bit) or later, Intel i3/AMD Ryzen 3+, 4GB RAM (8GB recommended), 500MB space, microphone, internet  
- iPhone: iOS 18.3 or newer, 500MB free space, internet

ALWAYS verify user meets minimum requirements BEFORE providing troubleshooting steps.
---

"""
            context_parts.append(requirements_header)
        
        for i, (doc, metadata, distance) in enumerate(zip(
            search_results["documents"],
            search_results["metadatas"],
            search_results["distances"]
        ), 1):
            context_parts.append(
                f"[Document {i}] (Source: {metadata['source']}, Page: {metadata['page']})\n{doc}\n"
            )
            retrieved_docs.append(
                RetrievedDocument(
                    content=doc,
                    source=metadata['source'],
                    page=str(metadata['page']),
                    relevance_score=round(1 - distance, 3)
                )
            )
        
        context = "\n".join(context_parts)
        return context, retrieved_docs
    
    def needs_clarification(self, query: str, retrieved_docs: List[RetrievedDocument]) -> Tuple[bool, str]:
        """Smart clarification - only when genuinely needed"""
        
        query_lower = query.lower()
        
        # Device-specific PROBLEMS (agent can't help without knowing device)
        device_specific_problems = [
            "not working", "won't work", "doesn't work", "can't get",
            "won't install", "won't open", "crash", "error", 
            "won't paste", "freezes", "won't sync", "not pasting"
        ]
        
        # Installation/Setup (needs platform)
        installation_keywords = ["install", "setup", "download", "get started"]
        
        device_indicators = ["mac", "windows", "iphone", "ios", "desktop", "mobile", "pc", "computer", "phone"]
        
        has_device = any(indicator in query_lower for indicator in device_indicators)
        
        # Check if it's a problem or installation
        is_problem = any(prob in query_lower for prob in device_specific_problems)
        is_installation = any(inst in query_lower for inst in installation_keywords)
        
        # Only ask if genuinely needed
        if (is_problem or is_installation) and not has_device:
            return True, "device"
        
        return False, ""
    
    def analyze_escalation(self, query: str, retrieved_docs: List[RetrievedDocument]) -> EscalationDecision:
        """Determine if query should be escalated to human"""
        
        escalation_triggers = {
            "account_deletion": ["delete my account", "remove my account", "close my account", 
                               "delete my data", "remove my information", "gdpr request"],
            "billing_dispute": ["refund", "charge me wrong", "incorrect charge", "overcharged",
                              "billing issue", "dispute charge", "payment failed"],
            "human_request": ["speak to human", "talk to person", "talk to a person", 
                            "real person", "customer service representative", "talk to support"]
        }
        
        query_lower = query.lower()
        
        # Check for explicit escalation triggers
        for category, triggers in escalation_triggers.items():
            for trigger in triggers:
                if trigger in query_lower:
                    if category == "account_deletion":
                        return EscalationDecision(
                            should_escalate=True,
                            reason="Account deletion/data request - requires human verification",
                            category=QueryCategory.ACCOUNT,
                            priority="urgent",
                            suggested_team="privacy"
                        )
                    elif category == "billing_dispute":
                        return EscalationDecision(
                            should_escalate=True,
                            reason=f"Billing dispute detected: '{trigger}'",
                            category=QueryCategory.BILLING,
                            priority="high",
                            suggested_team="billing"
                        )
                    elif category == "human_request":
                        return EscalationDecision(
                            should_escalate=True,
                            reason="User explicitly requested human support",
                            category=QueryCategory.GENERAL,
                            priority="medium",
                            suggested_team="general"
                        )
        
        # Check retrieval quality
        if not retrieved_docs:
            return EscalationDecision(
                should_escalate=True,
                reason="No relevant documentation found",
                category=QueryCategory.GENERAL,
                priority="low",
                suggested_team="general"
            )
        
        avg_relevance = sum(d.relevance_score for d in retrieved_docs) / len(retrieved_docs)
        if avg_relevance < 0.25:
            return EscalationDecision(
                should_escalate=True,
                reason=f"Low confidence - avg relevance: {avg_relevance:.2%}",
                category=QueryCategory.GENERAL,
                priority="low",
                suggested_team="general"
            )
        
        # No escalation needed
        return EscalationDecision(
            should_escalate=False,
            reason="Can be answered from documentation",
            category=QueryCategory.PRODUCT,
            priority="low",
            suggested_team=None
        )
    
    def generate_response(self, query: str) -> AgentResponse:
        """Generate complete response with RAG"""
        start_time = time.time()
        
        # Retrieve relevant context
        context, retrieved_docs = self.build_context(query)
        
        # Check if we need clarification FIRST
        needs_clarify, clarify_type = self.needs_clarification(query, retrieved_docs)
        
        if needs_clarify:
            if clarify_type == "device":
                response_text = """I can help with that! To give you the most accurate solution, could you let me know which device you're using?

- **Mac** (macOS)
- **Windows** (PC)
- **iPhone** (iOS)

Just let me know and I'll provide specific instructions for your device!"""
                
                confidence = ConfidenceLevel.MEDIUM
                escalation = EscalationDecision(
                    should_escalate=False,
                    reason="Requesting device clarification",
                    category=QueryCategory.TECHNICAL,
                    priority="low",
                    suggested_team=None
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                avg_relevance = sum(d.relevance_score for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0.0
                
                return AgentResponse(
                    query=query,
                    response=response_text,
                    escalation=escalation,
                    retrieved_docs=retrieved_docs,
                    confidence=confidence,
                    avg_relevance_score=round(avg_relevance, 3),
                    processing_time_ms=processing_time
                )
        
        # Check escalation
        escalation = self.analyze_escalation(query, retrieved_docs)
        
        if escalation.should_escalate:
            response_text = f"""I'd like to connect you with our support team for personalized assistance.

**Why:** {escalation.reason}
**Team:** {escalation.suggested_team or 'General Support'}
**Priority:** {escalation.priority}

You can reach support at: support@useflow.ai"""
            
            confidence = ConfidenceLevel.LOW
        else:
            # Build prompt for Gemini
            system_prompt = """You are FlowSupport AI, a helpful customer success agent for Wispr Flow.

Your role:
- Answer questions using ONLY the provided documentation
- BE CONCISE and natural - like helping a colleague
- For installation issues: ALWAYS check system requirements FIRST
- For troubleshooting: Provide specific solutions
- Match Wispr Flow's voice: professional but approachable

Installation Issue Protocol:
When user says Flow "won't install" or "can't install":
1. **FIRST:** State minimum requirements for their device
2. **THEN:** Ask if they meet these requirements  
3. **ONLY IF they meet requirements:** Provide troubleshooting steps

System Requirements (memorize these):
- Mac: macOS 12.0+, 500MB space, microphone, internet
- Windows: Windows 10 64-bit+, Intel i3/Ryzen 3+, 4GB RAM (8GB rec), 500MB space, microphone, internet
- iPhone: iOS 18.3+, 500MB space, internet

Example Installation Response:
❌ BAD: "Try these 10 troubleshooting steps..." [too long, skips requirements]
✅ GOOD: "Flow requires iOS 18.3+ and 500MB free space. Check Settings → General → About for your iOS version. If below 18.3, update iOS first. Let me know if you meet these!"

Conversation Style:
- Keep responses under 100 words for requirements checks
- Keep other responses under 150 words
- Give COMPLETE answers with clear next steps
- End naturally: "Hope that helps!", "Let me know if you need anything else!"
- Never ask "Does that answer your question?"
- Be warm and human, not robotic

Guidelines:
- Don't make up information
- Check requirements BEFORE troubleshooting
- Be helpful and complete
- End warmly and naturally"""

            user_prompt = f"""User Question: {query}

Relevant Documentation:
{context}

Instructions:
1. Identify if this is an INSTALLATION or SETUP issue
2. If installation: START with system requirements check (under 100 words)
3. Ask user to verify requirements BEFORE providing other troubleshooting
4. If NOT installation: provide complete answer (under 150 words)
5. End naturally: "Let me know if that works!" or "Hope that helps!"

Provide a helpful, accurate, COMPLETE response."""

            # Call Gemini
            try:
                response = self.model.generate_content(user_prompt)
                response_text = response.text
            except Exception as e:
                response_text = f"I encountered an error processing your question. Please try rephrasing or contact support. Error: {str(e)}"
                confidence = ConfidenceLevel.LOW
                escalation.should_escalate = True
            
            # Calculate confidence
            avg_relevance = sum(d.relevance_score for d in retrieved_docs) / len(retrieved_docs)
            if avg_relevance > 0.7:
                confidence = ConfidenceLevel.HIGH
            elif avg_relevance > 0.5:
                confidence = ConfidenceLevel.MEDIUM
            else:
                confidence = ConfidenceLevel.LOW
        
        processing_time = int((time.time() - start_time) * 1000)
        avg_relevance = sum(d.relevance_score for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0.0
        
        return AgentResponse(
            query=query,
            response=response_text,
            escalation=escalation,
            retrieved_docs=retrieved_docs,
            confidence=confidence,
            avg_relevance_score=round(avg_relevance, 3),
            processing_time_ms=processing_time
        )

if __name__ == "__main__":
    # Test the agent
    agent = FlowSupportAgent()
    
    test_queries = [
        "How do I cancel my Pro trial?",
        "What apps does Flow work with?",
        "does slack work?",
        "Flow won't install on iPhone",
        "I want a refund"
    ]
    
    print("🧪 Testing agent with sample queries...\n")
    
    for query in test_queries:
        print(f"❓ Query: {query}")
        result = agent.generate_response(query)
        print(f"💬 Response: {result.response[:300]}...")
        print(f"📊 Confidence: {result.confidence}")
        print(f"⚠️  Escalated: {result.escalation.should_escalate}")
        print(f"⏱️  Time: {result.processing_time_ms}ms")
        print("-" * 80 + "\n")