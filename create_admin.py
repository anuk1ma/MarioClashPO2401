"""
Create Admin User
Создает пользователя admin с паролем admin123
"""

from database_manager import DatabaseManager


def create_admin():
    db = DatabaseManager()

    print("=" * 60)
    print("Creating Admin User")
    print("=" * 60)

    # Удаляем старого админа если есть
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = 'admin'")
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        print("✓ Old admin removed")
    except:
        pass

    # Создаем нового админа
    result = db.register_user('admin', 'admin123')

    if result['success']:
        print("✓ User 'admin' created")

        # Делаем его админом
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
        conn.commit()
        cursor.close()
        db.release_connection(conn)

        print("✓ Role set to 'admin'")
        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print()
        print("Login credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print()
        print("You can now login to the game!")
        print("=" * 60)
    else:
        print(f"✗ Error: {result['error']}")

    db.close_all_connections()


if __name__ == "__main__":
    create_admin()