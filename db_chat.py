# db_chat.py

from db_pool import get_db_cursor

def add_message(sender_id, recipient_id, message_text, company_id):
    """
    Adds a new chat message to the database.
    - recipient_id can be None for public messages.
    - company_id can be None for global messages.
    """
    sql = """
        INSERT INTO chat_messages (sender_id, recipient_id, message_text, company_id)
        VALUES (%s, %s, %s, %s)
    """
    with get_db_cursor(commit=True) as cur:
        db_recipient_id = None if recipient_id == 'public' else recipient_id
        cur.execute(sql, (sender_id, db_recipient_id, message_text, company_id))


def get_public_messages(company_id):
    """
    Retrieves all public messages for a specific company, joining with the users
    table to get sender information.
    """
    if not company_id: 
        return []
        
    sql = """
        SELECT
            m.id, m.sender_id, m.message_text, m.timestamp,
            u.full_name as sender_name,
            u.email as sender_email
        FROM
            chat_messages m
        LEFT JOIN
            users u ON m.sender_id = u.id
        WHERE
            m.company_id = %s AND m.recipient_id IS NULL
        ORDER BY
            m.timestamp ASC;
    """
    with get_db_cursor() as cur:
        cur.execute(sql, (company_id,))
        return cur.fetchall()

def get_global_public_messages():
    """
    Retrieves all global public messages (where company_id is NULL).
    """
    sql = """
        SELECT
            m.id, m.sender_id, m.message_text, m.timestamp,
            u.full_name as sender_name,
            u.email as sender_email
        FROM
            chat_messages m
        LEFT JOIN
            users u ON m.sender_id = u.id
        WHERE
            m.company_id IS NULL AND m.recipient_id IS NULL
        ORDER BY
            m.timestamp ASC;
    """
    with get_db_cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def get_private_messages(user1_id, user2_id):
    """
    Retrieves the private conversation between two specific users.
    """
    sql = """
        SELECT
            m.id, m.sender_id, m.message_text, m.timestamp,
            u.full_name as sender_name,
            u.email as sender_email
        FROM
            chat_messages m
        LEFT JOIN
            users u ON m.sender_id = u.id
        WHERE
            (m.sender_id = %s AND m.recipient_id = %s) OR
            (m.sender_id = %s AND m.recipient_id = %s)
        ORDER BY
            m.timestamp ASC;
    """
    with get_db_cursor() as cur:
        cur.execute(sql, (user1_id, user2_id, user2_id, user1_id))
        return cur.fetchall()

# --- NEW: Function to mark messages as read for a specific conversation ---
def mark_messages_as_read(sender_id, recipient_id):
    """Marks all messages from a sender to a recipient as read."""
    sql = """
        UPDATE chat_messages
        SET is_read = TRUE
        WHERE sender_id = %s AND recipient_id = %s AND is_read = FALSE;
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(sql, (sender_id, recipient_id))

# --- UPDATED: get_conversations now includes unread_count ---
def get_conversations(user_id):
    """
    Retrieves a list of all users that the given user has had a private
    conversation with, and includes the count of unread messages from each.
    """
    sql = """
        SELECT
            u.*,
            c.name as company_name,
            (SELECT COUNT(*) 
             FROM chat_messages 
             WHERE sender_id = u.id AND recipient_id = %s AND is_read = FALSE
            ) AS unread_count
        FROM (
            -- Get IDs of all users I have interacted with
            SELECT recipient_id as partner_id
            FROM chat_messages
            WHERE sender_id = %s AND recipient_id IS NOT NULL
            
            UNION
            
            SELECT sender_id as partner_id
            FROM chat_messages
            WHERE recipient_id = %s
        ) AS partners
        JOIN users u ON u.id = partners.partner_id
        LEFT JOIN companies c ON u.company_id = c.id;
    """
    with get_db_cursor() as cur:
        cur.execute(sql, (user_id, user_id, user_id))
        return cur.fetchall()