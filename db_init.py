# db_init.py

import psycopg2
from db_pool import get_db_cursor

def init_db():
    """
    Initializes the database. Creates tables if they don't exist and
    safely applies schema updates by adding columns if they are missing.
    This script is safe to run on every application startup.
    """
    with get_db_cursor(commit=True) as cur:
        # 1. Create Foundational Tables (if they don't exist)
        # =======================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY, 
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, 
                email TEXT UNIQUE NOT NULL, 
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user', 
                industry TEXT NOT NULL DEFAULT 'General',
                company_id INTEGER, 
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                force_reset BOOLEAN DEFAULT FALSE, 
                can_access_observation BOOLEAN DEFAULT FALSE,
                can_access_training BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE SET NULL
            )
        """)
        
        # 2. Safely Add New Columns to the 'users' Table
        # =======================================================
        new_user_columns = {
            "can_access_lost_and_found": "BOOLEAN DEFAULT FALSE",
            "can_access_gate_pass": "BOOLEAN DEFAULT FALSE",
            "can_access_ask_ai": "BOOLEAN DEFAULT FALSE",
            "full_name": "TEXT",
            "job_title": "TEXT",
            "department": "TEXT",
            "employee_id": "TEXT",
            "phone_number": "TEXT",
            "profile_photo_bytes": "BYTEA",
            "preferred_language": "TEXT DEFAULT 'English'",
            "can_create_users": "BOOLEAN DEFAULT FALSE",
            "user_creation_limit": "INTEGER DEFAULT 0"
        }

        for col_name, col_type in new_user_columns.items():
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
            except psycopg2.errors.DuplicateColumn:
                cur.connection.rollback()
                pass

        # 3. Create Other Application Tables
        # =======================================================
        # (All other CREATE TABLE statements remain the same...)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER NOT NULL, 
                date_str TEXT NOT NULL,
                area_equipment TEXT NOT NULL, 
                description TEXT, 
                impact TEXT,
                likelihood INTEGER, 
                severity INTEGER, 
                risk_rating INTEGER,
                corrective_action TEXT, 
                deadline TEXT, 
                photo_bytes BYTEA,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trainings (
                id SERIAL PRIMARY KEY, 
                company_id INTEGER NOT NULL, 
                created_by_user_id INTEGER NOT NULL,
                name TEXT NOT NULL, 
                description TEXT, 
                video_link TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY(created_by_user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lost_and_found (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER NOT NULL, 
                company_id INTEGER,
                entry_date DATE NOT NULL,
                entry_time TEXT NOT NULL, 
                ticket_no TEXT NOT NULL, 
                item_type TEXT NOT NULL,
                item_description TEXT NOT NULL, 
                location_found TEXT NOT NULL, 
                found_by TEXT NOT NULL,
                department TEXT NOT NULL, 
                received_by_security TEXT, 
                stored_in TEXT, 
                photo_bytes BYTEA,
                owner_id_no TEXT, 
                claimer_receiver_disposer TEXT, 
                receiver_contact_no TEXT,
                claim_date DATE, 
                claim_time TEXT, 
                handed_over_by TEXT, 
                remarks TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                UNIQUE(company_id, ticket_no)
            )
        """)
        
        try:
            cur.execute("ALTER TABLE lost_and_found ADD COLUMN status TEXT DEFAULT 'Unclaimed';")
        except psycopg2.errors.DuplicateColumn:
            cur.connection.rollback()
            pass
        
        cur.execute("""
             CREATE TABLE IF NOT EXISTS training_questions (
                id SERIAL PRIMARY KEY, 
                training_id INTEGER NOT NULL, 
                question_order INTEGER NOT NULL,
                question_text TEXT NOT NULL, 
                option_1 TEXT, 
                option_2 TEXT, 
                option_3 TEXT, 
                option_4 TEXT,
                correct_answer INTEGER NOT NULL,
                FOREIGN KEY(training_id) REFERENCES trainings(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS training_attempts (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER NOT NULL, 
                training_id INTEGER NOT NULL,
                score FLOAT NOT NULL, 
                attempt_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(training_id) REFERENCES trainings(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS training_user_answers (
                id SERIAL PRIMARY KEY, 
                attempt_id INTEGER NOT NULL, 
                question_id INTEGER NOT NULL,
                selected_answer INTEGER NOT NULL, 
                is_correct BOOLEAN NOT NULL,
                FOREIGN KEY(attempt_id) REFERENCES training_attempts(id) ON DELETE CASCADE,
                FOREIGN KEY(question_id) REFERENCES training_questions(id) ON DELETE CASCADE
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gate_pass_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                company_id INTEGER,
                date_issued DATE,
                gate_pass_number TEXT,
                item_description TEXT,
                issued_to TEXT,
                company TEXT,
                purpose_of_removal TEXT,
                authorized_by TEXT,
                authorizing_department TEXT,
                type TEXT,
                date_to_be_returned DATE,
                item_picture_taken_out_bytes BYTEA,
                item_picture_returned_back_bytes BYTEA,
                status TEXT DEFAULT 'non returned',
                returned_date DATE,
                received_by TEXT,
                remarks TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                UNIQUE(company_id, gate_pass_number)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_ai_files (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                gemini_file_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                mime_type TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        try:
            cur.execute("ALTER TABLE user_ai_files ADD COLUMN gemini_file_uri TEXT;")
        except psycopg2.errors.DuplicateColumn:
            cur.connection.rollback()
            pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                company_id INTEGER,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER, -- NULL for public messages
                message_text TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(recipient_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # --- NEW: Safely add the is_read column to the chat_messages table ---
        try:
            cur.execute("ALTER TABLE chat_messages ADD COLUMN is_read BOOLEAN DEFAULT FALSE;")
        except psycopg2.errors.DuplicateColumn:
            cur.connection.rollback()
            pass

    print("Database tables checked/created successfully.")