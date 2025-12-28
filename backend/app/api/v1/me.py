from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import EmployeeOut
from app.repos.employees import get_employee_by_email

router = APIRouter(tags=["me"])

@router.get("/me", response_model=EmployeeOut)
def me(email: str = Query(...)):
    row = get_employee_by_email(email)
    if not row:
        raise HTTPException(status_code=404, detail="employee not found")
    return row