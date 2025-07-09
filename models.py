# models.py

from flask_login import UserMixin
import user_management
import base64

class User(UserMixin):
    """
    The User class for Flask-Login. This object represents the currently logged-in user
    and holds all their relevant data and permissions for the duration of their session.
    """
    def __init__(self, user_id):
        # Fetch all user data from the database using the business logic layer
        user_data = user_management.get_user_by_id(user_id)
        
        if user_data:
            # --- Standard User Attributes ---
            self.id = user_data['id']
            self.email = user_data['email']
            self.role = user_data['role']
            
            # --- Profile & Company Information (with safe .get() defaults) ---
            self.industry = user_data.get('industry', 'General')
            self.company_id = user_data.get('company_id')
            self.company_name = user_data.get('company_name')
            self.full_name = user_data.get('full_name')
            self.job_title = user_data.get('job_title')
            self.department = user_data.get('department')
            self.employee_id = user_data.get('employee_id')
            self.profile_photo_bytes = user_data.get('profile_photo_bytes')

            # --- Service-Level Permissions ---
            # Load all permission flags from the database record.
            self.can_access_observation = user_data.get('can_access_observation', False)
            self.can_access_training = user_data.get('can_access_training', False)
            self.can_access_lost_and_found = user_data.get('can_access_lost_and_found', False)
            self.can_access_gate_pass = user_data.get('can_access_gate_pass', False)
            self.can_access_ask_ai = user_data.get('can_access_ask_ai', False)
            
            # --- Admin-Specific Permissions ---
            # These are loaded for every user but will only be True/non-zero for admins.
            # This is safe and prevents errors when checking these attributes on regular users.
            self.can_create_users = user_data.get('can_create_users', False)
            self.user_creation_limit = user_data.get('user_creation_limit', 0)

        else:
            # If no user is found for the ID, set id to None
            self.id = None

    def get_id(self):
        """Required method for Flask-Login to get the user's ID."""
        return self.id

    @property
    def is_active(self):
        """
        Required property for Flask-Login. A user is considered active if they
        were successfully loaded from the database (i.e., self.id is not None).
        """
        return self.id is not None

    def has_permission(self, permission_name):
        """
        Centralized method to check if a user has a specific service permission.
        Super admins are a special case and always have all permissions.
        """
        if self.role == 'super_admin':
            return True
        # Use getattr() to safely check for the permission attribute on the self object.
        # This returns False if the attribute doesn't exist, preventing errors.
        return getattr(self, permission_name, False)
        
    def get_profile_photo_b64(self):
        """
        Returns the user's profile photo as a base64 encoded string for use in HTML,
        or None if no photo is set.
        """
        if self.profile_photo_bytes:
            return base64.b64encode(self.profile_photo_bytes).decode('utf-8')
        return None