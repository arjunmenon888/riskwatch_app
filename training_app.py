# training_app.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, no_update, ALL, dash_table
from flask_login import current_user
from dash.exceptions import PreventUpdate

import db_training
import db_users
from design_components import create_access_denied_page


def get_base_path():
    """Determines the base URL path based on the user's role."""
    if current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role == 'super_admin':
        return '/super-admin/training'
    return '/admin/training'


def create_training_management_layout():
    base_path = get_base_path()
    table_headers = ["Training Name", "Company", "Date Created", "Actions"] if current_user.role == 'super_admin' else ["Training Name", "Description", "Date Created", "Actions"]
    
    sort_options = [
        {'label': 'Sort: Newest', 'value': 'date_newest'},
        {'label': 'Sort: Oldest', 'value': 'date_oldest'},
        {'label': 'Sort: Name (A-Z)', 'value': 'name_asc'},
    ]
    if current_user.role == 'super_admin':
        sort_options.append({'label': 'Sort: Company (A-Z)', 'value': 'company_asc'})

    return html.Div([
        html.H1("Training Management"),
        html.P("Create, edit, and view results for training modules."),
        html.Div(id="training-action-status"),
        dcc.Link(dbc.Button("Create New Training", color="primary", className="mb-3"), href=f"{base_path}/create"),
        dbc.Row([
            dbc.Col(dbc.Input(id="training-search-input", placeholder="Search trainings...", debounce=True), md=6),
            dbc.Col(dcc.Dropdown(id="training-sort-dropdown", options=sort_options, value='date_newest', clearable=False), md=6)
        ], className="mb-3"),
        # FIX: Added responsive=True to the table
        dcc.Loading(children=dbc.Table([
            html.Thead(html.Tr([html.Th(h) for h in table_headers])),
            html.Tbody(id='training-table-body')
        ], bordered=True, striped=True, hover=True, responsive=True)),
        dbc.Modal([
            dbc.ModalHeader("Confirm Deletion"),
            dbc.ModalBody("Are you sure you want to delete this training module? This action cannot be undone."),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="delete-training-cancel", className="ml-auto"),
                dbc.Button("Delete", id="delete-training-confirm", color="danger")
            ])
        ], id="delete-training-modal"),
        dcc.Store(id='store-training-id-to-delete'),
        dcc.Store(id='refresh-training-list-signal', data=0)
    ])

def create_training_form_layout(training_id=None):
    title = "Edit Training" if training_id else "Create New Training"
    training_data, questions_data = {}, [{} for _ in range(10)]

    if training_id:
        company_id_filter = current_user.company_id if current_user.role == 'admin' else None
        training_data, questions_data = db_training.get_training_with_questions(training_id, company_id_filter)
        if not training_data:
            return html.Div("Training not found or access denied.", className="message-error")
        while len(questions_data) < 10:
            questions_data.append({})

    all_companies = db_users.get_all_companies() if current_user.role == 'super_admin' else []
    company_options = [{'label': c['name'], 'value': c['id']} for c in all_companies]
    company_dropdown_component = html.Div([
        dbc.Label("Assign to Company", html_for="training-company-dropdown", className="form-label fw-bold"),
        dcc.Dropdown(
            id="training-company-dropdown",
            options=company_options,
            placeholder="Select a company...",
            className="mb-3",
            value=training_data.get('company_id')
        )
    ], style={'display': 'block' if current_user.role == 'super_admin' else 'none'})

    question_blocks = []
    for i in range(1, 11):
        q_data = questions_data[i-1] if i <= len(questions_data) else {}
        question_blocks.append(
            dbc.Card(body=True, className="mb-4 shadow-sm", children=[
                html.H5(f"Question {i}"),
                dbc.Textarea(
                    id={'type': 'q-text', 'index': i},
                    value=q_data.get('question_text', ''),
                    placeholder=f"Enter the text for question {i}...",
                    rows=2,
                    className="mb-3"
                ),
                html.Hr(),
                dbc.Label("Answer Options & Correct Choice", className="fw-bold mt-2"),
                dbc.RadioItems(
                    id={'type': 'q-correct', 'index': i},
                    options=[
                        {'label': 'A', 'value': 1}, {'label': 'B', 'value': 2},
                        {'label': 'C', 'value': 3}, {'label': 'D', 'value': 4},
                    ],
                    value=q_data.get('correct_answer', 1),
                    inline=True,
                    className="mb-3"
                ),
                dbc.Input(id={'type': 'q-opt1', 'index': i}, value=q_data.get('option_1', ''), placeholder="Answer Option A", className="mb-2"),
                dbc.Input(id={'type': 'q-opt2', 'index': i}, value=q_data.get('option_2', ''), placeholder="Answer Option B", className="mb-2"),
                dbc.Input(id={'type': 'q-opt3', 'index': i}, value=q_data.get('option_3', ''), placeholder="Answer Option C", className="mb-2"),
                dbc.Input(id={'type': 'q-opt4', 'index': i}, value=q_data.get('option_4', ''), placeholder="Answer Option D"),
            ])
        )

    return html.Div([
        html.H1(title),
        dcc.Store(id='editing-training-id', data=training_id),
        dbc.Form([
            dbc.Label("Training Name", html_for="training-name", className="form-label fw-bold"),
            dbc.Input(id="training-name", type="text", value=training_data.get('name', ''), className="mb-3", required=True),
            dbc.Label("Description", html_for="training-description", className="form-label fw-bold"),
            dbc.Textarea(id="training-description", value=training_data.get('description', ''), className="mb-3"),
            company_dropdown_component,
            dbc.Label("Video Link (e.g., YouTube, Vimeo)", html_for="training-video-link", className="form-label fw-bold"),
            dbc.Input(id="training-video-link", type="url", value=training_data.get('video_link', ''), placeholder="https://...", className="mb-4"),
            html.H3("Quiz Questions", className="mt-4 mb-3"),
            *question_blocks,
            dbc.Button("Save Training", id="save-training-button", color="success", size="lg", className="mt-3 w-100")
        ]),
        html.Div(id="training-form-status")
    ])

def create_training_results_layout(training_id):
    company_id_filter = current_user.company_id if current_user.role == 'admin' else None
    training_data, _ = db_training.get_training_with_questions(training_id, company_id_filter)
    if not training_data:
        return html.Div("Training not found or access denied.")

    results = db_training.get_training_results_summary(training_id, company_id_filter)
    
    table_rows = []
    if not results:
        table_rows.append(html.Tr(html.Td("No users have attempted this training yet.", colSpan=4, className="text-center")))
    else:
        base_path = get_base_path()
        for res in results:
            user_display_name = res.get('full_name') or res['email']
            user_link = dcc.Link(user_display_name, href=f"{base_path}/results/{training_id}/user/{res['user_id']}")
            row = html.Tr([
                html.Td(user_link),
                html.Td(f"{res['best_score']:.0f}%"),
                html.Td(res['attempt_count']),
                html.Td(res['last_attempt_date'].strftime('%d-%b-%Y %H:%M')),
            ])
            table_rows.append(row)

    return html.Div([
        html.H1(f"Results for: {training_data['name']}"),
        html.P("Click on a user's name to see their detailed attempt history."),
        dbc.Table([
            html.Thead(html.Tr([html.Th("User"), html.Th("Best Score"), html.Th("Attempts"), html.Th("Last Attempt")])),
            html.Tbody(table_rows)
        ], bordered=True, striped=True, hover=True)
    ])

def create_user_attempts_layout(training_id, user_id):
    target_user = db_users.get_user_by_id(user_id)
    if current_user.role == 'admin' and (not target_user or target_user['company_id'] != current_user.company_id):
        return create_access_denied_page(message="User not in your company.")

    training_data, _ = db_training.get_training_with_questions(training_id)
    if not training_data:
        return html.Div("Training not found.")

    data = db_training.get_user_training_details_and_stats(user_id, training_id)
    
    user_display_name = target_user.get('full_name') or target_user['email']
    if not data or not data['attempts']:
        return html.Div([
            html.H1(f"Attempt History for {user_display_name}"),
            html.H3(f"Training: {training_data['name']}", className="text-muted"),
            html.Hr(),
            html.P("This user has not made any attempts for this training yet.", className="text-center mt-4")
        ])

    attempts_data_for_table = [{'attempt_date': a['attempt_date'].strftime('%d-%b-%Y %H:%M:%S'), 'score': f"{a['score']:.0f}"} for a in data['attempts']]
    questions_data_for_table = [{'question_text': q['question_text'], 'correct_answer_text': q['correct_answer_text'], 'pass_rate': f"{q['pass_rate']:.0f}%" if q['pass_rate'] is not None else "N/A"} for q in data['question_stats']]
    table_style_header = {'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
    table_style_cell = {'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Inter, sans-serif'}

    return html.Div([
        html.H1(f"Attempt History for {user_display_name}"),
        html.H3(f"Training: {training_data['name']}", className="text-muted"),
        html.Hr(),
        html.H4("Attempt History", className="mt-4"),
        dash_table.DataTable(
            id='attempts-table',
            columns=[{'name': 'Attempt Date & Time', 'id': 'attempt_date'}, {'name': 'Score (%)', 'id': 'score'}],
            data=attempts_data_for_table, style_header=table_style_header, style_cell=table_style_cell,
            sort_action="native", page_size=10, style_table={'overflowX': 'auto'}
        ),
        html.Hr(style={'marginTop': '40px'}),
        html.H4("Question Performance Summary", className="mt-4"),
        html.P("Pass rate for this user across all their attempts.", className="text-muted"),
        dash_table.DataTable(
            id='question-stats-table',
            columns=[
                {'name': 'Question', 'id': 'question_text'},
                {'name': 'Correct Answer', 'id': 'correct_answer_text'},
                {'name': 'User Pass Rate', 'id': 'pass_rate'},
            ],
            data=questions_data_for_table, style_header=table_style_header, style_cell=table_style_cell,
            style_cell_conditional=[
                {'if': {'column_id': 'question_text'}, 'width': '60%'},
                {'if': {'column_id': 'correct_answer_text'}, 'width': '25%'},
                {'if': {'column_id': 'pass_rate'}, 'textAlign': 'center'},
            ],
            style_table={'overflowX': 'auto'}
        ),
    ])

def register_callbacks(app):
    """Registers callbacks for the training management feature."""

    @app.callback(
        Output('training-table-body', 'children'),
        [Input('refresh-training-list-signal', 'data'),
         Input('training-search-input', 'value'),
         Input('training-sort-dropdown', 'value')],
        [State('url', 'pathname')]
    )
    def refresh_training_list(refresh_signal, search_term, sort_by, pathname):
        base_path = get_base_path()
        if pathname != base_path:
            raise PreventUpdate
        
        if not (current_user.is_authenticated and current_user.role in ['admin', 'super_admin']):
            raise PreventUpdate

        company_id_filter = current_user.company_id if current_user.role == 'admin' else None
        trainings = db_training.get_trainings(company_id=company_id_filter, search_term=search_term, sort_by=sort_by)

        if not trainings:
            return [html.Tr(html.Td("No training modules found.", colSpan=4, className="text-center"))]
        
        training_rows = []
        for t in trainings:
            row = html.Tr([
                html.Td(dcc.Link(t['name'], href=f"{base_path}/results/{t['id']}")),
                html.Td(t.get('company_name', 'N/A')) if current_user.role == 'super_admin' else html.Td(t['description']),
                html.Td(t['created_at'].strftime('%d-%m-%Y')),
                html.Td(html.Div([
                    dcc.Link(dbc.Button("Edit", color="secondary", size="sm"), href=f"{base_path}/edit/{t['id']}"),
                    dbc.Button("Delete", color="danger", size="sm", id={'type': 'delete-training', 'index': t['id']}, n_clicks=0)
                ], style={'display': 'flex', 'gap': '5px'}))
            ])
            training_rows.append(row)
        return training_rows

    @app.callback(
        Output("delete-training-modal", "is_open"),
        Output("store-training-id-to-delete", "data"),
        Input({'type': 'delete-training', 'index': ALL}, 'n_clicks'),
        Input("delete-training-cancel", "n_clicks"),
        Input("delete-training-confirm", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_delete_modal(delete_clicks, cancel_click, confirm_click):
        ctx = dash.callback_context
        triggered_id = ctx.triggered_id
        if isinstance(triggered_id, dict) and triggered_id.get('type') == 'delete-training':
            if not any(n and n > 0 for n in delete_clicks): raise PreventUpdate
            return True, triggered_id['index']
        return False, no_update

    @app.callback(
        Output("training-action-status", "children"),
        Output('refresh-training-list-signal', 'data'),
        Input("delete-training-confirm", "n_clicks"),
        State("store-training-id-to-delete", "data"),
        State('refresh-training-list-signal', 'data'),
        prevent_initial_call=True
    )
    def handle_delete_training(n_clicks, training_id, refresh_count):
        if not (n_clicks and training_id): raise PreventUpdate
        try:
            company_id_filter = current_user.company_id if current_user.role == 'admin' else None
            db_training.delete_training(training_id, company_id=company_id_filter)
            return dbc.Alert(f"Training ID #{training_id} has been deleted.", color="success", dismissable=True), refresh_count + 1
        except Exception as e:
            return dbc.Alert(f"Error deleting training: {e}", color="danger", dismissable=True), no_update

    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Output("training-form-status", "children"),
        Input("save-training-button", "n_clicks"),
        [
            State('editing-training-id', 'data'), State("training-name", "value"),
            State("training-description", "value"), State("training-company-dropdown", "value"),
            State("training-video-link", "value"), State({'type': 'q-text', 'index': ALL}, 'value'),
            State({'type': 'q-opt1', 'index': ALL}, 'value'), State({'type': 'q-opt2', 'index': ALL}, 'value'),
            State({'type': 'q-opt3', 'index': ALL}, 'value'), State({'type': 'q-opt4', 'index': ALL}, 'value'),
            State({'type': 'q-correct', 'index': ALL}, 'value'),
        ],
        prevent_initial_call=True
    )
    def handle_save_training(n_clicks, training_id, name, desc, selected_company_id, video, q_texts, q_opt1s, q_opt2s, q_opt3s, q_opt4s, q_corrects):
        if not name:
            return no_update, dbc.Alert("Training Name is a required field.", color="warning")

        company_id_to_save = selected_company_id if current_user.role == 'super_admin' else current_user.company_id
        if not company_id_to_save:
            error_msg = "Super Admin must select a company." if current_user.role == 'super_admin' else "Error: Your admin account is not associated with a company."
            return no_update, dbc.Alert(error_msg, color="danger")

        training_data = {'name': name, 'description': desc or '', 'video_link': video or ''}
        questions_data = []
        for i in range(10):
            if q_texts[i]:
                questions_data.append({
                    'order': i + 1, 'text': q_texts[i],
                    'opt1': q_opt1s[i] or '', 'opt2': q_opt2s[i] or '',
                    'opt3': q_opt3s[i] or '', 'opt4': q_opt4s[i] or '',
                    'correct': q_corrects[i]
                })
        
        try:
            # IMPLEMENTED FIX: Handle both create and edit (update) cases
            if not training_id:
                db_training.create_training_with_questions(training_data, questions_data, company_id_to_save, current_user.id)
            else:
                db_training.update_training_with_questions(training_id, training_data, questions_data)

            return get_base_path(), no_update
        except Exception as e:
            return no_update, dbc.Alert(f"An error occurred: {e}", color="danger")