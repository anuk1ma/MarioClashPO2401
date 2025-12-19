"""
Database Manager для Mario Clash
Управление подключением к PostgreSQL и операциями с БД
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import datetime, timedelta
import json


class DatabaseManager:
    def __init__(self, host='localhost', database='mario_clash_db',
                 user='mario_app_user', password='1708',
                 port=5432):
        """Инициализация менеджера БД с пулом соединений"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # min и max соединений
                host=host,
                database=database,
                user=user,
                password=password,
                port=port
            )
            if self.connection_pool:
                print("✓ Connection pool created successfully")
        except Exception as e:
            print(f"✗ Error creating connection pool: {e}")
            raise

    def get_connection(self):
        """Получить соединение из пула"""
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        """Вернуть соединение в пул"""
        self.connection_pool.putconn(conn)

    def close_all_connections(self):
        """Закрыть все соединения"""
        if self.connection_pool:
            self.connection_pool.closeall()

    # ==========================================
    # МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
    # ==========================================

    def hash_password(self, password):
        """Хеширование пароля с использованием bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        """Проверка пароля"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def register_user(self, username, password):
        """Регистрация нового пользователя"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Проверка существования пользователя
                cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return {'success': False, 'error': 'Username already exists'}

                # Создание пользователя
                hashed_password = self.hash_password(password)
                cur.execute("""
                    INSERT INTO users (username, password, role, current_level)
                    VALUES (%s, %s, 'player', 1)
                    RETURNING user_id, username, role, current_level
                """, (username, hashed_password))

                user = cur.fetchone()
                conn.commit()

                return {'success': True, 'user': dict(user)}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            self.release_connection(conn)

    def login_user(self, username, password):
        """Авторизация пользователя"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT user_id, username, password, role, total_score, 
                           current_level, banned
                    FROM users
                    WHERE username = %s
                """, (username,))

                user = cur.fetchone()

                if not user:
                    return {'success': False, 'error': 'User not found'}

                if user['banned']:
                    return {'success': False, 'error': 'Account is banned'}

                if not self.verify_password(password, user['password']):
                    return {'success': False, 'error': 'Invalid password'}

                # Удаляем пароль из ответа
                user_data = dict(user)
                del user_data['password']

                return {'success': True, 'user': user_data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            self.release_connection(conn)

    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        u.username,
                        u.total_score,
                        u.current_level,
                        COUNT(DISTINCT up.level_id) FILTER (WHERE up.completed = TRUE) as levels_completed,
                        COUNT(ua.achievement_id) as achievements_count,
                        COALESCE(SUM(up.time_spent), 0) as total_time_played
                    FROM users u
                    LEFT JOIN user_progress up ON u.user_id = up.user_id
                    LEFT JOIN user_achievements ua ON u.user_id = ua.user_id
                    WHERE u.user_id = %s
                    GROUP BY u.user_id
                """, (user_id,))

                return dict(cur.fetchone())
        finally:
            self.release_connection(conn)

    # ==========================================
    # МЕТОДЫ ДЛЯ УРОВНЕЙ И ПРОГРЕССА
    # ==========================================

    def get_levels(self):
        """Получить все уровни"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT level_id, title, max_score, difficulty
                    FROM levels
                    ORDER BY level_id
                """)
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.release_connection(conn)

    def get_user_progress(self, user_id):
        """Получить прогресс пользователя по всем уровням"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        l.level_id,
                        l.title,
                        l.max_score,
                        COALESCE(up.score, 0) as score,
                        COALESCE(up.completed, FALSE) as completed,
                        COALESCE(up.attempts, 0) as attempts,
                        COALESCE(up.best_time, 0) as best_time
                    FROM levels l
                    LEFT JOIN user_progress up ON l.level_id = up.level_id AND up.user_id = %s
                    ORDER BY l.level_id
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.release_connection(conn)

    def save_level_progress(self, user_id, level_id, score, time_spent,
                            enemies_killed, completed=False):
        """
        Сохранить прогресс уровня

        Система очков:
        - Обычная черепаха: 200 очков
        - Шипастая черепаха: 500 очков
        - Бонус за время: до 500 очков
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Проверяем существование записи
                cur.execute("""
                    SELECT progress_id, score, best_time, attempts
                    FROM user_progress
                    WHERE user_id = %s AND level_id = %s
                """, (user_id, level_id))

                existing = cur.fetchone()

                if existing:
                    # Обновляем только если новый счет лучше
                    old_score = existing['score']
                    old_best_time = existing['best_time']
                    attempts = existing['attempts'] + 1

                    new_score = max(old_score, score)
                    new_best_time = min(old_best_time, time_spent) if old_best_time else time_spent

                    cur.execute("""
                        UPDATE user_progress
                        SET score = %s,
                            completed = %s,
                            attempts = %s,
                            time_spent = %s,
                            best_time = %s,
                            completed_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE completed_at END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE progress_id = %s
                        RETURNING progress_id
                    """, (new_score, completed, attempts, time_spent, new_best_time,
                          completed, existing['progress_id']))
                else:
                    # Создаем новую запись
                    cur.execute("""
                        INSERT INTO user_progress 
                        (user_id, level_id, score, completed, attempts, time_spent, best_time, completed_at)
                        VALUES (%s, %s, %s, %s, 1, %s, %s, 
                                CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END)
                        RETURNING progress_id
                    """, (user_id, level_id, score, completed, time_spent, time_spent, completed))

                progress_id = cur.fetchone()['progress_id']

                # Обновляем текущий уровень пользователя
                if completed:
                    cur.execute("""
                        UPDATE users
                        SET current_level = GREATEST(current_level, %s)
                        WHERE user_id = %s
                    """, (level_id + 1, user_id))

                conn.commit()
                return {'success': True, 'progress_id': progress_id}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            self.release_connection(conn)

    # ==========================================
    # МЕТОДЫ ДЛЯ ЛИДЕРБОРДА
    # ==========================================

    def get_leaderboard(self, level_id=None, limit=10):
        """Получить лидерборд (общий или по уровню)"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if level_id:
                    # Лидерборд по конкретному уровню
                    cur.execute("""
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY score DESC, time_spent ASC) as rank,
                            username,
                            score,
                            time_spent
                        FROM leaderboard
                        WHERE level_id = %s
                        ORDER BY score DESC, time_spent ASC
                        LIMIT %s
                    """, (level_id, limit))
                else:
                    # Общий лидерборд
                    cur.execute("""
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank,
                            username,
                            total_score,
                            current_level
                        FROM users
                        WHERE banned = FALSE
                        ORDER BY total_score DESC
                        LIMIT %s
                    """, (limit,))

                return [dict(row) for row in cur.fetchall()]
        finally:
            self.release_connection(conn)

    def get_user_rank(self, user_id):
        """Получить ранг пользователя в общем лидерборде"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    WITH ranked_users AS (
                        SELECT 
                            user_id,
                            ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank
                        FROM users
                        WHERE banned = FALSE
                    )
                    SELECT rank FROM ranked_users WHERE user_id = %s
                """, (user_id,))

                result = cur.fetchone()
                return result['rank'] if result else None
        finally:
            self.release_connection(conn)

    # ==========================================
    # МЕТОДЫ ДЛЯ ДОСТИЖЕНИЙ
    # ==========================================

    def get_achievements(self):
        """Получить все достижения"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT achievement_id, title, description, icon, points
                    FROM achievements
                    ORDER BY points ASC
                """)
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.release_connection(conn)

    def get_user_achievements(self, user_id):
        """Получить достижения пользователя"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        a.achievement_id,
                        a.title,
                        a.description,
                        a.icon,
                        a.points,
                        ua.earned_at
                    FROM achievements a
                    JOIN user_achievements ua ON a.achievement_id = ua.achievement_id
                    WHERE ua.user_id = %s
                    ORDER BY ua.earned_at DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.release_connection(conn)

    def unlock_achievement(self, user_id, achievement_id):
        """Разблокировать достижение для пользователя"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_achievements (user_id, achievement_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, achievement_id) DO NOTHING
                    RETURNING user_achievement_id
                """, (user_id, achievement_id))

                result = cur.fetchone()
                conn.commit()
                return result is not None  # True если достижение только что разблокировано
        except Exception as e:
            conn.rollback()
            print(f"Error unlocking achievement: {e}")
            return False
        finally:
            self.release_connection(conn)

    def check_achievements(self, user_id):
        """Проверить и разблокировать достижения для пользователя"""
        conn = self.get_connection()
        newly_unlocked = []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Получаем статистику пользователя
                cur.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE completed = TRUE AND level_id = 1) as level1_completed,
                        COUNT(*) FILTER (WHERE completed = TRUE AND level_id = 3) as level3_completed,
                        COUNT(*) FILTER (WHERE completed = TRUE) as total_completed,
                        MIN(time_spent) FILTER (WHERE completed = TRUE) as best_time
                    FROM user_progress
                    WHERE user_id = %s
                """, (user_id,))

                stats = cur.fetchone()

                # Достижение 1: Завершить уровень 1
                if stats['level1_completed'] > 0:
                    if self.unlock_achievement(user_id, 1):
                        newly_unlocked.append(1)

                # Достижение 5: Завершить уровень 3
                if stats['level3_completed'] > 0:
                    if self.unlock_achievement(user_id, 5):
                        newly_unlocked.append(5)

                # Достижение 4: Speed Runner (меньше 60 секунд)
                if stats['best_time'] and stats['best_time'] < 60:
                    if self.unlock_achievement(user_id, 4):
                        newly_unlocked.append(4)

                # Достижение 7: Completionist (все уровни)
                if stats['total_completed'] >= 3:
                    if self.unlock_achievement(user_id, 7):
                        newly_unlocked.append(7)

        finally:
            self.release_connection(conn)

        return newly_unlocked



    def delete_inactive_accounts(self):
        """Удалить неактивные аккаунты (старше 7 дней)"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT delete_inactive_accounts()")
                deleted_count = cur.fetchone()[0]
                conn.commit()
                return deleted_count
        finally:
            self.release_connection(conn)

    def create_backup(self, backup_type='full'):
        """Создать резервную копию"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT create_backup(%s)", (backup_type,))
                backup_id = cur.fetchone()[0]
                conn.commit()
                return backup_id
        finally:
            self.release_connection(conn)



    def calculate_score(self, turtles_killed, spike_turtles_killed, time_spent, max_time=300):

        # Базовые очки
        turtle_score = turtles_killed * 200
        spike_turtle_score = spike_turtles_killed * 500

        # Бонус за время (чем быстрее, тем больше бонус)
        if time_spent < max_time:
            time_bonus = int((max_time - time_spent) / max_time * 500)
        else:
            time_bonus = 0

        total_score = turtle_score + spike_turtle_score + time_bonus

        return {
            'total_score': total_score,
            'breakdown': {
                'turtles': turtle_score,
                'spike_turtles': spike_turtle_score,
                'time_bonus': time_bonus
            }
        }


# Пример использования
if __name__ == "__main__":
    # Инициализация
    db = DatabaseManager()

    # Регистрация
    result = db.register_user("test_player", "password123")
    print("Register:", result)

    # Авторизация
    result = db.login_user("test_player", "password123")
    print("Login:", result)

    if result['success']:
        user_id = result['user']['user_id']

        # Сохранение прогресса
        score_data = db.calculate_score(turtles_killed=3, spike_turtles_killed=0, time_spent=95)
        db.save_level_progress(user_id, 1, score_data['total_score'], 95, 3, completed=True)

        # Проверка достижений
        achievements = db.check_achievements(user_id)
        print("New achievements:", achievements)

        # Получение статистики
        stats = db.get_user_stats(user_id)
        print("Stats:", stats)

        # Лидерборд
        leaderboard = db.get_leaderboard(limit=5)
        print("Leaderboard:", leaderboard)

    # Закрытие соединений
    db.close_all_connections()