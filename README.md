# AI SQL Agent

Ask a database questions in plain English.

## Flow
```
question -> schema -> LLM writes SQL -> validate -> execute -> explain
                          ^                  |          |
                          +---- retry on error ---------+
```

## Files
| File | Job |
|---|---|
| `db.py` | connect, read schema, run queries |
| `seed.py` | create sample shop database |
| `validator.py` | allow only one safe SELECT, add LIMIT |
| `agent.py` | LangGraph agent (generate, retry, explain, memory) |
| `api.py` | FastAPI `/ask` endpoint |
| `app.py` | Streamlit chat UI |

## Run
```bash
pip install -r requirements.txt
export GOOGLE_API_KEY=your-key       # Gemini key
python seed.py                       # creates shop.db
uvicorn api:api --reload             # terminal 1
streamlit run app.py                 # terminal 2
```
Quick test without UI: `python agent.py`

## Use MySQL
```bash
export DATABASE_URL="mysql+pymysql://readonly_user:pass@localhost:3306/shop"
```
Use a read-only DB user. The validator is one safety layer, permissions are the second.

## Try
- Total quantity sold for each product
- Top 3 customers by spending
- Now only Pune  *(follow-up)*
