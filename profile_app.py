# profile_app.py

import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from flask_login import current_user
import base64
import io

import user_management
from utils import compress_image

def create_profile_layout():
    """Layout for completing/editing a user profile."""
    # Fetch existing data to pre-fill the form
    user_data = user_management.get_user_by_id(current_user.id) or {}
    
    return html.Div([
        html.H1("Complete Your Profile"),
        html.P("Please provide the following details to continue."),
        html.Hr(className="mb-4"),
        html.Div(id='profile-update-message'),
        dbc.Row([
            dbc.Col([
                dbc.Label("Full Name (Required)"),
                dbc.Input(id="profile-full-name", value=user_data.get('full_name')),
            ], md=6),
            dbc.Col([
                dbc.Label("Job Title / Role (Required)"),
                dbc.Input(id="profile-job-title", value=user_data.get('job_title')),
            ], md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Department (Required)"),
                dbc.Input(id="profile-department", value=user_data.get('department')),
            ], md=6),
            dbc.Col([
                dbc.Label("Employee ID (Required)"),
                dbc.Input(id="profile-employee-id", value=user_data.get('employee_id')),
            ], md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Phone Number"),
                dbc.Input(id="profile-phone-number", value=user_data.get('phone_number')),
            ], md=6),
            dbc.Col([
                dbc.Label("Preferred Language"),
                dbc.Select(
                    id="profile-language",
                    options=[
                        {"label": "English", "value": "English"},
                        {"label": "Spanish", "value": "Spanish"},
                        {"label": "French", "value": "French"},
                        {"label": "Arabic", "value": "Arabic"},
                    ],
                    value=user_data.get('preferred_language', 'English')
                ),
            ], md=6),
        ], className="mb-3"),
        dbc.Row([
             dbc.Col([
                html.Label("Profile Photo (Optional)"),
                dcc.Upload(
                    id='profile-photo-upload',
                    children=html.Div(['Drag and Drop or ', html.A('Select a File')]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px',
                        'borderWidth': '1px', 'borderStyle': 'dashed',
                        'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
                    },
                    multiple=False
                ),
                html.Div(id='profile-photo-output')
             ])
        ], className="mb-4"),
        dcc.Loading(
            id="loading-profile-save",
            type="circle",
            children=[
                dbc.Button("Save Profile", id="save-profile-button", color="primary", n_clicks=0, size="lg", className="w-100")
            ]
        )
    ])

def register_callbacks(app):
    @app.callback(
        Output('profile-update-message', 'children'),
        Output('url', 'pathname', allow_duplicate=True),
        Input('save-profile-button', 'n_clicks'),
        [
            State('profile-full-name', 'value'),
            State('profile-job-title', 'value'),
            State('profile-department', 'value'),
            State('profile-employee-id', 'value'),
            State('profile-phone-number', 'value'),
            State('profile-language', 'value'),
            State('profile-photo-upload', 'contents'),
        ],
        prevent_initial_call=True
    )
    def update_profile(n_clicks, full_name, job_title, department, emp_id, phone, language, photo_contents):
        if not all([full_name, job_title, department, emp_id]):
            return dbc.Alert("Please fill in all required fields.", color="danger"), no_update

        photo_bytes = None
        if photo_contents:
            try:
                content_type, content_string = photo_contents.split(',')
                decoded_bytes = base64.b64decode(content_string)
                photo_bytes = compress_image(decoded_bytes, max_dimension=256, quality=80)
            except Exception as e:
                return dbc.Alert(f"There was an error processing the image: {e}", color="danger"), no_update
        
        profile_data = {
            "full_name": full_name,
            "job_title": job_title,
            "department": department,
            "employee_id": emp_id,
            "phone_number": phone,
            "preferred_language": language,
            "profile_photo_bytes": photo_bytes
        }

        try:
            user_management.update_user_profile(current_user.id, profile_data)
            # On success, redirect to the main dashboard
            return no_update, "/"
        except Exception as e:
            return dbc.Alert(f"An unexpected error occurred: {e}", color="danger"), no_update

    @app.callback(
        Output('profile-photo-output', 'children'),
        Input('profile-photo-upload', 'contents'),
        State('profile-photo-upload', 'filename')
    )
    def update_photo_upload_output(contents, filename):
        if contents:
            return html.Div(f"File selected: {filename}")
        # Try to show existing photo if no new one is uploaded
        elif current_user.profile_photo_bytes:
            b64_img = base64.b64encode(current_user.profile_photo_bytes).decode()
            return html.Div([
                "Current photo: ",
                html.Img(src=f"data:image/jpeg;base64,{b64_img}", height="50px")
            ])
        return html.Div("No photo selected.")