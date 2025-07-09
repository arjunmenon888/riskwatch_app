# db_users.py

import psycopg2
from psycopg2 import sql
import db_pool

# =============================================================================
# COMPANY-RELATED DATABASE FUNCTIONS
# =============================================================================

def get_all_companies():
    """Retrieves a list of all companies from the database."""
    with db_pool.get_db_cursor() as cur:
        cur.execute("SELECT * FROM companies ORDER BY name ASC")
        return cur.fetchall()

def get_company_by_name(name):
    """Retrieves a single company's data by its name."""
    with db_pool.get_db_cursor() as cur:
        cur.execute("SELECT * FROM companies WHERE name = %s", (name,))
        return cur.fetchone()

def create_company(name):
    """Adds a new company to the database and returns its new ID."""
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO companies (name) VALUES (%s) RETURNING id",
            (name,)
        )
        new_company = cur.fetchone()
        return new_company['id'] if new_company else None

def delete_company(company_id):
    """
    Deletes a company from the database.
    This will trigger cascade deletes on related tables like trainings, L&F, etc.
    """
    if not company_id: return
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM companies WHERE id = %s", (company_id,))
        if cur.rowcount > 0:
            print(f"Cascading delete: Company ID {company_id} was deleted.")


# =============================================================================
# USER-RELATED DATABASE FUNCTIONS
# =============================================================================

def add_user_to_db(email, password_hash, role='user', company_id=None):
    """Adds a new user to the users table."""
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash, role, company_id) VALUES (%s, %s, %s, %s)",
            (email, password_hash, role, company_id)
        )

def delete_user(user_id):
    """Deletes a user from the database by their ID."""
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No user found with ID {user_id} to delete.")

def delete_users_by_company(company_id):
    """Deletes all users with role 'user' from a specific company."""
    if not company_id: return
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM users WHERE company_id = %s AND role = 'user'", (company_id,))
        print(f"Cascading delete: {cur.rowcount} users from company ID {company_id} were deleted.")

def get_user_by_id(user_id):
    """Retrieves a single user's data by their unique ID, including company name."""
    with db_pool.get_db_cursor() as cur:
        cur.execute("""
            SELECT u.*, c.name as company_name 
            FROM users u 
            LEFT JOIN companies c ON u.company_id = c.id
            WHERE u.id = %s
        """, (user_id,))
        return cur.fetchone()

def get_user_by_email(email):
    """Retrieves a single user's data by their email, including company name."""
    with db_pool.get_db_cursor() as cur:
        cur.execute("""
            SELECT u.*, c.name as company_name
            FROM users u
            LEFT JOIN companies c ON u.company_id = c.id
            WHERE u.email = %s
        """, (email,))
        return cur.fetchone()

def get_all_users(search_term=None, sort_by='date_newest', company_id=None, role_filter=None):
    """
    Retrieves a list of users with advanced filtering and sorting.
    - search_term: Filters by email, name, or company name.
    - sort_by: Defines the order of the results.
    - company_id: Filters for users belonging to a specific company.
    - role_filter: Filters for users with a specific role (e.g., 'admin', 'user').
    """
    base_query = sql.SQL("""
        SELECT u.*, c.name as company_name 
        FROM users u 
        LEFT JOIN companies c ON u.company_id = c.id
    """)
    
    where_clauses = []
    params = []

    if company_id:
        where_clauses.append(sql.SQL("u.company_id = %s"))
        params.append(company_id)
    
    if role_filter:
        where_clauses.append(sql.SQL("u.role = %s"))
        params.append(role_filter)

    if search_term:
        # Case-insensitive search across multiple fields
        search_like = f"%{search_term}%"
        where_clauses.append(sql.SQL("(u.email ILIKE %s OR u.full_name ILIKE %s OR c.name ILIKE %s)"))
        params.extend([search_like, search_like, search_like])
    
    # Build the full query
    query = base_query
    if where_clauses:
        query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)

    # Safely handle sorting to prevent SQL injection
    sort_mapping = {
        'date_newest': sql.SQL(" ORDER BY u.created_at DESC"),
        'date_oldest': sql.SQL(" ORDER BY u.created_at ASC"),
        'name_asc': sql.SQL(" ORDER BY u.full_name ASC"),
        'email_asc': sql.SQL(" ORDER BY u.email ASC"),
        'company': sql.SQL(" ORDER BY c.name ASC, u.role DESC"),
        'role': sql.SQL(" ORDER BY u.role DESC, u.email ASC"),
    }
    order_clause = sort_mapping.get(sort_by, sort_mapping['date_newest']) # Default to newest
    query += order_clause

    with db_pool.get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

def update_user_password(user_id, new_password_hash):
    """Updates a user's password hash and unflags them for a forced reset."""
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s, force_reset = FALSE WHERE id = %s",
            (new_password_hash, user_id)
        )

def set_force_reset_flag(user_id, status):
    """Sets the 'force_reset' flag for a user, forcing a password change on next login."""
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET force_reset = %s WHERE id = %s",
            (status, user_id)
        )

def count_users_for_company(company_id):
    """Counts the number of users with role 'user' for a given company_id."""
    with db_pool.get_db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM users WHERE company_id = %s AND role = 'user'",
            (company_id,)
        )
        # The result of COUNT(*) is inside a 'count' key in the RealDictCursor
        result = cur.fetchone()
        return result['count'] if result else 0