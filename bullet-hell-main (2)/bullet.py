"""
Bullet classes and patterns for the bullet hell game
"""
import pygame
import math
from config import *
from utils import angle_to, distance


class Bullet:
    """Base bullet class"""
    def __init__(self, x, y, angle, speed, color=RED, damage=10, homing=False):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.damage = damage
        self.homing = homing
        self.size = BULLET_SIZE
        self.bullet_type = 'normal'  # Default bullet type
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = 0
        self.max_lifetime = 10000  # milliseconds
    
    def update(self, dt, target=None):
        """Update bullet position"""
        self.lifetime += dt
        
        # Homing behavior
        if self.homing and target:
            target_angle = angle_to((self.x, self.y), (target.x, target.y))
            # Gradually adjust angle towards target
            angle_diff = target_angle - self.angle
            # Normalize angle difference
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            # Apply small correction
            self.angle += angle_diff * 0.02
            self.vx = math.cos(self.angle) * self.speed
            self.vy = math.sin(self.angle) * self.speed
        
        self.x += self.vx
        self.y += self.vy
    
    def draw(self, screen):
        """Draw the bullet - futuristic energy projectile"""
        import math
        
        time_offset = pygame.time.get_ticks() * 0.005
        
        # Special rendering for laser beams
        if self.bullet_type == 'laser':
            # Draw a massive energy beam
            beam_width = self.size // 2
            beam_rect = pygame.Rect(int(self.x - beam_width), int(self.y - self.size), beam_width * 2, self.size * 2)
            
            # Outer glow layers
            for i in range(3):
                glow_width = beam_width * (2 - i * 0.3)
                glow_rect = pygame.Rect(int(self.x - glow_width), int(self.y - self.size * 1.2), glow_width * 2, int(self.size * 2.4))
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                glow_color = (*self.color[:3], 40)
                pygame.draw.rect(glow_surf, glow_color, (0, 0, glow_rect.width, glow_rect.height))
                screen.blit(glow_surf, glow_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
            
            # Main beam with energy effect
            pygame.draw.rect(screen, self.color, beam_rect)
            
            # Bright pulsing core
            core_width = beam_width // 2
            core_rect = pygame.Rect(int(self.x - core_width), int(self.y - self.size), core_width * 2, self.size * 2)
            pulse = abs(math.sin(time_offset * 2))
            core_brightness = int(200 + pulse * 55)
            pygame.draw.rect(screen, (core_brightness, core_brightness, core_brightness), core_rect)
            
            # Energy ripples along the beam
            num_ripples = 3
            for i in range(num_ripples):
                ripple_offset = (time_offset + i * 0.5) % 1.0
                ripple_y = self.y - self.size + ripple_offset * self.size * 2
                pygame.draw.line(screen, WHITE, 
                                (self.x - beam_width, ripple_y), 
                                (self.x + beam_width, ripple_y), 2)
        else:
            # Enhanced geometric energy orb design
            pulse = abs(math.sin(time_offset * 3))
            
            # Massive outer glow
            glow_surface = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            for i in range(3):
                glow_radius = self.size * (2 - i * 0.5)
                glow_alpha = int(80 - i * 20)
                pygame.draw.circle(glow_surface, (*self.color[:3], glow_alpha), 
                                 (self.size * 2, self.size * 2), int(glow_radius))
            screen.blit(glow_surface, (int(self.x - self.size * 2), int(self.y - self.size * 2)), 
                       special_flags=pygame.BLEND_ALPHA_SDL2)
            
            # Main orb body
            orb_size = int(self.size * (1 + pulse * 0.1))
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), orb_size)
            
            # Geometric pattern overlay - hexagonal energy matrix
            hex_points = []
            for i in range(6):
                angle = time_offset + i * math.pi / 3
                px = self.x + math.cos(angle) * self.size * 0.7
                py = self.y + math.sin(angle) * self.size * 0.7
                hex_points.append((px, py))
            
            # Draw hexagon outline
            if len(hex_points) > 2:
                pygame.draw.polygon(screen, WHITE, hex_points, 1)
            
            # Inner energy core - bright pulsing center
            core_size = int(self.size * 0.5 * (1 + pulse * 0.2))
            core_brightness = int(180 + pulse * 75)
            pygame.draw.circle(screen, (core_brightness, core_brightness, core_brightness), 
                             (int(self.x), int(self.y)), core_size)
            
            # Rotating energy trails
            for i in range(3):
                angle = time_offset * 2 + i * math.pi * 2 / 3
                trail_x = self.x + math.cos(angle) * self.size * 0.4
                trail_y = self.y + math.sin(angle) * self.size * 0.4
                pygame.draw.circle(screen, self.color, (int(trail_x), int(trail_y)), 2)
    
    def is_off_screen(self):
        """Check if bullet is off screen"""
        margin = 50
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or 
                self.y < -margin or self.y > GAME_AREA_HEIGHT + margin or
                self.lifetime > self.max_lifetime)
    
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)


class PlayerBullet(Bullet):
    """Player's bullet"""
    def __init__(self, x, y, angle=math.pi * 1.5, damage=PLAYER_BULLET_DAMAGE, bullet_type='normal'):
        super().__init__(x, y, angle, PLAYER_BULLET_SPEED, CYAN, damage)
        self.size = PLAYER_BULLET_SIZE
        self.bullet_type = bullet_type
        self.triggers_screen_shake = False  # Flag for screen shake
        
        # Adjust properties based on type
        if bullet_type == 'laser':
            self.size = 60  # Much larger beam
            self.speed = PLAYER_BULLET_SPEED * 2
            self.color = RED
            self.triggers_screen_shake = True
        elif bullet_type == 'burst':
            self.size = 10
            self.color = ORANGE
        elif bullet_type == 'rapid':
            self.size = 4
            self.damage *= 0.5
        elif bullet_type == 'homing':
            self.homing = True
            self.color = GREEN
            self.speed = PLAYER_BULLET_SPEED * 0.8


class BulletPattern:
    """Generates various bullet patterns"""
    
    @staticmethod
    def circle_pattern(x, y, num_bullets=16, speed=BULLET_SPEED, color=RED, offset_angle=0, damage=10):
        """Create a circle of bullets"""
        bullets = []
        angle_step = (2 * math.pi) / num_bullets
        for i in range(num_bullets):
            angle = i * angle_step + offset_angle
            bullets.append(Bullet(x, y, angle, speed, color, damage=damage))
        return bullets
    
    @staticmethod
    def spiral_pattern(x, y, num_bullets=20, speed=BULLET_SPEED, color=PURPLE, rotation=0, damage=10):
        """Create a spiral pattern"""
        bullets = []
        angle_step = (2 * math.pi) / 8  # 8 arms
        for i in range(num_bullets):
            angle = (i * angle_step / 2.5) + rotation
            bullets.append(Bullet(x, y, angle, speed + i * 0.1, color, damage=damage))
        return bullets
    
    @staticmethod
    def aimed_spread(x, y, target_x, target_y, num_bullets=5, spread=0.3, speed=BULLET_SPEED, color=YELLOW, damage=10):
        """Create a spread pattern aimed at target"""
        bullets = []
        base_angle = angle_to((x, y), (target_x, target_y))
        for i in range(num_bullets):
            offset = (i - num_bullets // 2) * spread
            angle = base_angle + offset
            bullets.append(Bullet(x, y, angle, speed, color, damage=damage))
        return bullets
    
    @staticmethod
    def wave_pattern(x, y, direction, num_bullets=10, speed=BULLET_SPEED, color=ORANGE, damage=10):
        """Create a wave pattern"""
        bullets = []
        for i in range(num_bullets):
            angle = direction + math.sin(i * 0.5) * 0.5
            bullets.append(Bullet(x, y, angle, speed, color, damage=damage))
        return bullets
    
    @staticmethod
    def random_burst(x, y, num_bullets=20, min_speed=2, max_speed=6, color=PINK, rng=None):
        """Create a random burst of bullets"""
        bullets = []
        if rng is None:
            import random
            rng = random
        for _ in range(num_bullets):
            angle = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(min_speed, max_speed)
            bullets.append(Bullet(x, y, angle, speed, color))
        return bullets
    
    @staticmethod
    def homing_bullets(x, y, num_bullets=5, speed=3, color=GREEN, damage=10):
        """Create homing bullets"""
        bullets = []
        angle_step = (2 * math.pi) / num_bullets
        for i in range(num_bullets):
            angle = i * angle_step
            bullets.append(Bullet(x, y, angle, speed, color, damage=damage, homing=True))
        return bullets
    
    @staticmethod
    def cross_pattern(x, y, speed=BULLET_SPEED, color=RED, thickness=3):
        """Create a cross/plus pattern"""
        bullets = []
        # Horizontal and vertical lines
        for i in range(thickness):
            offset = (i - thickness // 2) * 0.1
            bullets.append(Bullet(x, y, 0 + offset, speed, color))          # Right
            bullets.append(Bullet(x, y, math.pi + offset, speed, color))    # Left
            bullets.append(Bullet(x, y, math.pi/2 + offset, speed, color))  # Down
            bullets.append(Bullet(x, y, -math.pi/2 + offset, speed, color)) # Up
        return bullets
    
    @staticmethod
    def double_spiral(x, y, num_bullets=30, speed=BULLET_SPEED, color1=RED, color2=BLUE, rotation=0):
        """Create a double spiral pattern"""
        bullets = []
        for i in range(num_bullets):
            angle1 = (i * 0.3) + rotation
            angle2 = angle1 + math.pi
            bullets.append(Bullet(x, y, angle1, speed, color1))
            bullets.append(Bullet(x, y, angle2, speed, color2))
        return bullets
