# app/services/edinet/yuho_search.py
"""
- EDINETのdocuments.jsonを日付範囲で走査し、
  法人番号（JCN）一致かつ有価証券報告書（030000/030001）のみ返す機能。
"""
from __future__ import annotations
import time, datetime as dt, re
from typing import Dict, List
import requests
from fastapi import HTTPException
from app.core.config import EDINET_API_KEY, EDINET_BASE_URL

# 有価証券報告書（formCode）判定用コードセット
FORM_YUHO = {"030000", "030001"} 
# EDINET API の type パラメータ値（ 2: 決算期報告などの提出書類）
DOC_TYPE = 2 
# APIアクセスの間隔（秒） 
PAUSE = 0.12


""" ------------------------------------------
 requests のセッションオブジェクトを生成して返す関数
------------------------------------------ """
def _session() -> requests.Session:

    s = requests.Session()
    # OS/環境変数のプロキシ設定を無視
    s.trust_env = False
    return s

""" --------------------------------------------------------------
 指定日の EDINET 提出一覧（documents.json, type=2 決算系）を取得する関数
-------------------------------------------------------------- """
def _list_one_day(d: dt.date) -> List[Dict]:

    # APIキーが未設定ならエラー
    if not EDINET_API_KEY:
        raise HTTPException(500, "環境変数 EDINET_API_KEY が設定されていません。")
    
    # EDINET API に GET リクエストを送信
    r = _session().get(
        f"{EDINET_BASE_URL}/documents.json",
        headers={
            "Accept": "application/json",
            "User-Agent": "edinet-client/1.0",
            "Ocp-Apim-Subscription-Key": EDINET_API_KEY,
        },
        params={"date": d.isoformat(), "type": DOC_TYPE},
        timeout=30,
    )

    # HTTPエラー（4xx, 5xx）の場合は例外発生
    r.raise_for_status()
    
    # "results" 配列を返す（存在しない場合は空リスト）
    return r.json().get("results", []) or []


""" -----------------------------------------------------------------
    指定期間内に提出された EDINET 有価証券報告書（030000 / 030001）を検索し、
    指定した法人番号（JCN）と一致するものだけを返す関数。
----------------------------------------------------------------- """

def search_yuho(start_date: str, end_date: str, corporate_number: str, limit: int = 200) -> Dict:

    # 1. 入力バリデーション
    try:
        d0 = dt.date.fromisoformat(start_date)
        d1 = dt.date.fromisoformat(end_date)
        if d1 < d0:
            raise ValueError
    except Exception:
        raise HTTPException(400, "start_date/end_date は YYYY-MM-DD 形式で指定してください。")

    # 2. 検索準備
    rows: List[Dict] = []   # 検索結果を格納する空リスト
    cur = d0    # ループの開始日 を cur に設定

    # 3. 指定期間を1日ずつ走査
    while cur <= d1 and len(rows) < limit:
        # 1日分の提出一覧を取得
        day = _list_one_day(cur)
        # 有報のみ抽出
        day = [r for r in day if (r.get("formCode") or "") in FORM_YUHO]
        # JCN一致（12/13桁ゆれ吸収）
        day = [r for r in day if (r.get("JCN") or r.get("jcn") or "").replace("-", "")[-12:] == corporate_number[-12:]]

        rows.extend(day)
        time.sleep(PAUSE)
        cur += dt.timedelta(days=1)

    # 4. 必要最小限の情報だけ抽出
    def pick(x: Dict) -> Dict:
        return {
            "docID": x.get("docID"),
            "filerName": x.get("filerName"),
            "JCN": x.get("JCN") or x.get("jcn"),
            "formCode": x.get("formCode"),
            "submitDateTime": x.get("submitDateTime"),
        }

    items = [pick(x) for x in rows[:limit]]

    # 5. 新しい順にソート
    items.sort(key=lambda r: r.get("submitDateTime", ""), reverse=True) 

    return {"count": len(items), "items": items}