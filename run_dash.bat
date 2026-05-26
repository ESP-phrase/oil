@echo off
cd /d "C:\Users\aubre\Desktop\New folder"
set OILBOT_DB=oilbot.db
set STREAMLIT_EMAIL=
set EIA_API_KEY=mytqe9cWgvb30w7fYgIrAB6K2Dfq80e4VmKg9apL
set NEWSAPI_KEY=b9571ec6725649ca9107ae1dca3e5665
start /B streamlit run oilbot/dashboard/app.py --server.headless=true > dash_out.log 2>&1
