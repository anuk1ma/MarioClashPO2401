import pygame
import sys
import math
import time
import random

# Импорты для работы с базой данных
try:
    from database_manager import DatabaseManager
    from auth_screen import AuthScreen
    from achievement_notification import NotificationManager
    from pixel_art_system import PixelArtSprite, ParticleEffect, AnimatedBackground

    DB_AVAILABLE = True
except ImportError:
    print("Warning: Database modules not found. Running in offline mode.")
    DB_AVAILABLE = False


    # Создаём заглушку для NotificationManager если модуль не найден
    class NotificationManager:
        def __init__(self): pass

        def add_achievement(self, *args, **kwargs): pass

        def update(self, *args, **kwargs): pass

        def draw(self, *args, **kwargs): pass

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 835
SCREEN_HEIGHT = 700
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
BLUE = (50, 100, 220)
GREEN = (50, 200, 50)
DARK_GREEN = (30, 120, 30)
YELLOW = (255, 255, 0)
BROWN = (101, 67, 33)
ORANGE = (255, 165, 0)
PURPLE = (138, 43, 226)
DARK_RED = (139, 0, 0)

# Игровые константы
GRAVITY = 0.8
JUMP_POWER = -15
PLAYER_SPEED = 5


class Player(pygame.sprite.Sprite):
    # Загрузка спрайтов один раз для всех игроков
    _sprites_loaded = False
    _static_right = None  # 37x59
    _static_left = None  # 37x59
    _jump_right = None  # 41x62
    _jump_left = None  # 41x62

    @classmethod
    def load_sprites(cls):
        """Загрузить спрайты Марио один раз"""
        if not cls._sprites_loaded:
            try:
                cls._static_right = pygame.image.load('Images/static_right.png').convert_alpha()
                cls._static_left = pygame.image.load('Images/static_left.png').convert_alpha()
                cls._jump_right = pygame.image.load('Images/jump_right.png').convert_alpha()
                cls._jump_left = pygame.image.load('Images/jump_left.png').convert_alpha()
                print("Mario sprites loaded successfully")
                cls._sprites_loaded = True
            except Exception as e:
                print(f"⚠ Warning: Could not load Mario sprites: {e}")
                print("  Using fallback sprite")
                cls._sprites_loaded = False

    def __init__(self, x, y):
        super().__init__()

        # Загружаем спрайты
        Player.load_sprites()

        # Размеры (используем размер static спрайта как базовый, увеличены в 1.5 раза)
        self.original_width = 37  # Оригинальный размер
        self.original_height = 59  # Оригинальный размер
        self.width = self.original_width
        self.height = self.original_height

        # Для совместимости
        self.original_size = 40
        self.size = self.original_size

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.depth_layer = "front"
        self.lives = 3
        self.holding_shell = None
        self.teleport_cooldown = 0
        self.facing_right = True  # Направление взгляда

        # Обновляем спрайт
        self.update_sprite()

    def update_sprite(self):
        """Обновить спрайт в зависимости от состояния"""
        # DEBUG
        if not hasattr(self, '_debug_printed'):
            print(f"DEBUG Player: _sprites_loaded = {Player._sprites_loaded}")
            self._debug_printed = True

        if not Player._sprites_loaded:
            # Fallback - жёлтый квадрат
            self.pixel_sprite = pygame.Surface((self.width, self.height))
            self.pixel_sprite.fill(YELLOW)
            self.image = self.pixel_sprite
            return

        # Выбираем спрайт (размеры увеличены в 1.5 раза)
        if self.on_ground:
            # Стоит на земле
            sprite = Player._static_right if self.facing_right else Player._static_left
            sprite_width = 37  # Оригинальный размер
            sprite_height = 59  # Оригинальный размер
        else:
            # В прыжке
            sprite = Player._jump_right if self.facing_right else Player._jump_left
            sprite_width = 41  # Оригинальный размер
            sprite_height = 62  # Оригинальный размер

        # Масштабируем для заднего плана
        if self.depth_layer == "back":
            scaled_width = int(sprite_width * 0.6)
            scaled_height = int(sprite_height * 0.6)
        else:
            scaled_width = sprite_width
            scaled_height = sprite_height

        # Сохраняем старый центр
        old_centerx = self.rect.centerx
        old_bottom = self.rect.bottom

        # Создаём спрайт
        self.pixel_sprite = pygame.transform.scale(sprite, (scaled_width, scaled_height))
        self.image = self.pixel_sprite  # ВАЖНО!
        self.width = scaled_width
        self.height = scaled_height

        # Обновляем rect с сохранением позиции
        self.rect = self.pixel_sprite.get_rect()
        self.rect.centerx = old_centerx
        self.rect.bottom = old_bottom

    def update(self, platforms, pipes):
        keys = pygame.key.get_pressed()

        # Уменьшаем cooldown телепортации
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1

        # Горизонтальное движение
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False  # Смотрит влево
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True  # Смотрит вправо

        # Прыжок
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False

        # Бросок панциря
        if keys[pygame.K_e] and self.holding_shell:
            shell = self.holding_shell
            shell.thrown = True
            shell.vel_x = 8 if keys[pygame.K_RIGHT] or keys[pygame.K_d] else -8
            shell.depth_layer = self.depth_layer
            shell.update_sprite()  # Обновляем спрайт при броске
            self.holding_shell = None

        # Гравитация
        self.vel_y += GRAVITY

        # Движение
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Проверка границ экрана
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # Коллизия с платформами
        self.on_ground = False
        for platform in platforms:
            if platform.depth_layer == self.depth_layer:
                if self.rect.colliderect(platform.rect):
                    # Столкновение сверху
                    if self.vel_y > 0 and self.rect.bottom <= platform.rect.top + 20:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    # Столкновение снизу
                    elif self.vel_y < 0 and self.rect.top >= platform.rect.bottom - 20:
                        self.rect.top = platform.rect.bottom
                        self.vel_y = 0

        # Проверка труб (порталов)
        for pipe in pipes:
            if pipe.depth_layer == self.depth_layer:
                if self.rect.colliderect(pipe.rect) and self.teleport_cooldown == 0:
                    # Автоматическая телепортация при касании трубы
                    if pipe.target:
                        # Телепортируем на ФИКСИРОВАННЫЕ координаты
                        self.rect.centerx = pipe.target.teleport_x
                        self.rect.bottom = pipe.target.teleport_y

                        self.change_layer(pipe.target.depth_layer)
                        self.teleport_cooldown = 30  # Защита от повторной телепортации (0.5 секунды)

        # Падение за пределы экрана
        if self.rect.top > SCREEN_HEIGHT:
            self.take_damage()

        # Обновляем спрайт
        self.update_sprite()

    def change_layer(self, new_layer):
        self.depth_layer = new_layer
        if new_layer == "back":
            self.size = int(self.original_size * 0.6)  # Уменьшение на заднем плане
        else:
            self.size = self.original_size

        # Обновление изображения
        old_center = self.rect.center
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.update_sprite()  # Обновляем спрайт после смены слоя
        self.rect.center = old_center

    def take_damage(self):
        self.lives -= 1
        if self.lives > 0:
            # Респавн
            self.rect.x = SCREEN_WIDTH // 2
            self.rect.y = 100
            self.vel_y = 0
            self.depth_layer = "front"
            self.change_layer("front")

    def draw(self, screen):
        # Используем пиксель-арт спрайт
        if hasattr(self, 'pixel_sprite') and self.pixel_sprite:
            screen.blit(self.pixel_sprite, self.rect)
        else:
            # Fallback
            pygame.draw.rect(screen, YELLOW, self.rect)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, depth_layer):
        super().__init__()
        self.depth_layer = depth_layer
        self.width = width
        self.height = height

        if depth_layer == "back":
            # Уменьшение платформы на заднем плане
            actual_width = int(width * 0.6)
            actual_height = int(height * 0.6)
        else:
            actual_width = width
            actual_height = height

        self.image = pygame.Surface((actual_width, actual_height))
        color = BLUE if depth_layer == "front" else RED
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Pipe(pygame.sprite.Sprite):
    """Труба-портал (использует спрайты из Images/)"""

    # Загрузка спрайтов один раз для всех труб
    _sprites_loaded = False
    _pipe_left_img = None  # Передний план - левый
    _pipe_right_img = None  # Передний план - правый
    _pipe_left_back_img = None  # Задний план - левый
    _pipe_right_back_img = None  # Задний план - правый

    @classmethod
    def load_sprites(cls):
        """Загрузить спрайты труб один раз"""
        if not cls._sprites_loaded:
            try:
                # Загружаем изображения для ПЕРЕДНЕГО плана
                cls._pipe_left_img = pygame.image.load('Images/very_long_pipe_left.png').convert_alpha()
                cls._pipe_right_img = pygame.image.load('Images/very_long_pipe_right.png').convert_alpha()

                # Загружаем изображения для ЗАДНЕГО плана
                cls._pipe_left_back_img = pygame.image.load('Images/very_long_pipe_left.png').convert_alpha()
                cls._pipe_right_back_img = pygame.image.load('Images/very_long_pipe_right.png').convert_alpha()

                print("Pipe sprites loaded successfully (front + back)")
                cls._sprites_loaded = True
            except Exception as e:
                print(f"⚠ Warning: Could not load pipe sprites: {e}")
                print("  Using fallback rectangles")
                cls._sprites_loaded = False

    def __init__(self, x, y, depth_layer, is_top=True, teleport_x=400, teleport_y=600, is_left_side=True):
        super().__init__()
        self.depth_layer = depth_layer
        self.is_top = is_top
        self.teleport_x = teleport_x  # Куда телепортировать по X
        self.teleport_y = teleport_y  # Куда телепортировать по Y
        self.is_left_side = is_left_side  # Для выбора спрайта

        # Загружаем спрайты если ещё не загружены
        Pipe.load_sprites()

        # Размеры спрайта: 80x27
        width = 900
        height = 77

        # ВАЖНО: Масштабируем в зависимости от слоя
        if depth_layer == "back":
            # Задний план - меньше (60% от оригинала)
            scale_factor = 0.6
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
        else:
            # Передний план - оригинальный размер
            scaled_width = width
            scaled_height = height

        # Выбираем спрайт в зависимости от слоя и стороны
        if Pipe._sprites_loaded:
            if depth_layer == "back":
                # Задний план - используем very_long спрайты
                if is_left_side:
                    original_img = Pipe._pipe_left_back_img
                else:
                    original_img = Pipe._pipe_right_back_img
            else:
                # Передний план - используем long спрайты
                if is_left_side:
                    original_img = Pipe._pipe_left_img
                else:
                    original_img = Pipe._pipe_right_img

            # Масштабируем
            self.image = pygame.transform.scale(original_img, (scaled_width, scaled_height))
        else:
            # Fallback - простой прямоугольник (если спрайты не загрузились)
            self.image = pygame.Surface((scaled_width, scaled_height))
            self.image.fill(GREEN)
            pygame.draw.rect(self.image, DARK_GREEN, (2, 2, scaled_width - 4, scaled_height - 4), 2)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.target = None


class Enemy(pygame.sprite.Sprite):
    # Загрузка спрайтов один раз для всех врагов
    _sprites_loaded = False
    _turtle_right = None  # 26x15
    _turtle_left = None  # 26x15
    _shell = None  # 18x12
    _thorn_right = None  # 26x23
    _thorn_left = None  # 26x23
    _thorn_shell = None  # 18x12
    _ghost = None  # 16x18

    @classmethod
    def load_sprites(cls):
        """Загрузить спрайты врагов один раз"""
        if not cls._sprites_loaded:
            try:
                cls._turtle_right = pygame.image.load('Images/turtle_right.png').convert_alpha()
                cls._turtle_left = pygame.image.load('Images/turtle_left.png').convert_alpha()
                cls._shell = pygame.image.load('Images/shell.png').convert_alpha()
                cls._thorn_right = pygame.image.load('Images/thorn_right.png').convert_alpha()
                cls._thorn_left = pygame.image.load('Images/thorn_left.png').convert_alpha()
                cls._thorn_shell = pygame.image.load('Images/thorn_shell.png').convert_alpha()
                cls._ghost = pygame.image.load('Images/ghost.png').convert_alpha()
                print("Enemy sprites loaded successfully")
                cls._sprites_loaded = True
            except Exception as e:
                print(f"⚠ Warning: Could not load enemy sprites: {e}")
                print("  Using fallback sprites")
                cls._sprites_loaded = False

    def __init__(self, x, y, depth_layer, enemy_type="turtle", stay_on_platform=False):
        super().__init__()

        # Загружаем спрайты
        Enemy.load_sprites()

        self.depth_layer = depth_layer
        self.enemy_type = enemy_type
        self.stay_on_platform = stay_on_platform

        # Размеры зависят от типа врага (увеличены в 1.7 раза)
        if enemy_type == "turtle":
            base_width, base_height = int(26 * 1.7), int(15 * 1.7)  # 44x25
        elif enemy_type == "spike_turtle":
            base_width, base_height = int(26 * 1.7), int(23 * 1.7)  # 44x39
        elif enemy_type == "ghost":
            base_width, base_height = int(16 * 1.7), int(18 * 1.7)  # 27x30
        else:
            base_width, base_height = int(26 * 1.7), int(15 * 1.7)  # 44x25

        # Для совместимости
        self.size = 35 if depth_layer == "front" else 21

        # Масштабируем для заднего плана
        if depth_layer == "back":
            self.width = int(base_width * 0.6)
            self.height = int(base_height * 0.6)
        else:
            self.width = base_width
            self.height = base_height

        self.image = pygame.Surface((self.width, self.height))
        if enemy_type == "turtle":
            self.image.fill(GREEN)
        elif enemy_type == "spike_turtle":
            self.image.fill(PURPLE)
        elif enemy_type == "ghost":
            self.image.fill((200, 200, 200))

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vel_x = 1 if depth_layer == "front" else 0.6
        self.vel_y = 0
        self.alive = True
        self.direction = 1  # 1 = вправо, -1 = влево
        self.teleport_cooldown = 0
        self.platform_switches = 0
        self.want_teleport = False

        # Обновляем спрайт
        self.update_sprite()

        # НОВОЕ: Портальное патрулирование
        self.portal_patrol_enabled = not stay_on_platform  # Включено если враг может двигаться
        self.portal_cooldown_frames = 0
        self.portal_use_chance = 0.3  # 30% шанс использовать портал
        self.time_since_portal_check = 0
        self.portal_check_interval = 180  # Проверять каждые 3 секунды

        # Для черепах с шипами и призраков
        self.shoot_timer = 0
        if enemy_type == "ghost":
            self.shoot_cooldown = 5 * FPS  # 5 секунд для призраков
        else:
            self.shoot_cooldown = 4 * FPS  # 4 секунды для шипастых (было 10)

        # Для призраков
        self.float_offset = 0
        self.float_speed = 0.05
        self.base_y = y

        self.float_direction = 1  # Направление движения вверх/вниз

    def update_sprite(self):
        """Обновить спрайт в зависимости от типа и направления"""
        # DEBUG
        if not hasattr(self, '_debug_printed'):
            print(f"DEBUG Enemy: _sprites_loaded = {Enemy._sprites_loaded}, type = {self.enemy_type}")
            self._debug_printed = True

        if not Enemy._sprites_loaded:
            # Fallback
            # Обновляем спрайт
            self.update_sprite()
            return

        # Выбираем спрайт (размеры увеличены в 1.7 раза)
        if self.enemy_type == "turtle":
            sprite = Enemy._turtle_right if self.direction > 0 else Enemy._turtle_left
            sprite_width, sprite_height = int(26 * 1.7), int(15 * 1.7)  # 44x25
        elif self.enemy_type == "spike_turtle":
            sprite = Enemy._thorn_right if self.direction > 0 else Enemy._thorn_left
            sprite_width, sprite_height = int(26 * 1.7), int(23 * 1.7)  # 44x39
        elif self.enemy_type == "ghost":
            sprite = Enemy._ghost
            sprite_width, sprite_height = int(16 * 1.7), int(18 * 1.7)  # 27x30
        else:
            sprite = Enemy._turtle_right
            sprite_width, sprite_height = 26, 15

        # Масштабируем для заднего плана
        if self.depth_layer == "back":
            scaled_width = int(sprite_width * 0.6)
            scaled_height = int(sprite_height * 0.6)
        else:
            scaled_width = sprite_width
            scaled_height = sprite_height

        # Сохраняем позицию
        old_centerx = self.rect.centerx
        old_centery = self.rect.centery

        # Создаём спрайт
        self.pixel_sprite = pygame.transform.scale(sprite, (scaled_width, scaled_height))
        self.width = scaled_width
        self.height = scaled_height

        # Обновляем rect
        self.rect = self.pixel_sprite.get_rect()
        self.rect.centerx = old_centerx
        self.rect.centery = old_centery

    def update(self, platforms, pipes, projectiles_group, player=None):
        # Уменьшаем cooldown телепортации
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1

        # НОВОЕ: Уменьшаем кулдаун портального патрулирования
        if self.portal_cooldown_frames > 0:
            self.portal_cooldown_frames -= 1

        # НОВОЕ: Проверка использования портала для патрулирования
        if self.portal_patrol_enabled and self.portal_cooldown_frames == 0 and self.enemy_type != "ghost":
            self.time_since_portal_check += 1
            if self.time_since_portal_check >= self.portal_check_interval:
                self.time_since_portal_check = 0
                # Ищем ближайший портал на нашем плане
                for pipe in pipes:
                    if pipe.depth_layer == self.depth_layer and pipe.target:
                        dx = abs(pipe.rect.centerx - self.rect.centerx)
                        dy = abs(pipe.rect.centery - self.rect.centery)
                        # Если портал рядом (в пределах 80 пикселей)
                        if dx < 80 and dy < 80:
                            # Решаем, использовать ли портал
                            if random.random() < self.portal_use_chance:
                                # Используем портал для патрулирования
                                print(f"[PATROL] Enemy {self.enemy_type} using portal")

                                self.rect.centerx = pipe.target.teleport_x
                                self.rect.bottom = pipe.target.teleport_y
                                self.vel_y = 0

                                # МЕНЯЕМ НАПРАВЛЕНИЕ ПЕРЕД сменой слоя
                                self.direction *= -1

                                print(
                                    f"[PATROL] Enemy moved to FIXED coords: x={self.rect.centerx}, y={self.rect.bottom}, direction={self.direction}")

                                self.change_layer(pipe.target.depth_layer)
                                self.update_sprite()  # Обновляем спрайт после смены направления
                                self.portal_cooldown_frames = 120
                                break

        if self.enemy_type == "ghost":
            # Призраки летают вверх-вниз И влево-вправо
            self.rect.y += 2.5 * self.float_direction
            self.rect.x += 2 * self.direction

            # Проверяем границы движения вверх-вниз (150 пикселей от базовой позиции)
            if self.rect.y < self.base_y - 150:
                self.float_direction = 1
            elif self.rect.y > self.base_y + 150:
                self.float_direction = -1

            # Разворот при границах экрана
            if self.rect.left < 50 or self.rect.right > SCREEN_WIDTH - 50:
                self.direction *= -1
                self.update_sprite()  # Обновляем спрайт

            # Стрельба призраков - бьют вниз, не зависят от слоя игрока
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_cooldown:
                self.shoot_timer = 0
                # Пули призраков летят только вниз (from_ghost=True)
                projectile = Projectile(self.rect.centerx, self.rect.centery, self.depth_layer, 0, from_ghost=True)
                projectiles_group.add(projectile)
        else:
            # Гравитация для обычных врагов
            self.vel_y += GRAVITY

            # Простое движение влево-вправо
            self.rect.x += self.vel_x * self.direction
            self.rect.y += self.vel_y

            # Коллизия с платформами
            on_platform = False
            current_platform = None
            for platform in platforms:
                if platform.depth_layer == self.depth_layer:
                    if self.rect.colliderect(platform.rect):
                        if self.vel_y > 0:
                            self.rect.bottom = platform.rect.top
                            self.vel_y = 0
                            on_platform = True
                            current_platform = platform
                            break

            # ПРОСТАЯ ЛОГИКА: дошел до края - развернулся
            if on_platform and current_platform:
                # Проверяем края платформы
                if self.rect.left <= current_platform.rect.left + 5:
                    self.rect.left = current_platform.rect.left + 5
                    self.direction = 1  # Идем вправо
                elif self.rect.right >= current_platform.rect.right - 5:
                    self.rect.right = current_platform.rect.right - 5
                    self.direction = -1  # Идем влево

            # Телепортация через порталы (только если враг не привязан к платформе)
            if self.teleport_cooldown == 0 and not self.stay_on_platform:
                for pipe in pipes:
                    if pipe.depth_layer == self.depth_layer:
                        if self.rect.colliderect(pipe.rect) and pipe.target:
                            # DEBUG: Отслеживание телепортации
                            old_pos = (self.rect.centerx, self.rect.bottom)
                            old_layer = self.depth_layer

                            print(f"[TELEPORT] Enemy {self.enemy_type} entering pipe at {old_pos}, layer={old_layer}")

                            # Телепортируем на ФИКСИРОВАННЫЕ координаты
                            self.rect.centerx = pipe.target.teleport_x
                            self.rect.bottom = pipe.target.teleport_y

                            print(f"[TELEPORT] Teleported to FIXED coords: x={self.rect.centerx}, y={self.rect.bottom}")

                            self.vel_y = 0

                            new_pos = (self.rect.centerx, self.rect.bottom)
                            new_layer = pipe.target.depth_layer

                            print(f"[TELEPORT] Enemy teleported to {new_pos}, new_layer={new_layer}")
                            print(f"[TELEPORT] Target pipe at ({pipe.target.rect.centerx}, {pipe.target.rect.top})")

                            # МЕНЯЕМ НАПРАВЛЕНИЕ ПЕРЕД сменой слоя
                            self.direction *= -1
                            print(f"[TELEPORT] Direction changed to {self.direction}")

                            self.change_layer(pipe.target.depth_layer)
                            self.update_sprite()  # Обновляем спрайт после смены направления
                            self.teleport_cooldown = 30

                            print(f"[TELEPORT] Enemy alive={self.alive}, in groups={self.groups()}")
                            break

            # Стрельба для черепах с шипами
            if self.enemy_type == "spike_turtle" and player:
                if player.depth_layer == self.depth_layer:
                    self.shoot_timer += 1
                    if self.shoot_timer >= self.shoot_cooldown:
                        self.shoot_timer = 0
                        # Стреляем в направлении игрока
                        direction = 1 if player.rect.centerx > self.rect.centerx else -1
                        projectile = Projectile(self.rect.centerx, self.rect.centery, self.depth_layer, direction)
                        projectiles_group.add(projectile)
                else:
                    # Сбрасываем таймер если на разных слоях
                    self.shoot_timer = 0

        if self.rect.top > SCREEN_HEIGHT:
            print(f"[KILL] Enemy {self.enemy_type} fell off screen at y={self.rect.top}, killing")
            self.kill()

    def change_layer(self, new_layer):
        """Смена слоя глубины с обновлением спрайта"""
        self.depth_layer = new_layer

        # Обновляем скорость в зависимости от слоя

        if new_layer == "back":
            self.size = int(35 * 0.6)
            self.vel_x = 0.6  # Задний план - медленнее
        else:
            self.size = 35
            self.vel_x = 1  # Передний план - быстрее

        # Обновляем спрайт (это обновит размеры и image)
        self.update_sprite()

    def draw(self, screen):
        if hasattr(self, 'pixel_sprite') and self.pixel_sprite:
            # ТОЛЬКО спрайт, БЕЗ глаз и шипов
            screen.blit(self.pixel_sprite, self.rect)
        else:
            # Fallback - квадрат с глазами
            pygame.draw.rect(screen, self.image.get_at((0, 0)), self.rect, border_radius=5)

            # Глаза (только в fallback)
            eye_size = max(2, self.size // 10)
            pygame.draw.circle(screen, BLACK,
                               (self.rect.centerx - self.size // 4, self.rect.centery - self.size // 6),
                               eye_size)
            pygame.draw.circle(screen, BLACK,
                               (self.rect.centerx + self.size // 4, self.rect.centery - self.size // 6),
                               eye_size)

            # Шипы для spike_turtle (только в fallback)
            if self.enemy_type == "spike_turtle":
                spike_points = [
                    (self.rect.centerx, self.rect.top - 5),
                    (self.rect.centerx - 5, self.rect.top + 5),
                    (self.rect.centerx + 5, self.rect.top + 5)
                ]
                pygame.draw.polygon(screen, RED, spike_points)


class Projectile(pygame.sprite.Sprite):
    """Снаряд (пуля) выпущенная врагом"""

    def __init__(self, x, y, depth_layer, direction, from_ghost=False):
        super().__init__()
        self.depth_layer = depth_layer
        self.from_ghost = from_ghost  # Пули призраков летят через оба слоя

        # Размер снаряда
        if depth_layer == "back":
            self.size = 8  # Меньше на заднем плане
        else:
            self.size = 12

        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Скорость
        if from_ghost:
            # Пули призраков летят только вниз
            self.vel_x = 0
            self.vel_y = 5 if depth_layer == "front" else 3
        else:
            # Обычные пули летят горизонтально
            speed = 6 if depth_layer == "front" else 3.6
            self.vel_x = speed * direction
            self.vel_y = 0

        self.teleport_cooldown = 0

    def update(self, platforms, pipes):
        """Обновление снаряда"""
        # Уменьшаем cooldown телепортации
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1

        # Движение
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Телепортация через порталы (только для НЕ-призрачных пуль)
        if self.teleport_cooldown == 0 and not self.from_ghost:
            for pipe in pipes:
                if pipe.depth_layer == self.depth_layer:
                    if self.rect.colliderect(pipe.rect) and pipe.target:
                        # Телепортируем снаряд на фиксированные координаты
                        self.rect.centerx = pipe.target.teleport_x
                        self.rect.centery = pipe.target.teleport_y - 50

                        # Меняем слой
                        self.depth_layer = pipe.target.depth_layer
                        self.vel_x = -self.vel_x
                        # Обновляем размер для нового слоя
                        if self.depth_layer == "back":
                            self.size = 8
                            self.vel_x *= 0.6 if self.vel_x != 0 else 1
                        else:
                            self.size = 12
                            self.vel_x /= 0.6 if self.vel_x != 0 else 1

                        self.teleport_cooldown = 30
                        break

        # Удаление за границами экрана
        if (self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50 or
                self.rect.top > SCREEN_HEIGHT + 50 or self.rect.bottom < -50):
            self.kill()


class Shell(pygame.sprite.Sprite):
    # Спрайты панцирей (используются из Enemy)
    _sprites_loaded = False

    def __init__(self, x, y, depth_layer, shell_type="normal"):
        super().__init__()
        self.depth_layer = depth_layer
        self.shell_type = shell_type

        # Размеры панциря (увеличены в 1.7 раза)
        base_width, base_height = int(18 * 1.7), int(12 * 1.7)  # 30x20

        # Масштабируем для заднего плана
        if depth_layer == "back":
            self.width = int(base_width * 0.6)
            self.height = int(base_height * 0.6)
            self.size = 18
        else:
            self.width = base_width
            self.height = base_height
            self.size = 30

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BROWN if shell_type == "normal" else DARK_RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vel_x = 0
        self.vel_y = 0
        self.direction = 1
        self.thrown = False
        self.teleport_cooldown = 0
        self.lifetime = 3 * FPS
        self.from_ghost = False  # Флаг если панцирь от призрака

        # Загружаем спрайт панциря
        self.update_sprite()

    def update_sprite(self):
        """Обновить спрайт панциря"""
        # Сначала загружаем спрайты врагов если не загружены
        if not hasattr(Enemy, '_sprites_loaded'):
            Enemy.load_sprites()

        # Проверяем что спрайты загружены
        if not Enemy._sprites_loaded or Enemy._shell is None:
            # Fallback - коричневый прямоугольник
            self.pixel_sprite = pygame.Surface((self.width, self.height))
            self.pixel_sprite.fill(BROWN if self.shell_type == "normal" else DARK_RED)
            self.image = self.pixel_sprite
            return

        # Выбираем спрайт панциря
        if self.shell_type == "spike":
            sprite = Enemy._thorn_shell
        else:
            sprite = Enemy._shell

        # Увеличиваем размер в 1.7 раза
        scaled_width = int(18 * 1.7)  # 30
        scaled_height = int(12 * 1.7)  # 20

        # Учитываем depth_layer
        if self.depth_layer == "back":
            scaled_width = int(scaled_width * 0.6)
            scaled_height = int(scaled_height * 0.6)

        # Масштабируем
        self.pixel_sprite = pygame.transform.scale(sprite, (scaled_width, scaled_height))
        self.image = self.pixel_sprite  # ВАЖНО!

    def update(self, platforms, pipes=None):
        # Уменьшаем cooldown
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1

        if self.thrown:
            self.lifetime -= 1
            if self.lifetime <= 0:
                self.kill()
                return

        if self.thrown:
            self.vel_y += GRAVITY
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y

            # Коллизия с платформами
            for platform in platforms:
                if platform.depth_layer == self.depth_layer:
                    if self.rect.colliderect(platform.rect):
                        if self.vel_y > 0:
                            self.rect.bottom = platform.rect.top
                            self.vel_y = 0

            # Телепортация через порталы
                    # Телепортация через порталы
            if pipes and self.teleport_cooldown == 0:
                for pipe in pipes:
                    if pipe.depth_layer == self.depth_layer:
                        if self.rect.colliderect(pipe.rect) and pipe.target:
                            # Телепортируем панцирь на ФИКСИРОВАННЫЕ координаты
                            self.rect.centerx = pipe.target.teleport_x
                            self.rect.bottom = pipe.target.teleport_y

                            # ИЗМЕНЕНИЕ: Инвертируем направление движения, чтобы он вылетал ИЗ трубы, а не влетал обратно
                            self.vel_x = -self.vel_x

                                    # Смена слоя
                            old_layer = self.depth_layer
                            self.change_layer(pipe.target.depth_layer)

                                    # Корректировка скорости при смене планов (глубины)
                            if old_layer == "front" and pipe.target.depth_layer == "back":
                                self.vel_x *= 0.6
                            elif old_layer == "back" and pipe.target.depth_layer == "front":
                                self.vel_x /= 0.6

                            self.teleport_cooldown = 30
                            break

            # Границы экрана - убиваем если слишком далеко
            if self.rect.right < -500 or self.rect.left > SCREEN_WIDTH + 500:
                print(f"[KILL] Shell out of bounds at x={self.rect.centerx}, killing")
                self.kill()
                return# Телепортация через порталы
        if pipes and self.teleport_cooldown == 0:
            for pipe in pipes:
                if pipe.depth_layer == self.depth_layer:
                    if self.rect.colliderect(pipe.rect) and pipe.target:
                        # Запоминаем старый слой для масштабирования скорости
                        old_layer = self.depth_layer

                        # Телепортируем панцирь на фиксированные координаты выхода
                        self.rect.centerx = pipe.target.teleport_x
                        self.rect.bottom = pipe.target.teleport_y

                        # ИСПРАВЛЕНИЕ: Инвертируем направление (чтобы он вылетал ИЗ трубы)
                        self.vel_x = -self.vel_x

                        # Меняем слой и обновляем визуальный размер
                        self.change_layer(pipe.target.depth_layer)

                        # Корректируем скорость под масштаб нового слоя
                        if old_layer == "front" and pipe.target.depth_layer == "back":
                            self.vel_x *= 0.6
                        elif old_layer == "back" and pipe.target.depth_layer == "front":
                            self.vel_x /= 0.6

                        self.teleport_cooldown = 30
                        break

            if self.rect.top > SCREEN_HEIGHT:
                print(f"[KILL] Shell fell off screen at y={self.rect.top}, killing")
                self.kill()

    def change_layer(self, new_layer):
        """Смена слоя глубины"""
        self.depth_layer = new_layer

        # Обновляем размеры для нового слоя (с масштабированием 1.7x)
        base_width, base_height = int(18 * 1.7), int(12 * 1.7)  # 30x20
        if new_layer == "back":
            self.width = int(base_width * 0.6)
            self.height = int(base_height * 0.6)
        else:
            self.width = base_width
            self.height = base_height

        # Обновляем спрайт
        self.update_sprite()

    def update(self, platforms, pipes):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        # Пули призраков летят только вниз, не взаимодействуют с платформами
        if self.from_ghost:
            self.rect.y += self.vel_y
        else:
            # Обычные пули с гравитацией и коллизией
            self.vel_y += GRAVITY
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y

            # Коллизия с платформами (только для пуль черепах)
            for platform in platforms:
                if platform.depth_layer == self.depth_layer:
                    if self.rect.colliderect(platform.rect):
                        if self.vel_y > 0:
                            self.rect.bottom = platform.rect.top
                            self.vel_y = 0

            # Проход через трубы (только для пуль черепах)
            for pipe in pipes:
                if pipe.depth_layer == self.depth_layer:
                    if self.rect.colliderect(pipe.rect) and pipe.target:
                        # Телепортация на фиксированные координаты
                        self.rect.centerx = pipe.target.teleport_x
                        self.rect.centery = pipe.target.teleport_y - 50  # Чуть выше точки телепортации
                        self.change_layer(pipe.target.depth_layer)

        if self.rect.top > SCREEN_HEIGHT or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.kill()

    def change_layer(self, new_layer):
        self.depth_layer = new_layer
        if new_layer == "back":
            self.size = 9
        else:
            self.size = 15
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=self.rect.center)


class ExitPortal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 60))
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.animation_offset = 0

    def update(self):
        self.animation_offset += 0.1

    def draw(self, screen):
        # Анимированный портал
        for i in range(3):
            radius = 30 - i * 10 + int(math.sin(self.animation_offset + i) * 5)
            color_val = 200 + int(math.sin(self.animation_offset + i) * 55)
            pygame.draw.circle(screen, (color_val, color_val, 0), self.rect.center, radius, 3)


class Game:
    def __init__(self, user_data=None, db_manager=None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mario Clash - Прототип")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Данные пользователя и БД
        self.user_data = user_data
        self.db = db_manager
        self.user_id = user_data['user_id'] if user_data else None

        # Статистика текущего уровня
        self.level_start_time = 0
        self.enemies_killed = {'turtle': 0, 'spike_turtle': 0}

        # НОВОЕ: Менеджер уведомлений о достижениях
        self.notification_manager = NotificationManager()

        # Анимированный фон и частицы
        self.background = AnimatedBackground(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_effects = []

        # Счётчики для достижений
        self.total_enemies_killed = 0
        self.score = 0  # Счёт игрока
        self.portals_used_count = 0

        self.achievement_first_blood = False
        self.achievement_portal_master = False

        # НОВОЕ: Загрузка уже полученных достижений из БД
        self.unlocked_achievements = set()  # Множество ID полученных достижений
        self.level_completed = False
        if self.db and self.user_id:
            try:
                user_achievements = self.db.get_user_achievements(self.user_id)
                self.unlocked_achievements = {a["achievement_id"] for a in user_achievements}
                print(f"Loaded {len(self.unlocked_achievements)} achievements from DB")
            except Exception as e:
                print(f"Error loading achievements: {e}")

        # НОВОЕ: Загружаем текущий уровень из БД или начинаем с 1
        if self.user_data:
            self.current_level = self.user_data.get("current_level", 1)
        else:
            self.current_level = 1
        self.max_level = 3

        self.setup_level(self.current_level)

    def setup_level(self, level):
        # Сброс статистики уровня
        self.level_start_time = time.time()
        self.enemies_killed = {'turtle': 0, 'spike_turtle': 0}

        # НОВОЕ: Менеджер уведомлений о достижениях
        self.notification_manager = NotificationManager()

        # Анимированный фон и частицы
        self.background = AnimatedBackground(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_effects = []

        # Счётчики для достижений
        self.total_enemies_killed = 0
        self.score = 0  # Счёт игрока
        self.portals_used_count = 0

        self.achievement_first_blood = False
        self.achievement_portal_master = False

        # НОВОЕ: Загрузка уже полученных достижений из БД
        self.unlocked_achievements = set()  # Множество ID полученных достижений
        if self.db and self.user_id:
            try:
                user_achievements = self.db.get_user_achievements(self.user_id)
                self.unlocked_achievements = {a["achievement_id"] for a in user_achievements}
                print(f"Loaded {len(self.unlocked_achievements)} achievements from DB")
            except Exception as e:
                print(f"Error loading achievements: {e}")

        # Группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.pipes = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.shells = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.exit_portal = None

        # Создание игрока
        self.player = Player(SCREEN_WIDTH // 2, 100)
        self.all_sprites.add(self.player)

        # Создание платформ (согласно схеме)
        # Нижняя синяя платформа (центрирована)
        bottom_platform = Platform(15, 600, 800, 40, "front")
        self.platforms.add(bottom_platform)

        # Левая верхняя синяя
        top_left_blue = Platform(35, 420, 200, 30, "front")
        self.platforms.add(top_left_blue)

        # Правая верхняя синяя
        top_right_blue = Platform(595, 420, 200, 30, "front")
        self.platforms.add(top_right_blue)

        # Средняя маленькая синяя (под большой красной)
        middle_small_blue = Platform(375, 520, 80, 20, "front")
        self.platforms.add(middle_small_blue)

        # Средняя большая красная платформа (ниже маленькой синей)
        # Реальная ширина: 600 * 0.6 = 360, центрируем: (1000 - 360) / 2 = 320
        middle_red = Platform(235, 480, 600, 30, "back")
        self.platforms.add(middle_red)

        # Средняя маленькая красная (между двумя боковыми синими, на их уровне)
        # Реальная ширина: 100 * 0.6 = 60, центр: (1000 - 60) / 2 = 470
        middle_small_red = Platform(385, 420, 100, 20, "back")
        self.platforms.add(middle_small_red)

        # Левая верхняя красная

        top_left_red = Platform(155, 360, 150, 25, "back")
        self.platforms.add(top_left_red)

        # Правая верхняя красная
        top_right_red = Platform(585, 360, 150, 25, "back")
        self.platforms.add(top_right_red)


        # Труба на левой верхней синей платформе (FRONT)
        pipe_1a = Pipe(-845, 340, "front", False, teleport_x=80, teleport_y=368, is_left_side=True)
        # Труба на левой верхней красной платформе (BACK)
        pipe_1b = Pipe(-380, 310, "back", False, teleport_x=173, teleport_y=358, is_left_side=True)
        # Связь 1a <-> 1b
        pipe_1a.target = pipe_1b
        pipe_1b.target = pipe_1a

        # Труба на правой верхней синей платформе (FRONT)
        pipe_2a = Pipe(775, 340, "front", False, teleport_x=748, teleport_y=368, is_left_side=False)
        # Труба на правой верхней красной платформе (BACK)
        pipe_2b = Pipe(670, 310, "back", False, teleport_x=655, teleport_y=358, is_left_side=False)
        # Связь 2a <-> 2b
        pipe_2a.target = pipe_2b
        pipe_2b.target = pipe_2a

        # Труба на нижней синей платформе (FRONT, правый край)
        pipe_3a = Pipe(785, 520, "front", True, teleport_x=750, teleport_y=563, is_left_side=False)
        # Труба на средней красной платформе (BACK, правый край)
        pipe_3b = Pipe(580, 430, "back", False, teleport_x=555, teleport_y=483, is_left_side=False)
        # Связь 3a <-> 3b
        pipe_3a.target = pipe_3b
        pipe_3b.target = pipe_3a


        # Труба на нижней синей платформе (FRONT, левый край)
        pipe_4a = Pipe(-850, 520, "front", True, teleport_x=70, teleport_y=563, is_left_side=True)
        # Труба на средней красной платформе (BACK, левый край)
        pipe_4b = Pipe(-290, 430, "back", False, teleport_x=270, teleport_y=483, is_left_side=True)
        # Связь 4a <-> 4b
        pipe_4a.target = pipe_4b
        pipe_4b.target = pipe_4a

        # Добавляем все 8 труб
        self.pipes.add(
            pipe_1a, pipe_1b,
            pipe_2a, pipe_2b,
            pipe_3a, pipe_3b,
            pipe_4a, pipe_4b
        )

        # Создание врагов в зависимости от уровня
        if level == 1:
            # Уровень 1: только обычные черепахи
            # Боковые синие платформы - враги остаются там
            self.enemies.add(Enemy(115, 380, "front", "turtle", stay_on_platform=True))
            self.enemies.add(Enemy(715, 380, "front", "turtle", stay_on_platform=True))
            # Средняя красная платформа - враг может путешествовать
            self.enemies.add(Enemy(365, 440, "back", "turtle"))
            # НОВЫЙ: черепаха на центральной платформе заднего плана
            self.enemies.add(Enemy(415, 290, "back", "turtle", stay_on_platform=True))

        elif level == 2:
            # Уровень 2: обычные черепахи + черепахи с шипами
            # Боковые синие платформы - враги остаются там
            self.enemies.add(Enemy(115, 380, "front", "turtle", stay_on_platform=True))
            self.enemies.add(Enemy(715, 380, "front", "turtle", stay_on_platform=True))
            # Средняя красная платформа - враги могут путешествовать
            self.enemies.add(Enemy(315, 440, "back", "spike_turtle"))
            self.enemies.add(Enemy(515, 440, "back", "spike_turtle"))
            # НОВЫЕ: 2 шипастых черепахи на боковых платформах, используют порталы
            self.enemies.add(Enemy(115, 290, "back", "spike_turtle"))  # Левая боковая
            self.enemies.add(Enemy(715, 290, "back", "spike_turtle"))  # Правая боковая

        elif level == 3:
            # Уровень 3: все типы врагов + 2 призрака сверху карты
            # Боковая синяя платформа - враг остается там
            self.enemies.add(Enemy(115, 380, "front", "turtle", stay_on_platform=True))
            # Средняя красная платформа - враг может путешествовать
            self.enemies.add(Enemy(365, 440, "back", "spike_turtle"))
            # Призраки летают сверху карты, вверх-вниз и влево-вправо
            self.enemies.add(Enemy(215, 150, "front", "ghost"))  # Левый призрак
            self.enemies.add(Enemy(615, 150, "front", "ghost"))  # Правый призрак

            # НОВЫЕ ВРАГИ:
            # 2 обычных черепахи на синих платформах
            self.enemies.add(Enemy(415, 380, "back", "turtle", stay_on_platform=True))  # Центр
            self.enemies.add(Enemy(715, 380, "back", "turtle", stay_on_platform=True))  # Правая
            # 3 шипастых черепахи на красных платформах
            self.enemies.add(Enemy(115, 290, "back", "spike_turtle", stay_on_platform=True))  # Левая
            self.enemies.add(Enemy(715, 290, "back", "spike_turtle", stay_on_platform=True))  # Правая
            self.enemies.add(Enemy(415, 290, "back", "spike_turtle", stay_on_platform=True))  # Центр

    def check_collisions(self):
        # Столкновение игрока с врагами
        for enemy in self.enemies:
            if enemy.depth_layer == self.player.depth_layer:
                if self.player.rect.colliderect(enemy.rect):
                    # Проверка прыжка на врага
                    # Игрок должен падать сверху и его центр должен быть выше врага
                    if self.player.vel_y > 0 and self.player.rect.centery < enemy.rect.centery:
                        if enemy.enemy_type == "turtle":
                            # Убиваем черепаху, создаем панцирь
                            shell = Shell(enemy.rect.x, enemy.rect.y, enemy.depth_layer)
                            self.shells.add(shell)
                            enemy.kill()
                            self.player.vel_y = -8
                            # Частицы
                            self.particle_effects.append(
                                ParticleEffect(enemy.rect.centerx, enemy.rect.centery, (50, 200, 50), 15))  # Отскок
                            # Подсчет убитых врагов
                            self.enemies_killed['turtle'] += 1
                            self.total_enemies_killed += 1
                            self.score += 100  # +100 за убийство
                        elif enemy.enemy_type == "spike_turtle":
                            # Нельзя прыгнуть на черепаху с шипами
                            self.player.take_damage()
                    else:
                        # Обычное столкновение - урон игроку
                        if enemy.enemy_type != "ghost":
                            self.player.take_damage()
                        else:
                            self.player.take_damage()

        # Подбор панциря
        for shell in self.shells:
            if shell.depth_layer == self.player.depth_layer:
                if self.player.rect.colliderect(shell.rect) and not shell.thrown:
                    self.player.holding_shell = shell
                    shell.rect.center = self.player.rect.center

        # Панцирь убивает врагов
        for shell in self.shells:
            if shell.thrown:
                for enemy in self.enemies:
                    if enemy.depth_layer == shell.depth_layer:
                        if shell.rect.colliderect(enemy.rect):
                            # Подсчет убитых врагов
                            if enemy.enemy_type == "turtle":
                                self.enemies_killed['turtle'] += 1
                                self.total_enemies_killed += 1
                            elif enemy.enemy_type == "spike_turtle":
                                self.enemies_killed['spike_turtle'] += 1
                                self.total_enemies_killed += 1
                                # Создаем обычный панцирь
                                new_shell = Shell(enemy.rect.x, enemy.rect.y, enemy.depth_layer)
                                self.shells.add(new_shell)
                            enemy.kill()
                            shell.kill()

        # Снаряды попадают в игрока
        for proj in self.projectiles:
            # Пули призраков бьют на обоих планах, обычные пули только на своем слое
            if proj.from_ghost or proj.depth_layer == self.player.depth_layer:
                if self.player.rect.colliderect(proj.rect):
                    self.player.take_damage()
                    proj.kill()

        # Проверка победы - считаем только врагов, не призраков
        non_ghost_enemies = [e for e in self.enemies if e.enemy_type != "ghost"]
        if len(non_ghost_enemies) == 0 and self.exit_portal is None:
            # Создаем портал выхода
            self.exit_portal = ExitPortal(SCREEN_WIDTH // 2, 550)

        # Проход в портал выхода
        if self.exit_portal and self.player.rect.colliderect(self.exit_portal.rect):
            self.next_level()

    def check_achievements(self):
        """Проверка всех достижений 1-7"""
        # DEBUG: показываем счётчики
        print(
            f"[DEBUG] Враги: {self.total_enemies_killed}, Порталы: {self.portals_used_count}, Уровень: {self.current_level}, Разблокировано: {self.unlocked_achievements}")

        # ID 1: First Steps - Complete Level 1
        if self.current_level >= 2 and 1 not in self.unlocked_achievements:
            self.unlock_achievement(1, "First Steps", "Complete Level 1", "🎯")

        # ID 2: Turtle Slayer - Kill 50 turtles
        if self.total_enemies_killed >= 50 and 2 not in self.unlocked_achievements:
            self.unlock_achievement(2, "Turtle Slayer", "Kill 50 turtles", "T")

        # ID 3: Spike Master - Kill 20 spike turtles
        spike_kills = self.enemies_killed.get('spike_turtle', 0)
        if spike_kills >= 20 and 3 not in self.unlocked_achievements:
            self.unlock_achievement(3, "Spike Master", "Kill 20 spike turtles", "S")

        # ID 4: Speed Runner - Complete any level in under 60 seconds
        if hasattr(self, 'level_start_time'):
            level_time = time.time() - self.level_start_time
            if level_time < 60 and self.level_completed and 4 not in self.unlocked_achievements:
                self.unlock_achievement(4, "Speed Runner", "Complete level in under 60 seconds", "⚡")

        # ID 5: Ghost Hunter - Complete Level 3
        if self.current_level >= 4 and 5 not in self.unlocked_achievements:
            self.unlock_achievement(5, "Ghost Hunter", "Complete Level 3", "👻")

        # ID 6: Perfect Score - Get max score on any level
        # Используем total_score из user_data или текущий счёт
        current_score = self.user_data.get('total_score', 0) if self.user_data else 0
        if (hasattr(self, 'score') and self.score >= 5000) or current_score >= 5000:
            if 6 not in self.unlocked_achievements:
                self.unlock_achievement(6, "Perfect Score", "Get max score on any level", "⭐")

        # ID 7: Completionist - Complete all levels
        if self.current_level > 5 and 7 not in self.unlocked_achievements:
            self.unlock_achievement(7, "Completionist", "Complete all levels", "*")

    def unlock_achievement(self, achievement_id, title, description, icon):
        """Разблокировать достижение"""
        # Проверка что ещё не разблокировано
        if achievement_id in self.unlocked_achievements:
            return

        # Добавляем в локальный набор
        self.unlocked_achievements.add(achievement_id)

        # Показываем уведомление
        self.notification_manager.add_achievement(title, description, icon)

        # Сохраняем в БД
        if self.db and self.user_id:
            try:
                if self.db.unlock_achievement(self.user_id, achievement_id):
                    print(f"Achievement '{title}' (ID {achievement_id}) unlocked!")
            except Exception as e:
                print(f"Error unlocking achievement {achievement_id}: {e}")

    def save_level_progress(self, completed=True):
        """Сохранение прогресса уровня в базу данных"""
        if not self.db or not self.user_id:
            return  # Работаем без БД

        # Расчет времени
        time_spent = int(time.time() - self.level_start_time)

        # Расчет очков
        score_data = self.db.calculate_score(
            turtles_killed=self.enemies_killed['turtle'],
            spike_turtles_killed=self.enemies_killed['spike_turtle'],
            time_spent=time_spent
        )

        # Сохранение в БД
        result = self.db.save_level_progress(
            user_id=self.user_id,
            level_id=self.current_level,
            score=score_data['total_score'],
            time_spent=time_spent,
            enemies_killed=self.enemies_killed['turtle'] + self.enemies_killed['spike_turtle'],
            completed=completed
        )

        if result['success']:
            print(f"Level {self.current_level} progress saved!")

            print(f"Score: {score_data['total_score']}")
            print(f"  - Turtles: {score_data['breakdown']['turtles']}")
            print(f"  - Spike Turtles: {score_data['breakdown']['spike_turtles']}")
            print(f"  - Time Bonus: {score_data['breakdown']['time_bonus']}")

            # Проверка достижений
            new_achievements = self.db.check_achievements(self.user_id)
            if new_achievements:
                print(f"Unlocked {len(new_achievements)} new achievements!")
        else:
            print(f"Error saving progress: {result.get('error', 'Unknown error')}")

    def show_game_complete_screen(self):
        """Экран завершения всех уровней с итоговой статистикой"""
        if not self.db or not self.user_id:
            return

        # Получаем статистику
        stats = self.db.get_user_stats(self.user_id)

        self.screen.fill(WHITE)

        # Заголовок
        title_text = self.font.render("CONGRATULATIONS!", True, GREEN)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - 180, 100))

        # Статистика
        y_offset = 200
        stats_lines = [
            f"All Levels Completed!",
            f"",
            f"Total Score: {stats['total_score']}",
            f"Levels Completed: {stats['levels_completed']}",
            f"Achievements: {stats['achievements_count']}",
            f"Total Time: {stats['total_time_played']}s",
        ]

        for line in stats_lines:
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 150, y_offset))
            y_offset += 40

        # Лидерборд
        y_offset += 20
        leaderboard_title = self.font.render("TOP PLAYERS", True, BLUE)
        self.screen.blit(leaderboard_title, (SCREEN_WIDTH // 2 - 120, y_offset))
        y_offset += 50

        leaderboard = self.db.get_leaderboard(limit=5)
        for i, player in enumerate(leaderboard, 1):
            rank_color = ORANGE if player['username'] == self.user_data['username'] else BLACK
            text = self.small_font.render(
                f"{i}. {player['username']} - {player['total_score']} pts",
                True, rank_color
            )
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 150, y_offset))
            y_offset += 30

        # Инструкция
        instruction = self.small_font.render("Press SPACE to restart", True, DARK_GREEN)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT - 80))

        pygame.display.flip()

        # Ожидание нажатия
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False

    def next_level(self):
        # НОВОЕ: Уведомление о завершении уровня
        self.notification_manager.add_achievement(
            f"Уровень {self.current_level} пройден!",
            "Отличная работа!",
            "🎯"
        )

        # Сохраняем прогресс завершенного уровня
        self.save_level_progress(completed=True)

        self.level_completed = True
        self.current_level += 1
        if self.current_level > self.max_level:
            # Игра завершена - показываем финальную статистику
            self.show_game_complete_screen()
            self.current_level = 1  # Рестарт на первый уровень
        self.setup_level(self.current_level)

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Обновление
            self.player.update(self.platforms, self.pipes)

            # Обновление панциря, который держит игрок
            if self.player.holding_shell:
                self.player.holding_shell.rect.center = (
                    self.player.rect.centerx + (20 if self.player.vel_x >= 0 else -20),
                    self.player.rect.centery
                )

            for enemy in self.enemies:
                enemy.update(self.platforms, self.pipes, self.projectiles, self.player)

            for shell in self.shells:
                shell.update(self.platforms, self.pipes)

            for proj in self.projectiles:
                proj.update(self.platforms, self.pipes)

            if self.exit_portal:
                self.exit_portal.update()

            self.check_collisions()

            # НОВОЕ: Проверка достижений
            self.check_achievements()

            # Обновление частиц
            for effect in self.particle_effects[:]:
                effect.update()
                if not effect.is_alive():
                    self.particle_effects.remove(effect)

            # НОВОЕ: Обновление уведомлений
            self.notification_manager.update(SCREEN_WIDTH)

            # Отрисовка
            # Анимированный фон
            self.background.update()
            self.background.draw(self.screen)

            # Рисуем задний план
            for platform in self.platforms:
                if platform.depth_layer == "back":
                    # Пиксель-арт платформа (задний)
                    sprite = PixelArtSprite.create_platform_sprite(platform.rect.width, platform.rect.height, False)
                    self.screen.blit(sprite, platform.rect)
                    pygame.draw.rect(self.screen, (150, 30, 30), platform.rect, 2)

            for pipe in self.pipes:
                if pipe.depth_layer == "back":
                    # Используем загруженный спрайт из pipe.image
                    self.screen.blit(pipe.image, pipe.rect)

            for enemy in self.enemies:
                if enemy.depth_layer == "back":
                    enemy.draw(self.screen)

            for shell in self.shells:
                if shell.depth_layer == "back":
                    # Используем спрайт панциря
                    if hasattr(shell, 'pixel_sprite') and shell.pixel_sprite:
                        self.screen.blit(shell.pixel_sprite, shell.rect)
                    else:
                        pygame.draw.rect(self.screen, BROWN, shell.rect, border_radius=3)

            for proj in self.projectiles:
                if proj.depth_layer == "back":
                    pygame.draw.circle(self.screen, RED, proj.rect.center, proj.size // 2)

            # Игрок на заднем плане
            if self.player.depth_layer == "back":
                self.player.draw(self.screen)

            # Рисуем передний план
            for platform in self.platforms:
                if platform.depth_layer == "front":
                    # Пиксель-арт платформа
                    sprite = PixelArtSprite.create_platform_sprite(platform.rect.width, platform.rect.height, True)
                    self.screen.blit(sprite, platform.rect)
                    pygame.draw.rect(self.screen, (30, 60, 150), platform.rect, 3)

            for pipe in self.pipes:
                if pipe.depth_layer == "front":
                    # Используем загруженный спрайт из pipe.image
                    self.screen.blit(pipe.image, pipe.rect)

            for enemy in self.enemies:
                if enemy.depth_layer == "front":
                    enemy.draw(self.screen)

            for shell in self.shells:
                if shell.depth_layer == "front":
                    # Используем спрайт панциря
                    if hasattr(shell, 'pixel_sprite') and shell.pixel_sprite:
                        self.screen.blit(shell.pixel_sprite, shell.rect)
                    else:
                        pygame.draw.rect(self.screen, BROWN, shell.rect, border_radius=3)

            for proj in self.projectiles:
                if proj.depth_layer == "front":
                    pygame.draw.circle(self.screen, RED, proj.rect.center, proj.size // 2)

            # Игрок на переднем плане
            if self.player.depth_layer == "front":
                self.player.draw(self.screen)

            # Портал выхода
            if self.exit_portal:
                self.exit_portal.draw(self.screen)

            # HUD
            lives_text = self.font.render(f"Жизни: {self.player.lives}", True, BLACK)
            level_text = self.font.render(f"Уровень: {self.current_level}", True, BLACK)
            enemies_text = self.small_font.render(
                f"Врагов: {len([e for e in self.enemies if e.enemy_type != 'ghost'])}", True, BLACK)

            self.screen.blit(lives_text, (10, 10))
            self.screen.blit(level_text, (10, 50))
            self.screen.blit(enemies_text, (10, 90))

            # Статистика уровня (справа)
            if self.user_data:
                username_text = self.small_font.render(f"Игрок: {self.user_data['username']}", True, BLUE)
                self.screen.blit(username_text, (SCREEN_WIDTH - 180, 10))

                elapsed_time = int(time.time() - self.level_start_time)
                time_text = self.small_font.render(f"Время: {elapsed_time}s", True, BLACK)
                self.screen.blit(time_text, (SCREEN_WIDTH - 180, 40))

                kills_text = self.small_font.render(
                    f"Убито: {self.enemies_killed['turtle']}T {self.enemies_killed['spike_turtle']}S",
                    True, BLACK
                )
                self.screen.blit(kills_text, (SCREEN_WIDTH - 180, 70))

                # Предварительный счет
                if elapsed_time > 0:
                    preview_score = self.db.calculate_score(
                        self.enemies_killed['turtle'],
                        self.enemies_killed['spike_turtle'],
                        elapsed_time
                    )
                    score_text = self.small_font.render(
                        f"Счет: ~{preview_score['total_score']}",
                        True, GREEN
                    )
                    self.screen.blit(score_text, (SCREEN_WIDTH - 180, 100))

            # Инструкции
            controls = self.small_font.render(
                "A/D или Стрелки - движение | W/Space - прыжок | E - бросить панцирь | Трубы телепортируют автоматически",
                True, BLACK)
            self.screen.blit(controls, (SCREEN_WIDTH // 2 - 450, SCREEN_HEIGHT - 30))

            # НОВОЕ: Отрисовка уведомлений (ПОВЕРХ ВСЕГО!)
            self.notification_manager.draw(self.screen)

            # Частицы поверх всего
            for effect in self.particle_effects:
                effect.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)

            # Проверка конца игры
            if self.player.lives <= 0:
                game_over_text = self.font.render("GAME OVER! Нажмите ESC для выхода", True, RED)
                self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2))
                pygame.display.flip()

                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            waiting = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                running = False
                                waiting = False

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    if DB_AVAILABLE:
        print("=" * 60)
        print("MARIO CLASH - Database Mode")
        print("=" * 60)

        # Инициализация БД
        try:
            db = DatabaseManager()
            print("Database connection established")
        except Exception as e:
            print(f"Database connection failed: {e}")
            print("Running in offline mode...")
            db = None

        # Показываем экран авторизации
        if db:
            try:
                auth_screen = AuthScreen()
                user_data = auth_screen.run()

                if user_data:
                    print(f"\nWelcome, {user_data.get('username', 'Player')}!")
                    print(f"  Role: {user_data.get('role', 'player')}")
                    print(f"  Total Score: {user_data.get('total_score', 0)}")
                    print(f"  Current Level: {user_data.get('current_level', 1)}")

                    # Импортируем главное меню
                    from main_menu import MainMenuPixelArt as MainMenu

                    # Показываем главное меню
                    menu = MainMenu(user_data, db)
                    result = menu.run()

                    if result == 'play':
                        print("\nStarting game...")

                        # Запуск игры с данными пользователя
                        game = Game(user_data=user_data, db_manager=db)
                        game.run()
                    else:
                        print("\nGoodbye!")
                else:
                    print("Login cancelled")
                    sys.exit()
            except Exception as e:
                print(f"Error: {e}")
                import traceback

                traceback.print_exc()
                print("\nRunning in offline mode...")
                game = Game()
                game.run()
            finally:
                if db:
                    db.close_all_connections()
                    print("\nDatabase connections closed")
        else:
            # Работаем без БД
            game = Game()
            game.run()
    else:
        # БД недоступна - запускаем в оффлайн режиме
        print("=" * 60)
        print("MARIO CLASH - Offline Mode")
        print("Database modules not available")
        print("=" * 60)
        game = Game()
        game.run()