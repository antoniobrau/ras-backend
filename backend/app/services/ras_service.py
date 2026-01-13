# app/services/ras_service.py
import calendar
from typing import Any

from app.repos.ras_repo import RASRepo


class RASService:
    def __init__(self, repo: RASRepo | None = None):
        self.repo = repo or RASRepo()

    def get_month_summary(self, email: str, year: int, month: int, hours_per_workday: int = 8) -> dict[str, Any]:
        """
        Riepilogo mese: status + assenze + giorni lavorati + ore ordinarie stimate + extra/spese + check base.
        """
        sheet_id = self.repo.get_sheet_id(email, year, month)
        if sheet_id is None:
            return {
                "email": email,
                "year": year,
                "month": month,
                "exists": False,
            }

        absences = self.repo.get_absence_days(sheet_id)
        work_days = self.repo.count_work_days(sheet_id)
        extra_spese = self.repo.get_extra_and_expenses(sheet_id)

        days_in_month = calendar.monthrange(year, month)[1]
        empty_days = self.repo.get_days_without_lines(sheet_id, days_in_month)
        mixed_days = self.repo.get_mixed_days(sheet_id)

        commesse_giorni = self.repo.get_giorni_per_commessa(sheet_id)

        return {
            "email": email,
            "year": year,
            "month": month,
            "exists": True,
            "sheet_id": sheet_id,
            "absences": absences,  # dict: ferie_giorni, permesso_giorni, malattia_giorni
            "work_days": work_days,
            "commesse" : commesse_giorni,
            "ordinary_hours_est": work_days * hours_per_workday,
            "ore_extra_tot": extra_spese["ore_extra_tot"],
            "spese_tot": extra_spese["spese_tot"],
            "checks": {
                "days_without_lines": empty_days,
                "mixed_days": mixed_days,
            },
        }

    def get_period_summary(self, email: str, from_ym: int, to_ym: int, hours_per_workday: int = 8) -> dict[str, Any]:
        """
        Riepilogo periodo basato sui mesi presenti in ras_sheets.
        from_ym/to_ym in formato YYYYMM (es 202510).
        """
        sheets = self.repo.get_sheets_by_user(email)

        # filtra mesi nel range
        in_range = []
        for s in sheets:
            ym = s["year"] * 100 + s["month"]
            if from_ym <= ym <= to_ym:
                in_range.append(s)

        months = []
        tot_ferie = []; tot_perm = []; tot_mal = []
        tot_work_days = 0
        tot_ordinary = 0
        tot_extra = 0.0
        tot_spese = 0.0

        dizionario_commesse = {}

        for s in in_range:
            sheet_id = s["id"]
            absences = self.repo.get_absence_days(sheet_id)
            work_days = self.repo.count_work_days(sheet_id)
            extra_spese = self.repo.get_extra_and_expenses(sheet_id)
            commesse_giorni = self.repo.get_giorni_per_commessa(sheet_id)

            for _row in commesse_giorni:
                _cdc = _row["commessa_cdc"]
                _giorni = _row["giorni_commessa"]
                dizionario_commesse[_cdc] = dizionario_commesse.get(_cdc, 0.0) + _giorni

            tot_ferie.extend(absences["ferie_giorni"])
            tot_perm.extend(absences["permesso_giorni"])
            tot_mal.extend(absences["malattia_giorni"])
            tot_work_days += work_days
            tot_ordinary += work_days * hours_per_workday
            tot_extra += float(extra_spese["ore_extra_tot"])
            tot_spese += float(extra_spese["spese_tot"])

            months.append({
                "year": s["year"],
                "month": s["month"],
                "sheet_status": s["sheet_status"],
                "absences": absences,
                "work_days": work_days,
                "commesse" : commesse_giorni,
                "ordinary_hours_est": work_days * hours_per_workday,
                "ore_extra_tot": extra_spese["ore_extra_tot"],
                "spese_tot": extra_spese["spese_tot"],
            })

        tot_commesse =  [ {"commessa_cdc": cdc, "giorni_commessa": giorni} for cdc, giorni in dizionario_commesse.items()]
        return {
            "email": email,
            "from_ym": from_ym,
            "to_ym": to_ym,
            "months": months,
            "totals": {
                "ferie_giorni": tot_ferie,
                "permesso_giorni": tot_perm,
                "malattia_giorni": tot_mal,
                "work_days": tot_work_days,
                "commesse" : tot_commesse,
                "ordinary_hours_est": tot_ordinary,
                "ore_extra_tot": tot_extra,
                "spese_tot": tot_spese,
            }
        }
