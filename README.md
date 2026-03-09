# Customer Support Chatbot

Customer support chatbot for a fictional company (TechCorp) with 4 products. Uses LangChain + FAISS for knowledge retrieval and Groq (LLaMA 3.3 70B) as the LLM.

## What it does

- Loads product docs from text files, chunks them, and stores them in FAISS vector stores
- Routes user questions to the right product knowledge base using an LLM
- Has 6 tools the agent can call (ticket lookup, create ticket, diagnostics, upgrade calculator, compatibility check, callback scheduling)
- Keeps conversation context with LangChain memory
- Filters out hallucinations and provides escalation paths
- Works as both a CLI app and a Streamlit web app

## Project Structure

```
customer_support_chatbot/
├── data/
│   ├── product_a/          # CloudStore Pro docs
│   ├── product_b/          # SecureVault AI docs
│   ├── product_c/          # DataFlow Analytics docs
│   └── product_d/          # TeamFlow Pro docs
├── knowledge_bases/
│   ├── kb_manager.py       # KnowledgeBase + router
│   ├── product_a_kb.py
│   ├── product_b_kb.py
│   ├── product_c_kb.py
│   └── product_d_kb.py
├── tools/
│   ├── compatibility_checker.py
│   ├── diagnostics.py
│   ├── order_lookup.py
│   ├── ticket_manager.py
│   ├── callback_scheduler.py
│   └── plan_upgrade.py
├── conversation/
│   └── memory_manager.py
├── utils/
│   ├── document_processor.py
│   └── response_formatter.py
├── config.py
├── main.py                 # CLI
├── streamlit_app.py        # Web UI
└── requirements.txt
```

## LangChain Components

| Component | Where | What for |
|---|---|---|
| FAISS | document_processor.py | Vector store for each product |
| HuggingFaceEmbeddings | document_processor.py | all-MiniLM-L6-v2 embeddings |
| RecursiveCharacterTextSplitter | document_processor.py | Chunk docs before indexing |
| TextLoader / PyPDFLoader / CSVLoader | document_processor.py | Load different file types |
| RetrievalQA | kb_manager.py | QA chain over FAISS |
| LLMChain + PromptTemplate | kb_manager.py | Route queries to right KB |
| ConversationBufferMemory | memory_manager.py | Keep chat context |
| ConversationSummaryMemory | memory_manager.py | Summarize long conversations |
| BaseTool | tools/*.py | 6 custom tools |
| create_react_agent (LangGraph) | streamlit_app.py | Agent that picks which tool to use |
| ChatGroq | everywhere | LLM (Groq) |

## Setup

You need Python 3.10+ and a Groq API key (free at https://console.groq.com/keys).

```bash
# clone and cd into the project
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd project1_customer_support_v2

# (optional) virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# install packages
pip install -r requirements.txt
```

First run downloads the embedding model (~80 MB), after that it's cached.

## Running

**Streamlit UI (recommended):**
```bash
python -m streamlit run streamlit_app.py
```
Opens at http://localhost:8501. Paste your Groq API key in the sidebar and start chatting — no `.env` file needed.

**CLI:**
```bash
# for CLI you need a .env file
echo GROQ_API_KEY=gsk_your_key_here > .env
python main.py
```
Type questions like "My CloudStore sync stopped working" or "Check ticket TKT-005". Type `quit` to exit.

## Example queries

- `CloudStore sync stopped working` - routes to CloudStore KB
- `Check ticket TKT-005` - uses ticket lookup tool
- `Are CloudStore and DataFlow compatible?` - uses compatibility checker
- `What's the status of SecureVault AI?` - uses diagnostics tool
- `Upgrade CloudStore from Starter to Business` - uses plan upgrade tool
- `Schedule a callback for SSO help` - uses callback scheduler

## Deploying to Streamlit Cloud

1. Push to GitHub
2. Go to share.streamlit.io, click New App
3. Pick your repo, set main file to `streamlit_app.py`
4. In Advanced settings > Secrets, add: `GROQ_API_KEY = "gsk_your_key_here"`
5. Deploy

---
Built for Lab 4 - AI-Based Applications course.
