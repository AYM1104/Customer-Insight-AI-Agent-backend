# backend/main.py
import os, io, time, datetime as dt
from typing import List, Dict
import requests
# import pandas as pd  # 将来の拡張用（解析など）。未使用なら削ってOK
from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

# ====== 設定 ======
API_KEY = "9a9dc1eb51ba4cd8add13c014f82eeb4"   # ← 環境変数で設定: export EDINET_API_KEY='...'
BASE = "https://disclosure.edinet-fsa.go.jp/api/v2"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "edinet-client/1.0",
    "Ocp-Apim-Subscription-Key": API_KEY,
}
DEFAULT_DOC_TYPE = 2  # 2=決算系（有報/四半期など）
PAUSE = 0.15          # アクセスマナー

app = FastAPI(title="EDINET Helper (single-file)")
router = APIRouter(prefix="/edinet", tags=["EDINET"])

# ====== ユーティリティ ======
# 会社名の軽い正規化（表記ゆれ対策）
ALIASES = {"瓦斯": "ガス", "㈱": "株式会社", "(株)": "株式会社", "　": "", " ": ""}

import os, requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# .env ファイルの読み込み
load_dotenv()

# gBizINFO APIトークンを環境変数から取得
GBIZINFO_API_TOKEN = os.getenv("GBIZINFO_API_TOKEN")

# トークンが設定されていない場合はエラーを出す
if not GBIZINFO_API_TOKEN:
    raise ValueError("環境変数 GBIZINFO_API_TOKEN が設定されていません。")

# FastAPIインスタンス生成
app = FastAPI(
    title="Customer Insight AI Agent - Company Info API",
    description="会社名からgBizINFO APIを使って法人情報を取得するシンプルなAPI",
    version="1.0.0"
)

# gBizINFO APIのベースURL
GBIZINFO_BASE_URL = "https://info.gbiz.go.jp/hojin/v1/hojin"

@app.get("/company")
def get_company_info(name: str):
    """
    会社名を受け取り、gBizINFO APIから法人情報を取得して返すエンドポイント
    - name: 会社名（部分一致検索可）
    """
    # APIリクエストヘッダー（トークン認証）
    headers = {
        "Accept": "application/json",
        "X-hojinInfo-api-token": GBIZINFO_API_TOKEN
    }

    # gBizINFO APIにリクエスト送信
    params = {"name": name, "limit": 5}  # 最大5件取得
    response = requests.get(GBIZINFO_BASE_URL, headers=headers, params=params)

    # ステータスコードチェック
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="gBizINFO API request failed")

    data = response.json()

    # ✅ 検索結果のキー名に対応（"hojin-infos" が正）
    hits = data.get("hojin-infos") or data.get("hojin") or []

    if not hits:
        raise HTTPException(status_code=404, detail=f"No company found with that name: {name}")

    # 複数件ヒットするので配列で返す（必要なら1件目だけ返すように変更可）
    return {"count": len(hits), "results": hits}

def _norm(s: str) -> str:
    if not s: return ""
    t = s
    for a, b in ALIASES.items():
        t = t.replace(a, b)
    return t

def _list_by_date_any(d: dt.date, doc_type: int = DEFAULT_DOC_TYPE) -> List[Dict]:
    """指定日の提出一覧を取得"""
    s = requests.Session(); s.trust_env = False
    r = s.get(
        f"{BASE}/documents.json",
        params={"date": d.isoformat(), "type": doc_type},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("results", []) or []

# ====== API ======
@app.get("/healthz")
def healthz():
    return {"ok": True}

@router.get("/list")
def list_docs(
    start_date: str = Query(..., description="集計開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="集計終了日 YYYY-MM-DD"),
    doc_type: int = Query(DEFAULT_DOC_TYPE, description="EDINETのtype。2=決算系（有報/四半期ほか）"),
    company: str = Query("", description="会社名の部分一致（任意・表記ゆれ軽減あり）"),
    limit: int = Query(5000, description="返却上限（既定: 5000件）"),
):
    if not API_KEY:
        raise HTTPException(500, "EDINET_API_KEY が設定されていません")

    # 日付バリデーション
    try:
        d0 = dt.date.fromisoformat(start_date)
        d1 = dt.date.fromisoformat(end_date)
        if d1 < d0:
            raise ValueError
    except Exception:
        raise HTTPException(400, "start_date/end_date の形式が不正です（YYYY-MM-DD）")

    rows: List[Dict] = []
    cur = d0
    company_norm = _norm(company)

    while cur <= d1 and len(rows) < limit:
        day_rows = _list_by_date_any(cur, doc_type=doc_type)
        if company_norm:
            day_rows = [r for r in day_rows if company_norm in _norm(r.get("filerName") or "")]
        rows.extend(day_rows)
        time.sleep(PAUSE)  # マナー
        cur += dt.timedelta(days=1)

    # 返却項目（必要に応じて拡張してOK）
    def pick(r: Dict) -> Dict:
        return {
            "docID": r.get("docID"),
            "filerName": r.get("filerName"),
            "edinetCode": r.get("edinetCode"),
            "submitDateTime": r.get("submitDateTime"),
            "ordinanceCode": r.get("ordinanceCode"),
            "formCode": r.get("formCode"),
        }

    items = [pick(r) for r in rows[:limit]]
    return {"count": len(items), "items": items}

@router.get("/list.csv")
def list_docs_csv(
    start_date: str = Query(..., description="集計開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="集計終了日 YYYY-MM-DD"),
    doc_type: int = Query(DEFAULT_DOC_TYPE, description="EDINETのtype。2=決算系（有報/四半期ほか）"),
    company: str = Query("", description="会社名の部分一致（任意・表記ゆれ軽減あり）"),
    limit: int = Query(5000, description="返却上限（既定: 5000件）"),
):
    # 上のJSONエンドポイントを再利用
    data = list_docs(start_date, end_date, doc_type, company, limit)  # type: ignore[arg-type]

    # CSVに整形
    import csv
    from io import StringIO
    buf = StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["docID", "filerName", "edinetCode", "submitDateTime", "ordinanceCode", "formCode"],
    )
    writer.writeheader()
    for row in data["items"]:
        writer.writerow(row)
    buf.seek(0)

    filename = f"edinet_list_{start_date}_{end_date}_t{doc_type}.csv"
    return StreamingResponse(
        io.BytesIO(buf.read().encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# --- 追加: formCode→名称の軽いマップ（必要に応じて拡張）
FORM_NAME = {
    "030000": "有価証券報告書",
    "030001": "訂正有価証券報告書",
}

def _pick_latest_yuho(items: list[dict]) -> dict | None:
    # 030000/030001 に絞って、submitDateTime 降順で1件
    yuho = [r for r in items if (r.get("formCode") or "") in {"030000", "030001"}]
    if not yuho:
        return None
    yuho.sort(key=lambda x: x.get("submitDateTime", ""), reverse=True)
    return yuho[0]

@router.get("/latest-yuho-by-date")
def latest_yuho_by_date(
    start_date: str = Query(..., description="YYYY-MM-DD（例：2025-06-01）"),
    end_date: str = Query(..., description="YYYY-MM-DD（例：2025-06-30）"),
    company: str = Query("", description="会社名の部分一致（任意）"),
    doc_type: int = Query(DEFAULT_DOC_TYPE),
):
    # 既存の /edinet/list を内部呼び出し
    data = list_docs(start_date, end_date, doc_type, company, 5000)  # type: ignore[arg-type]
    hit = _pick_latest_yuho(data["items"])
    if not hit:
        raise HTTPException(404, "期間内に有価証券報告書が見つかりませんでした。")
    return {
        **hit,
        "formName": FORM_NAME.get(hit.get("formCode"), ""),
        "download": {
            "zip": f"/edinet/download/{hit['docID']}?type=zip",
            "pdf": f"/edinet/download/{hit['docID']}?type=pdf",
            "metaCsv": f"/edinet/download/{hit['docID']}?type=meta",
        },
    }

# --- 追加: ダウンロード（ZIP/PDF/メタCSV）をストリーミング返却
@router.get("/download/{doc_id}")
def download_doc(
    doc_id: str,
    type: str = Query("zip", pattern="^(zip|pdf|meta)$"),
):
    if not API_KEY:
        raise HTTPException(500, "EDINET_API_KEY が設定されていません")
    tmap = {"zip": 1, "pdf": 2, "meta": 3}
    s = requests.Session(); s.trust_env = False
    r = s.get(f"{BASE}/documents/{doc_id}", params={"type": tmap[type]}, headers=HEADERS, timeout=60)
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text[:200])

    filename = {"zip": f"{doc_id}.zip", "pdf": f"{doc_id}.pdf", "meta": f"{doc_id}_meta.csv"}[type]
    media = {"zip": "application/zip", "pdf": "application/pdf", "meta": "text/csv; charset=utf-8"}[type]
    return StreamingResponse(
        io.BytesIO(r.content),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

# ルーター登録
app.include_router(router)