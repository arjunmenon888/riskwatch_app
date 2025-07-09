# user_management.py

from werkzeug.security import generate_password_hash
from psycopg2 import sql
import db_users
import db_pool
import constants

# =============================================================================
# USER CREATION & VALIDATION
# =============================================================================

def create_user(email, password, role='user', company_name=None, creator_id=None):
    """
    Creates a new user, handling company association and creation rules.
    - Admins can create new companies on the fly if one doesn't exist.
    - Users must register under an existing company.
    - If a creator_id (an admin) is provided, their user creation limits are checked.
    - Sets a 'force_reset' flag for new admins and users.
    """
    # --- Admin User Creation Limit Validation ---
    if role == 'user' and creator_id:
        admin_creator = db_users.get_user_by_id(creator_id)
        if not admin_creator:
            raise PermissionError("Creator admin not found.")

        # Check if the admin is allowed to create users at all
        if not admin_creator.get('can_create_users'):
            raise PermissionError("You do not have permission to create users.")

        user_limit = admin_creator.get('user_creation_limit')
        # A limit of -1 signifies unlimited users, so we skip the count check
        if user_limit is not None and user_limit != -1:
            current_user_count = db_users.count_users_for_company(admin_creator['company_id'])
            if current_user_count >= user_limit:
                raise PermissionError(f"User creation limit of {user_limit} has been reached for your company.")
    
    hashed_password = generate_password_hash(password)
    company_id = None

    if role in ['admin', 'user'] and company_name:
        company = db_users.get_company_by_name(company_name)
        if company:
            company_id = company['id']
        elif role == 'admin' and creator_id is None: # Only Super Admin (no creator) can create a new company
            company_id = db_users.create_company(company_name)
        else:
            raise ValueError(f"Company '{company_name}' not found. Please select an existing company.")
            
    db_users.add_user_to_db(email, hashed_password, role, company_id)

    # After the user is created, if they are an admin or user, flag them for a password reset.
    if role in ['admin', 'user']:
        newly_created_user = db_users.get_user_by_email(email)
        if newly_created_user:
            db_users.set_force_reset_flag(newly_created_user['id'], True)


# =============================================================================
# USER RETRIEVAL & DELETION
# =============================================================================

def get_user_by_email(email):
    """Retrieves a single user's data by their email address."""
    return db_users.get_user_by_email(email)

def get_user_by_id(user_id):
    """Retrieves a single user's data by their unique ID."""
    return db_users.get_user_by_id(user_id)

def get_all_users(search_term=None, sort_by='date_newest', company_id=None, role_filter=None):
    """Retrieves a list of users with advanced filtering and sorting."""
    return db_users.get_all_users(search_term, sort_by, company_id, role_filter)

def delete_user(user_id):
    """
    Deletes a user from the database.
    If the user is an admin, it also deletes all users and the company associated with them.
    """
    user_to_delete = db_users.get_user_by_id(user_id)

    if not user_to_delete:
        raise ValueError(f"No user found with ID {user_id} to delete.")

    # If the user is an admin, trigger a full company data wipe.
    if user_to_delete.get('role') == 'admin':
        company_id = user_to_delete.get('company_id')
        if company_id:
            print(f"Admin deletion triggered for company ID: {company_id}. Cascading delete initiated.")
            # Step 1: Delete all 'user' role employees of the company.
            db_users.delete_users_by_company(company_id)
            # Step 2: Delete the admin user record itself.
            db_users.delete_user(user_id)
            # Step 3: Delete the company record. This will cascade-delete trainings, L&F, etc.
            db_users.delete_company(company_id)
            return # Exit after full company deletion.

    # If not an admin, or an admin with no company, just delete the single user record.
    db_users.delete_user(user_id)

# =============================================================================
# PERMISSION AND SETTINGS MANAGEMENT
# =============================================================================

def update_admin_settings(admin_id, can_create_users, user_creation_limit):
    """
    Updates an admin's ability to create users and their creation limit.
    A limit of -1 is treated as 'unlimited'.
    """
    # Sanitize input: limit cannot be None or less than -1
    if user_creation_limit is None or user_creation_limit < -1:
        user_creation_limit = 0

    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET can_create_users = %s, user_creation_limit = %s WHERE id = %s AND role = 'admin'",
            (can_create_users, user_creation_limit, admin_id)
        )
        if cur.rowcount == 0:
            raise ValueError("Could not find an admin with the specified ID to update.")

def update_user_permission(user_id, permission_name, status):
    """
    Updates a boolean permission for a user (e.g., 'can_access_training').
    If permission is revoked for an admin, it cascades to their users.
    """
    if permission_name not in constants.ALLOWED_PERMISSIONS:
        raise ValueError("Invalid permission name specified.")

    query = sql.SQL("UPDATE users SET {field} = %s WHERE id = %s").format(
        field=sql.Identifier(permission_name)
    )
    
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(query, (status, user_id))
        
    # If permission is being revoked for an admin, cascade the revocation to all their users
    if not status:
        target_user = get_user_by_id(user_id)
        if target_user and target_user['role'] == 'admin':
            revoke_permission_from_company_users(target_user['company_id'], permission_name)

def revoke_permission_from_company_users(company_id, permission_name):
    """
    Revokes a specific permission from all 'user' role accounts of a given company.
    """
    if not company_id or permission_name not in constants.ALLOWED_PERMISSIONS:
        return
        
    print(f"Cascading Revoke: Removing permission '{permission_name}' from all users in company ID {company_id}")
    
    query = sql.SQL("UPDATE users SET {field} = FALSE WHERE company_id = %s AND role = 'user'").format(
        field=sql.Identifier(permission_name)
    )
    
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(query, (company_id,))
        print(f"Update complete. {cur.rowcount} users affected.")

# =============================================================================
# PASSWORD AND PROFILE MANAGEMENT
# =============================================================================

def flag_user_for_reset(user_id):
    """Flags a user's account, requiring them to reset their password on next login."""
    db_users.set_force_reset_flag(user_id, True)

def reset_password_for_flagged_user(email, new_password):
    """Resets a password only if the user has been flagged for a reset by an admin."""
    user = get_user_by_email(email)
    if not user:
        raise ValueError("User not found.")
    if not user.get('force_reset'):
        raise PermissionError("Password reset not initiated for this user.")
    
    new_password_hash = generate_password_hash(new_password)
    db_users.update_user_password(user['id'], new_password_hash)

def update_user_profile(user_id, profile_data):
    """Updates a user's profile information (full_name, job_title, etc.)."""
    update_fields = {k: v for k, v in profile_data.items() if v is not None}
    
    if not update_fields:
        return # Nothing to update
        
    set_clause = sql.SQL(', ').join(
        sql.SQL("{field} = %s").format(field=sql.Identifier(k)) for k in update_fields.keys()
    )
    
    query = sql.SQL("UPDATE users SET {set_clause} WHERE id = %s").format(set_clause=set_clause)
    
    params = list(update_fields.values()) + [user_id]

    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(query, params)

def update_user_industry(user_id, new_industry):
    """Updates the 'industry' field for a specific user."""
    with db_pool.get_db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET industry = %s WHERE id = %s",
            (new_industry, user_id)
        )

# =============================================================================
# COMPANY MANAGEMENT
# =============================================================================

def get_all_companies():
    """Acts as a pass-through to the database layer to get all companies."""
    return db_users.get_all_companies()