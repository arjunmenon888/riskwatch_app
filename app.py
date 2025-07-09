# app.py

import os
import dash
from dash import dcc, html, Input, Output, State
from flask import Flask, redirect, send_from_directory  # <-- Import send_from_directory
from flask_login import LoginManager, logout_user, current_user
import dash_bootstrap_components as dbc

# App Modules
import routes
import design_components as dc
import db_pool
import db_init
import user_management
import db_ai_files  # For AI feature
from models import User

# Page/Feature-specific Modules
import observation_app
import landing_page
import auth_app
import admin_app
import admin_report_view_app
import super_admin_app
import training_app
import user_training_app
import lost_and_found_app
import profile_app
import gate_pass_app
import ask_ai_app
import social_app # NEW: Import social_app

# --- App Initialization ---
server = Flask(__name__)
server.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "a_very_secure_default_secret_key_for_development_only"
)

# --- NEW: PWA Configuration ---
# Override Dash's default HTML template to add PWA tags
app_index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#003366">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <script>
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('/sw.js').then(function(registration) {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                    }, function(err) {
                        console.log('ServiceWorker registration failed: ', err);
                    });
                });
            }
        </script>
    </body>
</html>
"""

# The 'assets_folder' is 'assets' by default. Dash will automatically look for 'favicon.ico' here.
app = dash.Dash(
    __name__,
    server=server,
    title="RiskWatch",
    update_title=None,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    index_string=app_index_string,  # <-- Add the custom index_string here
)


# --- NEW: Add routes to serve the service worker and manifest at the root level ---
@server.route("/sw.js")
def serve_sw():
    return send_from_directory(app.config.assets_folder, "sw.js")


@server.route("/manifest.json")
def serve_manifest():
    return send_from_directory(app.config.assets_folder, "manifest.json")


@server.route("/offline.html")
def serve_offline():
    return send_from_directory(app.config.assets_folder, "offline.html")


# --- Database and Login Manager Setup ---
with server.app_context():
    db_pool.init_db_pool()
    db_init.init_db()

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


@login_manager.user_loader
def load_user(user_id):
    user_data = user_management.get_user_by_id(user_id)
    if user_data:
        return User(user_id)
    return None


@server.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


# --- App Layout ---
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False), 
        html.Div(id="page-content"),
        # --- FIX: The dummy Div for the clientside callback has been removed from here ---
    ]
)

# --- Register All Callbacks from Modules ---
observation_app.register_callbacks(app)
landing_page.register_callbacks(app)
auth_app.register_callbacks(app)
admin_app.register_callbacks(app)
super_admin_app.register_callbacks(app)
training_app.register_callbacks(app)
user_training_app.register_callbacks(app)
admin_report_view_app.register_callbacks(app)
lost_and_found_app.register_callbacks(app)
profile_app.register_callbacks(app)
gate_pass_app.register_callbacks(app)
ask_ai_app.register_callbacks(app)
social_app.register_callbacks(app) # NEW: Register social_app callbacks


# --- Main Page Routing Callback ---
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    # Handle public static pages
    static_info_pages = {
        "/about": landing_page.create_about_page,
        "/privacy": landing_page.create_privacy_page,
        "/terms": landing_page.create_terms_page,
        "/coming-soon": landing_page.create_coming_soon_page,
    }
    if pathname in static_info_pages:
        content = static_info_pages[pathname]()
        if current_user.is_authenticated:
            return dc.create_main_layout(content)
        else:
            return landing_page.create_public_layout(content)

    # Handle unauthenticated users
    if not current_user.is_authenticated:
        if pathname in ["/login", "/register", "/reset-password"]:
            if pathname == "/login":
                return auth_app.build_login_layout()
            if pathname == "/register":
                return auth_app.build_register_layout()
            if pathname == "/reset-password":
                return auth_app.build_reset_password_layout()
        # For any other page, if not logged in, show the public landing page.
        return landing_page.build_full_public_landing_page()

    # --- Authenticated User Logic ---

    # Force profile completion if necessary
    is_profile_complete = bool(
        current_user.full_name
        and current_user.job_title
        and current_user.department
        and current_user.employee_id
    )
    if not is_profile_complete and pathname != "/complete-profile":
        return dcc.Location(pathname="/complete-profile", id="redirect-to-profile")

    # Handle the root URL ('/') for authenticated users
    if pathname == "/":
        return dc.create_main_layout(landing_page.create_hero_content())

    # For all other authenticated paths, call the central router
    page_content = routes.render_page_content(pathname)
    return dc.create_main_layout(page_content)


# --- Navbar Toggler Callback ---
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# --- Main Entry Point ---
if __name__ == "__main__":
    app.run(debug=True)