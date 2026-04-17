# SEM AI Platform — Backend

## Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configure
Copy `.env.example` to `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
uvicorn main:app --reload
```

API runs at http://localhost:8000
Swagger docs at http://localhost:8000/docs
# Tue Apr 14 23:07:18 IST 2026
# Fri Apr 17 02:51:51 IST 2026
# rebuild Fri Apr 17 22:23:50 IST 2026
