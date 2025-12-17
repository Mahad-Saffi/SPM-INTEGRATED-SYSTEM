"""
Employee Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from api.database import get_db
from api.models import Employee
from api.dependencies import verify_atlas_token, require_manager
from pydantic import BaseModel
import json

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


class UserSync(BaseModel):
    employee_id: str
    email: str
    name: str
    role: str = "member"


@router.post("/sync")
async def sync_employee(user_data: UserSync, db: Session = Depends(get_db)):
    """Create or update employee from orchestrator"""
    
    # Check if employee exists by email
    existing_emp = db.query(Employee).filter(Employee.email == user_data.email).first()
    
    if existing_emp:
        existing_emp.name = user_data.name
        db.commit()
        return {"status": "updated", "employee_id": existing_emp.id}
    
    # Create new employee
    new_emp = Employee(
        name=user_data.name,
        email=user_data.email,
        department="General",
        position=user_data.role,
        status="active"
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    
    return {"status": "created", "employee_id": new_emp.id}


class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str = None
    position: str = None
    status: str = "active"
    hire_date: datetime = None
    skills: Dict[str, Any] = None

class EmployeeUpdate(BaseModel):
    name: str = None
    email: str = None
    department: str = None
    position: str = None
    status: str = None
    hire_date: datetime = None
    skills: Dict[str, Any] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str = None
    position: str = None
    status: str
    hire_date: datetime = None
    skills: Dict[str, Any] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

def employee_to_dict(employee: Employee) -> Dict[str, Any]:
    """Convert Employee model to dict"""
    result = {
        "id": str(employee.id),
        "name": employee.name,
        "email": employee.email,
        "department": employee.department,
        "position": employee.position,
        "status": employee.status,
        "hire_date": employee.hire_date.isoformat() if employee.hire_date else None,
        "created_at": employee.created_at.isoformat() if employee.created_at else None,
        "updated_at": employee.updated_at.isoformat() if employee.updated_at else None,
    }
    if employee.skills:
        try:
            result["skills"] = json.loads(employee.skills) if isinstance(employee.skills, str) else employee.skills
        except:
            result["skills"] = {}
    return result

@router.get("", response_model=List[Dict[str, Any]])
async def get_employees(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all employees"""
    employees = db.query(Employee).all()
    return [employee_to_dict(emp) for emp in employees]

@router.get("/{employee_id}", response_model=Dict[str, Any])
async def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get employee by ID"""
    try:
        emp_id = int(employee_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")
    
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee_to_dict(employee)

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create new employee (manager only)"""
    require_manager(current_user)
    
    # Check if email already exists
    existing = db.query(Employee).filter(Employee.email == employee.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    
    db_employee = Employee(
        name=employee.name,
        email=employee.email,
        department=employee.department,
        position=employee.position,
        status=employee.status,
        hire_date=employee.hire_date,
        skills=json.dumps(employee.skills) if employee.skills else None
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return employee_to_dict(db_employee)

@router.put("/{employee_id}", response_model=Dict[str, Any])
async def update_employee(
    employee_id: str,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Update employee (manager only)"""
    require_manager(current_user)
    
    try:
        emp_id = int(employee_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")
    
    db_employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if employee.name is not None:
        db_employee.name = employee.name
    if employee.email is not None:
        # Check if email already exists for another employee
        existing = db.query(Employee).filter(Employee.email == employee.email, Employee.id != emp_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        db_employee.email = employee.email
    if employee.department is not None:
        db_employee.department = employee.department
    if employee.position is not None:
        db_employee.position = employee.position
    if employee.status is not None:
        db_employee.status = employee.status
    if employee.hire_date is not None:
        db_employee.hire_date = employee.hire_date
    if employee.skills is not None:
        db_employee.skills = json.dumps(employee.skills)
    
    db.commit()
    db.refresh(db_employee)
    return employee_to_dict(db_employee)

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Delete employee (manager only)"""
    require_manager(current_user)
    
    try:
        emp_id = int(employee_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")
    
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(employee)
    db.commit()
    return None

