from fastapi import APIRouter, Depends, HTTPException

from app.agent import tools
from app.db.mongo import db, to_employee
from app.models.schemas import Employee, EmployeeIn, EmployeeQuery, EmployeeUpdate
from app.security.auth import current_user

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[Employee])
async def list_employees(
    role: str | None = None,
    department: str | None = None,
    active: bool | None = None,
    limit: int = 50,
    user: dict = Depends(current_user),
):
    res = await tools.search_employees(
        role=role, department=department, active=active, limit=limit
    )
    return res["employees"]


@router.post("/query", response_model=list[Employee])
async def query_employees(q: EmployeeQuery, user: dict = Depends(current_user)):
    res = await tools.search_employees(
        role=q.role.value if q.role else None,
        department=q.department,
        joined_after=q.joined_after.isoformat() if q.joined_after else None,
        joined_before=q.joined_before.isoformat() if q.joined_before else None,
        active=q.active,
        limit=q.limit,
    )
    return res["employees"]


@router.post("", response_model=Employee, status_code=201)
async def create_employee(payload: EmployeeIn, user: dict = Depends(current_user)):
    res = await tools.create_employee(
        name=payload.name,
        email=str(payload.email),
        role=payload.role.value,
        department=payload.department,
        joined_on=payload.joined_on.isoformat(),
        manager_email=str(payload.manager_email) if payload.manager_email else None,
    )
    if not res["ok"]:
        raise HTTPException(409, res["reason"])
    return res["employee"]


@router.patch("/{email}", response_model=Employee)
async def update_employee(email: str, payload: EmployeeUpdate, user: dict = Depends(current_user)):
    """Partial edit for the Team page: role, department and/or active state."""
    patch = payload.model_dump(exclude_unset=True, mode="json")
    if not patch:
        raise HTTPException(400, "no fields to update")
    n = await db.col("employees").update_one({"email": email}, patch)
    if not n:
        raise HTTPException(404, "employee not found")
    await db.audit(user["email"], "employee.update", {"email": email, **patch})
    doc = await db.col("employees").find_one({"email": email})
    return to_employee(doc)


@router.delete("/{email}")
async def deactivate(email: str, user: dict = Depends(current_user)):
    res = await tools.deactivate_employee(email)
    if not res["ok"]:
        raise HTTPException(404, "employee not found")
    return res


@router.get("/stats/headcount")
async def headcount(dimension: str = "department", user: dict = Depends(current_user)):
    return await tools.headcount_by(dimension)


@router.get("/{email}", response_model=Employee)
async def get_employee(email: str, user: dict = Depends(current_user)):
    doc = await db.col("employees").find_one({"email": email})
    if not doc:
        raise HTTPException(404, "employee not found")
    return to_employee(doc)
