import pygame
import random
import math
from pygame.math import Vector2

class Particle:
    def __init__(self, bounds, speed_range, life_range, fade_range):
        self.bounds = bounds
        self.pos = Vector2(
            random.uniform(0.1 * bounds[0], 0.9 * bounds[0]),
            random.uniform(0.1 * bounds[1], 0.9 * bounds[1])
        )
        
        angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(*speed_range)
        self.velocity = Vector2(math.cos(angle), math.sin(angle)) * self.speed
        
        self.max_life = random.uniform(*life_range)
        self.life = self.max_life
        self.fade_time = random.uniform(*fade_range)
        
        self.alpha = 0
        self.fade_speed = 255 / self.fade_time
        self.size = random.uniform(2, 4)
        self.color = (255, 255, 255)

    def update(self, dt):
        self.pos += self.velocity * dt
        self.life -= dt
        
        # Отражение с энергопотерей
        if self.pos.x < 0 or self.pos.x > self.bounds[0]:
            self.velocity.x *= -0.98
            self.pos.x = max(1, min(self.pos.x, self.bounds[0]-1))
        if self.pos.y < 0 or self.pos.y > self.bounds[1]:
            self.velocity.y *= -0.98
            self.pos.y = max(1, min(self.pos.y, self.bounds[1]-1))
        
        # Плавное изменение альфа-канала (Хуй знает как исправить эту мутню)
        if self.life > self.max_life - self.fade_time:
            self.alpha = min(255, self.alpha + self.fade_speed * dt * 50)
        else:
            self.alpha = max(0, self.alpha - self.fade_speed * dt * 50)
        
        return self.life > 0 and self.alpha > 5

    def draw(self, surface):
        current_color = (*self.color, int(self.alpha))
        pygame.draw.circle(
            surface, 
            current_color, 
            (int(self.pos.x), int(self.pos.y)), 
            max(1, int(self.size * (self.alpha / 255)))
        )

class SpoilerEffect:
    def __init__(self, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (width, height), 
            pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SRCALPHA
        )
        self.clock = pygame.time.Clock()
        self.bounds = (width, height)
        self.particles = []
        
        # Настройки
        self.speed_range = (50, 150)
        self.life_range = (1.5, 3.0)
        self.fade_range = (0.8, 1.5)
        self.max_particles = 500
        self.gradient_colors = [
            (25, 25, 112),
            (70, 130, 180),
            (135, 206, 250)
        ]
        
        self.gradient = self.create_gradient()
        self.particle_layer = pygame.Surface(
            self.bounds, 
            pygame.SRCALPHA | pygame.HWSURFACE
        )
        
        self.font = pygame.font.SysFont('Arial', 16)
        self.show_stats = True

    def create_gradient(self):
        if not hasattr(self, '_gradient_cache'):
            gradient = pygame.Surface(self.bounds)
            for y in range(self.bounds[1]):
                t = y / self.bounds[1]
                color = tuple(int((1-t)*c1 + t*c2) for c1, c2 in zip(
                    self.gradient_colors[0], 
                    self.gradient_colors[-1]
                ))
                pygame.draw.line(gradient, color, (0, y), (self.bounds[0], y))
            self._gradient_cache = gradient.convert()
        return self._gradient_cache

    def update_params(self, speed=None, life=None, fade=None, max_part=None):
        if speed: 
            self.speed_range = (
                max(0, speed[0]), 
                max(0, speed[1])
            )
        if life: 
            self.life_range = (
                max(0.1, life[0]), 
                max(0.1, life[1])
            )
        if fade: 
            self.fade_range = (
                max(0.1, fade[0]), 
                max(0.1, fade[1])
            )
        if max_part: 
            self.max_particles = max(10, max_part)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            new_speed = (self.speed_range[0]+10, self.speed_range[1]+10)
            self.update_params(speed=new_speed)
        if keys[pygame.K_DOWN]:
            new_speed = (
                max(0, self.speed_range[0]-10), 
                max(0, self.speed_range[1]-10)
            )
            self.update_params(speed=new_speed)
        if keys[pygame.K_s]:
            self.show_stats = not self.show_stats

    def auto_adjust_particles(self):
        current_fps = self.clock.get_fps()
        if current_fps == 0:
            return
            
        if current_fps < 50 and self.max_particles > 100:
            self.max_particles = max(100, self.max_particles - 50)
        elif current_fps > 60 and self.max_particles < 2000:
            self.max_particles += 50

    def draw_stats(self):
        stats = [
            f"FPS: {self.clock.get_fps():.1f}",
            f"Particles: {len(self.particles)}",
            f"Speed: {self.speed_range}",
            f"Max: {self.max_particles}"
        ]
        
        y_offset = 5
        for text in stats:
            surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (5, y_offset))
            y_offset += 18

    def run(self):
        running = True
        last_update = pygame.time.get_ticks()
        
        while running:
            dt = self.clock.tick(60) / 1000.0
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self.handle_input()
            self.auto_adjust_particles()
            
            if len(self.particles) < self.max_particles:
                to_add = min(5, self.max_particles - len(self.particles))
                for _ in range(to_add):
                    self.particles.append(Particle(
                        self.bounds,
                        self.speed_range,
                        self.life_range,
                        self.fade_range
                    ))
            
            self.particles = [p for p in self.particles if p.update(dt)]
            
            self.screen.blit(self.gradient, (0, 0))
            self.particle_layer.fill((0, 0, 0, 0))
            
            for p in self.particles:
                p.draw(self.particle_layer)
            
            self.screen.blit(self.particle_layer, (0, 0))
            
            if self.show_stats:
                self.draw_stats()
            
            pygame.display.flip()
            
            if current_time - last_update > 30000:
                self.particles.clear()
                last_update = current_time

        pygame.quit()

if __name__ == "__main__":
    effect = SpoilerEffect(1280, 720)
    effect.run()
