from datetime import datetime
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

class AbsencesOut(BaseModel):
    ferie_giorni: int
    permesso_giorni: int
    malattia_giorni: int


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
    ordinary_hours_est: int

    ore_extra_tot: float
    spese_tot: float


class PeriodTotalsOut(BaseModel):
    ferie_giorni: int
    permesso_giorni: int
    malattia_giorni: int
    work_days: int
    ordinary_hours_est: int
    ore_extra_tot: float
    spese_tot: float


class PeriodSummaryOut(BaseModel):
    email: str
    from_ym: int
    to_ym: int
    months: list[PeriodMonthOut]
    totals: PeriodTotalsOut
