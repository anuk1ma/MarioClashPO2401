"""
Pixel Art Rendering System для Mario Clash
Система отрисовки пиксель-арт спрайтов и эффектов
"""

import pygame
import math
import random


class PixelArtSprite:
    """Базовый класс для пиксель-арт спрайтов"""

    @staticmethod
    def create_mario_sprite(size):
        """Создать спрайт Марио (игрок)"""
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        pixel_size = max(1, size // 8)

        # Красная шапка
        for x in range(2, 6):
            for y in range(1, 3):
                pygame.draw.rect(sprite, (220, 20, 20),
                               (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Лицо (бежевый)
        for x in range(2, 6):
            for y in range(3, 5):
                pygame.draw.rect(sprite, (255, 220, 177),
                               (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Глаза
        pygame.draw.rect(sprite, (0, 0, 0),
                        (3*pixel_size, 3*pixel_size, pixel_size, pixel_size))
        pygame.draw.rect(sprite, (0, 0, 0),
                        (5*pixel_size, 3*pixel_size, pixel_size, pixel_size))

        # Усы
        pygame.draw.rect(sprite, (100, 50, 0),
                        (3*pixel_size, 4*pixel_size, 2*pixel_size, pixel_size))

        # Синяя рубашка
        for x in range(2, 6):
            for y in range(5, 7):
                pygame.draw.rect(sprite, (30, 100, 220),
                               (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Кнопки (жёлтые)
        pygame.draw.rect(sprite, (255, 220, 0),
                        (4*pixel_size, 5*pixel_size, pixel_size, pixel_size))

        return sprite

    @staticmethod
    def create_turtle_sprite(size, is_front=True):
        """Создать спрайт черепахи"""
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        pixel_size = max(1, size // 7)

        # Зелёный панцирь
        color = (50, 200, 50) if is_front else (40, 160, 40)
        for x in range(1, 6):
            for y in range(1, 5):
                pygame.draw.rect(sprite, color,
                               (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Узор на панцире (тёмно-зелёный)
        dark_green = (30, 120, 30) if is_front else (25, 100, 25)
        pygame.draw.rect(sprite, dark_green,
                        (2*pixel_size, 2*pixel_size, pixel_size, pixel_size))
        pygame.draw.rect(sprite, dark_green,
                        (4*pixel_size, 2*pixel_size, pixel_size, pixel_size))

        # Голова (светло-зелёная)
        head_color = (100, 230, 100) if is_front else (80, 190, 80)
        for x in range(2, 5):
            pygame.draw.rect(sprite, head_color,
                           (x*pixel_size, 5*pixel_size, pixel_size, pixel_size))

        # Глаза
        pygame.draw.rect(sprite, (0, 0, 0),
                        (2*pixel_size, 5*pixel_size, pixel_size//2, pixel_size//2))
        pygame.draw.rect(sprite, (0, 0, 0),
                        (4*pixel_size, 5*pixel_size, pixel_size//2, pixel_size//2))

        return sprite

    @staticmethod
    def create_spike_turtle_sprite(size, is_front=True):
        """Создать спрайт черепахи с шипами"""
        sprite = PixelArtSprite.create_turtle_sprite(size, is_front)
        pixel_size = max(1, size // 7)

        # Красные шипы на панцире
        spike_color = (200, 50, 50)
        spike_points = [
            (3*pixel_size, pixel_size//2),
            (2*pixel_size, 1*pixel_size),
            (4*pixel_size, 1*pixel_size)
        ]
        pygame.draw.polygon(sprite, spike_color, spike_points)

        # Ещё шипы
        spike_points2 = [
            (5*pixel_size, 2*pixel_size),
            (4*pixel_size, 3*pixel_size),
            (6*pixel_size, 3*pixel_size)
        ]
        pygame.draw.polygon(sprite, spike_color, spike_points2)

        return sprite

    @staticmethod
    def create_ghost_sprite(size):
        """Создать спрайт призрака"""
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        pixel_size = max(1, size // 8)

        # Белое тело призрака
        for x in range(2, 6):
            for y in range(2, 6):
                pygame.draw.rect(sprite, (240, 240, 240),
                               (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Волнистый низ
        for x in range(2, 6):
            y = 6 if x % 2 == 0 else 5
            pygame.draw.rect(sprite, (240, 240, 240),
                           (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Глаза (чёрные)
        pygame.draw.rect(sprite, (0, 0, 0),
                        (3*pixel_size, 3*pixel_size, pixel_size, pixel_size))
        pygame.draw.rect(sprite, (0, 0, 0),
                        (5*pixel_size, 3*pixel_size, pixel_size, pixel_size))

        # Рот (открытый)
        pygame.draw.rect(sprite, (0, 0, 0),
                        (3*pixel_size, 5*pixel_size, 2*pixel_size, pixel_size))

        return sprite

    @staticmethod
    def create_shell_sprite(size, is_front=True):
        """Создать спрайт панциря"""
        sprite = pygame.Surface((int(size*1.2), int(size*0.8)), pygame.SRCALPHA)
        pixel_size = max(1, size // 6)

        # Коричневый панцирь
        color = (150, 100, 50) if is_front else (120, 80, 40)
        for x in range(1, 6):
            for y in range(1, 4):
                pygame.draw.rect(sprite, color,
                               (x*pixel_size, y*pixel_size, pixel_size, pixel_size))

        # Узор
        dark = (100, 60, 30) if is_front else (80, 50, 25)
        for x in [2, 4]:
            pygame.draw.rect(sprite, dark,
                           (x*pixel_size, 2*pixel_size, pixel_size, pixel_size))

        return sprite

    @staticmethod
    def create_pipe_sprite(width, height, is_front=True):
        """Создать спрайт трубы (портала)"""
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)

        # Зелёная труба
        green = (50, 180, 50) if is_front else (40, 145, 40)
        dark_green = (30, 120, 30) if is_front else (25, 100, 25)

        # Основная часть
        pygame.draw.rect(sprite, green, (0, height//4, width, height*3//4))

        # Верхняя часть (расширенная)
        lip_height = height // 4
        pygame.draw.rect(sprite, dark_green, (0, 0, width, lip_height))

        # Тень и свет
        pygame.draw.rect(sprite, dark_green, (0, 0, width//6, height), 0)
        pygame.draw.rect(sprite, (70, 200, 70) if is_front else (60, 165, 60),
                        (width*5//6, 0, width//6, height), 0)

        # Внутренняя часть (чёрная)
        inner_width = width * 3 // 5
        inner_x = (width - inner_width) // 2
        pygame.draw.ellipse(sprite, (0, 0, 0),
                           (inner_x, lip_height//3, inner_width, lip_height))

        return sprite

    @staticmethod
    def create_platform_sprite(width, height, is_front=True):
        """Создать спрайт платформы"""
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)

        # Цвета платформ
        if is_front:
            main_color = (50, 100, 220)  # Синий
            dark_color = (30, 60, 150)
            light_color = (70, 130, 255)
        else:
            main_color = (220, 50, 50)  # Красный
            dark_color = (150, 30, 30)
            light_color = (255, 80, 80)

        # Основной цвет
        pygame.draw.rect(sprite, main_color, (0, 0, width, height))

        # Кирпичный узор
        brick_height = max(4, height // 4)
        brick_width = max(8, width // 8)

        for row in range(0, height, brick_height):
            offset = brick_width // 2 if (row // brick_height) % 2 else 0
            for col in range(-brick_width, width, brick_width):
                x = col + offset
                # Тёмные линии между кирпичами
                pygame.draw.line(sprite, dark_color, (x, row), (x, row + brick_height), 2)
                pygame.draw.line(sprite, dark_color, (x, row), (x + brick_width, row), 2)

                # Светлая подсветка
                pygame.draw.line(sprite, light_color, (x+1, row+1), (x + brick_width-2, row+1), 1)
                pygame.draw.line(sprite, light_color, (x+1, row+1), (x+1, row + brick_height-2), 1)

        # Верхняя и нижняя границы
        pygame.draw.rect(sprite, light_color, (0, 0, width, 3))
        pygame.draw.rect(sprite, dark_color, (0, height-3, width, 3))

        return sprite

    @staticmethod
    def create_coin_sprite(size):
        """Создать спрайт монеты"""
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        radius = size // 3

        # Золотая монета
        pygame.draw.circle(sprite, (255, 215, 0), (center, center), radius)
        pygame.draw.circle(sprite, (218, 165, 32), (center, center), radius, 2)

        # Символ
        font = pygame.font.Font(None, int(size * 0.6))
        text = font.render("$", True, (218, 165, 32))
        text_rect = text.get_rect(center=(center, center))
        sprite.blit(text, text_rect)

        return sprite


class ParticleEffect:
    """Система частиц для эффектов"""

    def __init__(self, x, y, color, count=10):
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 2,  # Вверх
                'life': 1.0,
                'color': color,
                'size': random.randint(2, 5)
            })

    def update(self):
        """Обновить частицы"""
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.3  # Гравитация
            p['life'] -= 0.02

            if p['life'] <= 0:
                self.particles.remove(p)

    def draw(self, screen):
        """Отрисовать частицы"""
        for p in self.particles:
            alpha = int(255 * p['life'])
            color = (*p['color'], alpha)
            size = int(p['size'] * p['life'])
            if size > 0:
                surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (size, size), size)
                screen.blit(surf, (int(p['x']-size), int(p['y']-size)))

    def is_alive(self):
        """Живы ли частицы"""
        return len(self.particles) > 0


class AnimatedBackground:
    """Анимированный фон с облаками и холмами"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.clouds = []

        # Создаём облака
        for _ in range(5):
            self.clouds.append({
                'x': random.randint(0, width),
                'y': random.randint(50, height//3),
                'size': random.randint(40, 80),
                'speed': random.uniform(0.2, 0.5)
            })

    def update(self):
        """Обновить фон"""
        for cloud in self.clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > self.width + 100:
                cloud['x'] = -100

    def draw(self, screen):
        """Отрисовать фон"""
        # Градиентное небо
        for y in range(self.height):
            progress = y / self.height
            color = (
                int(135 + (200-135) * progress),  # R
                int(206 + (230-206) * progress),  # G
                int(235 + (255-235) * progress)   # B
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))

        # Облака
        for cloud in self.clouds:
            self.draw_cloud(screen, int(cloud['x']), int(cloud['y']), cloud['size'])

        # Холмы на горизонте
        self.draw_hills(screen)

    def draw_cloud(self, screen, x, y, size):
        """Отрисовать пиксельное облако"""
        cloud_surf = pygame.Surface((size*2, size), pygame.SRCALPHA)
        pixel_size = max(2, size // 8)

        # Белое облако
        positions = [
            (3, 2), (4, 2), (5, 2),
            (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
            (2, 4), (3, 4), (4, 4), (5, 4), (6, 4),
            (3, 5), (4, 5), (5, 5)
        ]

        for px, py in positions:
            pygame.draw.rect(cloud_surf, (255, 255, 255, 200),
                           (px*pixel_size, py*pixel_size, pixel_size, pixel_size))

        screen.blit(cloud_surf, (x, y))

    def draw_hills(self, screen):
        """Отрисовать холмы"""
        # Дальние холмы (тёмно-зелёные)
        hill_points_far = [
            (0, self.height),
            (self.width//4, self.height - 80),
            (self.width//2, self.height - 60),
            (self.width*3//4, self.height - 100),
            (self.width, self.height - 70),
            (self.width, self.height)
        ]
        pygame.draw.polygon(screen, (50, 150, 50), hill_points_far)

        # Ближние холмы (светло-зелёные)
        hill_points_near = [
            (0, self.height),
            (self.width//3, self.height - 50),
            (self.width*2//3, self.height - 80),
            (self.width, self.height - 40),
            (self.width, self.height)
        ]
        pygame.draw.polygon(screen, (80, 180, 80), hill_points_near)


# Тест системы
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pixel Art System Test")
    clock = pygame.time.Clock()

    # Создаём спрайты
    mario = PixelArtSprite.create_mario_sprite(64)
    turtle_front = PixelArtSprite.create_turtle_sprite(48, True)
    turtle_back = PixelArtSprite.create_turtle_sprite(32, False)
    ghost = PixelArtSprite.create_ghost_sprite(48)
    pipe = PixelArtSprite.create_pipe_sprite(60, 80, True)
    platform = PixelArtSprite.create_platform_sprite(200, 40, True)

    # Фон
    background = AnimatedBackground(800, 600)

    # Частицы
    particles = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Создать эффект частиц
                particles.append(ParticleEffect(event.pos[0], event.pos[1],
                                              (255, 215, 0), 20))

        # Обновление
        background.update()
        for p in particles[:]:
            p.update()
            if not p.is_alive():
                particles.remove(p)

        # Отрисовка
        background.draw(screen)

        screen.blit(platform, (100, 400))
        screen.blit(mario, (150, 300))
        screen.blit(turtle_front, (300, 350))
        screen.blit(turtle_back, (400, 360))
        screen.blit(ghost, (500, 250))
        screen.blit(pipe, (600, 320))

        for p in particles:
            p.draw(screen)

        # Инструкция
        font = pygame.font.Font(None, 24)
        text = font.render("Click to create particle effects!", True, (0, 0, 0))
        screen.blit(text, (250, 50))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()