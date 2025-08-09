"""
app/core/config.py
- アプリ全体で使用する設定値や環境変数の読み込みを行うモジュール。
"""
import os
from dotenv import load_dotenv

# .env を読み込み
load_dotenv()

# gBizINFO 設定
GBIZINFO_API_TOKEN = os.getenv("GBIZINFO_API_TOKEN", "")
GBIZINFO_BASE_URL = "https://info.gbiz.go.jp/hojin/v1/hojin"

# EDINET 設定
EDINET_API_KEY = os.getenv("EDINET_API_KEY", "")
EDINET_BASE_URL = "https://disclosure.edinet-fsa.go.jp/api/v2"

# 環境変数チェック（必須でない場合はコメントアウト可）
if not GBIZINFO_API_TOKEN:
    print("⚠️  環境変数 GBIZINFO_API_TOKEN が設定されていません。")
if not EDINET_API_KEY:
    print("⚠️  環境変数 EDINET_API_KEY が設定されていません。")