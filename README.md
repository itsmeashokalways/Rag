# RAG Document Q&A Assistant

## Overview

A Retrieval-Augmented Generation (RAG) based Document Question Answering system built using:

- Python  
- PostgreSQL with pgvector  
- Streamlit UI  
- Embeddings and LLM (OpenAI-compatible, Groq recommended)

### It allows you to:

- Upload documents (PDF, DOCX, TXT, MD)  
- Store embeddings in PostgreSQL  
- Ask questions based only on your documents  
- Get answers with source citations  

---

## How It Works

Documents → Chunking → Embeddings → PostgreSQL  
↓  
User Query  
↓  
Retrieve Top-K Chunks  
↓  
LLM Generates Answer  

---

## Features

### Core Capabilities

- Ask questions from your documents  
- Retrieve relevant chunks using vector similarity  
- Generate answers strictly from documents (no hallucination)  
- Show source citations  
- Support follow-up questions using chat context  

### Conversational Intelligence

- Handles follow-up queries such as:
  - "Explain about it"
  - "Why did it increase?"
- Uses last 6 chat messages for context  
- Query rewriting for better retrieval  

### Session Management

- Create multiple chat sessions  
- Store chat history in PostgreSQL  
- Resume previous conversations  
- Auto-name sessions based on first query  

### Data Management

- Refresh documents anytime from UI  
- Sync database with file system  
- Automatically removes deleted files  

---

## Architecture

User Input → Query Rewriting → Embedding → PostgreSQL → Top-K Chunks → LLM → Answer + Sources → Store Chat  

---

## Tech Stack

- UI: Streamlit  
- Backend: Python  
- Database: PostgreSQL  
- Vector DB: pgvector  
- Embeddings: Sentence Transformers  
- LLM: OpenAI-compatible (Groq supported)  

---

## Project Structure

app/
├── main.py  
├── llm.py  
├── retrivel.py  
├── db.py  
├── insert.py  
├── embedding.py  
├── chunk.py  
├── ingestion.py  
├── config.py  

Scripts/  
├── init_db.py  
├── init_db.sql  

---

## Setup Instructions

### 1. Create Virtual Environment

Windows:
python -m venv venv  
venv\Scripts\activate  

Mac/Linux:
python3 -m venv venv  
source venv/bin/activate  

---

### 2. Install Dependencies

pip install -r requirements.txt  

If installation fails:
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt  

If PostgreSQL error:
pip install psycopg2-binary  

Recommended Python version: 3.10 or 3.11  

---

### 3. Setup PostgreSQL

Install PostgreSQL and ensure it is running  

---

### 4. Install pgvector

Windows:
Download pgvector binaries and copy into PostgreSQL directory  

Linux:
sudo apt update  
sudo apt install postgresql-XX-pgvector  

Mac:
brew install pgvector  

---

### 5. Enable pgvector

Run in PostgreSQL:
CREATE EXTENSION IF NOT EXISTS vector;  

---

### 6. Environment Configuration

Copy .env.example to .env and update values  
- Use Groq API and model llama-3.3-70b-versatile
  ```LLM_API_KEY=YOUR API KEY
  LLM_MODEL=YOUR API MODEL(llama-3.3-70b-versatile is recommended)
  EMBEDDING_MODEL=all-MiniLM-L6-v2(USE THIS EMBEDDING MODEL)

  DOCS_PATH=data

  POSTGRES_HOST=YOUR_HOST
  POSTGRES_PORT=5432(USE THIS DEFAULT PORT)
  POSTGRES_DB=YOUR_DB
  POSTGRES_USER=USERNAME
  POSTGRES_PASSWORD=PASSWORD
  
  TOP_K=4
  CHUNK_SIZE=800
  CHUNK_OVERLAP=100
  MAX_HISTORY_MESSAGES=6
  
  APP_PORT=8501 ```  

---

### 7. Initialize Database

python -m Scripts.init_db  

---

### 8. Add Documents

Supported formats:
PDF, TXT, DOCX, MD  

---

### 9. Run Application

streamlit run app/main.py  

---

## Usage

- Click New Chat  
- Ask questions  
- View answers with sources  
- Continue conversation  
- Refresh documents after adding files  

---

## Author

Ashok V  


---

## Main Notes

- Avoid restricted networks (SSL issues may block API calls)  
- Use Groq API and model llama-3.3-70b-versatile  
- Run in order: init_db.py → main.py  
- Always refresh documents before querying  
