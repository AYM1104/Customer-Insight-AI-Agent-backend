"""
- app/services/gbizinfo/company_detail.py
- gBizINFO を法人番号（corporate_number）で検索し、企業詳細を返すサービス。
- 会社名・所在地などの基本情報に加えて、詳細フィールドがあれば併せて返す。
"""

import re
import requests
from fastapi import HTTPException
from app.core.config import GBIZINFO_API_TOKEN, GBIZINFO_BASE_URL

_CORP_NO_RE = re.compile(r"^\d{13}$")

def _session() -> requests.Session:
    s = requests.Session()
    s.trust_env = False
    return s


""" --------------------------------------------------------
 法人番号（13桁）で gBizINFO を検索し、最初の一致レコードを返す関数。
-------------------------------------------------------- """
def get_company_detail(corporate_number: str) -> dict:

    # 環境変数に API トークンが設定されていない場合は 500 エラーを返す
    if not GBIZINFO_API_TOKEN:
        raise HTTPException(500, "環境変数 GBIZINFO_API_TOKEN が設定されていません。")

    # 引数 corporate_number が None の場合も考慮して文字列化し、前後の空白を削除
    corporate_number = (corporate_number or "").strip()

    # 法人番号が 13 桁の数字であることを正規表現でチェック
    if not _CORP_NO_RE.match(corporate_number):
        raise HTTPException(400, "corporate_number は13桁の数字で指定してください。")

    # gBizINFO API に送る HTTP ヘッダー（認証トークン付き）
    headers = {
        "Accept": "application/json",
        "X-hojinInfo-api-token": GBIZINFO_API_TOKEN,
    }

    # エンドポイント用URLを生成   
    url = f"{GBIZINFO_BASE_URL}/{corporate_number}" 

    # gBizINFO API に GET リクエストを送信（30秒タイムアウト）
    try:
        r = _session().get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        # 接続エラー時は 502 エラーを返す
        raise HTTPException(502, f"gBizINFO API への接続に失敗しました: {e}")

    # ステータスコードが 200（成功）以外ならエラーとして返す
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"gBizINFO API エラー: {r.text[:200]}")

    # レスポンス JSON を Python の辞書型に変換
    data = r.json()

    # 法人情報リストを取得
    hits = data.get("hojin-infos") or data.get("hojin") or []

    # 該当企業が1件もない場合は 404 エラーを返す
    if not hits:
        raise HTTPException(404, f"法人番号「{corporate_number}」に一致する企業が見つかりませんでした。")

    # 整最初のヒットをそのまま返す
    return hits[0]