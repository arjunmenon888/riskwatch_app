# social_app.py

import dash
from dash import (
    dcc,
    html,
    Input,
    Output,
    State,
    no_update,
    ALL,
    clientside_callback,
    ctx,
)
import dash_bootstrap_components as dbc
from flask_login import current_user
from dash.exceptions import PreventUpdate
import re
import time
from datetime import date, timedelta

import user_management
import db_chat

# =============================================================================
# UI Components
# =============================================================================


def create_social_layout():
    """Creates the WhatsApp-style layout with mobile navigation."""

    # --- Sidebar (Left Column) ---
    contact_list_items = []
    
    # Add Global Discussion for all users
    contact_list_items.append(
        dcc.Link(
            dbc.ListGroupItem(
                [
                    html.I(className="fa-solid fa-globe fa-lg me-3 text-primary"),
                    html.Div(
                        [
                            html.Div("Global Discussion", className="contact-name"),
                            html.Div("All users, all companies", className="last-message"),
                        ],
                        className="flex-grow-1",
                    ),
                ],
                className="contact-item d-flex align-items-center",
            ),
            href="/social/public/global",
            style={"textDecoration": "none"},
        )
    )

    # Add company-specific public chat only for non-super-admins
    if current_user.role != "super_admin":
        contact_list_items.append(
            dcc.Link(
                dbc.ListGroupItem(
                    [
                        html.I(className="fa-solid fa-users fa-lg me-3 text-secondary"),
                        html.Div(
                            [
                                html.Div("Public Discussion", className="contact-name"),
                                html.Div(
                                    "Company-wide channel", className="last-message"
                                ),
                            ],
                            className="flex-grow-1",
                        ),
                    ],
                    className="contact-item d-flex align-items-center",
                ),
                href="/social/public",
                style={"textDecoration": "none"},
            )
        )
    
    contact_list_items.append(html.Hr(className="my-2"))
    
    # Populate the chat list with existing private conversations
    conversations = db_chat.get_conversations(current_user.id)
    for user in conversations:
        user_display = user.get("full_name") or user["email"]
        company_name_display = (
            f" ({user.get('company_name')})"
            if current_user.role == "super_admin" and user.get('company_name')
            else ""
        )
        # --- NEW: Logic to display the unread badge ---
        unread_badge = None
        if user.get('unread_count', 0) > 0:
            unread_badge = dbc.Badge(
                user['unread_count'], 
                color="warning", 
                pill=True, 
                text_color="dark", 
                className="ms-auto"
            )

        contact_list_items.append(
            dcc.Link(
                dbc.ListGroupItem(
                    [
                        html.I(className="fa-solid fa-user fa-lg me-3 text-secondary"),
                        html.Div(
                            [
                                html.Div(
                                    f"{user_display}{company_name_display}",
                                    className="contact-name",
                                ),
                                html.Div(
                                    user["job_title"] or "User",
                                    className="last-message",
                                ),
                            ],
                            className="flex-grow-1",
                        ),
                        unread_badge # Add the badge here
                    ],
                    className="contact-item d-flex align-items-center",
                ),
                href=f"/social/{user['id']}",
                style={"textDecoration": "none"},
            )
        )
    
    sidebar = dbc.Col(
        [
            html.Div(
                [
                    html.I(className="fa-solid fa-shield-halved fa-2x text-warning"),
                    html.H5("RiskWatch Chat", className="ms-3"),
                ],
                className="sidebar-header d-flex align-items-center",
            ),
            html.Div([
                dbc.InputGroup(
                    [
                        dbc.Input(id="email-search-input", placeholder="Find user by email..."),
                        dbc.Button(
                            html.Img(src="/assets/search_icon.png", style={'height': '20px'}), 
                            id="email-search-button", 
                            n_clicks=0,
                            color="light"
                        ),
                    ]
                ),
                html.Div(id="search-feedback", className="mt-2 px-2")
            ], className="p-2 border-bottom"),
            html.Div(
                dbc.ListGroup(contact_list_items, flush=True),
                id="contact-list-container",
                style={"overflow-y": "auto"},
            ),
        ],
        id="sidebar-col",
        xs=12,
        md=4,
        className="sidebar d-flex flex-column h-100 p-0",
    )

    # (Chat pane layout remains the same)
    chat_pane = dbc.Col(
        [
            html.Div(
                [
                    dcc.Link(html.I(className="fa-solid fa-arrow-left me-3"), href="/social", className="d-md-none text-secondary"),
                    html.I(id="chat-header-icon", className="fa-solid fa-users fa-2x me-2 me-md-3 text-secondary"),
                    html.Div([
                        html.Div("Select a chat", className="contact-name", id="chat-header-name"),
                        html.Div(" ", className="contact-status", id="chat-header-status"),
                    ]),
                ],
                className="chat-header d-flex align-items-center",
            ),
            html.Div(
                dcc.Loading(html.Div(id="chat-history", className="p-3"), type="circle"),
                id="chat-history-container",
                style={"overflowY": "auto", "flexGrow": 1},
            ),
            html.Div(
                [
                    dcc.Input(id="message-input", placeholder="Type a message...", className="flex-grow-1 me-2 form-control-lg", style={"border-radius": "20px"}, n_submit=0, autoComplete='off'),
                    dbc.Button("Send", id="send-button", className="send-button rounded-pill px-4", n_clicks=0),
                ],
                id="message-input-area",
                className="message-input-area d-flex",
            ),
        ],
        id="chat-pane-col",
        xs=12, md=8,
        className="chat-pane d-flex flex-column h-100 p-0",
    )

    return dbc.Container(
        [
            html.Div(id='clientside-dummy-output', style={'display': 'none'}),
            dcc.Store(id="message-sent-signal"),
            dcc.Interval(id="chat-interval", interval=2 * 1000, n_intervals=0),
            dbc.Row(
                [sidebar, chat_pane],
                className="g-0",
                style={"height": "calc(100vh - 75px)"},
            ),
        ],
        fluid=True,
        className="p-0",
        style={
            "height": "calc(100vh - 75px)",
            "max-height": "calc(100vh - 75px)",
            "overflow": "hidden",
        },
    )


# =============================================================================
# Callbacks
# =============================================================================


def register_callbacks(app):
    
    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Output('search-feedback', 'children'),
        Output('email-search-input', 'value'),
        Input('email-search-button', 'n_clicks'),
        State('email-search-input', 'value'),
        prevent_initial_call=True
    )
    def handle_email_search(n_clicks, email):
        if not email or not email.strip():
            raise PreventUpdate
        
        if email.lower() == current_user.email.lower():
            return no_update, dbc.Alert("You cannot start a chat with yourself.", color="warning", duration=3000), no_update

        found_user = user_management.get_user_by_email(email)
        
        if found_user:
            return f"/social/{found_user['id']}", None, ""
        else:
            return no_update, dbc.Alert("User not found.", color="danger", duration=3000), email


    @app.callback(
        Output("sidebar-col", "className"),
        Output("chat-pane-col", "className"),
        Input("url", "pathname"),
    )
    def update_mobile_view(pathname):
        sidebar_base_class = "sidebar d-flex flex-column h-100 p-0"
        chat_pane_base_class = "chat-pane d-flex flex-column h-100 p-0"
        is_chat_open = re.match(r"/social/(public/.+|\d+)", pathname)

        if is_chat_open:
            sidebar_class = f"{sidebar_base_class} d-none d-md-flex"
            chat_pane_class = f"{chat_pane_base_class} d-flex"
        else:
            sidebar_class = f"{sidebar_base_class} d-flex"
            chat_pane_class = f"{chat_pane_base_class} d-none d-md-flex"
        
        return sidebar_class, chat_pane_class

    @app.callback(
        Output("message-sent-signal", "data"),
        Output("message-input", "value"),
        [Input("send-button", "n_clicks"), Input("message-input", "n_submit")],
        [State("message-input", "value"), State("url", "pathname")],
        prevent_initial_call=True,
    )
    def send_and_save_message(send_clicks, enter_presses, message_text, pathname):
        if not message_text or not message_text.strip():
            return no_update, no_update

        path_parts = pathname.split("/")
        
        is_global_public = pathname == "/social/public/global"
        is_company_public = (pathname == "/social/public")
        is_private = len(path_parts) > 2 and path_parts[2].isdigit()

        if not (is_global_public or is_company_public or is_private):
            return no_update, ""

        company_id_for_message = None
        recipient_id_str = 'public' if (is_global_public or is_company_public) else path_parts[2]

        if is_global_public: company_id_for_message = None
        elif is_company_public:
            if current_user.role == 'super_admin': return no_update, "" 
            company_id_for_message = current_user.company_id
        elif is_private:
            try:
                recipient_user = user_management.get_user_by_id(int(recipient_id_str))
                if recipient_user: company_id_for_message = recipient_user.get("company_id")
            except (ValueError, TypeError): return no_update, ""
        
        db_chat.add_message(sender_id=current_user.id, recipient_id=recipient_id_str, message_text=message_text, company_id=company_id_for_message)
        return time.time(), ""

    @app.callback(
        Output("chat-history", "children"),
        Output("chat-header-name", "children"),
        Output("chat-header-status", "children"),
        Output("chat-header-icon", "className"),
        Output("message-input-area", "style"),
        Output("contact-list-container", "children"),
        Input("url", "pathname"),
        Input("chat-interval", "n_intervals"),
        Input("message-sent-signal", "data"),
    )
    def display_chat_and_refresh_list(pathname, n_intervals, sent_signal):
        no_chat_selected_outputs = (html.P("Select a chat to start messaging.", className="text-center text-muted p-5"), "No Chat Selected", " ", "fa-solid fa-comments fa-2x me-2 me-md-3 text-secondary", {"display": "none"}, no_update)

        path_parts = pathname.split("/")
        is_global_public = pathname == "/social/public/global"
        is_company_public = pathname == "/social/public"
        is_private = len(path_parts) > 2 and path_parts[2].isdigit()
        is_any_public = is_global_public or is_company_public

        if is_private:
            try:
                partner_id = int(path_parts[2])
                db_chat.mark_messages_as_read(sender_id=partner_id, recipient_id=current_user.id)
            except (ValueError, IndexError):
                pass 

        contact_list_items = []
        contact_list_items.append(dcc.Link(dbc.ListGroupItem([html.I(className="fa-solid fa-globe fa-lg me-3 text-primary"),html.Div([html.Div("Global Discussion", className="contact-name"),html.Div("All users, all companies", className="last-message")],className="flex-grow-1")],className="contact-item d-flex align-items-center"),href="/social/public/global",style={"textDecoration": "none"}))
        if current_user.role != "super_admin":
            contact_list_items.append(dcc.Link(dbc.ListGroupItem([html.I(className="fa-solid fa-users fa-lg me-3 text-secondary"),html.Div([html.Div("Public Discussion", className="contact-name"),html.Div("Company-wide channel", className="last-message")],className="flex-grow-1")],className="contact-item d-flex align-items-center"),href="/social/public",style={"textDecoration": "none"}))
        contact_list_items.append(html.Hr(className="my-2"))
        conversations = db_chat.get_conversations(current_user.id)
        for user in conversations:
            user_display, company_name_display = (user.get("full_name") or user["email"]), (f" ({user.get('company_name')})" if current_user.role == "super_admin" and user.get('company_name') else "")
            unread_badge = dbc.Badge(user['unread_count'], color="warning", pill=True, text_color="dark", className="ms-auto") if user.get('unread_count', 0) > 0 else None
            contact_list_items.append(dcc.Link(dbc.ListGroupItem([html.I(className="fa-solid fa-user fa-lg me-3 text-secondary"),html.Div([html.Div(f"{user_display}{company_name_display}",className="contact-name"),html.Div(user["job_title"] or "User",className="last-message")],className="flex-grow-1"), unread_badge],className="contact-item d-flex align-items-center"),href=f"/social/{user['id']}",style={"textDecoration": "none"}))
        refreshed_contact_list = dbc.ListGroup(contact_list_items, flush=True)

        if not (is_any_public or is_private):
            return (*no_chat_selected_outputs[:-1], refreshed_contact_list)

        messages_data, header_name, header_status, header_icon = [], "...", " ", "fa-solid fa-comments fa-2x me-2 me-md-3 text-secondary"
        
        if is_global_public:
            messages_data, header_name, header_status, header_icon = db_chat.get_global_public_messages(), "Global Discussion", "All users, all companies", "fa-solid fa-globe fa-2x me-2 me-md-3 text-primary"
        elif is_company_public:
            if current_user.role == 'super_admin': return html.P("Access restricted.", className="text-center text-danger p-5"), "Access Denied", " ", "fa-solid fa-lock fa-2x me-2 me-md-3 text-danger", {"display": "flex"}, refreshed_contact_list
            messages_data, header_name, header_status, header_icon = db_chat.get_public_messages(current_user.company_id), f"Public: {current_user.company_name}", "Company-wide channel", "fa-solid fa-users fa-2x me-2 me-md-3 text-secondary"
        elif is_private:
            try:
                room_id = int(path_parts[2])
                messages_data = db_chat.get_private_messages(current_user.id, room_id)
                partner = user_management.get_user_by_id(room_id)
                if partner: header_name, header_status, header_icon = partner.get("full_name") or partner.get("email"), partner.get("job_title") or "User", "fa-solid fa-user fa-2x me-2 me-md-3 text-secondary"
            except (ValueError, TypeError): return no_chat_selected_outputs

        chat_bubbles, last_message_date, today, yesterday = [], None, date.today(), date.today() - timedelta(days=1)
        if not messages_data:
            return html.P("No messages yet.", className="text-center text-muted p-5"), header_name, header_status, header_icon, {"display": "flex"}, refreshed_contact_list

        for msg in messages_data:
            current_message_date = msg["timestamp"].date()
            if current_message_date != last_message_date:
                date_str = "Today" if current_message_date == today else "Yesterday" if current_message_date == yesterday else current_message_date.strftime("%B %d, %Y")
                chat_bubbles.append(html.Div(html.Span(date_str, className="date-separator-text"), className="date-separator-container"))
                last_message_date = current_message_date
            is_current_user, bubble_class = msg["sender_id"] == current_user.id, "sent" if msg["sender_id"] == current_user.id else "received"
            user_display_name = msg.get("sender_name") or msg.get("sender_email", "Deleted User")
            bubble_content = [html.Div(user_display_name, className="message-user") if is_any_public and not is_current_user else None, html.P(msg["message_text"], className="message-text"), html.Span(msg["timestamp"].strftime("%I:%M %p"), className="message-timestamp")]
            chat_bubbles.append(html.Div(html.Div(bubble_content, className=f"message-bubble {bubble_class}"), className=f"message-alignment-container {bubble_class}"))

        return chat_bubbles, header_name, header_status, header_icon, {"display": "flex"}, refreshed_contact_list

    # --- FIX: Add the required placeholder function definition ---
    app.clientside_callback(
        """
        function(children) {
            setTimeout(function() {
                var chatContainer = document.getElementById('chat-history-container');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }, 50);
            return '';
        }
        """,
        Output("clientside-dummy-output", "children"),
        Input("chat-history", "children"),
    )
    def scroll_chat_window(children):
        pass # This function is a placeholder and is never executed on the server.