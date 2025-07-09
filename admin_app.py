# admin_app.py

import dash
from dash import dcc, html, Input, Output, State, no_update, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user
import user_management
import constants

# =============================================================================
# LAYOUT DEFINITION
# =============================================================================


def create_admin_layout():
    """
    Creates the layout for the company admin panel.
    The permission toggles and table columns will only be shown if the admin
    themself has that corresponding permission.
    """
    # Dynamically build the permission options for the "Add User" form
    # based on the logged-in admin's own rights.
    permission_options = []
    if current_user.has_permission(constants.PERM_OBSERVATION):
        permission_options.append(
            {"label": "Observation Access", "value": constants.PERM_OBSERVATION}
        )
    if current_user.has_permission(constants.PERM_TRAINING):
        permission_options.append(
            {"label": "Training Access", "value": constants.PERM_TRAINING}
        )
    if current_user.has_permission(constants.PERM_LF):
        permission_options.append(
            {"label": "Lost & Found Access", "value": constants.PERM_LF}
        )
    if current_user.has_permission(constants.PERM_GATE_PASS):
        permission_options.append(
            {"label": "Gate Pass Access", "value": constants.PERM_GATE_PASS}
        )
    if current_user.has_permission(constants.PERM_ASK_AI):
        permission_options.append(
            {"label": "Ask Me AI Access", "value": constants.PERM_ASK_AI}
        )

    create_user_form = html.Div(
        [
            html.Div(id="create-user-message"),
            dbc.Label("Company", html_for="admin-create-user-company"),
            dbc.Input(
                id="admin-create-user-company",
                value=current_user.company_name,
                disabled=True,
                className="mb-2",
            ),
            dbc.Input(
                id="new-user-email",
                type="email",
                placeholder="User Email",
                className="mb-2",
            ),
            dbc.Input(
                id="new-user-password",
                type="password",
                placeholder="User Password",
                className="mb-3",
            ),
            dbc.Label("User Permissions:"),
            dbc.Checklist(
                options=permission_options,  # Use the dynamically generated options
                value=[],
                id="new-user-permissions",
                switch=True,
                inline=True,
                className="mb-3",
            ),
            dbc.Button(
                "Create User",
                id="create-user-button",
                color="primary",
                n_clicks=0,
                className="w-100",
            ),
        ]
    )

    # Dynamically build the table headers based on the admin's rights.
    table_headers = [html.Th("Full Name"), html.Th("User Email")]
    if current_user.has_permission(constants.PERM_OBSERVATION):
        table_headers.append(html.Th("Obs.", style={"textAlign": "center"}))
    if current_user.has_permission(constants.PERM_TRAINING):
        table_headers.append(html.Th("Train.", style={"textAlign": "center"}))
    if current_user.has_permission(constants.PERM_LF):
        table_headers.append(html.Th("L&F", style={"textAlign": "center"}))
    if current_user.has_permission(constants.PERM_GATE_PASS):
        table_headers.append(html.Th("Gate Pass", style={"textAlign": "center"}))
    if current_user.has_permission(constants.PERM_ASK_AI):
        table_headers.append(html.Th("Ask AI", style={"textAlign": "center"}))
    table_headers.append(html.Th("Actions", style={"width": "200px"}))

    return html.Div(
        [
            html.H1(f"Admin Panel: {current_user.company_name}"),
            dbc.Modal(
                [dbc.ModalHeader("Add New User"), dbc.ModalBody(create_user_form)],
                id="admin-add-user-modal",
                is_open=False,
                size="lg",
            ),
            html.H2("Company Users"),
            html.P("Manage permissions for users within your company."),
            dbc.Button(
                "Add New User",
                id="open-add-user-modal-button",
                color="success",
                className="mb-3",
            ),
            html.Div(id="admin-action-message"),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Input(
                            id="admin-user-search",
                            placeholder="Search by name or email...",
                            debounce=True,
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="admin-user-sort",
                            options=[
                                {"label": "Sort: Newest", "value": "date_newest"},
                                {"label": "Sort: Oldest", "value": "date_oldest"},
                                {"label": "Sort: Name (A-Z)", "value": "name_asc"},
                                {"label": "Sort: Email (A-Z)", "value": "email_asc"},
                            ],
                            value="date_newest",
                            clearable=False,
                        ),
                        md=6,
                    ),
                ],
                className="mb-3",
            ),
            dcc.Loading(
                children=dbc.Table(
                    [
                        html.Thead(html.Tr(table_headers)),  # Use the dynamic headers
                        html.Tbody(id="admin-user-table-body"),
                    ],
                    bordered=True,
                    striped=True,
                    hover=True,
                    responsive=True,
                )
            ),
            dcc.Store(id="admin-refresh-signal", data=0),
            dcc.ConfirmDialog(
                id="admin-confirm-delete-user",
                message="Are you sure you want to delete this user from your company?",
            ),
            dcc.Store(id="admin-user-to-delete"),
        ]
    )


# =============================================================================
# CALLBACK REGISTRATION
# =============================================================================


def register_callbacks(app):
    @app.callback(
        Output("admin-add-user-modal", "is_open"),
        Input("open-add-user-modal-button", "n_clicks"),
        State("admin-add-user-modal", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_add_user_modal(n_clicks, is_open):
        """Toggles the visibility of the 'Add User' modal."""
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output("create-user-message", "children"),
        Output("admin-refresh-signal", "data", allow_duplicate=True),
        Output("admin-add-user-modal", "is_open", allow_duplicate=True),
        Output("new-user-email", "value"),
        Output("new-user-password", "value"),
        Output("new-user-permissions", "value"),
        Input("create-user-button", "n_clicks"),
        [
            State("new-user-email", "value"),
            State("new-user-password", "value"),
            State("new-user-permissions", "value"),
            State("admin-refresh-signal", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_create_user(n_clicks, email, password, permissions, refresh_count):
        """Handles the logic for creating a new user, including limit checks."""
        clear_form = (False, "", "", [])  # Tuple to reset form fields on success
        no_change = (
            no_update,
            no_update,
            no_update,
            no_update,
        )  # Tuple for no change on error

        if not all([email, password]):
            return (
                dbc.Alert("Email and Password are required.", color="warning"),
                no_update,
                True,
                *no_change,
            )

        try:
            # Pass current_user.id as the creator for backend validation
            user_management.create_user(
                email,
                password,
                role="user",
                company_name=current_user.company_name,
                creator_id=current_user.id,
            )

            # If creation succeeds, set the user's initial permissions
            new_user = user_management.get_user_by_email(email)
            if new_user:
                for perm in permissions:
                    user_management.update_user_permission(new_user["id"], perm, True)

            return (
                dbc.Alert(
                    f"User created successfully.", color="success", dismissable=True
                ),
                refresh_count + 1,
                *clear_form,
            )

        except PermissionError as e:
            # Catch specific error if user limit is reached
            return (
                dbc.Alert(f"Error: {e}", color="danger"),
                no_update,
                True,
                *no_change,
            )
        except Exception as e:
            # Catch other potential errors (e.g., duplicate email)
            return (
                dbc.Alert(f"An unexpected error occurred: {e}", color="danger"),
                no_update,
                True,
                *no_change,
            )

    @app.callback(
        Output("admin-user-table-body", "children"),
        [
            Input("admin-refresh-signal", "data"),
            Input("admin-user-search", "value"),
            Input("admin-user-sort", "value"),
        ],
    )
    def update_user_list(refresh_signal, search_term, sort_by):
        """Updates the list of users based on search and sort criteria."""
        company_users = user_management.get_all_users(
            company_id=current_user.company_id,
            search_term=search_term,
            sort_by=sort_by,
            role_filter="user",  # We only want to manage 'user' roles here
        )
        rows = []

        for user in company_users:
            row_cells = [
                html.Td(user.get("full_name", "N/A")),
                html.Td(
                    dcc.Link(
                        user["email"],
                        href=f"/admin/view-report/{user['id']}",
                        style={"display": "none"}
                        if not current_user.has_permission(constants.PERM_OBSERVATION)
                        else {},
                    )
                ),
            ]

            # Dynamically build the permission toggle cells based on the admin's rights
            if current_user.has_permission(constants.PERM_OBSERVATION):
                row_cells.append(
                    html.Td(
                        dbc.Checklist(
                            options=[{"label": "", "value": 1}],
                            id={
                                "type": "user-perm-toggle",
                                "user_id": user["id"],
                                "perm": constants.PERM_OBSERVATION,
                            },
                            value=[1] if user.get(constants.PERM_OBSERVATION) else [],
                            switch=True,
                        ),
                        style={"textAlign": "center"},
                    )
                )
            if current_user.has_permission(constants.PERM_TRAINING):
                row_cells.append(
                    html.Td(
                        dbc.Checklist(
                            options=[{"label": "", "value": 1}],
                            id={
                                "type": "user-perm-toggle",
                                "user_id": user["id"],
                                "perm": constants.PERM_TRAINING,
                            },
                            value=[1] if user.get(constants.PERM_TRAINING) else [],
                            switch=True,
                        ),
                        style={"textAlign": "center"},
                    )
                )
            if current_user.has_permission(constants.PERM_LF):
                row_cells.append(
                    html.Td(
                        dbc.Checklist(
                            options=[{"label": "", "value": 1}],
                            id={
                                "type": "user-perm-toggle",
                                "user_id": user["id"],
                                "perm": constants.PERM_LF,
                            },
                            value=[1] if user.get(constants.PERM_LF) else [],
                            switch=True,
                        ),
                        style={"textAlign": "center"},
                    )
                )
            if current_user.has_permission(constants.PERM_GATE_PASS):
                row_cells.append(
                    html.Td(
                        dbc.Checklist(
                            options=[{"label": "", "value": 1}],
                            id={
                                "type": "user-perm-toggle",
                                "user_id": user["id"],
                                "perm": constants.PERM_GATE_PASS,
                            },
                            value=[1] if user.get(constants.PERM_GATE_PASS) else [],
                            switch=True,
                        ),
                        style={"textAlign": "center"},
                    )
                )
            if current_user.has_permission(constants.PERM_ASK_AI):
                row_cells.append(
                    html.Td(
                        dbc.Checklist(
                            options=[{"label": "", "value": 1}],
                            id={
                                "type": "user-perm-toggle",
                                "user_id": user["id"],
                                "perm": constants.PERM_ASK_AI,
                            },
                            value=[1] if user.get(constants.PERM_ASK_AI) else [],
                            switch=True,
                        ),
                        style={"textAlign": "center"},
                    )
                )

            row_cells.append(
                html.Td(
                    html.Div(
                        [
                            dbc.Button(
                                "Delete",
                                id={"type": "admin-delete-user", "user_id": user["id"]},
                                color="danger",
                                size="sm",
                            ),
                            dbc.Button(
                                "Reset Pass",
                                id={"type": "admin-reset-pass", "user_id": user["id"]},
                                color="warning",
                                size="sm",
                                className="ms-1",
                            ),
                        ],
                        className="d-flex",
                    )
                )
            )

            rows.append(html.Tr(row_cells))
        return rows

    @app.callback(
        Output("admin-action-message", "children", allow_duplicate=True),
        Input({"type": "user-perm-toggle", "user_id": ALL, "perm": ALL}, "value"),
        prevent_initial_call=True,
    )
    def handle_user_permission_toggle(values):
        """Handles toggling a specific service permission for a user."""
        ctx = dash.callback_context
        if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
            raise PreventUpdate

        user_id = ctx.triggered_id["user_id"]
        permission = ctx.triggered_id["perm"]
        new_status = bool(ctx.triggered[0]["value"])
        try:
            target_user = user_management.get_user_by_id(user_id)
            if not target_user or target_user["company_id"] != current_user.company_id:
                return dbc.Alert(
                    "Permission Denied: User not in your company.", color="danger"
                )

            user_management.update_user_permission(user_id, permission, new_status)
            return dbc.Alert("Permission updated.", color="success", duration=2000)
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger")

    @app.callback(
        Output("admin-confirm-delete-user", "displayed"),
        Output("admin-user-to-delete", "data"),
        Input({"type": "admin-delete-user", "user_id": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def display_admin_delete_confirmation(n_clicks_list):
        """Shows the delete confirmation dialog."""
        if not any(n for n in n_clicks_list if n):
            raise PreventUpdate
        return True, dash.callback_context.triggered_id["user_id"]

    @app.callback(
        Output("admin-action-message", "children", allow_duplicate=True),
        Output("admin-refresh-signal", "data", allow_duplicate=True),
        Input("admin-confirm-delete-user", "submit_n_clicks"),
        [State("admin-user-to-delete", "data"), State("admin-refresh-signal", "data")],
        prevent_initial_call=True,
    )
    def process_admin_user_deletion(submit_n_clicks, user_id, refresh_count):
        """Deletes a user after confirmation."""
        if not user_id:
            return no_update, no_update
        try:
            user_to_delete = user_management.get_user_by_id(user_id)
            if (
                not user_to_delete
                or user_to_delete["company_id"] != current_user.company_id
            ):
                raise PermissionError(
                    "You can only delete users from your own company."
                )
            user_management.delete_user(user_id)
            return dbc.Alert(
                "User deleted successfully.", color="success", duration=3000
            ), refresh_count + 1
        except Exception as e:
            return dbc.Alert(f"Error deleting user: {e}", color="danger"), no_update

    @app.callback(
        Output("admin-action-message", "children", allow_duplicate=True),
        Input({"type": "admin-reset-pass", "user_id": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_password_reset_flag(n_clicks):
        """Flags a user's password for reset."""
        if not any(n for n in n_clicks if n):
            raise PreventUpdate
        user_id = dash.callback_context.triggered_id["user_id"]
        user_to_reset = user_management.get_user_by_id(user_id)
        if not user_to_reset or user_to_reset["company_id"] != current_user.company_id:
            return dbc.Alert("Permission Denied.", color="danger")
        try:
            user_management.flag_user_for_reset(user_id)
            return dbc.Alert(
                f"Password reset initiated for {user_to_reset['email']}.",
                color="info",
                duration=5000,
            )
        except Exception as e:
            return dbc.Alert(f"Error initiating reset: {e}", color="danger")
