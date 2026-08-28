def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s;
    """, (table, column))
    return cur.fetchone() is not None


def ensure_tables_exist():
    """Создаёт таблицы, если их нет, и мигрирует старую схему к актуальной."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # --- users ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL
            );
        """)

        if not _column_exists(cur, "users", "password_hash"):
            cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);")

            # Если есть старая колонка с открытым паролем — переносим,
            # хешируя значения на лету, и убираем старую колонку.
            if _column_exists(cur, "users", "password"):
                cur.execute("SELECT id, password FROM users WHERE password IS NOT NULL;")
                rows = cur.fetchall()
                for user_id, plain_password in rows:
                    hashed = hash_password(plain_password)
                    cur.execute(
                        "UPDATE users SET password_hash = %s WHERE id = %s;",
                        (hashed, user_id),
                    )
                cur.execute("ALTER TABLE users DROP COLUMN password;")

            cur.execute("ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;")

        # --- favorites ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id VARCHAR(100) PRIMARY KEY
            );
        """)

        if not _column_exists(cur, "favorites", "favorite_ids"):
            cur.execute("ALTER TABLE favorites ADD COLUMN favorite_ids INTEGER[];")

            # Старая колонка hero хранила имена героев строками — формат
            # несовместим с ID, так что просто убираем её; пользователям
            # нужно будет заново отметить любимых героев один раз.
            if _column_exists(cur, "favorites", "heroes"):
                cur.execute("ALTER TABLE favorites DROP COLUMN heroes;")

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка создания/миграции таблиц: {e}")
