@echo off
cd /d "C:\Users\aubre\Desktop\New folder"
set OILBOT_DB=oilbot.db
set EIA_API_KEY=mytqe9cWgvb30w7fYgIrAB6K2Dfq80e4VmKg9apL
set NEWSAPI_KEY=b9571ec6725649ca9107ae1dca3e5665
set PYTHONUNBUFFERED=1
set PYTHONDONTWRITEBYTECODE=1
python -u -m oilbot.main > bot_out.log 2>&1
