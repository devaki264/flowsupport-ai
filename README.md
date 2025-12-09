# FlowSupport AI: Building Scalable Customer Success Operations

> An AI-powered support system that handles tier-1 queries autonomously while intelligently routing complex issues to the right team with full context.

**Built by:** Dev | **For:** Wispr Flow CS AI Agent Engineer Role  
**Timeline:** 48 hours from concept to working demo  
**Tech Stack:** Gemini 2.0 Flash, ChromaDB, Sentence Transformers, Pydantic, Streamlit

---

## 🎬 The Story: From Problem to Production-Ready Demo

### The Challenge

When I read the Wispr Flow CS AI Agent Engineer job description, one requirement stood out:

> "AI agents handle a majority of support interactions autonomously."

But what does "autonomously" really mean? It's not just answering questions—it's:
- **Knowing when you CAN help** (and doing it well)
- **Knowing when you CAN'T help** (and escalating gracefully)
- **Gathering the right context** (without annoying the user)
- **Providing consistent quality** (24/7, across all scenarios)

So I built FlowSupport AI to demonstrate how I'd approach this challenge.

---

## 🚀 What I Built

### Core System: Autonomous Support with Intelligent Guardrails

FlowSupport AI is a **RAG-powered customer success agent** that:

1. **Answers tier-1 queries** using Wispr Flow documentation
2. **Asks smart clarification questions** only when genuinely needed
3. **Escalates appropriately** with full context (team, priority, reason)
4. **Tracks performance** in real-time (resolution rate, confidence, response time)

But the interesting part isn't *what* I built—it's *how* I built it and *what I learned*.

---

## 📸 Demo: See It In Action

### Feature 1: Smart Clarification System
**The Problem:** Most chatbots either ask too many questions (annoying) or too few (give wrong answers).

**My Solution:** Context-aware clarification that only triggers when the agent genuinely needs device info to help.

![Smart Clarification](Screenshot_2025-12-09_110239.png)

**What's Happening:**
- User says "Flow won't install" (no device specified)
- Agent detects: installation problem + no device indicator
- Asks for device ONLY because it's needed to provide correct instructions
- Won't ask for billing questions, features, etc.

**Code Logic:**
```python


