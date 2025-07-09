# db_lost_and_found.py

from db_pool import get_db_cursor
from db_users import get_user_by_id


def add_lost_and_found_item_to_db(data, user_id, company_id):
    """
    Adds a new Lost & Found item to the database, including its company_id.
    The 'status' field will default to 'Unclaimed' in the database.
    """
    sql = """
        INSERT INTO lost_and_found (
            user_id, company_id, entry_date, entry_time, ticket_no, item_type, 
            item_description, location_found, found_by, department, 
            received_by_security, stored_in, photo_bytes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            sql,
            (
                user_id,
                company_id,
                data["entry_date"],
                data["entry_time"],
                data["ticket_no"],
                data["item_type"],
                data["item_description"],
                data["location_found"],
                data["found_by"],
                data["department"],
                data["received_by_security"],
                data["stored_in"],
                data.get("photo_bytes"),
            ),
        )
        return cur.fetchone()["id"]


def get_lost_and_found_items_from_db(user_id, search_term=None):
    """
    Retrieves Lost & Found items, filtered by the user's company
    or all items for a super_admin.
    """
    user_data = get_user_by_id(user_id)
    if not user_data:
        return []

    query = "SELECT * FROM lost_and_found lf"
    params = []
    where_clauses = []

    if user_data["role"] != "super_admin":
        if not user_data.get("company_id"):
            return []  # A non-super-admin user must have a company
        where_clauses.append("lf.company_id = %s")
        params.append(user_data["company_id"])

    if search_term:
        where_clauses.append(
            "(lf.ticket_no ILIKE %s OR lf.item_description ILIKE %s OR lf.location_found ILIKE %s OR lf.status ILIKE %s)"
        )
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like, search_like])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY lf.created_at DESC"

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_all_lf_items_for_user_role(user_id):
    """
    Gets all L&F items for a company if user is admin/user,
    or all items from all companies if user is super_admin.
    Used for the Excel download.
    """
    user_data = get_user_by_id(user_id)
    if not user_data:
        return []

    if user_data["role"] == "super_admin":
        query = "SELECT * FROM lost_and_found ORDER BY entry_date ASC, entry_time ASC"
        params = []
    else:
        if not user_data.get("company_id"):
            return []
        query = "SELECT * FROM lost_and_found WHERE company_id = %s ORDER BY entry_date ASC, entry_time ASC"
        params = [user_data["company_id"]]

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_lost_and_found_item_by_id(item_id, user_id):
    """
    Gets a single Lost & Found item by its ID, ensuring the user has
    permission to view it based on their company.
    """
    user_data = get_user_by_id(user_id)
    if not user_data:
        return None

    if user_data["role"] == "super_admin":
        query = "SELECT * FROM lost_and_found WHERE id = %s"
        params = (item_id,)
    else:
        if not user_data.get("company_id"):
            return None
        query = "SELECT * FROM lost_and_found WHERE id = %s AND company_id = %s"
        params = (item_id, user_data["company_id"])

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def update_lost_and_found_item_in_db(item_id, data, user_id):
    """
    Updates the 'claimed' status fields of a Lost & Found item,
    ensuring the user has permission to do so.
    """
    user_data = get_user_by_id(user_id)
    if not user_data:
        raise PermissionError("User not found.")
    
    # --- FIX: Include the 'status' field in the UPDATE query ---
    common_sql = """
        UPDATE lost_and_found
        SET
            status = %s, owner_id_no = %s, claimer_receiver_disposer = %s, receiver_contact_no = %s,
            claim_date = %s, claim_time = %s, handed_over_by = %s, remarks = %s
    """
    common_params = (
        data["status"], data["owner_id_no"], data["claimer_receiver_disposer"], data["receiver_contact_no"],
        data["claim_date"], data["claim_time"], data["handed_over_by"], data["remarks"],
    )
    # --- End of fix ---

    if user_data["role"] == "super_admin":
        sql = common_sql + " WHERE id = %s;"
        params = common_params + (item_id,)
    else:
        if not user_data.get("company_id"):
            raise PermissionError("User is not associated with a company.")
        sql = common_sql + " WHERE id = %s AND company_id = %s;"
        params = common_params + (item_id, user_data["company_id"],)

    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, params)
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or record not found.")


def delete_lost_and_found_item_from_db(item_id, user_id):
    """
    Deletes a Lost & Found item, ensuring the user has permission.
    """
    user_data = get_user_by_id(user_id)
    if not user_data:
        raise PermissionError("User not found.")

    if user_data["role"] == "super_admin":
        sql = "DELETE FROM lost_and_found WHERE id = %s;"
        params = (item_id,)
    else:
        if not user_data.get("company_id"):
            raise PermissionError("User is not associated with a company.")
        sql = "DELETE FROM lost_and_found WHERE id = %s AND company_id = %s;"
        params = (item_id, user_data["company_id"])

    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, params)
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or record not found.")