# db_training.py

from db_pool import get_db_cursor

def get_trainings(company_id=None, search_term=None, sort_by="date_newest"):
    query = "SELECT t.*, c.name as company_name FROM trainings t LEFT JOIN companies c ON t.company_id = c.id"
    params = []
    where_clauses = []

    if company_id:
        where_clauses.append("t.company_id = %s")
        params.append(company_id)

    if search_term:
        # Search on training name and description
        where_clauses.append("(t.name ILIKE %s OR t.description ILIKE %s)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    if sort_by == "name_asc":
        query += " ORDER BY t.name ASC"
    elif sort_by == "company_asc":
        query += " ORDER BY c.name ASC, t.name ASC"
    elif sort_by == "date_oldest":
        query += " ORDER BY t.created_at ASC"
    else:  # default to date_newest
        query += " ORDER BY t.created_at DESC"

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_training_with_questions(training_id, company_id=None):
    training_data = None
    questions_data = []
    with get_db_cursor() as cur:
        query = "SELECT * FROM trainings WHERE id = %s"
        params = [training_id]
        if company_id:
            query += " AND company_id = %s"
            params.append(company_id)
        cur.execute(query, params)
        training_data = cur.fetchone()
        if not training_data:
            return None, None
        cur.execute(
            "SELECT * FROM training_questions WHERE training_id = %s ORDER BY question_order ASC",
            (training_id,),
        )
        questions_data = cur.fetchall()
    return training_data, questions_data


def create_training_with_questions(training_data, questions_data, company_id, user_id):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO trainings (company_id, created_by_user_id, name, description, video_link) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (
                company_id,
                user_id,
                training_data["name"],
                training_data["description"],
                training_data["video_link"],
            ),
        )
        training_id = cur.fetchone()["id"]
        for q in questions_data:
            cur.execute(
                """
                INSERT INTO training_questions 
                (training_id, question_order, question_text, option_1, option_2, option_3, option_4, correct_answer)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    training_id,
                    q["order"],
                    q["text"],
                    q["opt1"],
                    q["opt2"],
                    q["opt3"],
                    q["opt4"],
                    q["correct"],
                ),
            )
    return training_id


# IMPLEMENTED FIX: Function to update an existing training module
def update_training_with_questions(training_id, training_data, questions_data):
    """Updates training details, deletes old questions, and inserts new ones."""
    with get_db_cursor(commit=True) as cur:
        # 1. Update the main training details
        cur.execute(
            "UPDATE trainings SET name = %s, description = %s, video_link = %s WHERE id = %s",
            (
                training_data["name"],
                training_data["description"],
                training_data["video_link"],
                training_id,
            ),
        )

        # 2. Delete all old questions associated with this training
        cur.execute("DELETE FROM training_questions WHERE training_id = %s", (training_id,))

        # 3. Insert the new set of questions
        for q in questions_data:
            cur.execute(
                """
                INSERT INTO training_questions 
                (training_id, question_order, question_text, option_1, option_2, option_3, option_4, correct_answer)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    training_id,
                    q["order"],
                    q["text"],
                    q["opt1"],
                    q["opt2"],
                    q["opt3"],
                    q["opt4"],
                    q["correct"],
                ),
            )


def delete_training(training_id, company_id=None):
    with get_db_cursor(commit=True) as cur:
        query = "DELETE FROM trainings WHERE id = %s"
        params = [training_id]
        if company_id:
            query += " AND company_id = %s"
            params.append(company_id)
        cur.execute(query, params)
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or training not found.")


def save_quiz_attempt_and_answers(user_id, training_id, answers):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id, correct_answer FROM training_questions WHERE training_id = %s",
            (training_id,),
        )
        correct_answers = {row["id"]: row["correct_answer"] for row in cur.fetchall()}

        total_questions = len(correct_answers)
        score = 100.0
        if total_questions > 0:
            correct_count = sum(
                1
                for ans in answers
                if correct_answers.get(ans["question_id"]) == ans["selected_answer"]
            )
            score = (correct_count / total_questions) * 100

        cur.execute(
            "INSERT INTO training_attempts (user_id, training_id, score) VALUES (%s, %s, %s) RETURNING id",
            (user_id, training_id, score),
        )
        attempt_id = cur.fetchone()["id"]

        for ans in answers:
            is_correct = (
                correct_answers.get(ans["question_id"]) == ans["selected_answer"]
            )
            cur.execute(
                "INSERT INTO training_user_answers (attempt_id, question_id, selected_answer, is_correct) VALUES (%s, %s, %s, %s)",
                (attempt_id, ans["question_id"], ans["selected_answer"], is_correct),
            )
        return attempt_id


def get_training_results_summary(training_id, company_id=None):
    query = """
        SELECT 
            u.id as user_id,
            u.email,
            u.full_name,
            COUNT(a.id) as attempt_count,
            MAX(a.score) as best_score,
            MAX(a.attempt_date) as last_attempt_date
        FROM users u
        JOIN training_attempts a ON u.id = a.user_id
        WHERE a.training_id = %s
    """
    params = [training_id]
    if company_id:
        query += " AND u.company_id = %s"
        params.append(company_id)

    query += " GROUP BY u.id, u.email, u.full_name ORDER BY MAX(a.attempt_date) DESC"

    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_user_quiz_result(attempt_id, user_id):
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT * FROM training_attempts WHERE id = %s AND user_id = %s",
            (attempt_id, user_id),
        )
        attempt_data = cur.fetchone()
        if not attempt_data:
            return None

        cur.execute(
            "SELECT name FROM trainings WHERE id = %s", (attempt_data["training_id"],)
        )
        training_data = cur.fetchone()

        cur.execute(
            """
            SELECT 
                tua.is_correct, tua.selected_answer,
                tq.question_order, tq.question_text, tq.correct_answer,
                tq.option_1, tq.option_2, tq.option_3, tq.option_4
            FROM training_user_answers tua
            JOIN training_questions tq ON tua.question_id = tq.id
            WHERE tua.attempt_id = %s
            ORDER BY tq.question_order ASC
        """,
            (attempt_id,),
        )
        answers_data = cur.fetchall()

        for ans in answers_data:
            options = {
                1: ans["option_1"],
                2: ans["option_2"],
                3: ans["option_3"],
                4: ans["option_4"],
            }
            ans["selected_answer_text"] = options.get(ans["selected_answer"], "N/A")
            ans["correct_answer_text"] = options.get(ans["correct_answer"], "N/A")

        return {
            "attempt": attempt_data,
            "training": training_data,
            "answers": answers_data,
        }


def get_user_training_details_and_stats(user_id, training_id):
    results = {"attempts": [], "question_stats": []}
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT id, attempt_date, score FROM training_attempts WHERE user_id = %s AND training_id = %s ORDER BY attempt_date DESC",
            (user_id, training_id),
        )
        results["attempts"] = cur.fetchall()
        cur.execute(
            """
            SELECT
                tq.id AS question_id,
                tq.question_text,
                (CASE tq.correct_answer
                    WHEN 1 THEN tq.option_1 WHEN 2 THEN tq.option_2
                    WHEN 3 THEN tq.option_3 WHEN 4 THEN tq.option_4
                    ELSE 'N/A'
                END) AS correct_answer_text,
                (
                    SUM(CASE WHEN tua.is_correct THEN 1 ELSE 0 END)::float /
                    NULLIF(COUNT(tua.id), 0)::float
                ) * 100 AS pass_rate
            FROM training_questions tq
            LEFT JOIN training_user_answers tua ON tq.id = tua.question_id
            LEFT JOIN training_attempts ta ON tua.attempt_id = ta.id AND ta.user_id = %s
            WHERE tq.training_id = %s
            GROUP BY tq.id, tq.question_text, correct_answer_text
            ORDER BY tq.question_order;
        """,
            (user_id, training_id),
        )
        results["question_stats"] = cur.fetchall()
    return results