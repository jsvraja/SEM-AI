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
