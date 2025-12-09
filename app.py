# ui/app.py
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agent_gemini import FlowSupportAgent

st.set_page_config(
    page_title="FlowSupport AI - CS Operations Demo",
    page_icon="🎤",
    layout="wide"
)

# Initialize agent
@st.cache_resource
def load_agent():
    return FlowSupportAgent()

agent = load_agent()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
    st.session_state.escalations = 0
    st.session_state.high_confidence = 0
    st.session_state.clarifications = 0

# Header
st.title("🎤 FlowSupport AI")
st.caption("AI-Powered Customer Success Operations for Wispr Flow")

# Sidebar with metrics
with st.sidebar:
    st.header("📊 Operations Metrics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Queries", st.session_state.query_count)
    with col2:
        st.metric("Escalations", st.session_state.escalations)
    
    if st.session_state.query_count > 0:
        autonomous_rate = ((st.session_state.query_count - st.session_state.escalations) / st.session_state.query_count) * 100
        st.metric("Autonomous Resolution", f"{autonomous_rate:.1f}%", 
                 delta=f"Target: 70%", delta_color="normal")
        
        confidence_rate = (st.session_state.high_confidence / st.session_state.query_count) * 100
        st.metric("High Confidence Rate", f"{confidence_rate:.1f}%")
        
        clarification_rate = (st.session_state.clarifications / st.session_state.query_count) * 100
        st.metric("Context Gathering", f"{clarification_rate:.1f}%")
    
    st.divider()
    
    st.subheader("💡 Example Queries")
    st.caption("Test different scenarios:")
    
    example_questions = [
        "How do I cancel my trial?",
        "What apps does Flow work with?",
        "Flow won't install",  # Triggers clarification
        "My transcription is bad",  # Triggers clarification
        "I want a refund"  # Triggers escalation
    ]
    
    for q in example_questions:
        if st.button(q, key=f"example_{q}", use_container_width=True):
            st.session_state.current_query = q
    
    st.divider()
    
    st.subheader("🎯 TAM Productivity Impact")
    st.markdown("""
    **What this agent enables:**
    - ✅ 24/7 support coverage
    - ✅ Instant responses (<2s)
    - ✅ Consistent quality
    - ✅ Frees TAMs for complex issues
    - ✅ Scalable knowledge base
    """)

# Main chat interface
st.subheader("💬 Customer Support Interface")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant" and "metadata" in message:
            with st.expander("📊 Agent Intelligence Details"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Confidence", message["metadata"]["confidence"].upper())
                with col2:
                    st.metric("Relevance", f"{message['metadata']['relevance']:.1%}")
                with col3:
                    st.metric("Response Time", f"{message['metadata']['time']}ms")
                
                if message["metadata"]["escalated"]:
                    st.error(f"🚨 **ESCALATED TO: {message['metadata'].get('team', 'Support').upper()}**")
                    st.caption(f"Reason: {message['metadata']['escalation_reason']}")
                    st.caption(f"Priority: {message['metadata'].get('priority', 'medium').upper()}")
                
                if message["metadata"]["clarification"]:
                    st.info("💬 Context gathering - asking follow-up question")
                
                if message["metadata"]["docs"]:
                    st.write("**Retrieved Knowledge:**")
                    for i, doc in enumerate(message["metadata"]["docs"][:3], 1):
                        st.caption(f"{i}. {doc['source']} (Page {doc['page']}) - {doc['relevance']:.1%} match")

# Chat input
if prompt := st.chat_input("Ask about Wispr Flow...") or st.session_state.get("current_query"):
    if "current_query" in st.session_state:
        prompt = st.session_state.current_query
        del st.session_state.current_query
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            result = agent.generate_response(prompt)
            
            # Update metrics
            st.session_state.query_count += 1
            if result.escalation.should_escalate:
                st.session_state.escalations += 1
            if result.confidence == "high":
                st.session_state.high_confidence += 1
            if result.escalation.reason == "Requesting device clarification":
                st.session_state.clarifications += 1
            
            # Display response
            if result.escalation.should_escalate:
                st.warning("⚠️ Escalation Recommended")
            
            st.markdown(result.response)
            
            # Add to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.response,
                "metadata": {
                    "confidence": result.confidence,
                    "relevance": result.avg_relevance_score,
                    "time": result.processing_time_ms,
                    "escalated": result.escalation.should_escalate,
                    "escalation_reason": result.escalation.reason,
                    "priority": result.escalation.priority,
                    "team": result.escalation.suggested_team,
                    "clarification": result.escalation.reason == "Requesting device clarification",
                    "docs": [
                        {
                            "source": doc.source,
                            "page": doc.page,
                            "relevance": doc.relevance_score
                        } for doc in result.retrieved_docs[:3]
                    ]
                }
            })

# Footer
st.divider()
st.caption("**CS Operations Demo** | Built with Gemini 2.0, ChromaDB & Streamlit | Portfolio Project for Wispr Flow")