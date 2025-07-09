# db_gate_pass.py

from db_pool import get_db_cursor
from db_users import get_user_by_id

def add_gate_pass_record_to_db(data, user_id, company_id):
    """Adds a new Gate Pass record to the database."""
    sql = """
        INSERT INTO gate_pass_records (
            user_id, company_id, date_issued, gate_pass_number, item_description,
            issued_to, company, purpose_of_removal, authorized_by, authorizing_department,
            type, date_to_be_returned, item_picture_taken_out_bytes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (
            user_id, company_id, data["date_issued"], data["gate_pass_number"],
            data["item_description"], data["issued_to"], data["company"],
            data["purpose_of_removal"], data["authorized_by"], data["authorizing_department"],
            data["type"], data.get("date_to_be_returned"), data.get("item_picture_taken_out_bytes")
        ))
        return cur.fetchone()["id"]

def get_gate_pass_records_from_db(user_id, search_term=None):
    """Retrieves Gate Pass records, filtered by the user's company."""
    user_data = get_user_by_id(user_id)
    if not user_data: return []

    query = "SELECT * FROM gate_pass_records gp"
    params = []
    where_clauses = []

    if user_data["role"] != "super_admin":
        if not user_data.get("company_id"): return []
        where_clauses.append("gp.company_id = %s")
        params.append(user_data["company_id"])

    if search_term:
        where_clauses.append(
            """(gp.gate_pass_number ILIKE %s OR gp.item_description ILIKE %s
               OR gp.issued_to ILIKE %s OR gp.company ILIKE %s)"""
        )
        search_like = f"%{search_term}%"
        params.extend([search_like] * 4)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY gp.created_at DESC"
    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

def get_all_gp_records_for_user_role(user_id):
    """Gets all Gate Pass records for a company or all companies for excel download."""
    user_data = get_user_by_id(user_id)
    if not user_data: return []

    if user_data["role"] == "super_admin":
        query = "SELECT * FROM gate_pass_records ORDER BY date_issued ASC, gate_pass_number ASC"
        params = []
    else:
        if not user_data.get("company_id"): return []
        query = "SELECT * FROM gate_pass_records WHERE company_id = %s ORDER BY date_issued ASC, gate_pass_number ASC"
        params = [user_data["company_id"]]

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

def get_gate_pass_record_by_id(item_id, user_id):
    """Gets a single Gate Pass record by ID, ensuring user permission."""
    user_data = get_user_by_id(user_id)
    if not user_data: return None

    if user_data["role"] == "super_admin":
        query = "SELECT * FROM gate_pass_records WHERE id = %s"
        params = (item_id,)
    else:
        if not user_data.get("company_id"): return None
        query = "SELECT * FROM gate_pass_records WHERE id = %s AND company_id = %s"
        params = (item_id, user_data["company_id"])

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()

def update_gate_pass_record_in_db(item_id, data, user_id):
    """Updates the 'returned' status fields of a Gate Pass record."""
    user_data = get_user_by_id(user_id)
    if not user_data: raise PermissionError("User not found.")

    # Conditionally build the SET part of the query
    set_parts = [
        "status = %s", "returned_date = %s", "received_by = %s", "remarks = %s"
    ]
    params = [
        data["status"], data["returned_date"], data["received_by"], data["remarks"]
    ]
    if data.get("item_picture_returned_back_bytes") is not None:
        set_parts.append("item_picture_returned_back_bytes = %s")
        params.append(data["item_picture_returned_back_bytes"])

    set_clause = ", ".join(set_parts)
    
    if user_data["role"] == "super_admin":
        sql = f"UPDATE gate_pass_records SET {set_clause} WHERE id = %s;"
        params.append(item_id)
    else:
        if not user_data.get("company_id"): raise PermissionError("User is not in a company.")
        sql = f"UPDATE gate_pass_records SET {set_clause} WHERE id = %s AND company_id = %s;"
        params.extend([item_id, user_data["company_id"]])

    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, tuple(params))
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or record not found.")

def delete_gate_pass_record_from_db(item_id, user_id):
    """Deletes a Gate Pass record, ensuring the user has permission."""
    user_data = get_user_by_id(user_id)
    if not user_data: raise PermissionError("User not found.")

    if user_data["role"] == "super_admin":
        sql = "DELETE FROM gate_pass_records WHERE id = %s;"
        params = (item_id,)
    else:
        if not user_data.get("company_id"): raise PermissionError("User is not in a company.")
        sql = "DELETE FROM gate_pass_records WHERE id = %s AND company_id = %s;"
        params = (item_id, user_data["company_id"])

    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, params)
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or record not found.")