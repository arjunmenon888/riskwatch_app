# routes.py

import re
from flask_login import current_user
import design_components as dc
import constants

# Import layout functions from their respective modules
import observation_app
import admin_app
import super_admin_app
import training_app
import user_training_app
import admin_report_view_app
import lost_and_found_app
import landing_page
import profile_app
import gate_pass_app
import ask_ai_app
import social_app # NEW: Import social_app

def render_page_content(pathname):
    """
    This is the central router for the application. It takes the URL pathname
    and returns the appropriate page content layout based on the user's role
    and the specific route. It also enforces access control.
    """
    
    # Profile completion is mandatory for all authenticated users.
    if pathname == '/complete-profile':
        return profile_app.create_profile_layout()

    # --- FIX: Change from '==' to 'startswith' to catch all sub-routes ---
    # This will now correctly handle '/social', '/social/public', and '/social/<user_id>'
    elif pathname.startswith('/social'):
        return social_app.create_social_layout()

    # --- Standard User Routes (Permission-Based) ---
    
    if pathname == '/observation':
        if current_user.has_permission(constants.PERM_OBSERVATION):
            return observation_app.create_observation_form_layout()
    
    elif pathname == '/report':
        if current_user.has_permission(constants.PERM_OBSERVATION):
            return observation_app.create_report_layout()
            
    elif pathname.startswith('/training'):
        if current_user.has_permission(constants.PERM_TRAINING):
            match_view = re.fullmatch(r'/training/view/(\d+)', pathname)
            match_result = re.fullmatch(r'/training/result/(\d+)', pathname)

            if match_view:
                training_id = int(match_view.group(1))
                return user_training_app.create_quiz_page_layout(training_id)
            elif match_result:
                attempt_id = int(match_result.group(1))
                return user_training_app.create_result_page_layout(attempt_id)
            elif pathname == '/training':
                return user_training_app.create_user_training_list_layout()
    
    elif pathname == '/lost-and-found':
        if current_user.has_permission(constants.PERM_LF):
            return lost_and_found_app.create_lost_and_found_form_layout()

    elif pathname == '/lost-and-found/report':
        if current_user.has_permission(constants.PERM_LF):
            return lost_and_found_app.create_lost_and_found_report_layout()
            
    elif pathname == '/gate-pass':
        if current_user.has_permission(constants.PERM_GATE_PASS):
            return gate_pass_app.create_gate_pass_form_layout()

    elif pathname == '/gate-pass/report':
        if current_user.has_permission(constants.PERM_GATE_PASS):
            return gate_pass_app.create_gate_pass_report_layout()
    
    elif pathname == '/ask-ai':
        if current_user.has_permission(constants.PERM_ASK_AI):
            return ask_ai_app.create_ask_ai_layout()
        
    # --- Admin and Super Admin Routes (Role-Based with Permission Checks) ---

    elif pathname.startswith('/admin'):
        if current_user.role == 'admin':
            
            # --- CORRECTED: Route guard for admins with user management rights ---
            # All general admin pages require the 'can_create_users' flag.
            # This check is now reliable because models.py loads the attribute.
            if current_user.can_create_users:
                if re.fullmatch(r'/admin/view-report/(\d+)', pathname):
                    # This route is part of the observation report feature,
                    # so it still respects the observation permission.
                    if current_user.has_permission(constants.PERM_OBSERVATION):
                        user_id = int(pathname.split('/')[-1])
                        return admin_report_view_app.create_admin_user_report_layout(user_id)
                
                if pathname == '/admin':
                    return admin_app.create_admin_layout()

            # The training management page is separate from user management
            # and is controlled by its own service permission.
            if pathname.startswith('/admin/training'):
                if not current_user.has_permission(constants.PERM_TRAINING):
                    return dc.create_access_denied_page()

                match_user_attempts = re.fullmatch(r'/admin/training/results/(\d+)/user/(\d+)', pathname)
                match_results = re.fullmatch(r'/admin/training/results/(\d+)', pathname)
                match_edit = re.fullmatch(r'/admin/training/edit/(\d+)', pathname)

                if match_user_attempts:
                    training_id, user_id = map(int, match_user_attempts.groups())
                    return training_app.create_user_attempts_layout(training_id, user_id)
                elif match_results:
                    training_id = int(match_results.group(1))
                    return training_app.create_training_results_layout(training_id)
                elif match_edit:
                    training_id = int(match_edit.group(1))
                    return training_app.create_training_form_layout(training_id=training_id)
                elif pathname == '/admin/training/create':
                    return training_app.create_training_form_layout()
                elif pathname == '/admin/training':
                    return training_app.create_training_management_layout()

    elif pathname.startswith('/super-admin'):
        if current_user.role == 'super_admin':
            if pathname.startswith('/super-admin/training'):
                # Super admin training management routes
                match_user_attempts = re.fullmatch(r'/super-admin/training/results/(\d+)/user/(\d+)', pathname)
                match_results = re.fullmatch(r'/super-admin/training/results/(\d+)', pathname)
                match_edit = re.fullmatch(r'/super-admin/training/edit/(\d+)', pathname)

                if match_user_attempts:
                    training_id, user_id = map(int, match_user_attempts.groups())
                    return training_app.create_user_attempts_layout(training_id, user_id)
                elif match_results:
                    training_id = int(match_results.group(1))
                    return training_app.create_training_results_layout(training_id)
                elif match_edit:
                    training_id = int(match_edit.group(1))
                    return training_app.create_training_form_layout(training_id=training_id)
                elif pathname == '/super-admin/training/create':
                    return training_app.create_training_form_layout()
                elif pathname == '/super-admin/training':
                    return training_app.create_training_management_layout()

            elif pathname == '/super-admin':
                return super_admin_app.create_super_admin_layout()

    # If no route has matched by this point, the user does not have permission.
    return dc.create_access_denied_page()