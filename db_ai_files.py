# db_ai_files.py

from db_pool import get_db_cursor

def add_user_file(user_id, gemini_file_id, gemini_file_uri, original_filename, mime_type):
    """Saves a record of a user's uploaded AI file to the database, including its URI."""
    sql = """
        INSERT INTO user_ai_files (user_id, gemini_file_id, gemini_file_uri, original_filename, mime_type)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (user_id, gemini_file_id, gemini_file_uri, original_filename, mime_type))
        return cur.fetchone()['id']

def get_user_files(user_id):
    """Retrieves all AI file records for a given user, including the crucial URI."""
    sql = "SELECT id, gemini_file_id, gemini_file_uri, original_filename, mime_type, created_at FROM user_ai_files WHERE user_id = %s ORDER BY created_at DESC;"
    with get_db_cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()

def get_user_file_by_id(file_db_id, user_id):
    """Retrieves a single file record, ensuring it belongs to the user."""
    # This is primarily used for deletion, so we just need the gemini_file_id.
    sql = "SELECT id, gemini_file_id FROM user_ai_files WHERE id = %s AND user_id = %s;"
    with get_db_cursor() as cur:
        cur.execute(sql, (file_db_id, user_id))
        return cur.fetchone()

def delete_user_file(file_db_id, user_id):
    """Deletes a file record from the database, ensuring ownership."""
    sql = "DELETE FROM user_ai_files WHERE id = %s AND user_id = %s;"
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (file_db_id, user_id))
        if cur.rowcount == 0:
            raise PermissionError("Permission denied or file not found.")