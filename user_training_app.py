# user_training_app.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, no_update, ALL
from flask_login import current_user
from dash.exceptions import PreventUpdate
import urllib.parse

import db_training

def create_user_training_list_layout():
    company_id_to_check = current_user.company_id
    trainings = db_training.get_trainings(company_id=company_id_to_check)
    
    training_cards = []
    if not trainings:
        training_cards.append(html.P("No training modules are currently available for your company.", className="text-center mt-5"))
    else:
        for t in trainings:
            card = dbc.Card(className="mb-3", body=True, children=[
                html.H5(t['name'], className="card-title"),
                html.P(t['description'], className="card-text"),
                dcc.Link(dbc.Button("Start Training", color="primary"), href=f"/training/view/{t['id']}")
            ])
            training_cards.append(card)

    return html.Div([
        html.H1("Available Trainings"),
        html.P("Select a training module below to begin."),
        html.Hr(),
        *training_cards
    ])

def create_quiz_page_layout(training_id):
    training_data, questions_data = db_training.get_training_with_questions(training_id, company_id=current_user.company_id)
    if not training_data:
        return html.Div([html.H1("Not Found"), html.P("This training module could not be found or is not available for your company.")])

    video_id = None
    if training_data.get('video_link'):
        try:
            parsed_url = urllib.parse.urlparse(training_data['video_link'])
            if 'youtube.com' in parsed_url.netloc:
                video_id = urllib.parse.parse_qs(parsed_url.query).get('v', [None])[0]
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')
        except Exception as e:
            print(f"Could not parse video URL: {e}")

    video_embed = html.Div("No video provided for this training.", className="text-center text-muted p-5 border rounded")
    if video_id:
        video_embed = html.Div(html.Iframe(src=f"https://www.youtube.com/embed/{video_id}", className="w-100", style={'aspectRatio': '16/9', 'border': '0'}), className="ratio ratio-16x9 mb-5")

    question_blocks = []
    for q in questions_data:
        # FIX: Ensure a clean, single-column vertical layout for each question.
        question_blocks.append(
            dbc.Card(body=True, className="mb-3", children=[
                html.Div([
                    html.P(f"Question {q['question_order']}: {q['question_text']}", className="fw-bold mb-3"),
                    dbc.RadioItems(
                        id={'type': 'user-answer', 'index': q['id']},
                        options=[
                            {'label': q['option_1'], 'value': 1},
                            {'label': q['option_2'], 'value': 2},
                            {'label': q['option_3'], 'value': 3},
                            {'label': q['option_4'], 'value': 4},
                        ]
                    )
                ])
            ])
        )

    return html.Div([
        html.H1(training_data['name']),
        html.P(training_data['description']),
        html.Hr(),
        video_embed,
        html.H3("Quiz", className="mt-5 mb-3"),
        dcc.Store(id='store-training-id', data=training_id),
        *question_blocks,
        html.Div(id='quiz-submit-status', className="mt-3"),
        dbc.Button("Submit Quiz", id="submit-quiz-button", color="success", size="lg", className="mt-3 w-100")
    ])

def create_result_page_layout(attempt_id):
    result_data = db_training.get_user_quiz_result(attempt_id, user_id=current_user.id)
    if not result_data:
        return html.Div("Result not found or you do not have permission to view it.")

    training_info = result_data['training']
    attempt_info = result_data['attempt']
    answers_info = result_data['answers']
    
    score_percent = attempt_info['score']
    score_color = "success" if score_percent >= 80 else "danger"

    answer_details = []
    for ans in answers_info:
        if ans['is_correct']:
            answer_details.append(dbc.ListGroupItem(f"Q{ans['question_order']}: {ans['question_text']} - Correct", color="success"))
        else:
            incorrect_item = dbc.ListGroupItem([
                html.Div(f"Q{ans['question_order']}: {ans['question_text']} - Incorrect", className="fw-bold"),
                html.Div(f"Your Answer: {ans['selected_answer_text']}", className="text-danger"),
                html.Div(f"Correct Answer: {ans['correct_answer_text']}", className="text-success")
            ], color="danger")
            answer_details.append(incorrect_item)

    return html.Div([
        html.H1(f"Results for: {training_info['name']}"),
        html.P(f"Attempt Date: {attempt_info['attempt_date'].strftime('%d-%b-%Y %H:%M')}"),
        dbc.Alert(f"Your Score: {score_percent:.0f}%", color=score_color, className="h3"),
        html.H4("Answer Breakdown", className="mt-4"),
        dbc.ListGroup(answer_details),
        dcc.Link(dbc.Button("Back to Training List", color="secondary", className="mt-4"), href="/training")
    ])


def register_callbacks(app):
    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Output('quiz-submit-status', 'children'),
        Input('submit-quiz-button', 'n_clicks'),
        [
            State('store-training-id', 'data'),
            State({'type': 'user-answer', 'index': ALL}, 'id'),
            State({'type': 'user-answer', 'index': ALL}, 'value')
        ],
        prevent_initial_call=True
    )
    def submit_quiz(n_clicks, training_id, answer_ids, answer_values):
        if not current_user.is_authenticated: raise PreventUpdate
        
        if None in answer_values:
            return no_update, dbc.Alert("Please answer all questions before submitting.", color="warning")

        answers = [{'question_id': ans_id['index'], 'selected_answer': ans_val} for ans_id, ans_val in zip(answer_ids, answer_values)]
        
        try:
            attempt_id = db_training.save_quiz_attempt_and_answers(current_user.id, training_id, answers)
            return f'/training/result/{attempt_id}', no_update
        except Exception as e:
            print(f"Error saving quiz: {e}")
            return no_update, dbc.Alert("An error occurred while saving your results. Please try again.", color="danger")