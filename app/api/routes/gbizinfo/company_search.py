"""
- app/api/routes/gbizinfo/company_search.py
- gBizINFO を使った会社検索用のAPIルーター。
"""

from fastapi import APIRouter, Query
from app.services.gbizinfo.company_search import search_company_by_name


# ルーターを定義
router = APIRouter(prefix="/gbiz", tags=["gBizINFO"])


""" ----------------------------------------------------------
 会社名を受け取り、gBizINFO APIから法人情報を取得して返すエンドポイント
---------------------------------------------------------- """
@router.get("/company-search")
def get_company_info(
    name: str = Query(..., description="会社名（部分一致可）"),
    limit: int = Query(10, ge=1, le=50, description="取得件数の上限（1〜50）")
):
    """
    gBizINFO API を利用して正式会社名と法人番号を取得します。
    - **name**: 検索対象の会社名（部分一致可）
    - **limit**: 最大取得件数（1〜50）
    """
    return search_company_by_name(name=name, limit=limit)