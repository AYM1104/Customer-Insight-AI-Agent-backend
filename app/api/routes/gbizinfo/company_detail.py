"""
- app/api/routes/gbizinfo/company_detail.py
- 法人番号で企業詳細を取得するAPIルーター。
"""

from fastapi import APIRouter, Query
from app.services.gbizinfo.company_detail import get_company_detail

# エンドポイントのルーターを定義
router = APIRouter(prefix="/gbiz", tags=["gBizINFO"])


""" ----------------------------------------------------------
 法人番号を受け取り、gBizINFO APIから企業詳細情報を取得して返すエンドポイント
---------------------------------------------------------- """
@router.get("/company-detail")
def get_company_detail_info(
    corporate_number: str = Query(..., description="法人番号（13桁の数字）")
):
    """
    gBizINFO API を利用して13桁の法人番号から企業の詳細情報を取得します。
    """
    return get_company_detail(corporate_number=corporate_number)