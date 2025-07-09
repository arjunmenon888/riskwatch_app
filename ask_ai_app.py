# ask_ai_app.py

import dash
from dash import dcc, html, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from flask_login import current_user
import traceback

import ai_module
import db_ai_files

# Helper to map file extensions to MIME types Gemini understands
MIME_TYPE_MAP = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp'
}

ACCEPTED_FILE_TYPES = ".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.webp"

def create_ask_ai_layout():
    """
    Creates the enhanced 'Ask Me (AI)' page with location awareness and advanced logic.
    """
    return html.Div(className="observation-form-container", style={'maxWidth': '800px', 'margin': 'auto'}, children=[
        # Session storage for location
        dcc.Store(id='ai-location-store', storage_type='session'),
        
        html.Div(id='ask-ai-message'),
        dcc.Store(id='ai-refresh-signal', data=0),

        html.Div(className="form-content", children=[
            html.H1("Ask Me (AI)", className="form-title", style={'marginBottom': '35px'}),

            # Location Input Field
            html.Div(className="form-group", children=[
                html.Label("Location (City or Country)"),
                html.P("Provide a location to get region-specific regulatory answers.", className="text-muted", style={'fontSize': '0.9em', 'marginTop': '-10px'}),
                dbc.Input(
                    id='ai-location-input',
                    placeholder="e.g., Dubai, UAE or London, UK",
                    type="text",
                    debounce=True, # Updates the store after user stops typing
                )
            ]),

            # File Upload Section
            html.Div(className="form-group", children=[
                html.Label("Upload Documents or Images (Optional)"),
                html.P("Upload files to provide specific context for your question.", className="text-muted", style={'fontSize': '0.9em', 'marginTop': '-10px'}),
                dcc.Loading(id="loading-upload-wrapper", type="default", children=[
                    dcc.Upload(
                        id='ai-doc-upload',
                        className="photo-upload-area-styled",
                        children=html.Div([
                            html.Img(src='/assets/upload-icon.png', className="upload-icon-img-styled"),
                            html.Span("Drag and Drop or Select Files")
                        ], className="photo-upload-button-styled"),
                        multiple=True,
                        accept=ACCEPTED_FILE_TYPES,
                        disabled=False
                    ),
                ]),
                html.Div(id="upload-status-message", className="mt-3")
            ]),

            # Question Input Field
            html.Div(className="form-group", children=[
                html.Label("Ask a Question"),
                dbc.Textarea(
                    id='ai-user-question',
                    placeholder="e.g., What are the requirements for food handler training?",
                    rows=6
                )
            ]),

            # Submit Button with Loading Indicator
            html.Div(className="submit-button-container", children=[
                 dcc.Loading(
                    id="loading-ai-submit",
                    type="circle",
                    children=[
                        html.Button("Get Answer", id="ai-submit-button", n_clicks=0, className="submit-button-style")
                    ]
                 )
            ]),
            
            # AI Response Area
            dcc.Loading(
                id="loading-ai-answer",
                type="default",
                children=html.Div(id="ai-answer-container", children=[
                    dcc.Markdown(className='ai-answer-box mt-4')
                ])
            )
        ]),

        html.Hr(className="my-5"),
        html.H4("Your Stored Documents"),
        dcc.Loading(children=html.Div(id='ai-documents-list'))
    ])

def register_callbacks(app):
    # Callback to store the location in the user's session
    @app.callback(
        Output('ai-location-store', 'data'),
        Input('ai-location-input', 'value')
    )
    def store_location(location):
        return {'location': location}

    # Callback to display the list of stored documents
    @app.callback(
        Output('ai-documents-list', 'children'),
        Input('ai-refresh-signal', 'data')
    )
    def update_documents_list(refresh_signal):
        user_files = db_ai_files.get_user_files(current_user.id)
        if not user_files:
            return html.P("You have no documents stored.", className="text-center text-muted")
        
        return dbc.ListGroup([
            dbc.ListGroupItem([
                html.Div([
                    html.I(className="bi bi-file-earmark-text me-2"),
                    file['original_filename']
                ], className="fw-bold"),
                dbc.Button("Delete", id={'type': 'delete-ai-file', 'index': file['id']}, 
                           color="danger", size="sm", outline=True, className="ms-auto")
            ], className="d-flex align-items-center justify-content-between")
            for file in user_files
        ], flush=True)

    # Callback to handle new file uploads
    @app.callback(
        Output('ai-refresh-signal', 'data'),
        Output('upload-status-message', 'children'),
        Output('ai-doc-upload', 'disabled'),
        Input('ai-doc-upload', 'contents'),
        [
            State('ai-doc-upload', 'filename'),
            State('ai-refresh-signal', 'data')
        ],
        prevent_initial_call=True
    )
    def handle_file_upload(list_of_contents, list_of_names, refresh_count):
        if not list_of_contents:
            return no_update, no_update, False

        is_disabled = True # Disable upload while processing
        
        total_files = len(list_of_contents)
        for i, (content, name) in enumerate(zip(list_of_contents, list_of_names)):
            try:
                ext = name.split('.')[-1].lower()
                mime_type = MIME_TYPE_MAP.get(ext)
                if not mime_type:
                    raise ValueError(f"Unsupported file type: {name}")

                # This is now a non-blocking call.
                gemini_file = ai_module.upload_file_to_gemini(content, name, mime_type)
                
                # We save the file to our DB immediately with a 'PROCESSING' status.
                db_ai_files.add_user_file(
                    user_id=current_user.id,
                    gemini_file_id=gemini_file.name,
                    gemini_file_uri=gemini_file.uri,
                    original_filename=name,
                    mime_type=mime_type
                )
            
            except Exception as e:
                print("--- AI FILE UPLOAD ERROR ---")
                print(f"User: {current_user.email}, File: {name}")
                print(traceback.format_exc())
                print("--------------------------")
                
                user_friendly_error = f"An error occurred while uploading '{name}'. Please try again."
                # Re-enable upload on error
                return no_update, dbc.Alert(user_friendly_error, color="danger", dismissable=True), False
        
        # --- FIX: Update success message to reflect asynchronous processing ---
        success_message = f"Started processing {total_files} file(s). They will be ready to use shortly."
        return refresh_count + 1, dbc.Alert(success_message, color="info", duration=8000), False

    # Callback to handle deleting a file
    @app.callback(
        Output('ai-refresh-signal', 'data', allow_duplicate=True),
        Output('ask-ai-message', 'children', allow_duplicate=True),
        Input({'type': 'delete-ai-file', 'index': ALL}, 'n_clicks'),
        State('ai-refresh-signal', 'data'),
        prevent_initial_call=True
    )
    def handle_delete_file(n_clicks, refresh_count):
        if not any(n for n in n_clicks if n):
            raise PreventUpdate
        
        file_db_id = dash.callback_context.triggered_id['index']
        
        try:
            file_to_delete = db_ai_files.get_user_file_by_id(file_db_id, current_user.id)
            if not file_to_delete:
                return no_update, dbc.Alert("File not found or permission denied.", color="warning")

            ai_module.delete_ai_file(file_to_delete['gemini_file_id'])
            db_ai_files.delete_user_file(file_db_id, current_user.id)

            return refresh_count + 1, dbc.Alert("File deleted successfully.", color="info", duration=3000)

        except Exception as e:
            print("--- AI FILE DELETE ERROR ---")
            print(f"User: {current_user.email}, DB File ID: {file_db_id}")
            print(traceback.format_exc())
            print("--------------------------")
            return no_update, dbc.Alert("An error occurred while deleting the file. Please try again.", color="danger")

    # Callback for asking a question
    @app.callback(
        Output('ai-answer-container', 'children'),
        Output('ask-ai-message', 'children', allow_duplicate=True),
        Input('ai-submit-button', 'n_clicks'),
        [
            State('ai-user-question', 'value'),
            State('ai-location-store', 'data')
        ],
        prevent_initial_call=True
    )
    def handle_ask_ai_submission(n_clicks, question, location_data):
        if not question:
            return no_update, dbc.Alert("Please enter a question.", color="warning")
        
        location = location_data.get('location') if location_data else None

        try:
            user_files_from_db = db_ai_files.get_user_files(current_user.id)
            
            file_objects_for_prompt = []
            if user_files_from_db:
                print(f"Fetching {len(user_files_from_db)} file objects from Gemini API for context...")
                for file_meta in user_files_from_db:
                    file_id = file_meta['gemini_file_id']
                    try:
                        # --- FIX: Check the file state before using it ---
                        # This network call is now inside the main callback, which can cause slowness
                        # but is a necessary step without a background worker.
                        file_obj = ai_module.genai.get_file(name=file_id)
                        
                        if file_obj.state.name == "PROCESSING":
                            user_error = f"The file '{file_meta['original_filename']}' is still being processed. Please wait a moment and try again."
                            return no_update, dbc.Alert(user_error, color="warning", duration=5000)
                        elif file_obj.state.name != "ACTIVE":
                             user_error = f"The file '{file_meta['original_filename']}' could not be processed (state: {file_obj.state.name}). Please try deleting and re-uploading it."
                             return no_update, dbc.Alert(user_error, color="danger")
                        
                        file_objects_for_prompt.append(file_obj)
                    except Exception as get_file_error:
                        print(f"Could not retrieve file {file_id}. Error: {get_file_error}")
                        user_error = f"Error: Could not access the stored file '{file_meta['original_filename']}'. It might have been deleted or expired. Please try re-uploading it."
                        return no_update, dbc.Alert(user_error, color="danger")

            answer = ai_module.get_answer_from_docs(
                file_objects=file_objects_for_prompt,
                user_question=question,
                location=location
            )
            
            return dcc.Markdown(answer, className='ai-answer-box mt-4'), None
        
        except Exception as e:
            print("--- ASK ME AI SUBMISSION ERROR ---")
            print(f"User: {current_user.email}")
            print(traceback.format_exc())
            print("---------------------------------")
            
            user_friendly_error = "An error was encountered while getting the AI response. Please try again later."
            return no_update, dbc.Alert(user_friendly_error, color="danger", dismissable=True)