# Datazoic AI v4.1

Professional Gemini-powered business/invoice chatbot built on the Invoice Agent v3 backend.

## v4.1 fixes
- Gemini answers general questions instead of being limited to the RAG knowledge base.
- Company-specific knowledge is passed to Gemini as authoritative context.
- Invoice/system actions remain deterministic and are never invented by Gemini.
- Browser conversation state is persisted in localStorage, so refresh/back/forward navigation does not lose the chat.
- `/chat` accepts recent conversation history.
- `/health` reports Gemini configuration without exposing the API key.

## Run on Windows
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/

## Important
The included `.env` contains the Gemini key supplied for this build. Do not commit it to source control. Rotate the key after testing if it has been exposed outside your trusted environment.
