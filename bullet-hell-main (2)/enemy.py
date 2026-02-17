"""
Enemy classes for the bullet hell game
"""
import pygame
import math
from config import *
from bullet import Bullet, BulletPattern
from utils import angle_to, distance
import sprites

class Enemy:
    """Base enemy class"""
    def __init__(self, x, y, health, stage_num, rng, wave_num=1, enemy_count=1, sprite_type='scout'):
        self.x = x
        self.y = y
        self.sprite_type = sprite_type  # Sprite type for rendering
        self.base_health = health
        self.stage_num = stage_num
        self.wave_num = wave_num
        self.rng = rng
        
        # Apply difficulty scaling (stage + wave)
        stage_scaling = (stage_num - 1)
        wave_scaling = (wave_num - 1) * 0.3  # Each wave adds 30% of a stage's difficulty
        total_difficulty = stage_scaling + wave_scaling
        
        self.health = health * (DIFFICULTY_SCALING['enemy_health'] ** total_difficulty)
        self.max_health = self.health
        
        # Scale size based on enemy count - more enemies = smaller size
        size_scale = max(0.4, 1.0 - (enemy_count / 60.0))  # Shrink as more enemies on screen
        self.size = int(ENEMY_BASE_SIZE * size_scale)
        self.size = max(ENEMY_MIN_SIZE, self.size)  # Minimum size
        
        self.speed = ENEMY_BASE_SPEED * (DIFFICULTY_SCALING['enemy_speed'] ** total_difficulty)
        self.bullet_speed = BULLET_SPEED * (DIFFICULTY_SCALING['bullet_speed'] ** total_difficulty)
        
        # Enemy damage scales with difficulty - base 10 damage, scales up per stage
        self.bullet_damage = 10 * (1.2 ** total_difficulty)  # 20% per stage/wave difficulty
        
        self.shoot_cooldown = 0
        self.shoot_timer = 0
        self.color = RED
        self.movement_timer = 0
        self.target_x = x
        self.target_y = y
        
        # Sprite cache for optimization
        self.sprite_cache = {}
        self.last_health_percent = None
    
    def update(self, dt, player):
        """Update enemy state"""
        self.movement_timer += dt
        self.shoot_timer += dt
        
        # Move towards target position
        if abs(self.x - self.target_x) > 2:
            self.x += (self.target_x - self.x) * 0.02
        if abs(self.y - self.target_y) > 2:
            self.y += (self.target_y - self.y) * 0.02
        
        bullets = []
        if self.shoot_timer >= self.shoot_cooldown:
            bullets = self.shoot(player)
            self.shoot_timer = 0
        
        return bullets
    
    def shoot(self, player):
        """Shoot bullets (override in subclasses)"""
        return []
    
    def take_damage(self, damage):
        """Take damage"""
        self.health -= damage
        return self.health <= 0
    
    def draw(self, screen):
        """Draw the enemy with sprites"""
        # Try to load sprite
        if sprites.sprite_loader:
            sprite = sprites.sprite_loader.get_enemy_sprite(self.sprite_type)
            if sprite:
                # Calculate health ratio for caching check
                health_ratio = self.health / self.max_health
                health_state = int(health_ratio * 3)  # 0-3 states
                
                # Use cached sprite if health state hasn't changed
                if health_state == self.last_health_percent and 'sprite' in self.sprite_cache:
                    scaled_sprite = self.sprite_cache['sprite']
                else:
                    # Scale sprite based on size (3x larger - not too big)
                    scaled_sprite = pygame.transform.scale(sprite, (int(self.size * 3), int(self.size * 3)))
                    self.sprite_cache['sprite'] = scaled_sprite
                    self.last_health_percent = health_state
                
                # Apply health-based color tint if needed
                # Tint removed - use health bar for damage indication instead
                
                rect = scaled_sprite.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(scaled_sprite, rect)
                
                # Draw health bar
                bar_width = self.size * 2
                bar_height = 4
                bar_x = self.x - bar_width / 2
                bar_y = self.y - self.size - 10
                
                # Dark background
                pygame.draw.rect(screen, (30, 30, 30), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
                # Red background
                pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
                # Health
                health_width = bar_width * (self.health / self.max_health)
                health_color = self.color if self.health / self.max_health > 0.3 else RED
                pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
                # Border
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
                return
        
        # Fallback to geometric drawing if sprites not loaded
        import math
        
        time_offset = pygame.time.get_ticks() * 0.002
        pulse = abs(math.sin(time_offset))
        
        # Glow effect
        glow_surf = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
        glow_color = (*self.color[:3], 60)
        for i in range(3):
            glow_radius = self.size * (1.5 - i * 0.3)
            pygame.draw.circle(glow_surf, glow_color, (self.size * 2, self.size * 2), int(glow_radius))
        screen.blit(glow_surf, (int(self.x - self.size * 2), int(self.y - self.size * 2)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Different designs based on enemy color/type
        if self.color == RED:  # BasicEnemy - Combat Drone
            # Triangular body
            points = [
                (self.x, self.y - self.size),
                (self.x - self.size * 0.8, self.y + self.size * 0.6),
                (self.x + self.size * 0.8, self.y + self.size * 0.6)
            ]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
            # Core
            pygame.draw.circle(screen, (255, 100, 100), (int(self.x), int(self.y)), int(self.size * 0.3))
            # Weapon hardpoints
            pygame.draw.circle(screen, RED, (int(self.x - self.size * 0.5), int(self.y + self.size * 0.3)), 3)
            pygame.draw.circle(screen, RED, (int(self.x + self.size * 0.5), int(self.y + self.size * 0.3)), 3)  # CircleEnemy - Rotating Disc Drone
            # Rotating outer ring
            num_segments = 8
            for i in range(num_segments):
                angle = (time_offset * 2 + i * math.pi * 2 / num_segments)
                x1 = self.x + math.cos(angle) * self.size
                y1 = self.y + math.sin(angle) * self.size
                pygame.draw.circle(screen, PURPLE, (int(x1), int(y1)), 4)
            # Main body
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size * 0.7))
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(self.size * 0.7), 2)
            # Central core
            pygame.draw.circle(screen, (200, 100, 255), (int(self.x), int(self.y)), int(self.size * 0.4))
            # Rotating energy lines
            for i in range(3):
                angle = time_offset * 2 + i * math.pi * 2 / 3
                end_x = self.x + math.cos(angle) * self.size * 0.6
                end_y = self.y + math.sin(angle) * self.size * 0.6
                pygame.draw.line(screen, PURPLE, (self.x, self.y), (end_x, end_y), 2)
                
        elif self.color == ORANGE:  # SpiralEnemy - Spinning Energy Construct
            # Octagonal body
            num_points = 8
            points = []
            for i in range(num_points):
                angle = time_offset * 3 + i * math.pi * 2 / num_points
                x = self.x + math.cos(angle) * self.size
                y = self.y + math.sin(angle) * self.size
                points.append((x, y))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
            # Spiral energy trails
            for i in range(4):
                angle = time_offset * 3 + i * math.pi / 2
                trail_length = self.size * 0.6
                start_x = self.x + math.cos(angle) * self.size * 0.3
                start_y = self.y + math.sin(angle) * self.size * 0.3
                end_x = self.x + math.cos(angle) * trail_length
                end_y = self.y + math.sin(angle) * trail_length
                pygame.draw.line(screen, ORANGE, (start_x, start_y), (end_x, end_y), 3)
            # Core
            pygame.draw.circle(screen, (255, 180, 100), (int(self.x), int(self.y)), int(self.size * 0.3))
            
        elif self.color == GREEN:  # HomingEnemy - Targeting Drone
            # Diamond body
            points = [
                (self.x, self.y - self.size),
                (self.x + self.size, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size, self.y)
            ]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
            # Sensor arrays (pulsing)
            sensor_size = int(5 + pulse * 3)
            pygame.draw.circle(screen, (100, 255, 100), (int(self.x), int(self.y - self.size * 0.5)), sensor_size)
            pygame.draw.circle(screen, (100, 255, 100), (int(self.x), int(self.y + self.size * 0.5)), sensor_size)
            # Targeting reticle
            reticle_size = int(self.size * 0.5)
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), reticle_size, 1)
            pygame.draw.line(screen, GREEN, (self.x - reticle_size, self.y), (self.x + reticle_size, self.y), 1)
            pygame.draw.line(screen, GREEN, (self.x, self.y - reticle_size), (self.x, self.y + reticle_size), 1)
            
        else:  # WaveEnemy (YELLOW) - Wave Emitter Drone
            # Hexagonal main body
            num_points = 6
            points = []
            for i in range(num_points):
                angle = i * math.pi * 2 / num_points
                x = self.x + math.cos(angle) * self.size * 0.8
                y = self.y + math.sin(angle) * self.size * 0.8
                points.append((x, y))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
            # Wave emitters (pulsing rings)
            for i in range(3):
                wave_offset = (time_offset * 5 + i * 0.5) % 2
                wave_radius = self.size * (0.3 + wave_offset * 0.4)
                wave_alpha = int(150 * (1 - wave_offset / 2))
                wave_surf = pygame.Surface((wave_radius * 4, wave_radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(wave_surf, (*YELLOW[:3], wave_alpha), (int(wave_radius * 2), int(wave_radius * 2)), int(wave_radius), 2)
                screen.blit(wave_surf, (int(self.x - wave_radius * 2), int(self.y - wave_radius * 2)), special_flags=pygame.BLEND_ALPHA_SDL2)
            # Central emitter core
            pygame.draw.circle(screen, (255, 255, 150), (int(self.x), int(self.y)), int(self.size * 0.3))
        
        # Draw health bar for fallback geometric enemies
        bar_width = self.size * 2
        bar_height = 4
        bar_x = self.x - bar_width / 2
        bar_y = self.y - self.size - 10
        
        # Dark background
        pygame.draw.rect(screen, (30, 30, 30), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        # Red background
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Health
        health_width = bar_width * (self.health / self.max_health)
        health_color = self.color if self.health / self.max_health > 0.3 else RED
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        # Border
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
    
    def get_rect(self):
        """Get collision rectangle - circular for pizza shape"""
        # Return a circular bounding box (approximate)
        return pygame.Rect(
            self.x - self.size * 0.7,
            self.y - self.size * 0.7,
            self.size * 1.4,
            self.size * 1.4
        )


class BasicEnemy(Enemy):
    """Basic enemy that shoots simple patterns"""
    def __init__(self, x, y, stage_num, rng, wave_num=1, enemy_count=1):
        super().__init__(x, y, ENEMY_HEALTH, stage_num, rng, wave_num, enemy_count, sprite_type='scout')
        self.shoot_cooldown = 2000
        self.color = RED
        self.target_y = 150
    
    def shoot(self, player):
        """Shoot aimed bullets at player"""
        return BulletPattern.aimed_spread(
            self.x, self.y, player.x, player.y,
            num_bullets=3, spread=0.2, speed=self.bullet_speed, color=RED,
            damage=int(self.bullet_damage)
        )


class CircleEnemy(Enemy):
    """Enemy that shoots in a circle pattern"""
    def __init__(self, x, y, stage_num, rng, wave_num=1, enemy_count=1):
        super().__init__(x, y, ENEMY_HEALTH * 1.5, stage_num, rng, wave_num, enemy_count, sprite_type='frigate')
        self.shoot_cooldown = 3000
        self.color = PURPLE
        self.target_y = 120
        self.rotation = 0
    
    def update(self, dt, player):
        """Update with rotation"""
        self.rotation += dt * 0.001
        return super().update(dt, player)
    
    def shoot(self, player):
        """Shoot in a circle"""
        return BulletPattern.circle_pattern(
            self.x, self.y, num_bullets=12, speed=self.bullet_speed,
            color=PURPLE, offset_angle=self.rotation, damage=int(self.bullet_damage)
        )


class SpiralEnemy(Enemy):
    """Enemy that shoots spiral patterns"""
    def __init__(self, x, y, stage_num, rng, wave_num=1, enemy_count=1):
        super().__init__(x, y, ENEMY_HEALTH * 1.3, stage_num, rng, wave_num, enemy_count, sprite_type='bomber')
        self.shoot_cooldown = 1500
        self.color = ORANGE
        self.target_y = 180
        self.rotation = 0
    
    def update(self, dt, player):
        """Update with rotation"""
        self.rotation += dt * 0.002
        return super().update(dt, player)
    
    def shoot(self, player):
        """Shoot spiral"""
        return BulletPattern.spiral_pattern(
            self.x, self.y, num_bullets=15, speed=self.bullet_speed,
            color=ORANGE, rotation=self.rotation, damage=int(self.bullet_damage)
        )


class HomingEnemy(Enemy):
    """Enemy that shoots homing bullets"""
    def __init__(self, x, y, stage_num, rng, wave_num=1, enemy_count=1):
        super().__init__(x, y, ENEMY_HEALTH * 0.8, stage_num, rng, wave_num, enemy_count, sprite_type='dreadnought')
        self.shoot_cooldown = 3500
        self.color = GREEN
        self.target_y = 140
    
    def shoot(self, player):
        """Shoot homing bullets"""
        return BulletPattern.homing_bullets(
            self.x, self.y, num_bullets=4, speed=self.bullet_speed * 0.6, color=GREEN,
            damage=int(self.bullet_damage)
        )


class WaveEnemy(Enemy):
    """Enemy that shoots wave patterns"""
    def __init__(self, x, y, stage_num, rng, wave_num=1, enemy_count=1):
        super().__init__(x, y, ENEMY_HEALTH, stage_num, rng, wave_num, enemy_count, sprite_type='battlecruiser')
        self.shoot_cooldown = 2500
        self.color = YELLOW
        self.target_y = 160
    
    def shoot(self, player):
        """Shoot wave pattern"""
        angle = angle_to((self.x, self.y), (player.x, player.y))
        return BulletPattern.wave_pattern(
            self.x, self.y, angle, num_bullets=8, speed=self.bullet_speed, color=YELLOW,
            damage=int(self.bullet_damage)
        )


def spawn_enemy(stage_num, rng, wave_num=1, enemy_count=1):
    """Spawn a random enemy based on stage and wave"""
    enemy_types = [BasicEnemy, CircleEnemy, SpiralEnemy, HomingEnemy, WaveEnemy]
    
    # Weight towards harder enemies in later stages and waves
    total_progress = stage_num + (wave_num - 1) * 0.3
    weights = [max(1, int(6 - total_progress)), 1, 1, 1, 1]
    
    enemy_class = rng.choices(enemy_types, weights=weights)[0]
    x = rng.randint(50, PLAYABLE_AREA_WIDTH - 50)
    y = -50
    
    return enemy_class(x, y, stage_num, rng, wave_num, enemy_count)
