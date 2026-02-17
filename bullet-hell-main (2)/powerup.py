"""
Power-up system for the bullet hell game
"""
import pygame
import math
from config import *
import sprites


class PowerUp:
    """Base power-up class"""
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.type = powerup_type
        self.size = POWERUP_SIZE
        self.speed = 2
        self.lifetime = 10000  # 10 seconds before disappearing
        self.pulse_timer = 0
        
        # Icon mapping for each powerup type
        self.icon_mapping = {
            'health': 1,            # Fresh Slice
            'damage': 2,            # Extra Spicy
            'speed': 3,             # Quick Crust
            'shield': 4,            # Cheese Shield
            'power': 5,             # Power Leaven
            'style': 6,             # Topping Variety
            'ultimate_type': 7,     # Ultimate Recipe
            'ability_glass_cannon': 8,   # Paper Thin Crust
            'ability_berserker': 9,      # Pizza Fury
            'ability_invincible': 10     # Brick Oven Force
        }
        
        # Set color based on type - Pizza themed!
        self.colors = {
            'health': (255, 200, 80),   # Golden crust
            'damage': (255, 50, 50),    # Red hot pepperoni
            'speed': (255, 215, 0),     # Golden yellow
            'shield': (255, 200, 100),  # Melted cheese
            'power': (255, 100, 50),    # Baked orange
            'style': (255, 140, 0),     # Deep orange
            'ultimate_type': (255, 69, 0),    # Brick red oven
            'ability_glass_cannon': (220, 180, 80),  # Crispy thin
            'ability_berserker': (255, 30, 30),      # Fiery hot
            'ability_invincible': (255, 165, 50)     # Brick oven glow
        }
        self.color = self.colors.get(powerup_type, WHITE)
    
    def update(self, dt):
        """Update power-up position"""
        self.y += self.speed
        self.lifetime -= dt
        self.pulse_timer += dt
    
    def draw(self, screen):
        """Draw pizza-themed powerups"""
        import math
        pulse = abs(math.sin(self.pulse_timer * 0.005))
        size = int(self.size * (0.8 + pulse * 0.4))
        
        if self.type == 'health':
            # Pizza slice
            slice_points = [
                (int(self.x), int(self.y - size * 0.9)),  # Top point
                (int(self.x + size * 0.8), int(self.y + size * 0.6)),  # Bottom right
                (int(self.x - size * 0.8), int(self.y + size * 0.6)),  # Bottom left
            ]
            pygame.draw.polygon(screen, (220, 80, 60), slice_points)  # Red sauce
            pygame.draw.polygon(screen, (255, 220, 130), slice_points, 3)  # Cheese outline
            pygame.draw.circle(screen, (200, 40, 40), (int(self.x), int(self.y - size * 0.2)), size // 4)  # Pepperoni
            
        elif self.type == 'damage':
            # Spicy pepperoni
            pygame.draw.circle(screen, (200, 40, 40), (int(self.x), int(self.y)), size + 2, 0)
            pygame.draw.circle(screen, (255, 100, 80), (int(self.x), int(self.y)), size)
            pygame.draw.circle(screen, (255, 200, 100), (int(self.x - size * 0.3), int(self.y - size * 0.3)), int(size * 0.4))
            
        elif self.type == 'speed':
            # Golden fast crust piece
            pygame.draw.circle(screen, (255, 215, 0), (int(self.x), int(self.y)), size, 0)
            pygame.draw.circle(screen, (255, 235, 100), (int(self.x), int(self.y)), int(size * 0.7))
            # Speed lines
            for i in range(3):
                angle = self.pulse_timer * 0.01 + i * math.pi / 1.5
                line_len = size * (0.5 + i * 0.3)
                end_x = self.x + math.cos(angle) * line_len
                end_y = self.y + math.sin(angle) * line_len
                pygame.draw.line(screen, (255, 255, 150), (int(self.x), int(self.y)), (int(end_x), int(end_y)), 2)
            
        elif self.type == 'shield':
            # Cheese shield circle
            pygame.draw.circle(screen, (255, 220, 130), (int(self.x), int(self.y)), size, 4)
            pygame.draw.circle(screen, (255, 240, 150), (int(self.x), int(self.y)), int(size * 0.7))
            # Shield lines
            for i in range(4):
                angle = i * math.pi / 2
                ex = self.x + math.cos(angle) * size * 0.8
                ey = self.y + math.sin(angle) * size * 0.8
                pygame.draw.line(screen, (255, 220, 130), (int(self.x), int(self.y)), (int(ex), int(ey)), 2)
            
        elif self.type == 'power':
            # Levain/dough power
            pygame.draw.circle(screen, (210, 180, 100), (int(self.x), int(self.y)), size, 0)
            pygame.draw.circle(screen, (240, 200, 140), (int(self.x), int(self.y)), int(size * 0.8))
            # Power rings
            for i in range(3):
                ring_size = int(size * (0.9 - i * 0.25))
                pygame.draw.circle(screen, (255, 200, 100), (int(self.x), int(self.y)), ring_size, 2)
            
        elif self.type == 'style':
            # Rainbow topping variety
            colors_variety = [(255, 100, 80), (80, 180, 80), (100, 150, 255), (255, 200, 100), (200, 100, 200)]
            for i in range(5):
                angle = self.pulse_timer * 0.005 + i * math.pi * 2 / 5
                seg_x = self.x + math.cos(angle) * size * 0.7
                seg_y = self.y + math.sin(angle) * size * 0.7
                pygame.draw.circle(screen, colors_variety[i], (int(seg_x), int(seg_y)), int(size * 0.4))
            pygame.draw.circle(screen, (255, 220, 130), (int(self.x), int(self.y)), int(size * 0.3))
            
        elif self.type == 'ultimate_type':
            # Pizza box
            box_size = size
            pygame.draw.rect(screen, (200, 100, 50), (int(self.x - box_size), int(self.y - box_size), box_size * 2, box_size * 2), 0)
            pygame.draw.rect(screen, (255, 150, 80), (int(self.x - box_size * 0.9), int(self.y - box_size * 0.9), box_size * 1.8, box_size * 1.8))
            pygame.draw.rect(screen, (200, 100, 50), (int(self.x - box_size), int(self.y - box_size), box_size * 2, box_size * 2), 3)
            # Box lid fold
            pygame.draw.line(screen, (200, 100, 50), (int(self.x - box_size * 0.8), int(self.y - box_size * 0.8)), (int(self.x + box_size * 0.8), int(self.y - box_size * 0.8)), 3)
            
        elif self.type == 'ability_glass_cannon':
            # Paper thin crispy crust
            pygame.draw.circle(screen, (220, 180, 100), (int(self.x), int(self.y)), size, 0)
            pygame.draw.circle(screen, (255, 200, 120), (int(self.x), int(self.y)), int(size * 0.8))
            # Thin crispy lines
            for i in range(8):
                angle = i * math.pi / 4
                ex = self.x + math.cos(angle) * size * 0.9
                ey = self.y + math.sin(angle) * size * 0.9
                pygame.draw.line(screen, (200, 160, 80), (int(self.x), int(self.y)), (int(ex), int(ey)), 1)
            
        elif self.type == 'ability_berserker':
            # Fiery hot pizza
            pygame.draw.circle(screen, (255, 50, 0), (int(self.x), int(self.y)), size, 0)
            pygame.draw.circle(screen, (255, 100, 0), (int(self.x), int(self.y)), int(size * 0.8))
            # Flame effects
            for i in range(6):
                flame_angle = self.pulse_timer * 0.01 + i * math.pi / 3
                flame_len = size * (0.6 + abs(math.sin(self.pulse_timer * 0.005 + i)) * 0.3)
                flame_x = self.x + math.cos(flame_angle) * flame_len
                flame_y = self.y + math.sin(flame_angle) * flame_len - size * 0.3
                pygame.draw.circle(screen, (255, 150, 0), (int(flame_x), int(flame_y)), int(size * 0.3))
            
        elif self.type == 'ability_invincible':
            # Brick oven force - golden glowing
            pygame.draw.circle(screen, (255, 200, 100), (int(self.x), int(self.y)), size, 3)
            pygame.draw.circle(screen, (255, 220, 140), (int(self.x), int(self.y)), int(size * 0.8))
            # Oven glow effect
            glow_surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            for i in range(3):
                glow_radius = size * (1.5 - i * 0.4)
                glow_alpha = int(100 - i * 25)
                pygame.draw.circle(glow_surface, (255, 200, 100, glow_alpha), (int(size * 2), int(size * 2)), int(glow_radius))
            screen.blit(glow_surface, (int(self.x - size * 2), int(self.y - size * 2)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
    
    def is_off_screen(self):
        """Check if power-up is off screen or expired"""
        return self.y > GAME_AREA_HEIGHT + 50 or self.lifetime <= 0
    
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(
            self.x - self.size,
            self.y - self.size,
            self.size * 2,
            self.size * 2
        )
    
    def apply(self, player):
        """Apply power-up effect to player"""
        import random
        if self.type == 'health':
            player.heal(30)
            return "Fresh Slice +30!"
        elif self.type == 'damage':
            player.add_damage_boost()
            return "Extra Spicy!"
        elif self.type == 'speed':
            player.speed = min(PLAYER_SPEED * 1.5, player.speed + 1)
            player.slow_speed = min(PLAYER_SLOW_SPEED * 1.5, player.slow_speed + 0.5)
            return "Quick Crust Boost!"
        elif self.type == 'shield':
            player.add_shield()
            return "Cheese Shield!"
        elif self.type == 'power':
            player.add_power()
            return f"Power Leaven {player.power_level}!"
        elif self.type == 'style':
            new_style = player.switch_style()
            style_names = {
                'normal': 'Classic Pies',
                'burst': 'Burst Bake',
                'laser': 'Laser Oven',
                'spread': 'Spread Toppings',
                'homing': 'Guided Slices',
                'rapid': 'Rapid Fire Oven'
            }
            return f"Topping: {style_names.get(new_style, new_style)}!"
        elif self.type == 'ultimate_type':
            new_type = player.switch_ultimate_type()
            ultimate_names = {
                'laser_grid': 'Square Slices',
                'clone': 'Clone Recipe'
            }
            return f"Ultimate: {ultimate_names.get(new_type, new_type)}!"
        elif self.type == 'ability_berserker':
            player.switch_ability_type('berserker')
            return "PIZZA FURY"
        elif self.type == 'ability_glass_cannon':
            player.switch_ability_type('glass_cannon')
            return "THIN CRUST"
        elif self.type == 'ability_invincible':
            player.switch_ability_type('invincible')
            return "BRICK OVEN"
        
        return "Pizza Power Up!"


def spawn_powerup(x, y, rng):
    """Spawn a random power-up"""
    if rng.random() < POWERUP_SPAWN_CHANCE:
        # 10% chance for ability type powerups
        if rng.random() < 0.1:
            powerup_type = rng.choice(['ability_berserker', 'ability_glass_cannon', 'ability_invincible'])
        else:
            powerup_type = rng.choice(['health', 'damage', 'power', 'shield', 'style', 'ultimate_type'])
        return PowerUp(x, y, powerup_type)
    return None
