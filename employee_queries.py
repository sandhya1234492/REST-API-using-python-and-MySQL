from database import create_connection


def run_query(query, values=(), fetch_one=False, fetch_all=False):
    """Run one parameterized SQL query and close its database resources."""
    connection = create_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, values)

        if fetch_one:
            return cursor.fetchone()

        if fetch_all:
            return cursor.fetchall()

        connection.commit()
        return {"rowcount": cursor.rowcount, "lastrowid": cursor.lastrowid}
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def get_all_employees():
    query = "SELECT id, name, email, department, salary FROM employees ORDER BY id"
    return run_query(query, fetch_all=True)


def get_employee_by_id(employee_id):
    query = (
        "SELECT id, name, email, department, salary "
        "FROM employees WHERE id = %s"
    )
    return run_query(query, (employee_id,), fetch_one=True)


def add_employee(employee):
    query = (
        "INSERT INTO employees (name, email, department, salary) "
        "VALUES (%s, %s, %s, %s)"
    )
    values = (
        employee["name"],
        employee["email"],
        employee["department"],
        employee["salary"],
    )
    return run_query(query, values)


def update_employee(employee_id, employee):
    query = (
        "UPDATE employees SET name = %s, email = %s, department = %s, salary = %s "
        "WHERE id = %s"
    )
    values = (
        employee["name"],
        employee["email"],
        employee["department"],
        employee["salary"],
        employee_id,
    )
    return run_query(query, values)


def delete_employee(employee_id):
    query = "DELETE FROM employees WHERE id = %s"
    return run_query(query, (employee_id,))


def search_employees(name=None, department=None):
    query = (
        "SELECT id, name, email, department, salary "
        "FROM employees WHERE "
    )
    conditions = []
    values = []

    if name is not None:
        conditions.append("name LIKE %s")
        values.append(f"%{name}%")

    if department is not None:
        conditions.append("department LIKE %s")
        values.append(f"%{department}%")

    query += " AND ".join(conditions) + " ORDER BY id"
    return run_query(query, tuple(values), fetch_all=True)
