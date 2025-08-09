# app/main.py
from fastapi import FastAPI
from app.api.routes.gbizinfo import company_search, company_detail

app = FastAPI(
    title="顧客理解AIエージェント",
    description="法人情報取得や企業分析のためのAPI",
    version="1.0.0"
)

# ルーター登録
app.include_router(company_search.router)
app.include_router(company_detail.router)

# 動作確認用
@app.get("/")
def read_root():
    return {"message": "今日もがんばろう！"}