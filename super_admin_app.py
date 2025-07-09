# super_admin_app.py

import dash
from dash import dcc, html, Input, Output, State, no_update, ALL, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import user_management
import constants
import db_users # Directly used for counting users for the UI display

# =============================================================================
# LAYOUT DEFINITION
# =============================================================================

def create_super_admin_layout():
    return html.Div([
        html.H1("Super Admin Dashboard"),
        dbc.Modal(id="super-admin-add-admin-modal", scrollable=True, size="lg"),
        dbc.Modal(id="super-admin-edit-admin-modal", scrollable=True, size="lg"),
        html.H2("Company Admins Management"),
        html.P("Click on an Admin to view their users and edit their settings."),
        dbc.Button("Add New Admin", id="open-add-admin-modal-button", color="success", className="mb-3"),
        html.Div(id='super-admin-action-message'),
        dcc.Loading(children=html.Div(id='super-admin-admin-list-container')),
        dcc.Store(id='super-admin-refresh-signal', data=0),
        dcc.ConfirmDialog(id='super-admin-confirm-delete-user', message='Are you sure you want to delete this user? This action cannot be undone.'),
        dcc.Store(id='super-admin-user-to-delete')
    ])

# =============================================================================
# UI HELPER FUNCTIONS
# =============================================================================

def build_admin_accordion_item(admin_user):
    user_count = db_users.count_users_for_company(admin_user['company_id'])
    limit = admin_user.get('user_creation_limit', 0)
    can_create = admin_user.get('can_create_users', False)

    if can_create:
        limit_str = f"Limit: {user_count} / {limit if limit != -1 else '∞'}"
        status_color = "success" if (limit == -1 or user_count < limit) else "warning"
        status_badge = dbc.Badge(limit_str, color=status_color, className="me-2", pill=True)
    else:
        status_badge = dbc.Badge("User Creation Disabled", color="secondary", className="me-2", pill=True)

    accordion_header = html.Div([
        html.Div([
            html.Strong(admin_user.get('company_name', 'No Company')),
            html.Div(admin_user.get('email'), className="text-muted small")
        ]),
        html.Div([
            status_badge,
            dbc.Button("Edit Settings", id={'type': 'edit-admin-settings-btn', 'admin_id': admin_user['id']}, size="sm", color="secondary", outline=True, className="ms-1"),
            dbc.Button("Reset Pass", id={'type': 'super-admin-reset-admin-pass', 'admin_id': admin_user['id']}, size="sm", color="warning", outline=True, className="ms-1"),
            dbc.Button("Delete", id={'type': 'super-admin-delete-admin', 'admin_id': admin_user['id']}, size="sm", color="danger", outline=True, className="ms-1")
        ], className="ms-auto d-flex align-items-center")
    ], className="d-flex w-100 justify-content-between align-items-center")

    accordion_body = dcc.Loading(html.Div(id={'type': 'admin-user-list', 'admin_id': admin_user['id']}))
    item_id_str = f"accordion-item-{admin_user['id']}"
    return dbc.AccordionItem(title=accordion_header, children=accordion_body, item_id=item_id_str)

def build_user_table_for_admin(users):
    if not users:
        return html.P("This admin has not created any users.", className="p-3 text-center text-muted")
    header = html.Thead(html.Tr([
        html.Th("Full Name"), html.Th("Email"), html.Th("Actions", style={'width': '200px'})
    ]))
    rows = []
    for user in users:
        rows.append(html.Tr([
            html.Td(user.get('full_name', 'N/A')),
            html.Td(user['email']),
            html.Td(html.Div([
                dbc.Button("Reset Pass", id={'type': 'super-admin-reset-pass', 'user_id': user['id']}, color='warning', size='sm', outline=True),
                dbc.Button("Delete", id={'type': 'super-admin-delete-user', 'user_id': user['id']}, color='danger', size='sm', outline=True, className="ms-1")
            ], className='d-flex'))
        ]))
    return dbc.Table([header, html.Tbody(rows)], bordered=False, striped=True, hover=True, size="sm", className="mb-0")

# =============================================================================
# CALLBACK REGISTRATION
# =============================================================================

def register_callbacks(app):
    @app.callback(
        Output('super-admin-admin-list-container', 'children'),
        Input('super-admin-refresh-signal', 'data')
    )
    def update_admin_list(refresh_signal):
        admins = user_management.get_all_users(role_filter='admin', sort_by='company')
        if not admins:
            return html.P("No admins found.", className="text-center mt-4")
        accordion_items = [build_admin_accordion_item(admin) for admin in admins]
        return dbc.Accordion(accordion_items, id='admin-accordion', flush=True, always_open=True, className="mt-3")

    @app.callback(
        Output({'type': 'admin-user-list', 'admin_id': ALL}, 'children'),
        Input('admin-accordion', 'active_item'),
        prevent_initial_call=True
    )
    def load_users_for_active_admin(active_items):
        if not active_items: return [no_update] * len(ctx.outputs_list)
        if not isinstance(active_items, list): active_items = [active_items]
        triggered_admin_ids = [int(item.split('-')[-1]) for item in active_items]
        outputs = [no_update] * len(ctx.outputs_list)
        for i, output_spec in enumerate(ctx.outputs_list):
            admin_id_from_output = output_spec['id']['admin_id']
            if admin_id_from_output in triggered_admin_ids:
                admin_details = user_management.get_user_by_id(admin_id_from_output)
                if admin_details:
                    users = user_management.get_all_users(company_id=admin_details['company_id'], role_filter='user')
                    outputs[i] = build_user_table_for_admin(users)
        return outputs

    @app.callback(
        Output("super-admin-add-admin-modal", "is_open"),
        Output("super-admin-add-admin-modal", "children"),
        Input("open-add-admin-modal-button", "n_clicks"),
        prevent_initial_call=True
    )
    def open_add_admin_modal(n_clicks):
        modal_content = [
            dbc.ModalHeader("Add New Company Admin"),
            dbc.ModalBody([
                html.Div(id='create-admin-message'),
                dbc.Input(id='new-admin-email', type='email', placeholder='Admin Email', className="mb-2"),
                dbc.Input(id='new-admin-password', type='password', placeholder='Admin Password', className="mb-2"),
                dbc.Input(id='new-admin-company', type='text', placeholder='Company Name (must be unique)', className="mb-3"),
            ]),
            dbc.ModalFooter(dbc.Button("Create Admin", id='create-admin-button', color='primary'))
        ]
        return True, modal_content

    @app.callback(
        Output('create-admin-message', 'children'),
        Output('super-admin-refresh-signal', 'data', allow_duplicate=True),
        Output('super-admin-add-admin-modal', 'is_open', allow_duplicate=True),
        Input('create-admin-button', 'n_clicks'),
        [State('new-admin-email', 'value'), State('new-admin-password', 'value'),
         State('new-admin-company', 'value'), State('super-admin-refresh-signal', 'data')],
        prevent_initial_call=True
    )
    def handle_create_admin(n_clicks, email, password, company, refresh_count):
        if not all([email, password, company]):
            return dbc.Alert("All fields are required.", color="warning"), no_update, True
        try:
            user_management.create_user(email, password, role='admin', company_name=company, creator_id=None)
            return None, refresh_count + 1, False
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger"), no_update, True

    # --- THIS IS THE NEW CALLBACK TO FIX THE UI ---
    @app.callback(
        Output({'type': 'edit-admin-limit', 'admin_id': ALL}, 'disabled'),
        Input({'type': 'edit-admin-can-create', 'admin_id': ALL}, 'value'),
        prevent_initial_call=True
    )
    def toggle_limit_field_disabled_state(can_create_values):
        outputs = []
        for val in can_create_values:
            outputs.append(not bool(val))
        return outputs

    @app.callback(
        Output("super-admin-edit-admin-modal", "is_open"),
        Output("super-admin-edit-admin-modal", "children"),
        Input({'type': 'edit-admin-settings-btn', 'admin_id': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def open_edit_admin_modal(n_clicks):
        if not ctx.triggered_id or not any(n for n in n_clicks if n): raise PreventUpdate
        admin_id = ctx.triggered_id['admin_id']
        admin = user_management.get_user_by_id(admin_id)
        if not admin: return False, dbc.Alert("Admin not found.", color="danger")
        current_service_perms = [p for p in constants.ALLOWED_PERMISSIONS if admin.get(p)]
        service_perm_options = [
            {"label": "Observation Access", "value": constants.PERM_OBSERVATION},
            {"label": "Training Access", "value": constants.PERM_TRAINING},
            {"label": "Lost & Found Access", "value": constants.PERM_LF},
            {"label": "Gate Pass Access", "value": constants.PERM_GATE_PASS},
            {"label": "Ask AI Access", "value": constants.PERM_ASK_AI},
        ]
        can_create_users_bool = admin.get('can_create_users', False)
        modal_content = [
            dbc.ModalHeader(f"Edit Settings for {admin['email']}"),
            dbc.ModalBody([
                html.Div(id='edit-admin-message'),
                html.H5("User Management", className="mt-2"), html.Hr(),
                dbc.Checklist(
                    options=[{"label": "Allow this admin to create users", "value": True}],
                    value=[True] if can_create_users_bool else [],
                    id={'type': 'edit-admin-can-create', 'admin_id': admin_id},
                    switch=True, className="mb-3"
                ),
                dbc.Label("User Creation Limit (-1 for unlimited)"),
                dbc.Input(id={'type': 'edit-admin-limit', 'admin_id': admin_id}, type="number", value=admin.get('user_creation_limit', 0), min=-1, step=1, disabled=not can_create_users_bool),
                html.H5("Service Permissions", className="mt-4"),
                html.P("These permissions determine which services the admin (and their users) can access.", className="text-muted small"), html.Hr(),
                dbc.Checklist(options=service_perm_options, value=current_service_perms, id={'type': 'edit-admin-service-perms', 'admin_id': admin_id}, switch=True)
            ]),
            dbc.ModalFooter(dbc.Button("Save Settings", id={'type': 'save-admin-settings-btn', 'admin_id': admin_id}, color='primary'))
        ]
        return True, modal_content

    @app.callback(
        Output('edit-admin-message', 'children'),
        Output('super-admin-refresh-signal', 'data', allow_duplicate=True),
        Output("super-admin-edit-admin-modal", "is_open", allow_duplicate=True),
        Input({'type': 'save-admin-settings-btn', 'admin_id': ALL}, 'n_clicks'),
        [State({'type': 'edit-admin-can-create', 'admin_id': ALL}, 'value'),
         State({'type': 'edit-admin-limit', 'admin_id': ALL}, 'value'),
         State({'type': 'edit-admin-service-perms', 'admin_id': ALL}, 'value'),
         State('super-admin-refresh-signal', 'data')],
        prevent_initial_call=True
    )
    def save_admin_settings(n_clicks, can_create_values, limit_values, service_perm_values, refresh_count):
        if not ctx.triggered_id or not any(n for n in n_clicks if n): raise PreventUpdate
        admin_id = ctx.triggered_id['admin_id']
        can_create_list = next((v for s, v in zip(ctx.states_list[0], can_create_values) if s['id']['admin_id'] == admin_id), [])
        limit_val = next((v for s, v in zip(ctx.states_list[1], limit_values) if s['id']['admin_id'] == admin_id), 0)
        selected_perms = next((v for s, v in zip(ctx.states_list[2], service_perm_values) if s['id']['admin_id'] == admin_id), [])
        can_create_bool = bool(can_create_list)
        try:
            user_management.update_admin_settings(admin_id, can_create_bool, limit_val)
            for perm in constants.ALLOWED_PERMISSIONS:
                user_management.update_user_permission(admin_id, perm, perm in selected_perms)
            return None, refresh_count + 1, False
        except Exception as e:
            return dbc.Alert(f"Error saving settings: {e}", color="danger"), no_update, True

    @app.callback(
        Output('super-admin-confirm-delete-user', 'displayed'),
        Output('super-admin-user-to-delete', 'data'),
        Input({'type': 'super-admin-delete-user', 'user_id': ALL}, 'n_clicks'),
        Input({'type': 'super-admin-delete-admin', 'admin_id': ALL}, 'n_clicks'),
        prevent_initial_call=True,
    )
    def display_delete_confirmation(user_n_clicks, admin_n_clicks):
        """Shows the delete confirmation dialog for either a user or an admin."""
        triggered_id = ctx.triggered_id
        if not triggered_id or not (any(c for c in user_n_clicks if c) or any(c for c in admin_n_clicks if c)):
            raise PreventUpdate

        if triggered_id['type'] == 'super-admin-delete-user':
            id_to_delete = triggered_id['user_id']
        elif triggered_id['type'] == 'super-admin-delete-admin':
            id_to_delete = triggered_id['admin_id']
        else:
            raise PreventUpdate
            
        return True, id_to_delete

    @app.callback(
        Output('super-admin-action-message', 'children', allow_duplicate=True),
        Output('super-admin-refresh-signal', 'data', allow_duplicate=True),
        Input('super-admin-confirm-delete-user', 'submit_n_clicks'),
        [State('super-admin-user-to-delete', 'data'), State('super-admin-refresh-signal', 'data')],
        prevent_initial_call=True
    )
    def process_user_deletion(submit_n_clicks, user_id, r_count):
        if not user_id: return no_update, no_update
        try:
            user_management.delete_user(user_id)
            return dbc.Alert("User deleted successfully.", color="info", duration=3000), r_count + 1
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger"), no_update

    @app.callback(
        Output('super-admin-action-message', 'children', allow_duplicate=True),
        Input({'type': 'super-admin-reset-pass', 'user_id': ALL}, 'n_clicks'),
        Input({'type': 'super-admin-reset-admin-pass', 'admin_id': ALL}, 'n_clicks'),
        prevent_initial_call=True,
    )
    def handle_password_reset(user_n_clicks, admin_n_clicks):
        """Flags a user's or an admin's password for reset."""
        triggered_id = ctx.triggered_id
        if not triggered_id or not (any(c for c in user_n_clicks if c) or any(c for c in admin_n_clicks if c)):
            raise PreventUpdate
            
        if triggered_id['type'] == 'super-admin-reset-pass':
            id_to_reset = triggered_id['user_id']
        elif triggered_id['type'] == 'super-admin-reset-admin-pass':
            id_to_reset = triggered_id['admin_id']
        else:
            raise PreventUpdate

        try:
            user_management.flag_user_for_reset(id_to_reset)
            user = user_management.get_user_by_id(id_to_reset)
            return dbc.Alert(f"Password reset flagged for {user['email']}.", "info", duration=5000),
        except Exception as e:
            return dbc.Alert(f"Error: {e}", "danger"),