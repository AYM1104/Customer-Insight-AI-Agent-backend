# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api.routes.gbizinfo import company_search, company_detail
from app.api.routes.edinet import yuho_search

app = FastAPI(
    title="顧客理解AIエージェント",
    description="法人情報取得や企業分析のためのAPI",
    version="1.0.0"
)

# CORS（フロントからの呼び出し許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 許可するオリジン
    allow_credentials=True,
    allow_methods=["*"],             # 全HTTPメソッド許可
    allow_headers=["*"],             # 全ヘッダー許可
)

# ルーター登録
app.include_router(company_search.router)
app.include_router(company_detail.router)
app.include_router(yuho_search.router)

# 動作確認用
@app.get("/")
def read_root():
    return {"message": "今日もがんばろう！"}