

import sys
from datetime import datetime
from database_manager import DatabaseManager

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting automation task...")

    try:
        db = DatabaseManager()

        # Удаление неактивных аккаунтов
        print("Running account cleanup...")
        deleted_count = db.delete_inactive_accounts()
        print(f"✓ Deleted {deleted_count} inactive accounts")

        # Создание резервной копии
        print("Creating backup...")
        backup_id = db.create_backup('full')
        print(f"✓ Backup created (ID: {backup_id})")

        db.close_all_connections()
        print("✓ All tasks completed successfully")
        return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())