# app/routes/ras.py
from fastapi import APIRouter, Query
from app.services.ras_service import RASService
from app.models.schemas import PeriodSummaryOut, MonthSummaryOut

router = APIRouter(prefix="/ras", tags=["ras"])
svc = RASService()

@router.get("/month-summary", response_model= MonthSummaryOut)
def month_summary(email: str, year: int, month: int, hours_per_workday: int = 8, ):
    return svc.get_month_summary(email, year, month, hours_per_workday)

@router.get("/period-summary", response_model = PeriodSummaryOut)
def period_summary(
    email: str,
    from_ym: int = Query(..., description="YYYYMM, es 202510"),
    to_ym: int = Query(..., description="YYYYMM, es 202512"),
    hours_per_workday: int = 8
):
    return svc.get_period_summary(email, from_ym, to_ym, hours_per_workday)
