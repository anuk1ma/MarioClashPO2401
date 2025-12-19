"""
Achievement Notification System
Система всплывающих уведомлений о достижениях
"""

import pygame
import time


class AchievementNotification:
    """Всплывающее уведомление о получении достижения"""

    def __init__(self, achievement_name, achievement_description, icon="🏆"):
        self.name = achievement_name
        self.description = achievement_description
        self.icon = icon

        # Параметры анимации
        self.width = 400
        self.height = 100
        self.target_y = 20  # Конечная позиция
        self.current_y = -self.height  # Начальная позиция (за экраном)

        # Время жизни уведомления
        self.created_at = time.time()
        self.display_duration = 4.0  # Показывать 4 секунды
        self.fade_duration = 0.5  # Плавное исчезновение 0.5 сек

        # Анимация появления
        self.slide_speed = 8  # Скорость выезда
        self.is_sliding_in = True
        self.is_sliding_out = False

        # Цвета (БЕЗ альфа-канала!)
        self.bg_color = (46, 204, 113)  # Зелёный
        self.bg_dark = (39, 174, 96)
        self.text_color = (255, 255, 255)

        # Шрифты
        self.font_title = pygame.font.Font(None, 32)
        self.font_desc = pygame.font.Font(None, 24)
        self.font_icon = pygame.font.Font(None, 48)

    def update(self, screen_width):
        """Обновление позиции уведомления"""
        elapsed = time.time() - self.created_at

        # Анимация появления
        if self.is_sliding_in:
            self.current_y += self.slide_speed
            if self.current_y >= self.target_y:
                self.current_y = self.target_y
                self.is_sliding_in = False

        # Начало исчезновения
        elif elapsed > self.display_duration - self.fade_duration:
            if not self.is_sliding_out:
                self.is_sliding_out = True

        # Анимация исчезновения
        if self.is_sliding_out:
            self.current_y -= self.slide_speed

        # Позиция X (по центру экрана)
        self.x = (screen_width - self.width) // 2

        return elapsed < self.display_duration

    def draw(self, screen):
        """Отрисовка уведомления"""
        # Прозрачность для анимации исчезновения
        elapsed = time.time() - self.created_at
        alpha = 255

        if elapsed > self.display_duration - self.fade_duration:
            fade_progress = (self.display_duration - elapsed) / self.fade_duration
            alpha = int(255 * max(0, fade_progress))

        # Создание поверхности с альфа-каналом
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Тень (отдельная поверхность)
        shadow_surf = pygame.Surface((self.width + 8, self.height + 8), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(4, 4, self.width, self.height)
        shadow_color = (0, 0, 0, min(255, alpha // 3))
        pygame.draw.rect(shadow_surf, shadow_color, shadow_rect, 0, 15)
        screen.blit(shadow_surf, (self.x - 4, int(self.current_y) - 4))

        # Основной фон
        main_rect = pygame.Rect(0, 0, self.width, self.height)
        bg_color = (*self.bg_color, alpha)
        pygame.draw.rect(surface, bg_color, main_rect, 0, 15)

        # Тёмная рамка
        border_color = (*self.bg_dark, alpha)
        pygame.draw.rect(surface, border_color, main_rect, 3, 15)

        # Текст (применяем альфа через set_alpha)
        if alpha < 255:
            # Иконка
            icon_surface = self.font_icon.render(self.icon, True, self.text_color)
            icon_surface.set_alpha(alpha)
            surface.blit(icon_surface, (20, 25))

            # Заголовок
            title_surface = self.font_title.render("ДОСТИЖЕНИЕ!", True, self.text_color)
            title_surface.set_alpha(alpha)
            surface.blit(title_surface, (80, 15))

            # Название
            name_surface = self.font_title.render(self.name, True, self.text_color)
            name_surface.set_alpha(alpha)
            surface.blit(name_surface, (80, 40))

            # Описание
            desc_surface = self.font_desc.render(self.description, True, self.text_color)
            desc_surface.set_alpha(alpha)
            surface.blit(desc_surface, (80, 68))
        else:
            # Полная непрозрачность - без set_alpha (быстрее)
            icon_surface = self.font_icon.render(self.icon, True, self.text_color)
            surface.blit(icon_surface, (20, 25))

            title_surface = self.font_title.render("ДОСТИЖЕНИЕ!", True, self.text_color)
            surface.blit(title_surface, (80, 15))

            name_surface = self.font_title.render(self.name, True, self.text_color)
            surface.blit(name_surface, (80, 40))

            desc_surface = self.font_desc.render(self.description, True, self.text_color)
            surface.blit(desc_surface, (80, 68))

        # Отрисовка на главном экране
        screen.blit(surface, (self.x, int(self.current_y)))


class NotificationManager:
    """Менеджер уведомлений - управляет очередью уведомлений"""

    def __init__(self):
        self.notifications = []
        self.max_notifications = 3  # Максимум одновременно показываемых
        self.shown_achievements = set()  # Какие достижения уже показаны В ЭТОЙ СЕССИИ

    def add_achievement(self, name, description, icon="🏆"):
        """Добавить уведомление о достижении"""
        # Проверка дубликата - не показываем одно и то же достижение дважды
        achievement_key = (name, description)
        if achievement_key in self.shown_achievements:
            print(f"[DEBUG] Достижение '{name}' уже было показано в этой сессии, пропускаем")
            return

        # Если уже 3 уведомления, не добавляем новое
        if len(self.notifications) >= self.max_notifications:
            print(f"[DEBUG] Слишком много уведомлений, пропускаем '{name}'")
            return

        # Добавляем в набор показанных
        self.shown_achievements.add(achievement_key)
        print(f"[DEBUG] Показываем новое достижение: '{name}'")

        notification = AchievementNotification(name, description, icon)

        # Смещение по Y для нескольких уведомлений
        offset = len(self.notifications) * 110
        notification.target_y += offset
        notification.current_y = -notification.height + offset

        self.notifications.append(notification)

    def update(self, screen_width):
        """Обновление всех уведомлений"""
        # Обновляем и удаляем истекшие
        self.notifications = [
            n for n in self.notifications
            if n.update(screen_width)
        ]

    def draw(self, screen):
        """Отрисовка всех уведомлений"""
        for notification in self.notifications:
            notification.draw(screen)

    def has_notifications(self):
        """Есть ли активные уведомления"""
        return len(self.notifications) > 0