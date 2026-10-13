from decimal import Decimal, InvalidOperation

import mysql.connector
from fastapi import Body, FastAPI, HTTPException, Path, Query

import employee_queries

app = FastAPI(title="Employee Management API")

EMPLOYEE_FIELDS = {"name", "email", "department", "salary"}


def validate_employee(employee_data):
    """Check employee input and return cleaned values for SQL."""
    if set(employee_data) != EMPLOYEE_FIELDS:
        raise HTTPException(
            status_code=422,
            detail="Provide exactly these fields: name, email, department, salary.",
        )

    cleaned_employee = {}
    for field_name in ("name", "email", "department"):
        value = employee_data[field_name]
        if not isinstance(value, str) or not value.strip():
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} must be a non-empty string.",
            )
        cleaned_employee[field_name] = value.strip()

    email = cleaned_employee["email"]
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=422,
            detail="email must be a valid email address.",
        )

    try:
        salary = Decimal(str(employee_data["salary"]))
    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=422,
            detail="salary must be a valid number.",
        )

    if not salary.is_finite() or salary < 0:
        raise HTTPException(
            status_code=422,
            detail="salary must be a non-negative finite number.",
        )

    if salary.as_tuple().exponent < -2 or salary > Decimal("99999999.99"):
        raise HTTPException(
            status_code=422,
            detail="salary must be at most 99999999.99 with no more than 2 decimals.",
        )

    cleaned_employee["salary"] = salary
    return cleaned_employee


def handle_database_error(error):
    """Translate expected database failures into useful HTTP responses."""
    if isinstance(error, mysql.connector.Error) and error.errno == 1062:
        raise HTTPException(
            status_code=409,
            detail="An employee with this email address already exists.",
        ) from error

    raise HTTPException(
        status_code=503,
        detail=(
            "The database is unavailable. Check that MySQL is running "
            "and the .env settings are correct."
        ),
    ) from error


@app.post("/employees", status_code=201)
def create_employee(employee_data: dict = Body(...)):
    employee = validate_employee(employee_data)

    try:
        result = employee_queries.add_employee(employee)
        return employee_queries.get_employee_by_id(result["lastrowid"])
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        handle_database_error(error)


@app.get("/employees/search")
def find_employees(
    name: str | None = Query(default=None),
    department: str | None = Query(default=None),
):
    if (name is None or not name.strip()) and (
        department is None or not department.strip()
    ):
        raise HTTPException(
            status_code=422,
            detail="Provide a non-empty name or department search value.",
        )

    name_filter = name.strip() if name is not None else None
    department_filter = department.strip() if department is not None else None

    try:
        return employee_queries.search_employees(name_filter, department_filter)
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        handle_database_error(error)


@app.get("/employees")
def list_employees():
    try:
        return employee_queries.get_all_employees()
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        handle_database_error(error)


@app.get("/employees/{employee_id}")
def read_employee(employee_id: int = Path(..., gt=0)):
    try:
        employee = employee_queries.get_employee_by_id(employee_id)
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        handle_database_error(error)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return employee


@app.put("/employees/{employee_id}")
def replace_employee(
    employee_data: dict = Body(...),
    employee_id: int = Path(..., gt=0),
):
    employee = validate_employee(employee_data)

    try:
        employee_queries.update_employee(employee_id, employee)
        updated_employee = employee_queries.get_employee_by_id(employee_id)
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        handle_database_error(error)

    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return updated_employee


@app.delete("/employees/{employee_id}")
def remove_employee(employee_id: int = Path(..., gt=0)):
    try:
        result = employee_queries.delete_employee(employee_id)
    except (mysql.connector.Error, RuntimeError, ValueError) as error:
        handle_database_error(error)

    if result["rowcount"] == 0:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return {"message": "Employee deleted successfully."}
