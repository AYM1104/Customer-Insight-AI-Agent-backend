"""
- app/api/routes/edinet/yuho_search.py
- 有価証券報告書（030000/030001）を検索する最小APIルーター。
"""
from fastapi import APIRouter, Query
from app.services.edinet.yuho_search import search_yuho

# エンドポイントのルーターを定義
router = APIRouter(prefix="/edinet", tags=["EDINET"])

""" ----------------------------------------------------------
 指定期間・会社名・法人番号で有価証券報告書を検索するエンドポイント
---------------------------------------------------------- """
@router.get("/yuho-search")
def yuho_search(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    corporate_number: str = Query(..., description="法人番号"),
    limit: int = Query(200, ge=1, le=5000, description="返却上限"),
):
    """
    EDINETの提出一覧から有価証券報告書（030000/030001）のみ抽出します。
    - **start_date / end_date**: 検索期間（必須）
    - **corporate_number**: 法人番号
    - **limit**: 返却上限
    """
    return search_yuho(start_date, end_date, corporate_number=corporate_number, limit=limit)