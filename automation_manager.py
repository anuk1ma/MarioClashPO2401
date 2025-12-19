

import schedule
import time
from datetime import datetime
from database_manager import DatabaseManager


class AutomationManager:
    """Менеджер автоматизации для Windows"""

    def __init__(self):
        self.db = DatabaseManager()
        print("=" * 60)
        print("MARIO CLASH - Automation Manager")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def cleanup_inactive_accounts(self):
        """Удаление неактивных аккаунтов (старше 7 дней)"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running account cleanup...")
        try:
            deleted_count = self.db.delete_inactive_accounts()
            print(f"  ✓ Deleted {deleted_count} inactive accounts")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    def create_daily_backup(self):
        """Создание ежедневной резервной копии"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Creating daily backup...")
        try:
            backup_id = self.db.create_backup('full')
            print(f"  ✓ Backup created (ID: {backup_id})")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    def generate_weekly_report(self):
        """Генерация еженедельного отчета"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating weekly report...")
        try:
            # Получаем статистику
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                # Общая статистика
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(*) FILTER (WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days') as new_users,
                        COALESCE(SUM(total_score), 0) as total_scores
                    FROM users
                    WHERE banned = FALSE
                """)
                stats = cur.fetchone()

                print(f"  Total Users: {stats[0]}")
                print(f"  New Users (7 days): {stats[1]}")
                print(f"  Total Scores: {stats[2]}")

            self.db.release_connection(conn)
            print(f"  ✓ Report generated")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    def run_scheduler(self):
        """Запуск планировщика задач"""
        # Планирование задач
        schedule.every().day.at("03:00").do(self.cleanup_inactive_accounts)
        schedule.every().day.at("02:00").do(self.create_daily_backup)
        schedule.every().monday.at("09:00").do(self.generate_weekly_report)

        print("Scheduled tasks:")
        print("  - Account cleanup: Daily at 03:00")
        print("  - Daily backup: Daily at 02:00")
        print("  - Weekly report: Monday at 09:00")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print()

        # Основной цикл
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Проверка каждую минуту
        except KeyboardInterrupt:
            print("\n\nStopping automation manager...")
            self.db.close_all_connections()
            print("✓ Shutdown complete")


if __name__ == "__main__":
    manager = AutomationManager()
    manager.run_scheduler()