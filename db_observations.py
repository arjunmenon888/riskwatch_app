# db_observations.py

import base64
from db_pool import get_db_cursor


def add_observation_to_db(observation_dict, user_id):
    likelihood = observation_dict.get("likelihood", 0)
    severity = observation_dict.get("severity", 0)
    sql = """
        INSERT INTO observations (user_id, date_str, area_equipment, description, impact, likelihood, severity, risk_rating, corrective_action, deadline, photo_bytes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            sql,
            (
                user_id,
                observation_dict.get("date_str"),
                observation_dict.get("area_equipment"),
                observation_dict.get("description"),
                observation_dict.get("impact"),
                likelihood,
                severity,
                likelihood * severity,
                observation_dict.get("corrective_action"),
                observation_dict.get("deadline"),
                observation_dict.get("photo_bytes"),
            ),
        )
        return cur.fetchone()["id"]


def get_observations_from_db(user_id, search_term=None, sort_by="date_newest"):
    search_clause = ""
    params = [user_id]
    if search_term:
        search_clause = "AND (description ILIKE %s OR area_equipment ILIKE %s)"
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like])
    order_by_clause = "ORDER BY id DESC"
    if sort_by == "date_oldest":
        order_by_clause = "ORDER BY id ASC"
    elif sort_by == "risk_high":
        order_by_clause = "ORDER BY risk_rating DESC, id DESC"
    query = f"""
        WITH NumberedObservations AS (SELECT *, ROW_NUMBER() OVER(ORDER BY id DESC) as display_id FROM observations WHERE user_id = %s {search_clause})
        SELECT * FROM NumberedObservations {order_by_clause};
    """
    with get_db_cursor() as cur:
        cur.execute(query, params)
        observations = cur.fetchall()
    for obs in observations:
        obs["photo_b64"] = (
            base64.b64encode(obs["photo_bytes"]).decode("utf-8")
            if obs.get("photo_bytes")
            else None
        )
    return observations


def delete_observation_from_db(observation_id, current_user_id, is_admin=False):
    with get_db_cursor(commit=True) as cur:
        if is_admin:
            sql = "DELETE FROM observations WHERE id = %s;"
        else:
            sql = "DELETE FROM observations WHERE id = %s AND user_id = %s;"
        params = (observation_id,) if is_admin else (observation_id, current_user_id)
        cur.execute(sql, params)
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or record not found.")