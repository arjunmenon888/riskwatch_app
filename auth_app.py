# auth_app.py

import re
from dash import dcc, html, Input, Output, State, no_update
from werkzeug.security import check_password_hash
from flask_login import login_user, current_user

import user_management
from models import User

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def build_login_layout():
    """Builds the login page layout."""
    return html.Div(className="auth-page-wrapper", children=[
        html.Div(className="auth-form-container", children=[
            dcc.Link(href="/", children=[html.Img(src='/assets/riskwatch-logo.png', className="auth-logo")]),
            html.H1("Log In to Your Account"),
            html.P("Enter your credentials to access your dashboard."),
            
            html.Div(id='login-message', className='auth-message-error', style={'display': 'none'}),
            
            html.Div([
                html.Div(className="form-group", children=[
                    html.Label("Email", htmlFor="login-email"),
                    dcc.Input(id="login-email", type="email", n_submit=0)
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Password", htmlFor="login-password"),
                    dcc.Input(id="login-password", type="password", n_submit=0)
                ]),
                html.Div(dcc.Link("Forgot Password?", href="/reset-password"), style={'textAlign': 'right', 'fontSize': '14px', 'marginBottom': '15px'}),
                html.Button("Log In", id="login-button", n_clicks=0, className="auth-submit-button"),
            ], id='login-form'),
            html.Div(className="auth-switch-link", children=["Don't have an account? ", dcc.Link("Register here", href="/register")])
        ])
    ])

def build_register_layout():
    """Builds the registration page layout with a company dropdown."""
    # Fetch existing companies to populate the dropdown.
    try:
        companies = user_management.get_all_companies()
        company_options = [{'label': c['name'], 'value': c['name']} for c in companies]
    except Exception as e:
        # Fallback in case of DB connection error on page load.
        print(f"Error fetching companies for registration form: {e}")
        company_options = []
        # Optionally, display an error to the user in the layout itself.

    return html.Div(className="auth-page-wrapper", children=[
        html.Div(className="auth-form-container", children=[
            dcc.Link(href="/", children=[html.Img(src='/assets/riskwatch-logo.png', className="auth-logo")]),
            html.H1("Create a New Account"),
            html.P("Join RiskWatch to start managing safety observations."),
            html.Div(id='register-message', className='auth-message-error', style={'display': 'none'}),
            html.Div([
                # Company input is now a dropdown of existing companies.
                html.Div(className="form-group", children=[
                    html.Label("Select Your Company", htmlFor="register-company"), 
                    dcc.Dropdown(
                        id="register-company", 
                        options=company_options,
                        placeholder="Select from existing companies...",
                    )
                ]),
                html.Div(className="form-group", children=[html.Label("Email Address", htmlFor="register-email"), dcc.Input(id="register-email", type="email", n_submit=0)]),
                html.Div(className="form-group", children=[html.Label("Password", htmlFor="register-password"), dcc.Input(id="register-password", type="password", minLength=8, n_submit=0)]),
                html.Div(className="form-group", children=[html.Label("Confirm Password", htmlFor="register-confirm-password"), dcc.Input(id="register-confirm-password", type="password", n_submit=0)]),
                html.Button("Register", id="register-button", n_clicks=0, className="auth-submit-button"),
            ], id='register-form'),
            html.Div(className="auth-switch-link", children=["Already have an account? ", dcc.Link("Log in", href="/login")])
        ])
    ])

def build_reset_password_layout(message="", success=False):
    """Layout for the user to set a new password if they have been flagged by an admin."""
    message_class = 'auth-message-success' if success else 'auth-message-error'
    return html.Div(className="auth-page-wrapper", children=[
        html.Div(className="auth-form-container", children=[
            html.Img(src='/assets/riskwatch-logo.png', className="auth-logo"),
            html.H1("Reset Your Password"),
            html.P("Enter your email and new password. This will only work if an admin has initiated a reset for your account."),
            html.Div(message, id='reset-password-message', className=message_class),
            html.Div(className="form-group", children=[html.Label("Your Email Address"), dcc.Input(id="reset-email", type="email")]),
            html.Div(className="form-group", children=[html.Label("New Password"), dcc.Input(id="reset-new-password", type="password", minLength=8)]),
            html.Div(className="form-group", children=[html.Label("Confirm New Password"), dcc.Input(id="reset-confirm-password", type="password")]),
            html.Button("Set New Password", id="set-new-password-button", className="auth-submit-button"),
            html.Div(className="auth-switch-link", children=["Remembered your password? ", dcc.Link("Log In", href="/login")])
        ])
    ])


def register_callbacks(app):
    @app.callback(
        Output('login-message', 'children', allow_duplicate=True),
        Output('login-message', 'className', allow_duplicate=True),
        Output('login-message', 'style', allow_duplicate=True),
        Input('url', 'search'),
        prevent_initial_call=True
    )
    def display_url_message(search):
        if search:
            query_params = {q.split('=')[0]: q.split('=')[1] for q in search.strip('?').split('&') if '=' in q}
            message = query_params.get('message', '').replace('%20', ' ')
            if message:
                return message, 'auth-message-success', {'display': 'block'}
        return no_update, no_update, no_update


    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Output('login-message', 'children', allow_duplicate=True),
        Output('login-message', 'className', allow_duplicate=True),
        Output('login-message', 'style', allow_duplicate=True),
        Input('login-button', 'n_clicks'),
        [State('login-email', 'value'), State('login-password', 'value')],
        prevent_initial_call=True
    )
    def login_user_callback(n_clicks, email, password):
        error_style = {'display': 'block'}
        no_error_style = {'display': 'none'}
        error_class = 'auth-message-error'

        if not email or not password:
            return no_update, "Please enter both email and password.", error_class, error_style

        user_data = user_management.get_user_by_email(email)
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            # Password is correct. Now, check the reset flag.
            if user_data.get('force_reset'):
                # The user must reset their password. Redirect them.
                # They are not logged in yet.
                return '/reset-password', no_update, no_update, no_error_style
            else:
                # Normal login. The main app router will handle profile completion.
                user_obj = User(user_data['id'])
                login_user(user_obj)
                return '/', no_update, no_update, no_error_style
        else:
            # User not found or password incorrect.
            return no_update, "Invalid email or password.", error_class, error_style

    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Output('register-message', 'children'),
        Output('register-message', 'style'),
        Input('register-button', 'n_clicks'),
        [State('register-company', 'value'), 
         State('register-email', 'value'), 
         State('register-password', 'value'), 
         State('register-confirm-password', 'value')],
        prevent_initial_call=True
    )
    def register_user_callback(n_clicks, company_name, email, password, confirm_password):
        error_style = {'display': 'block'}
        no_error_style = {'display': 'none'}
        
        if not all([company_name, email, password, confirm_password]): 
            return no_update, "Please fill in all fields, including selecting a company.", error_style
        if not re.match(EMAIL_REGEX, email): 
            return no_update, "Please enter a valid email address.", error_style
        if password != confirm_password: 
            return no_update, "Passwords do not match.", error_style
        if len(password) < 8: 
            return no_update, "Password must be at least 8 characters long.", error_style
        if user_management.get_user_by_email(email): 
            return no_update, "This email address is already registered.", error_style
        
        try:
            # The backend logic in user_management.py now prevents users from
            # creating new companies, so this call is safe.
            user_management.create_user(email, password, role='user', company_name=company_name)
            user_data = user_management.get_user_by_email(email)
            user_obj = User(user_data['id'])
            login_user(user_obj)
            return '/', '', no_error_style
        except ValueError as e: 
            # This will catch the "Company not found" error from user_management
            return no_update, str(e), error_style
        except Exception as e: 
            return no_update, f"An unexpected error occurred: {e}", error_style

    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Output('reset-password-message', 'children'),
        Output('reset-password-message', 'className'),
        Input('set-new-password-button', 'n_clicks'),
        [State('reset-email', 'value'),
         State('reset-new-password', 'value'),
         State('reset-confirm-password', 'value')],
        prevent_initial_call=True
    )
    def handle_set_new_password(n_clicks, email, new_pass, confirm_pass):
        if not all([email, new_pass, confirm_pass]):
            return no_update, "Please fill all fields.", 'auth-message-error'

        if len(new_pass) < 8:
            return no_update, "Password must be at least 8 characters long.", 'auth-message-error'

        if new_pass != confirm_pass:
            return no_update, "Passwords do not match.", 'auth-message-error'

        try:
            # Get user data before resetting to log them in after.
            user_to_reset = user_management.get_user_by_email(email)
            if not user_to_reset:
                raise ValueError("User not found.")
            
            # This function updates the password and sets force_reset=False
            user_management.reset_password_for_flagged_user(email, new_pass)
            
            # Now, log the user in so the app can redirect to profile completion.
            user_obj = User(user_to_reset['id'])
            login_user(user_obj)

            # Redirect to the main page. The main router in app.py will check
            # for profile completion and redirect if necessary.
            return '/', no_update, no_update
        except (ValueError, PermissionError) as e:
            return no_update, str(e), 'auth-message-error'
        except Exception as e:
            print(f"ERROR in handle_set_new_password: {e}")
            return no_update, "An unexpected server error occurred.", 'auth-message-error'