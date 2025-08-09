"""
- app/services/company_search.py
- このファイルは、gBizINFO API を利用して会社名から法人情報を検索するサービス関数を提供します。
"""

import requests
from fastapi import HTTPException
from app.core.config import GBIZINFO_API_TOKEN, GBIZINFO_BASE_URL


""" ----------------------------------------------
    gBizINFO APIを使って会社名から法人情報を取得する関数
---------------------------------------------- """
def search_company_by_name(name: str, limit: int = 10):
    
    # APIトークン未設定時はエラーを返す
    if not GBIZINFO_API_TOKEN:
        raise HTTPException(status_code=500, detail="GBIZINFO_API_TOKENが設定されていません")

    # APIリクエストヘッダーを作成（認証用トークンを含む）
    headers = {
        "Accept": "application/json",
        "X-hojinInfo-api-token": GBIZINFO_API_TOKEN
    }

    # APIクエリパラメータを作成
    params = {"name": name, "limit": limit}

    # gBizINFO APIへリクエスト送信
    response = requests.get(GBIZINFO_BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="gBizINFO API の呼び出しに失敗しました。")

    # レスポンスをJSON形式に変換
    data = response.json()

    # API仕様により、法人情報は "hojin-infos" または "hojin" に入る
    hits = data.get("hojin-infos") or data.get("hojin") or []

    # ヒットなしの場合は404エラー
    if not hits:
        raise HTTPException(status_code=404, detail=f"会社名「{name}」に一致する企業は見つかりませんでした。")

    # 取得するデータを整形
    def pick(x):
        return {
            # 会社概要
            "name": x.get("name"),  # 法人名
            "corporate_number": x.get("corporate_number") or x.get("jcn"),  # 法人番号
            "established_date": x.get("established_date") or x.get("founding_year"),  # 設立日または設立年
            "capital": x.get("capital"),  # 資本金
            "employee_number": x.get("employee_number"),  # 従業員数
            "address": x.get("address"),  # 本社所在地

            # 事業構成
            "business_summary": x.get("business_summary"),  # 事業概要

            # 公式発信
            "homepage": x.get("url") or x.get("homepage"),  # 企業URL
        }

    # 整形済みデータを返す
    return {"count": len(hits), "results": [pick(x) for x in hits]}