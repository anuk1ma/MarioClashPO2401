"""
Animated Auth Screen для Mario Clash
Красивый экран авторизации в пиксель-арт стиле
"""

import pygame
import sys
import math
from database_manager import DatabaseManager
from pixel_art_system import PixelArtSprite, AnimatedBackground, ParticleEffect


class AnimatedButton:
    """Анимированная кнопка"""

    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.Font(None, 36)
        self.hover_scale = 1.0
        self.target_scale = 1.0
        self.pulse = 0

    def update(self, mouse_pos):
        """Обновление анимации"""
        if self.rect.collidepoint(mouse_pos):
            self.target_scale = 1.1
            self.current_color = self.hover_color
        else:
            self.target_scale = 1.0
            self.current_color = self.color

        # Плавная анимация масштаба
        self.hover_scale += (self.target_scale - self.hover_scale) * 0.2
        self.pulse += 0.1

    def draw(self, screen):
        """Отрисовка кнопки"""
        # Вычисляем новый rect с учётом масштаба
        scaled_width = int(self.rect.width * self.hover_scale)
        scaled_height = int(self.rect.height * self.hover_scale)
        scaled_x = self.rect.centerx - scaled_width // 2
        scaled_y = self.rect.centery - scaled_height // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)

        # Тень
        shadow_rect = scaled_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, 0, 15)

        # Основная кнопка
        pygame.draw.rect(screen, self.current_color, scaled_rect, 0, 15)

        # Рамка с пульсацией
        pulse_width = 3 + int(math.sin(self.pulse) * 1)
        border_color = tuple(min(255, c + 30) for c in self.current_color)
        pygame.draw.rect(screen, border_color, scaled_rect, pulse_width, 15)

        # Текст
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, event):
        """Проверка клика"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class InputField:
    """Поле ввода с анимацией"""

    def __init__(self, x, y, width, height, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.text = ""
        self.active = False
        self.font = pygame.font.Font(None, 32)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.shake_offset = 0
        self.shake_time = 0

    def handle_event(self, event):
        """Обработка событий"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True
            elif len(self.text) < 20:
                self.text += event.unicode

        return False

    def shake(self):
        """Эффект тряски при ошибке"""
        self.shake_time = 20

    def update(self):
        """Обновление анимации"""
        # Курсор мигает
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

        # Тряска при ошибке
        if self.shake_time > 0:
            self.shake_time -= 1
            self.shake_offset = int(math.sin(self.shake_time * 0.5) * (self.shake_time * 0.3))
        else:
            self.shake_offset = 0

    def draw(self, screen):
        """Отрисовка поля"""
        # Применяем смещение тряски
        draw_rect = self.rect.copy()
        draw_rect.x += self.shake_offset

        # Фон
        color = (255, 255, 255) if self.active else (240, 240, 240)
        pygame.draw.rect(screen, color, draw_rect, 0, 10)

        # Рамка
        border_color = (50, 150, 255) if self.active else (180, 180, 180)
        border_width = 3 if self.active else 2
        pygame.draw.rect(screen, border_color, draw_rect, border_width, 10)

        # Текст или placeholder
        if self.text:
            text_surface = self.font.render(self.text, True, (0, 0, 0))
        else:
            text_surface = self.font.render(self.placeholder, True, (150, 150, 150))

        text_rect = text_surface.get_rect(midleft=(draw_rect.left + 15, draw_rect.centery))
        screen.blit(text_surface, text_rect)

        # Курсор
        if self.active and self.cursor_visible and self.text:
            cursor_x = text_rect.right + 2
            pygame.draw.line(screen, (0, 0, 0),
                           (cursor_x, draw_rect.centery - 12),
                           (cursor_x, draw_rect.centery + 12), 2)


class FloatingMario:
    """Плавающий спрайт Марио для украшения"""

    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.base_y = y
        self.size = size
        self.sprite = PixelArtSprite.create_mario_sprite(size)
        self.float_offset = 0
        self.float_speed = 0.05

    def update(self):
        """Обновление позиции"""
        self.float_offset += self.float_speed
        self.y = self.base_y + math.sin(self.float_offset) * 15

    def draw(self, screen):
        """Отрисовка"""
        screen.blit(self.sprite, (int(self.x), int(self.y)))


class AuthScreen:
    """Красивый экран авторизации"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1000, 700))
        pygame.display.set_caption("Mario Clash - Login")
        self.clock = pygame.time.Clock()

        # База данных
        try:
            self.db = DatabaseManager()
        except:
            print("Running without database")
            self.db = None

        # Фон
        self.background = AnimatedBackground(1000, 700)

        # Анимированный Марио
        self.mario = FloatingMario(50, 200, 100)

        # Поля ввода
        self.username_field = InputField(350, 300, 300, 50, "Username")
        self.password_field = InputField(350, 370, 300, 50, "Password")

        # Кнопки
        self.login_button = AnimatedButton(350, 450, 140, 50, "Login", (46, 204, 113), (39, 174, 96))
        self.register_button = AnimatedButton(510, 450, 140, 50, "Register", (52, 152, 219), (41, 128, 185))

        # Заголовок
        self.title_font = pygame.font.Font(None, 80)
        self.message_font = pygame.font.Font(None, 28)

        # Сообщение об ошибке/успехе
        self.message = ""
        self.message_color = (255, 0, 0)
        self.message_timer = 0

        # Частицы
        self.particles = []

        # Анимация заголовка
        self.title_bounce = 0

    def show_message(self, text, is_error=True):
        """Показать сообщение"""
        self.message = text
        self.message_color = (231, 76, 60) if is_error else (46, 204, 113)
        self.message_timer = 180  # 3 секунды

        if is_error:
            self.username_field.shake()
            self.password_field.shake()

    def handle_login(self):
        """Обработка входа"""
        if not self.db:
            self.show_message("Database not available", True)
            return None

        username = self.username_field.text
        password = self.password_field.text

        if not username or not password:
            self.show_message("Please fill all fields", True)
            return None

        result = self.db.login_user(username, password)

        if result['success']:
            # Успех - создаём эффект частиц
            for _ in range(30):
                self.particles.append(ParticleEffect(500, 400, (46, 204, 113), 10))

            self.show_message("Login successful!", False)
            pygame.time.wait(500)
            return result['user']
        else:
            self.show_message(result.get('error', 'Login failed'), True)
            return None

    def handle_register(self):
        """Обработка регистрации"""
        if not self.db:
            self.show_message("Database not available", True)
            return

        username = self.username_field.text
        password = self.password_field.text

        if not username or not password:
            self.show_message("Please fill all fields", True)
            return

        if len(password) < 4:
            self.show_message("Password too short (min 4 chars)", True)
            return

        result = self.db.register_user(username, password)

        if result['success']:
            self.show_message("Registration successful! Please login.", False)
            self.password_field.text = ""
        else:
            self.show_message(result.get('error', 'Registration failed'), True)

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

                # Поля ввода
                if self.username_field.handle_event(event):
                    # Enter в поле username - переход к password
                    self.password_field.active = True
                    self.username_field.active = False

                if self.password_field.handle_event(event):
                    # Enter в поле password - попытка входа
                    user = self.handle_login()
                    if user:
                        return user

                # Кнопки
                if self.login_button.is_clicked(event):
                    user = self.handle_login()
                    if user:
                        return user

                if self.register_button.is_clicked(event):
                    self.handle_register()

            # Обновление
            self.background.update()
            self.mario.update()
            self.username_field.update()
            self.password_field.update()
            self.login_button.update(mouse_pos)
            self.register_button.update(mouse_pos)

            # Анимация заголовка
            self.title_bounce += 0.05

            # Частицы
            for p in self.particles[:]:
                p.update()
                if not p.is_alive():
                    self.particles.remove(p)

            # Сообщение
            if self.message_timer > 0:
                self.message_timer -= 1

            # Отрисовка
            self.background.draw(self.screen)

            # Марио
            self.mario.draw(self.screen)

            # Заголовок с анимацией
            title_y = 150 + math.sin(self.title_bounce) * 10
            title_text = self.title_font.render("MARIO CLASH", True, (220, 20, 20))
            title_shadow = self.title_font.render("MARIO CLASH", True, (100, 0, 0))

            title_rect = title_text.get_rect(center=(500, title_y))
            shadow_rect = title_shadow.get_rect(center=(503, title_y + 3))

            self.screen.blit(title_shadow, shadow_rect)
            self.screen.blit(title_text, title_rect)

            # Панель авторизации
            panel_rect = pygame.Rect(300, 250, 400, 300)
            panel_surf = pygame.Surface((400, 300), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (255, 255, 255, 230), (0, 0, 400, 300), 0, 20)
            pygame.draw.rect(panel_surf, (100, 100, 100), (0, 0, 400, 300), 3, 20)
            self.screen.blit(panel_surf, panel_rect.topleft)

            # Поля и кнопки
            self.username_field.draw(self.screen)
            self.password_field.draw(self.screen)
            self.login_button.draw(self.screen)
            self.register_button.draw(self.screen)

            # Сообщение
            if self.message_timer > 0:
                message_surf = self.message_font.render(self.message, True, self.message_color)
                message_rect = message_surf.get_rect(center=(500, 250))

                # Фон для сообщения
                bg_rect = message_rect.inflate(20, 10)
                pygame.draw.rect(self.screen, (255, 255, 255, 200), bg_rect, 0, 10)
                pygame.draw.rect(self.screen, self.message_color, bg_rect, 2, 10)

                self.screen.blit(message_surf, message_rect)

            # Частицы
            for p in self.particles:
                p.draw(self.screen)

            # Подсказка
            hint_text = self.message_font.render("Press ESC to exit", True, (100, 100, 100))
            self.screen.blit(hint_text, (10, 670))

            pygame.display.flip()
            self.clock.tick(60)

        return None


# Тест
if __name__ == "__main__":
    auth = AuthScreen()
    user = auth.run()

    if user:
        print(f"Logged in as: {user.get('username')}")
    else:
        print("Login cancelled")

    pygame.quit()