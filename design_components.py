# design_components.py

from dash import dcc, html
import dash_bootstrap_components as dbc
from flask_login import current_user
import base64
import constants

# =============================================================================
# 1. UNIVERSAL COMPONENTS
# =============================================================================

def create_user_profile_dropdown():
    """Creates the user profile picture and dropdown menu for the navbar."""
    
    default_photo = '/assets/profile icon.png'
    
    if current_user.is_authenticated:
        photo_b64 = current_user.get_profile_photo_b64()
        photo_src = f"data:image/jpeg;base64,{photo_b64}" if photo_b64 else default_photo
    else:
        # Should not happen on authenticated pages, but as a fallback
        photo_src = default_photo

    # Use just the circular image as the clickable label for a cleaner look
    profile_label = html.Img(
        src=photo_src, 
        className="rounded-circle", 
        height="40px", 
        width="40px", 
        style={'objectFit': 'cover', 'cursor': 'pointer'}
    )

    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem(f"Signed in as {current_user.email}", header=True),
            dbc.DropdownMenuItem("Profile", href="/complete-profile"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Logout", href="/logout", external_link=True),
        ],
        nav=True,
        in_navbar=True,
        label=profile_label,
        align_end=True,
        toggle_style={'background': 'none', 'border': 'none'}
    )

def create_universal_navbar():
    """
    Creates a single, responsive navbar that adapts to the current user's role and permissions.
    """
    if not current_user.is_authenticated:
        return None

    # Build the list of main navigation items
    nav_items = []
    # --- NEW: Add Social Tab ---
    nav_items.append(dbc.NavItem(dbc.NavLink("Social", href="/social")))
    nav_items.append(dbc.NavItem(dbc.NavLink("Coming Soon", href="/coming-soon")))
    nav_items.append(dbc.NavItem(dbc.NavLink("About", href="/about")))

    # Dynamically build the services dropdown based on user permissions
    service_menu_items = []
    if current_user.has_permission(constants.PERM_OBSERVATION):
        service_menu_items.append(dbc.DropdownMenuItem("Observation", href="/observation"))
    if current_user.has_permission(constants.PERM_TRAINING):
        service_menu_items.append(dbc.DropdownMenuItem("Training", href="/training"))
    if current_user.has_permission(constants.PERM_LF):
        service_menu_items.append(dbc.DropdownMenuItem("Lost & Found", href="/lost-and-found"))
    if current_user.has_permission(constants.PERM_GATE_PASS):
        service_menu_items.append(dbc.DropdownMenuItem("Gate Pass", href="/gate-pass"))
    
    if service_menu_items and current_user.has_permission(constants.PERM_ASK_AI):
        service_menu_items.append(dbc.DropdownMenuItem(divider=True))
        service_menu_items.append(dbc.DropdownMenuItem("Ask Me (AI)", href="/ask-ai"))
    elif not service_menu_items and current_user.has_permission(constants.PERM_ASK_AI):
         service_menu_items.append(dbc.DropdownMenuItem("Ask Me (AI)", href="/ask-ai"))

    if service_menu_items:
        nav_items.append(dbc.DropdownMenu(
            label="Services", children=service_menu_items, nav=True, in_navbar=True
        ))
    
    # --- CORRECTED: Role-specific navigation links ---
    if current_user.role == 'admin':
        # The User object now reliably has the 'can_create_users' attribute from models.py
        if current_user.can_create_users:
            nav_items.append(dbc.NavItem(dbc.NavLink("Admin Panel", href="/admin")))
        
        # The "Training Mgmt" link depends on a separate service permission.
        if current_user.has_permission(constants.PERM_TRAINING):
             nav_items.append(dbc.NavItem(dbc.NavLink("Training Mgmt", href="/admin/training")))
             
    elif current_user.role == 'super_admin':
        nav_items.append(dbc.NavItem(dbc.NavLink("Super Admin Panel", href="/super-admin")))
        # Super admin can always manage training
        nav_items.append(dbc.NavItem(dbc.NavLink("Training Mgmt", href="/super-admin/training")))

    nav_items.append(create_user_profile_dropdown())

    right_aligned_nav = dbc.Nav(
        nav_items,
        className="ms-auto d-flex align-items-center",
        navbar=True
    )
    
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [dbc.Col(html.Img(src='/assets/riskwatch-logo.png', height="40px"))],
                        align="center", className="g-0"
                    ),
                    href="/", style={"textDecoration": "none"}
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    right_aligned_nav,
                    id="navbar-collapse",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="light", dark=False, className="mb-4", sticky="top",
    )
    return navbar


def create_footer():
    """Creates the standard application footer."""
    return html.Footer(className="app-footer mt-auto py-3", children=[
        html.P("Risk Watch © 2025 | Empowering professionals to track risks, improve safety, and ensure compliance."),
        html.Div(className="footer-links", children=[
            dcc.Link("Privacy Policy", href="/privacy"),
            html.Span(" | ", className="mx-2"),
            dcc.Link("Terms of Use", href="/terms")
        ])
    ])

def create_main_layout(page_content):
    """
    A wrapper for all authenticated pages. Provides the universal navbar,
    a container for the page's content, and the universal footer.
    """
    return html.Div([
        create_universal_navbar(),
        dbc.Container(page_content, fluid=False, className="py-4 flex-grow-1"),
        create_footer()
    ], className="d-flex flex-column min-vh-100")

# =============================================================================
# 2. UTILITY & REUSABLE COMPONENTS
# =============================================================================

def create_access_denied_page(message="You do not have permission to view this page."):
    """Creates a generic access denied message page."""
    return html.Div(style={'textAlign': 'center', 'padding': '50px'}, children=[
        html.H1("Access Denied", style={'color': '#dc3545'}),
        html.P(f"{message} Please contact your administrator if you believe this is an error."),
        dcc.Link("Go to Homepage", href="/", className="btn btn-primary mt-3")
    ])

def create_observation_card(obs_data, is_admin_view=False):
    """Creates a display card for a single Observation record."""
    risk = obs_data.get('risk_rating', 0)
    risk_class = 'risk-low'
    if 5 <= risk <= 9: risk_class = 'risk-medium'
    elif 10 <= risk <= 15: risk_class = 'risk-high'
    elif risk >= 16: risk_class = 'risk-critical'
    delete_button_text = 'Delete (Admin)' if is_admin_view else 'Delete'
    delete_button_id = {'type': 'admin-delete-obs-button', 'index': obs_data['id']} if is_admin_view else {'type': 'delete-button', 'index': obs_data['id']}
    return html.Div(className="obs-card", children=[
        html.Div(className="card-body", children=[
            html.Div(className="card-main", children=[
                html.H3(f"Obs #{obs_data['display_id']}: {obs_data['area_equipment']}"),
                html.P([html.B("Date: "), obs_data['date_str']]),
                html.P([html.B("Impact: "), obs_data['impact']]),
                html.P([html.B("Description: "), obs_data['description']]),
                html.P([html.B("Corrective Action: "), obs_data['corrective_action']]),
                html.P([html.B("Deadline: "), f"{obs_data.get('deadline', 'N/A')}"])
            ]),
            html.Div(className="card-sidebar", children=[
                html.Div(className="risk-box", children=[
                    html.P("Risk Rating", className="risk-title"),
                    html.P(risk, className=f"risk-value {risk_class}")
                ]),
                html.Img(src=f"data:image/png;base64,{obs_data['photo_b64']}" if obs_data['photo_b64'] else '/assets/placeholder.png', className="card-photo")
            ])
        ]),
        html.Div(className="card-footer", children=[
            html.Button(delete_button_text, id=delete_button_id, n_clicks=0, className='card-delete-button')
        ])
    ])

def create_lost_and_found_card(item_data):
    """Creates a display card for a single Lost & Found item."""
    is_admin = current_user.role in ['admin', 'super_admin']
    
    photo_b64 = None
    if item_data.get('photo_bytes'):
        photo_b64 = base64.b64encode(item_data['photo_bytes']).decode('utf-8')

    status = item_data.get('status', 'Unclaimed')
    
    status_color_map = {
        "Unclaimed": "warning",
        "Claimed": "success",
        "Handed over to police": "info",
        "Disposed": "secondary"
    }
    status_color = status_color_map.get(status, "light")

    action_buttons = [
        dbc.Button("Edit", id={'type': 'lf-edit-btn', 'index': item_data['id']}, size="sm", color="secondary", className="me-2")
    ]
    if is_admin:
        action_buttons.append(
            dbc.Button("Delete", id={'type': 'lf-delete-btn', 'index': item_data['id']}, size="sm", color="danger")
        )

    return html.Div(className="obs-card", children=[
        html.Div(className="card-body", children=[
            html.Div(className="card-main", children=[
                html.H3(f"Ticket #{item_data['ticket_no']}: {item_data['item_description']}"),
                html.P([html.B("Date Found: "), item_data['entry_date'].strftime('%d-%b-%Y'), " at ", item_data.get('entry_time', 'N/A')]),
                html.P([html.B("Location: "), item_data['location_found']]),
                html.P([html.B("Found By: "), item_data['found_by'], " (", item_data.get('department', 'N/A'), ")"]),
                html.P([html.B("Stored In: "), item_data['stored_in']]),
                html.Hr(),
                html.P([html.B("Claimer/Disposer: "), item_data.get('claimer_receiver_disposer') or "N/A"]),
                html.P([html.B("Contact: "), item_data.get('receiver_contact_no') or "N/A"]),
                html.P([html.B("Handed Over By: "), item_data.get('handed_over_by') or "N/A"]),
                html.P([html.B("Remarks: "), item_data.get('remarks') or "N/A"]),
            ]),
            html.Div(className="card-sidebar", children=[
                dbc.Badge(status, color=status_color, className="w-100 mb-3 p-2"),
                html.Img(src=f"data:image/png;base64,{photo_b64}" if photo_b64 else '/assets/placeholder.png', className="card-photo")
            ])
        ]),
        html.Div(className="card-footer", children=action_buttons)
    ])

def create_gate_pass_card(item_data):
    """Creates a display card for a single Gate Pass record."""
    is_admin = current_user.role in ['admin', 'super_admin']

    def get_b64_src(field_name):
        photo_bytes = item_data.get(field_name)
        if photo_bytes:
            return f"data:image/png;base64,{base64.b64encode(photo_bytes).decode('utf-8')}"
        return '/assets/placeholder.png'
    
    status = item_data.get('status', 'non returned')
    status_color = "success" if status == "returned" else "danger"
    
    action_buttons = [
        dbc.Button("Update Status", id={'type': 'gp-edit-btn', 'index': item_data['id']}, size="sm", color="secondary", className="me-2")
    ]
    if is_admin:
        action_buttons.append(
            dbc.Button("Delete", id={'type': 'gp-delete-btn', 'index': item_data['id']}, size="sm", color="danger")
        )

    return html.Div(className="obs-card", children=[
        html.Div(className="card-body", children=[
            html.Div(className="card-main", children=[
                html.H3(f"Gate Pass #{item_data['gate_pass_number']}"),
                dbc.Badge(status.title(), color=status_color, className="mb-3 p-2"),
                html.P([html.B("Item Description: "), item_data['item_description']]),
                html.P([html.B("Date Issued: "), item_data['date_issued'].strftime('%d-%b-%Y')]),
                html.P([html.B("Issued To: "), item_data.get('issued_to', 'N/A'), " (", item_data.get('company', 'N/A'), ")"]),
                html.P([html.B("Purpose: "), item_data.get('purpose_of_removal', 'N/A')]),
                html.P([html.B("Authorized By: "), item_data.get('authorized_by', 'N/A'), " (", item_data.get('authorizing_department', 'N/A'), ")"]),
                html.Hr(),
                html.P([html.B("Return Status: "), status.title()]),
                html.P([html.B("Received By: "), item_data.get('received_by') or "N/A"]),
                html.P([html.B("Returned On: "), item_data['returned_date'].strftime('%d-%b-%Y') if item_data.get('returned_date') else "N/A"]),
                html.P([html.B("Remarks: "), item_data.get('remarks') or "N/A"]),
            ]),
            html.Div(className="card-sidebar", children=[
                html.Div([
                    html.P("Picture (Out)", className="text-center text-muted fw-bold"),
                    html.Img(src=get_b64_src('item_picture_taken_out_bytes'), className="card-photo mb-3")
                ]),
                html.Div([
                    html.P("Picture (Returned)", className="text-center text-muted fw-bold"),
                    html.Img(src=get_b64_src('item_picture_returned_back_bytes'), className="card-photo")
                ]),
            ])
        ]),
        html.Div(className="card-footer", children=action_buttons)
    ])