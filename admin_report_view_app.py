# admin_report_view_app.py

import dash
from dash import dcc, html, Input, Output, State, no_update, ALL
from dash.exceptions import PreventUpdate
from flask_login import current_user
import json

import db_observations
import user_management
import design_components

def create_admin_user_report_layout(user_id):
    """Layout for an admin viewing a specific user's report page."""
    try:
        user = user_management.get_user_by_id(user_id)
        if not user:
            return html.H1("Error: User Not Found")
        if user.get('company_id') != current_user.company_id:
             return design_components.create_access_denied_page(message="User is not in your company.")
        user_email = user['email']
    except Exception as e:
        return html.H1(f"Error fetching user: {e}")

    return html.Div([
        dcc.Store(id='store-target-user-id', data=user_id),
        dcc.ConfirmDialog(id='admin-confirm-delete-dialog', message='ADMIN ACTION: Are you sure you want to delete this user\'s observation?'),
        dcc.Store(id='admin-store-id-to-delete'),
        dcc.Store(id='admin-store-refresh-signal', data=0),
        html.H1(f"Viewing Report For: {user_email}"),
        html.Div(className="report-main-content", children=[
            html.Div(id='admin-delete-status-message'),
            html.Div(className="report-controls", children=[
                dcc.Input(id='admin-search-input', type='text', placeholder=f'Search in {user_email}\'s reports...', debounce=True, className='search-bar'),
                dcc.Dropdown(
                    id='admin-sort-dropdown',
                    options=[
                        {'label': 'Sort: Newest First', 'value': 'date_newest'},
                        {'label': 'Sort: Oldest First', 'value': 'date_oldest'},
                        {'label': 'Sort: Highest Risk', 'value': 'risk_high'},
                    ], value='date_newest', clearable=False, className='sort-dropdown-wrapper'
                ),
            ]),
            dcc.Loading(id="loading-admin-report", type="default", children=html.Div(id='admin-report-content-container'))
        ])
    ])

def register_callbacks(app):
    @app.callback(
        Output('admin-report-content-container', 'children'),
        Input('admin-search-input', 'value'),
        Input('admin-sort-dropdown', 'value'),
        Input('admin-store-refresh-signal', 'data'),
        State('store-target-user-id', 'data')
    )
    def update_admin_report_view(search_term, sort_by, refresh_signal, target_user_id):
        if not target_user_id:
            raise PreventUpdate
        
        if not (current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role == 'admin'):
            return html.Div("Access Denied.", className="message-error")

        target_user = user_management.get_user_by_id(target_user_id)
        if not target_user or target_user['company_id'] != current_user.company_id:
            return html.Div("Access Denied.", className="message-error")

        observations = db_observations.get_observations_from_db(target_user_id, search_term, sort_by)
        
        if not observations:
            return html.P("This user has no observations.", style={'textAlign': 'center', 'padding': '50px', 'fontSize': '1.2em'})
        
        cards = [design_components.create_observation_card(obs, is_admin_view=True) for obs in observations]
        return cards

    @app.callback(
        Output('admin-confirm-delete-dialog', 'displayed'),
        Output('admin-store-id-to-delete', 'data'),
        Input({'type': 'admin-delete-obs-button', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def display_admin_delete_confirmation(n_clicks_list):
        if not any(n > 0 for n in n_clicks_list if n is not None):
            raise PreventUpdate
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
            
        prop_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
        prop_id = json.loads(prop_id_str)
        obs_id_to_delete = prop_id['index']
        return True, obs_id_to_delete

    @app.callback(
        Output('admin-store-refresh-signal', 'data'),
        Output('admin-delete-status-message', 'children'),
        Input('admin-confirm-delete-dialog', 'submit_n_clicks'),
        State('admin-store-id-to-delete', 'data'),
        State('store-target-user-id', 'data'),
        State('admin-store-refresh-signal', 'data'),
        prevent_initial_call=True
    )
    def process_admin_deletion(submit_n_clicks, obs_id, target_user_id, refresh_count):
        if not obs_id: return no_update, no_update
        try:
            target_user = user_management.get_user_by_id(target_user_id)
            if not target_user or target_user['company_id'] != current_user.company_id:
                raise PermissionError("Admin does not have permission for this user.")

            db_observations.delete_observation_from_db(obs_id, target_user_id, is_admin=True)
            message = html.Div(f"Observation #{obs_id} was successfully deleted by admin.", className="message-success")
            return refresh_count + 1, message
        except Exception as e:
            message = html.Div(f"Error: Could not delete observation #{obs_id}. Details: {e}", className="message-error")
            return no_update, message