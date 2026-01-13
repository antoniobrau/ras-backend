from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    email: str
    site: str | None = None
    level: str | None = None
    company: str | None = None
    active: bool
    created_at: datetime

#-------------------------------------------------------------


class CommessaDaysOut(BaseModel):
    commessa_cdc: str
    giorni_commessa: float

class AbsencesOut(BaseModel):
    ferie_giorni: list[date]
    permesso_giorni: list[date]
    malattia_giorni: list[date]


class ChecksOut(BaseModel):
    days_without_lines: list[int]
    mixed_days: list[int]


class MonthSummaryOut(BaseModel):
    email: str
    year: int
    month: int
    exists: bool

    sheet_id: Optional[int] = None
    absences: Optional[AbsencesOut] = None
    work_days: Optional[int] = None
    commesse: list[CommessaDaysOut]
    ordinary_hours_est: Optional[int] = None
    ore_extra_tot: Optional[float] = None
    spese_tot: Optional[float] = None
    checks: Optional[ChecksOut] = None

#-----------------------------------------------------------------------------------------------

class PeriodMonthOut(BaseModel):
    year: int
    month: int
    sheet_status: str

    absences: AbsencesOut
    work_days: int
    commesse : list[CommessaDaysOut]
    ordinary_hours_est: int

    ore_extra_tot: float
    spese_tot: float


class PeriodTotalsOut(BaseModel):
    ferie_giorni : list[date]
    permesso_giorni : list[date]
    malattia_giorni : list[date]
    work_days: int
    commesse : list[CommessaDaysOut]
    ordinary_hours_est: int
    ore_extra_tot: float
    spese_tot: float


class PeriodSummaryOut(BaseModel):
    email: str
    from_ym: int
    to_ym: int
    months: list[PeriodMonthOut]
    totals: PeriodTotalsOut


