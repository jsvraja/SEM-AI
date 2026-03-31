#!/bin/bash
cd ~/Personal/sem-app/backend
source venv/bin/activate
export GEMINI_API_KEY=AIzaSyAVp_F9Qyp_Md1Y7d2z0W7THG9XLgvfTxA
export GOOGLE_CLIENT_ID=70585307844-8g4fvtt725t78ebdl15a6p8ru2uc7tid.apps.googleusercontent.com
export GOOGLE_CLIENT_SECRET=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
export GOOGLE_ADS_DEVELOPER_TOKEN=4qhmtyOKxSLVC5voobpxsQ
export GOOGLE_ADS_LOGIN_CUSTOMER_ID=6525543013
export GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
export FRONTEND_URL=http://localhost:5173
uvicorn main_with_ads:app --reload
