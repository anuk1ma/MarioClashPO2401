"""
Pixel Art Main Menu для Mario Clash
Красивое главное меню в стиле пиксель-арт
"""

import pygame
import sys
import math
import time
from database_manager import DatabaseManager
from pixel_art_system import PixelArtSprite, AnimatedBackground, ParticleEffect


class PixelButton:
    """Пиксельная кнопка в стиле Mario"""

    def __init__(self, x, y, width, height, text, color_scheme='green'):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hover_scale = 1.0
        self.target_scale = 1.0
        self.bounce = 0

        # Цветовые схемы
        schemes = {
            'green': {
                'main': (46, 204, 113),
                'dark': (39, 174, 96),
                'light': (80, 230, 140)
            },
            'blue': {
                'main': (52, 152, 219),
                'dark': (41, 128, 185),
                'light': (100, 180, 255)
            },
            'red': {
                'main': (231, 76, 60),
                'dark': (192, 57, 43),
                'light': (255, 120, 100)
            },
            'orange': {
                'main': (243, 156, 18),
                'dark': (211, 132, 15),
                'light': (255, 180, 60)
            }
        }

        self.colors = schemes.get(color_scheme, schemes['green'])
        self.font = pygame.font.Font(None, 48)

    def update(self, mouse_pos):
        """Обновление анимации"""
        if self.rect.collidepoint(mouse_pos):
            self.target_scale = 1.05
        else:
            self.target_scale = 1.0

        self.hover_scale += (self.target_scale - self.hover_scale) * 0.15
        self.bounce += 0.08

    def draw(self, screen):
        """Отрисовка кнопки"""
        # Вычисляем размер с анимацией
        scaled_width = int(self.rect.width * self.hover_scale)
        scaled_height = int(self.rect.height * self.hover_scale)
        scaled_x = self.rect.centerx - scaled_width // 2
        scaled_y = self.rect.centery - scaled_height // 2

        # Небольшой bounce эффект при hover
        if self.hover_scale > 1.01:
            scaled_y += int(math.sin(self.bounce * 3) * 3)

        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)

        # Тень (3D эффект)
        shadow_offset = 6
        shadow_rect = scaled_rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, 0, 15)

        # Тёмная основа (3D край)
        dark_rect = scaled_rect.copy()
        dark_rect.y += 4
        pygame.draw.rect(screen, self.colors['dark'], dark_rect, 0, 15)

        # Основная кнопка
        pygame.draw.rect(screen, self.colors['main'], scaled_rect, 0, 15)

        # Световой блик сверху
        highlight_rect = pygame.Rect(scaled_rect.x + 10, scaled_rect.y + 8,
                                     scaled_rect.width - 20, scaled_rect.height // 3)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (*self.colors['light'], 80),
                        (0, 0, highlight_rect.width, highlight_rect.height), 0, 10)
        screen.blit(highlight_surf, highlight_rect)

        # Рамка
        pygame.draw.rect(screen, self.colors['dark'], scaled_rect, 4, 15)

        # Текст с тенью
        text_shadow = self.font.render(self.text, True, (50, 50, 50))
        text_surface = self.font.render(self.text, True, (255, 255, 255))

        text_rect = text_surface.get_rect(center=scaled_rect.center)
        shadow_rect = text_shadow.get_rect(center=(scaled_rect.centerx + 2, scaled_rect.centery + 2))

        screen.blit(text_shadow, shadow_rect)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, event):
        """Проверка клика"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self.rect.collidepoint(event.pos)
        return False


class UserCard:
    """Карточка пользователя"""

    def __init__(self, x, y, width, height, user, is_selected=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.user = user
        self.is_selected = is_selected
        self.hover = False
        self.font_name = pygame.font.Font(None, 32)
        self.font_info = pygame.font.Font(None, 24)

    def update(self, mouse_pos):
        """Обновление"""
        self.hover = self.rect.collidepoint(mouse_pos)

    def draw(self, screen):
        """Отрисовка"""
        # Цвет фона
        if self.is_selected:
            bg_color = (255, 235, 100)
            border_color = (243, 156, 18)
        elif self.hover:
            bg_color = (240, 240, 255)
            border_color = (52, 152, 219)
        else:
            bg_color = (250, 250, 250)
            border_color = (200, 200, 200)

        # Фон
        pygame.draw.rect(screen, bg_color, self.rect, 0, 10)
        pygame.draw.rect(screen, border_color, self.rect, 3, 10)

        # Иконка роли
        icon = "👑" if self.user['role'] == 'admin' else "👤"
        icon_text = self.font_name.render(icon, True, (0, 0, 0))
        screen.blit(icon_text, (self.rect.x + 15, self.rect.y + 10))

        # Имя
        name_color = (243, 156, 18) if self.user['role'] == 'admin' else (52, 73, 94)
        name_text = self.font_name.render(self.user['username'][:15], True, name_color)
        screen.blit(name_text, (self.rect.x + 60, self.rect.y + 12))

        # Очки
        score_text = self.font_info.render(f"Счёт: {self.user.get('total_score', 0)}", True, (100, 100, 100))
        screen.blit(score_text, (self.rect.x + 60, self.rect.y + 42))

        # Статус бана
        if self.user.get('banned', False):
            ban_text = self.font_info.render("🚫 ЗАБАНЕН", True, (231, 76, 60))
            screen.blit(ban_text, (self.rect.right - 150, self.rect.centery - 10))


class MainMenuPixelArt:
    """Главное меню в пиксель-арт стиле"""

    def __init__(self, user_data, db_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((1400, 800))
        pygame.display.set_caption("Mario Clash - Main Menu")
        self.clock = pygame.time.Clock()

        self.user_data = user_data
        self.db = db_manager
        self.is_admin = user_data['role'] == 'admin'

        # Шрифты
        self.font_title = pygame.font.Font(None, 96)
        self.font_subtitle = pygame.font.Font(None, 36)
        self.font_info = pygame.font.Font(None, 28)

        # Анимированный фон
        self.background = AnimatedBackground(1400, 800)

        # Плавающий Марио
        self.mario_sprite = PixelArtSprite.create_mario_sprite(120)
        self.mario_y = 250
        self.mario_float = 0

        # Врагики для украшения
        self.decorations = []
        self.decorations.append({
            'sprite': PixelArtSprite.create_turtle_sprite(60, True),
            'x': 1250, 'y': 600, 'base_y': 600, 'offset': 0, 'speed': 0.03
        })
        self.decorations.append({
            'sprite': PixelArtSprite.create_ghost_sprite(60),
            'x': 1280, 'y': 150, 'base_y': 150, 'offset': 1.5, 'speed': 0.04
        })

        # Кнопки
        self.create_buttons()

        # Данные
        self.leaderboard = []
        self.all_users = []
        self.selected_user = None
        self.scroll_offset = 0

        # Частицы
        self.particles = []

        # Анимация заголовка
        self.title_wave = 0

        self.load_data()

    def create_buttons(self):
        """Создание кнопок"""
        # Главная кнопка ИГРАТЬ
        self.play_button = PixelButton(580, 450, 240, 70, "ИГРАТЬ", 'green')

        # Кнопка выхода
        self.logout_button = PixelButton(580, 540, 240, 60, "Выход", 'red')

        # Админские кнопки
        if self.is_admin:
            self.ban_button = PixelButton(1050, 400, 180, 50, "Ban", 'red')
            self.unban_button = PixelButton(1050, 460, 180, 50, "Unban", 'green')
            self.reset_button = PixelButton(1050, 520, 180, 50, "Reset", 'orange')
            self.delete_button = PixelButton(1050, 580, 180, 50, "Delete", 'red')
            self.refresh_button = PixelButton(1050, 650, 180, 50, "Refresh", 'blue')

    def load_data(self):
        """Загрузка данных"""
        self.leaderboard = self.db.get_leaderboard(limit=8)

        if self.is_admin:
            conn = self.db.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, username, role, total_score, current_level, banned
                        FROM users
                        ORDER BY total_score DESC
                    """)
                    rows = cur.fetchall()
                    self.all_users = [
                        {
                            'user_id': r[0], 'username': r[1], 'role': r[2],
                            'total_score': r[3], 'current_level': r[4], 'banned': r[5]
                        }
                        for r in rows
                    ]
            finally:
                self.db.release_connection(conn)

    def draw_title(self):
        """Анимированный заголовок"""
        self.title_wave += 0.1

        # MARIO
        mario_text = "MARIO"
        x_offset = 400
        for i, char in enumerate(mario_text):
            y_offset = math.sin(self.title_wave + i * 0.5) * 15

            # Тень
            shadow = self.font_title.render(char, True, (100, 0, 0))
            shadow_rect = shadow.get_rect(center=(x_offset + i * 80 + 3, 100 + y_offset + 3))
            self.screen.blit(shadow, shadow_rect)

            # Буква
            letter = self.font_title.render(char, True, (220, 20, 20))
            letter_rect = letter.get_rect(center=(x_offset + i * 80, 100 + y_offset))
            self.screen.blit(letter, letter_rect)

        # CLASH
        clash_text = "CLASH"
        x_offset = 780
        for i, char in enumerate(clash_text):
            y_offset = math.sin(self.title_wave + i * 0.5 + 2) * 15

            # Тень
            shadow = self.font_title.render(char, True, (0, 50, 100))
            shadow_rect = shadow.get_rect(center=(x_offset + i * 70 + 3, 100 + y_offset + 3))
            self.screen.blit(shadow, shadow_rect)

            # Буква
            letter = self.font_title.render(char, True, (52, 152, 219))
            letter_rect = letter.get_rect(center=(x_offset + i * 70, 100 + y_offset))
            self.screen.blit(letter, letter_rect)

    def draw_user_panel(self):
        """Панель приветствия пользователя"""
        # Фон панели
        panel_rect = pygame.Rect(400, 200, 600, 220)
        panel_surf = pygame.Surface((600, 220), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (255, 255, 255, 230), (0, 0, 600, 220), 0, 20)
        pygame.draw.rect(panel_surf, (52, 152, 219), (0, 0, 600, 220), 4, 20)
        self.screen.blit(panel_surf, panel_rect.topleft)

        # Приветствие
        welcome = self.font_subtitle.render(f"Привет, {self.user_data['username']}!", True, (52, 73, 94))
        welcome_rect = welcome.get_rect(center=(700, 240))
        self.screen.blit(welcome, welcome_rect)

        # Статистика
        stats = self.db.get_user_stats(self.user_data['user_id'])

        info_lines = [
            f"Текущий уровень: {stats['current_level']}",
            f"Общий счёт: {stats['total_score']}",
            f"Достижений: {stats['achievements_count']}"
        ]

        y = 290
        for line in info_lines:
            text = self.font_info.render(line, True, (100, 100, 100))
            text_rect = text.get_rect(center=(700, y))
            self.screen.blit(text, text_rect)
            y += 35

        # Админ бейдж
        if self.is_admin:
            admin_text = self.font_info.render("ADMIN", True, (243, 156, 18))
            admin_rect = admin_text.get_rect(center=(700, 390))
            self.screen.blit(admin_text, admin_rect)

    def draw_leaderboard(self):
        """Лидерборд слева"""
        # Заголовок
        title = self.font_subtitle.render("TOP 8", True, (243, 156, 18))
        self.screen.blit(title, (50, 200))

        # Панель
        panel_rect = pygame.Rect(40, 250, 300, 500)
        panel_surf = pygame.Surface((300, 500), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (255, 255, 255, 230), (0, 0, 300, 500), 0, 15)
        pygame.draw.rect(panel_surf, (243, 156, 18), (0, 0, 300, 500), 3, 15)
        self.screen.blit(panel_surf, panel_rect.topleft)

        # Список
        font_rank = pygame.font.Font(None, 28)
        y = 265

        for i, player in enumerate(self.leaderboard[:8], 1):
            # Медали
            if i == 1:
                medal = "🥇"
                color = (243, 156, 18)
            elif i == 2:
                medal = "🥈"
                color = (149, 165, 166)
            elif i == 3:
                medal = "🥉"
                color = (205, 127, 50)
            else:
                medal = f"{i}."
                color = (52, 73, 94)

            # Подсветка текущего игрока
            if player['username'] == self.user_data['username']:
                highlight = pygame.Rect(45, y - 3, 290, 32)
                pygame.draw.rect(self.screen, (255, 235, 100, 200), highlight, 0, 8)

            # Ранг и имя
            rank_text = font_rank.render(f"{medal} {player['username'][:12]}", True, color)
            self.screen.blit(rank_text, (55, y))

            # Счёт
            score_text = font_rank.render(f"{player['total_score']}", True, (100, 100, 100))
            score_rect = score_text.get_rect(right=330, centery=y + 10)
            self.screen.blit(score_text, score_rect)

            y += 60

    def draw_admin_panel(self):
        """Админ-панель справа"""
        if not self.is_admin:
            return

        # Заголовок
        title = self.font_subtitle.render("ADMIN", True, (231, 76, 60))
        self.screen.blit(title, (1050, 200))

        # Панель пользователей
        panel_rect = pygame.Rect(1040, 250, 340, 130)
        panel_surf = pygame.Surface((340, 130), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (255, 255, 255, 230), (0, 0, 340, 130), 0, 15)
        pygame.draw.rect(panel_surf, (231, 76, 60), (0, 0, 340, 130), 3, 15)
        self.screen.blit(panel_surf, panel_rect.topleft)

        # Список пользователей
        font_small = pygame.font.Font(None, 22)
        y = 260
        max_visible = 3

        for user in self.all_users[self.scroll_offset:self.scroll_offset + max_visible]:
            user_rect = pygame.Rect(1050, y, 320, 35)

            # Выделение
            if self.selected_user and user['user_id'] == self.selected_user['user_id']:
                pygame.draw.rect(self.screen, (255, 235, 100), user_rect, 0, 5)
            elif user_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (240, 240, 255), user_rect, 0, 5)

            # Иконка
            icon = "👑" if user['role'] == 'admin' else ("" if user['banned'] else "👤")
            icon_text = font_small.render(icon, True, (0, 0, 0))
            self.screen.blit(icon_text, (1055, y + 7))

            # Имя
            color = (231, 76, 60) if user['banned'] else (52, 73, 94)
            name = font_small.render(user['username'][:18], True, color)
            self.screen.blit(name, (1085, y + 8))

            # Счёт
            score = font_small.render(str(user['total_score']), True, (100, 100, 100))
            score_rect = score.get_rect(right=1360, centery=y + 17)
            self.screen.blit(score, score_rect)

            y += 38

        # Кнопки
        self.ban_button.draw(self.screen)
        self.unban_button.draw(self.screen)
        self.reset_button.draw(self.screen)
        self.delete_button.draw(self.screen)
        self.refresh_button.draw(self.screen)

    def handle_admin_action(self, action):
        """Обработка админ-действий"""
        if not self.selected_user:
            return

        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                if action == 'ban':
                    cur.execute("UPDATE users SET banned = TRUE WHERE user_id = %s",
                              (self.selected_user['user_id'],))
                elif action == 'unban':
                    cur.execute("UPDATE users SET banned = FALSE WHERE user_id = %s",
                              (self.selected_user['user_id'],))
                elif action == 'reset':
                    cur.execute("DELETE FROM user_progress WHERE user_id = %s",
                              (self.selected_user['user_id'],))
                    cur.execute("UPDATE users SET total_score = 0, current_level = 1 WHERE user_id = %s",
                              (self.selected_user['user_id'],))
                elif action == 'delete':
                    if self.selected_user['user_id'] != self.user_data['user_id']:
                        cur.execute("DELETE FROM users WHERE user_id = %s",
                                  (self.selected_user['user_id'],))
                        self.selected_user = None

                conn.commit()
                # Частицы
                self.particles.append(ParticleEffect(700, 400, (46, 204, 113), 20))
        finally:
            self.db.release_connection(conn)

        self.load_data()

    def run(self):
        """Главный цикл"""
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None

                # Скроллинг админ-панели
                if self.is_admin and event.type == pygame.MOUSEWHEEL:
                    if 1040 < mouse_pos[0] < 1380 and 250 < mouse_pos[1] < 380:
                        self.scroll_offset = max(0, min(
                            len(self.all_users) - 3,
                            self.scroll_offset - event.y
                        ))

                # Выбор пользователя
                if self.is_admin and event.type == pygame.MOUSEBUTTONDOWN:
                    if 1050 < mouse_pos[0] < 1370 and 260 < mouse_pos[1] < 370:
                        idx = (mouse_pos[1] - 260) // 38 + self.scroll_offset
                        if 0 <= idx < len(self.all_users):
                            self.selected_user = self.all_users[idx]

                # Кнопки
                if self.play_button.is_clicked(event):
                    # Эффект
                    for _ in range(3):
                        self.particles.append(ParticleEffect(700, 485, (46, 204, 113), 15))
                    pygame.time.wait(200)
                    return 'play'

                if self.logout_button.is_clicked(event):
                    return None

                # Админ-кнопки
                if self.is_admin:
                    if self.ban_button.is_clicked(event) and self.selected_user and not self.selected_user['banned']:
                        self.handle_admin_action('ban')
                    if self.unban_button.is_clicked(event) and self.selected_user and self.selected_user['banned']:
                        self.handle_admin_action('unban')
                    if self.reset_button.is_clicked(event) and self.selected_user:
                        self.handle_admin_action('reset')
                    if self.delete_button.is_clicked(event) and self.selected_user:
                        if self.selected_user['user_id'] != self.user_data['user_id']:
                            self.handle_admin_action('delete')
                    if self.refresh_button.is_clicked(event):
                        self.load_data()
                        self.particles.append(ParticleEffect(1140, 675, (52, 152, 219), 15))

            # Обновление
            self.background.update()
            self.play_button.update(mouse_pos)
            self.logout_button.update(mouse_pos)

            if self.is_admin:
                self.ban_button.update(mouse_pos)
                self.unban_button.update(mouse_pos)
                self.reset_button.update(mouse_pos)
                self.delete_button.update(mouse_pos)
                self.refresh_button.update(mouse_pos)

            # Плавающий Марио
            self.mario_float += 0.05
            self.mario_y = 250 + math.sin(self.mario_float) * 20

            # Декорации
            for deco in self.decorations:
                deco['offset'] += deco['speed']
                deco['y'] = deco['base_y'] + math.sin(deco['offset']) * 15

            # Частицы
            for p in self.particles[:]:
                p.update()
                if not p.is_alive():
                    self.particles.remove(p)

            # Отрисовка
            self.background.draw(self.screen)

            # Марио
            self.screen.blit(self.mario_sprite, (100, int(self.mario_y)))

            # Декорации
            for deco in self.decorations:
                self.screen.blit(deco['sprite'], (deco['x'], int(deco['y'])))

            # UI
            self.draw_title()
            self.draw_user_panel()
            self.draw_leaderboard()

            if self.is_admin:
                self.draw_admin_panel()

            # Кнопки
            self.play_button.draw(self.screen)
            self.logout_button.draw(self.screen)

            # Частицы
            for p in self.particles:
                p.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

        return None


if __name__ == "__main__":
    # Тест
    from auth_screen import AuthScreen

    auth = AuthScreen()
    user = auth.run()

    if user:
        db = DatabaseManager()
        menu = MainMenuPixelArt(user, db)
        result = menu.run()

        if result == 'play':
            print("Starting game...")

        db.close_all_connections()

    pygame.quit()