"""
Boss classes for the bullet hell game
"""
import pygame
import math
from config import *
from bullet import Bullet, BulletPattern
from utils import angle_to, distance
from enemy import Enemy


class Boss(Enemy):
    """Base boss class"""
    def __init__(self, x, y, stage_num, rng, name="Boss"):
        base_health = BOSS_BASE_HEALTH
        super().__init__(x, y, base_health, stage_num, rng)
        self.health = base_health * (DIFFICULTY_SCALING['boss_health'] ** (stage_num - 1))
        self.max_health = self.health
        self.size = BOSS_SIZE
        self.name = name
        self.phase = 1
        self.max_phases = 3
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.current_attack = 0
        self.phase_transition_time = 0
        self.intro_time = 2000  # 2 seconds intro
        self.is_intro = True
        self.powerup_drop_timer = 0  # Timer for periodic powerup drops
        
    def update(self, dt, player):
        """Update boss"""
        if self.is_intro:
            self.intro_time -= dt
            if self.intro_time <= 0:
                self.is_intro = False
            return []
        
        self.attack_timer += dt
        self.movement_timer += dt
        self.powerup_drop_timer += dt
        
        # Phase transitions
        health_percent = self.health / self.max_health
        new_phase = self.max_phases - int(health_percent * self.max_phases)
        new_phase = max(1, min(self.max_phases, new_phase + 1))
        
        if new_phase != self.phase:
            self.phase = new_phase
            self.phase_transition_time = 1000
            self.attack_timer = 0
        
        if self.phase_transition_time > 0:
            self.phase_transition_time -= dt
            return []
        
        # Movement pattern
        self.update_movement(dt)
        
        # Attack pattern
        bullets = []
        if self.attack_timer >= self.attack_cooldown:
            bullets = self.attack(player)
            self.attack_timer = 0
            self.current_attack = (self.current_attack + 1) % self.get_num_attacks()
        
        return bullets
    
    def update_movement(self, dt):
        """Update boss movement (override in subclasses)"""
        # Default: gentle side-to-side movement (within playable area)
        self.target_x = PLAYABLE_AREA_WIDTH / 2 + math.sin(self.movement_timer * 0.001) * 150
        self.target_y = 150
        
        self.x += (self.target_x - self.x) * 0.01
        self.y += (self.target_y - self.y) * 0.01
        
        # Constrain to playable area (with margin for boss size)
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def attack(self, player):
        """Perform attack (override in subclasses)"""
        return []
    
    def get_num_attacks(self):
        """Get number of different attacks"""
        return 1
    
    def should_drop_powerup(self):
        """Check if boss should drop a powerup"""
        from config import BOSS_POWERUP_DROP_INTERVAL
        if self.powerup_drop_timer >= BOSS_POWERUP_DROP_INTERVAL:
            self.powerup_drop_timer = 0
            return True
        return False
    
    def draw(self, screen):
        """Draw the boss - massive intelligent machine design"""
        import math
        
        time_offset = pygame.time.get_ticks() * 0.001
        pulse = abs(math.sin(time_offset * 2))
        
        # Phase transition effect
        flash_intensity = 1.0
        if self.phase_transition_time > 0:
            flash = int(self.phase_transition_time / 100) % 2 == 0
            flash_intensity = 1.5 if flash else 0.7
        
        # Massive energy glow aura
        glow_surf = pygame.Surface((self.size * 5, self.size * 5), pygame.SRCALPHA)
        glow_color = (*self.color[:3], int(40 * flash_intensity))
        for i in range(5):
            glow_radius = self.size * (2.0 - i * 0.3)
            pygame.draw.circle(glow_surf, glow_color, (int(self.size * 2.5), int(self.size * 2.5)), int(glow_radius))
        screen.blit(glow_surf, (int(self.x - self.size * 2.5), int(self.y - self.size * 2.5)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Main chassis - octagonal structure
        num_points = 8
        main_points = []
        for i in range(num_points):
            angle = time_offset * 0.3 + i * math.pi * 2 / num_points
            x = self.x + math.cos(angle) * self.size * 0.9
            y = self.y + math.sin(angle) * self.size * 0.9
            main_points.append((x, y))
        
        # Draw main body with phase-dependent color
        body_color = tuple(min(255, int(c * flash_intensity)) for c in self.color[:3])
        pygame.draw.polygon(screen, body_color, main_points)
        pygame.draw.polygon(screen, WHITE, main_points, 3)
        
        # Inner defensive ring
        inner_ring_size = self.size * 0.7
        pygame.draw.circle(screen, (50, 50, 50), (int(self.x), int(self.y)), int(inner_ring_size))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(inner_ring_size), 3)
        
        # Phase-dependent visual evolution
        if self.phase >= 2:
            # Phase 2: Open weapon ports (rotating energy nodes)
            for i in range(6):
                angle = time_offset * 2 + i * math.pi * 2 / 6
                node_x = self.x + math.cos(angle) * self.size * 0.6
                node_y = self.y + math.sin(angle) * self.size * 0.6
                pygame.draw.circle(screen, self.color, (int(node_x), int(node_y)), 8)
                pygame.draw.circle(screen, WHITE, (int(node_x), int(node_y)), 8, 2)
                # Energy beams to center
                pygame.draw.line(screen, self.color, (self.x, self.y), (node_x, node_y), 2)
        
        if self.phase >= 3:
            # Phase 3: Overload state (chaotic energy arcs)
            for i in range(8):
                angle = time_offset * 5 + i * math.pi / 4
                arc_length = self.size * (0.8 + pulse * 0.3)
                arc_x = self.x + math.cos(angle) * arc_length
                arc_y = self.y + math.sin(angle) * arc_length
                arc_color = tuple(min(255, int(c * 1.5)) for c in self.color[:3])
                pygame.draw.line(screen, arc_color, (self.x, self.y), (arc_x, arc_y), 3)
        
        # Central core - pulsing energy reactor
        core_size = int(self.size * 0.3 * (1 + pulse * 0.2))
        core_brightness = int(200 + pulse * 55)
        pygame.draw.circle(screen, (core_brightness, core_brightness, core_brightness), (int(self.x), int(self.y)), core_size)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), core_size, 3)
        
        # Rotating scanner arrays (eyes replacement)
        for i in range(2):
            angle = time_offset + i * math.pi
            scanner_x = self.x + math.cos(angle) * self.size * 0.4
            scanner_y = self.y + math.sin(angle) * self.size * 0.4
            # Scanner housing
            pygame.draw.circle(screen, (100, 100, 100), (int(scanner_x), int(scanner_y)), 10)
            # Scanner lens
            pygame.draw.circle(screen, RED, (int(scanner_x), int(scanner_y)), 6)
            pygame.draw.circle(screen, (255, 100, 100), (int(scanner_x), int(scanner_y)), 3)
        
        # Health bar - futuristic HUD style (positioned in playable area, not at top)
        bar_width = 550
        bar_height = 30
        bar_x = 50
        bar_y = 250  # Moved down from top to avoid panel overlap
        
        # Dark background with border
        pygame.draw.rect(screen, (20, 20, 20), (bar_x - 3, bar_y - 3, bar_width + 6, bar_height + 6))
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Health segments (multiple bars for visual interest)
        health_width = max(0, bar_width * (self.health / self.max_health))
        
        # Color changes based on health
        if self.health / self.max_health > 0.6:
            health_color = NEON_GREEN
            health_glow = (100, 255, 100)
        elif self.health / self.max_health > 0.3:
            health_color = ORANGE
            health_glow = (255, 180, 50)
        else:
            health_color = RED
            health_glow = (255, 50, 50)
        
        # Glowing health bar (only draw if health > 0)
        if health_width > 0:
            glow_surf = pygame.Surface((int(health_width), bar_height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*health_glow, 100), (0, 0, int(health_width), bar_height))
            screen.blit(glow_surf, (bar_x, bar_y), special_flags=pygame.BLEND_ALPHA_SDL2)
            
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Segmented appearance
        segment_width = bar_width / 20
        for i in range(20):
            segment_x = bar_x + i * segment_width
            pygame.draw.line(screen, (30, 30, 30), (segment_x, bar_y), (segment_x, bar_y + bar_height), 2)
        
        # Border
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Corner accents
        accent_size = 6
        pygame.draw.line(screen, CYAN, (bar_x - 3, bar_y - 3), (bar_x + accent_size, bar_y - 3), 2)
        pygame.draw.line(screen, CYAN, (bar_x - 3, bar_y - 3), (bar_x - 3, bar_y + accent_size), 2)
        pygame.draw.line(screen, CYAN, (bar_x + bar_width + 3, bar_y - 3), (bar_x + bar_width - accent_size, bar_y - 3), 2)
        pygame.draw.line(screen, CYAN, (bar_x + bar_width + 3, bar_y - 3), (bar_x + bar_width + 3, bar_y + accent_size), 2)
        
        # Boss name and phase with futuristic font
        font = pygame.font.Font(None, 28)
        phase_text = f"PHASE {self.phase}"
        name_text = f"{self.name.upper()}"
        
        # Draw name with glow
        name_surface = font.render(name_text, True, WHITE)
        phase_surface = font.render(phase_text, True, CYAN)
        
        screen.blit(name_surface, (bar_x, bar_y - 30))
        screen.blit(phase_surface, (bar_x + bar_width - phase_surface.get_width(), bar_y - 30))


class InfernoOven(Boss):
    """Boss 1: Raging inferno oven - spins with sharp angular design"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "INFERNO OVEN")
        self.color = RED
        self.attack_cooldown = 1500
        self.rotation = 0
    
    def update_movement(self, dt):
        self.rotation += dt * 0.001
        super().update_movement(dt)
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Circle pattern
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=16 + self.phase * 4,
                speed=self.bullet_speed, color=RED, offset_angle=self.rotation
            )
        elif self.current_attack == 1:
            # Double circle
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=12, speed=self.bullet_speed, color=RED
            )
            bullets += BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=12, speed=self.bullet_speed * 0.7,
                color=ORANGE, offset_angle=math.pi / 12
            )
        else:
            # Spiral
            bullets = BulletPattern.spiral_pattern(
                self.x, self.y, num_bullets=20 + self.phase * 5,
                speed=self.bullet_speed, color=RED, rotation=self.rotation
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a whole pizza with pepperoni"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Pizza crust - golden circle
        pygame.draw.circle(screen, (210, 180, 100), (int(self.x), int(self.y)), int(self.size), 0)
        
        # Cheese layer
        pygame.draw.circle(screen, (255, 220, 130), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
        
        # Crust edge
        pygame.draw.circle(screen, (210, 180, 100), (int(self.x), int(self.y)), int(self.size), 3)
        
        # Red sauce base
        pygame.draw.circle(screen, (220, 80, 60), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Pepperoni - red circles with varying sizes
        num_pepperoni = 12 + self.phase * 3
        for i in range(num_pepperoni):
            angle = self.rotation + i * math.pi * 2 / num_pepperoni
            pep_dist = self.size * (0.3 + (i % 3) * 0.2)
            pep_x = self.x + math.cos(angle) * pep_dist
            pep_y = self.y + math.sin(angle) * pep_dist
            pep_size = int(8 + abs(math.sin(time_offset * 2 + i)) * 4)
            pygame.draw.circle(screen, (200, 40, 40), (int(pep_x), int(pep_y)), pep_size)
            pygame.draw.circle(screen, (255, 100, 80), (int(pep_x), int(pep_y)), pep_size - 2)
        
        # Health bar
        self._draw_health_bar(screen)
    
    def _draw_health_bar(self, screen):
        """Draw health bar base method"""
        bar_width = 250
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 40)
        
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        
        pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class PepperoniSerpent(Boss):
    """Boss 2: Sinuous pepperoni snake - undulating wispy design"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "PEPPERONI SERPENT")
        self.color = PURPLE
        self.attack_cooldown = 1350
        self.sine_offset = 0
    
    def update_movement(self, dt):
        # Serpentine movement
        self.sine_offset += dt * 0.002
        self.target_x = PLAYABLE_AREA_WIDTH / 2 + math.sin(self.sine_offset) * 200
        self.target_y = 180 + math.cos(self.sine_offset * 0.7) * 30
        
        self.x += (self.target_x - self.x) * 0.02
        self.y += (self.target_y - self.y) * 0.02
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Aimed spread
            bullets = BulletPattern.aimed_spread(
                self.x, self.y, player.x, player.y,
                num_bullets=5 + self.phase * 2, spread=0.3,
                speed=self.bullet_speed, color=PURPLE
            )
        elif self.current_attack == 1:
            # Wave pattern
            angle = angle_to((self.x, self.y), (player.x, player.y))
            bullets = BulletPattern.wave_pattern(
                self.x, self.y, angle, num_bullets=10 + self.phase * 2,
                speed=self.bullet_speed, color=PINK
            )
        else:
            # Cross pattern
            bullets = BulletPattern.cross_pattern(
                self.x, self.y, speed=self.bullet_speed, color=PURPLE, thickness=3 + self.phase
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a serpent made of pizza slices"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Pizza slice segments forming a serpent
        num_segments = 8
        for i in range(num_segments):
            offset = i / num_segments
            wave_x = self.x + math.sin(time_offset * 2 + offset * 4) * (self.size * 0.5)
            wave_y = self.y - (self.size * 0.8) + (i * self.size * 0.25)
            seg_size = int(self.size * (0.8 - offset * 0.3))
            
            # Draw pizza slice (triangular)
            slice_points = [
                (wave_x, wave_y - seg_size * 0.5),  # Top point
                (wave_x + seg_size * 0.6, wave_y + seg_size * 0.4),  # Bottom right
                (wave_x - seg_size * 0.6, wave_y + seg_size * 0.4),  # Bottom left
            ]
            pygame.draw.polygon(screen, (220, 80, 60), slice_points)  # Red sauce
            pygame.draw.polygon(screen, (255, 220, 130), slice_points, 2)  # Cheese outline
            
            # Pepperoni on slice
            pygame.draw.circle(screen, (200, 40, 40), (int(wave_x), int(wave_y)), int(seg_size * 0.3))
        
        # Head - large pizza slice
        head_size = int(self.size * 0.5)
        head_points = [
            (int(self.x), int(self.y) - head_size),
            (int(self.x) + head_size, int(self.y) + head_size * 0.5),
            (int(self.x) - head_size, int(self.y) + head_size * 0.5),
        ]
        pygame.draw.polygon(screen, (210, 180, 100), head_points)
        pygame.draw.polygon(screen, (255, 220, 130), head_points, 3)
        
        # Health bar
        bar_width = 250
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y + self.size + 30)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class FreezPizzaMaker(Boss):
    """Boss 3: Frozen ice pizza crafting guardian - crystalline geometric design"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "FROZEN PIZZA MAKER")
        self.color = CYAN
        self.attack_cooldown = 1650
        self.orbital_angle = 0
    
    def update_movement(self, dt):
        # Orbital movement
        self.orbital_angle += dt * 0.0015
        radius = 120
        self.target_x = PLAYABLE_AREA_WIDTH / 2 + math.cos(self.orbital_angle) * radius
        self.target_y = 200 + math.sin(self.orbital_angle) * 50
        
        self.x += (self.target_x - self.x) * 0.015
        self.y += (self.target_y - self.y) * 0.015
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Homing bullets
            bullets = BulletPattern.homing_bullets(
                self.x, self.y, num_bullets=4 + self.phase,
                speed=self.bullet_speed * 0.7, color=GREEN
            )
        elif self.current_attack == 1:
            # Random burst
            bullets = BulletPattern.random_burst(
                self.x, self.y, num_bullets=15 + self.phase * 5,
                min_speed=self.bullet_speed * 0.5, max_speed=self.bullet_speed * 1.5,
                color=CYAN, rng=self.rng
            )
        else:
            # Circle with homing
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=12, speed=self.bullet_speed, color=CYAN
            )
            bullets += BulletPattern.homing_bullets(
                self.x, self.y, num_bullets=3, speed=self.bullet_speed * 0.6, color=GREEN
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a frozen pizza with ice crystals"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Frozen pizza - lighter colors (ice crusted)
        pygame.draw.circle(screen, (200, 220, 240), (int(self.x), int(self.y)), int(self.size), 0)
        
        # Icy cheese base
        pygame.draw.circle(screen, (220, 230, 250), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
        
        # Crust edge
        pygame.draw.circle(screen, (150, 180, 220), (int(self.x), int(self.y)), int(self.size), 3)
        
        # Frozen toppings (lighter versions)
        pygame.draw.circle(screen, (180, 200, 240), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Ice crystal toppings instead of pepperoni
        for i in range(6):
            angle = self.orbital_angle + i * math.pi / 3
            px = self.x + math.cos(angle) * self.size * 0.9
            py = self.y + math.sin(angle) * self.size * 0.9
            # Ice shards
            for j in range(3):
                sub_angle = angle + j * 0.3
                sx = px + math.cos(sub_angle) * 15
                sy = py + math.sin(sub_angle) * 15
                pygame.draw.line(screen, (100, 200, 255), (int(px), int(py)), (int(sx), int(sy)), 2)
        
        # Pulsing frozen core
        core = int(self.size * 0.3 * (1 + abs(math.sin(time_offset * 2)) * 0.3))
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), core)
        
        # Health bar  
        bar_width = 250
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y + self.size + 30)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (20, 40, 60), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class MegaPizzaTitan(Boss):
    """Boss 4: Massive mega pizza giant - spiky aggressive design"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "MEGA PIZZA TITAN")
        self.color = ORANGE
        self.attack_cooldown = 1200
        self.rotation = 0
    
    def update_movement(self, dt):
        self.rotation += dt * 0.002
        # Aggressive movement toward player
        self.target_x = PLAYABLE_AREA_WIDTH / 2
        self.target_y = 200
        
        self.x += (self.target_x - self.x) * 0.01
        self.y += (self.target_y - self.y) * 0.01
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Double spiral
            bullets = BulletPattern.double_spiral(
                self.x, self.y, num_bullets=25 + self.phase * 5,
                speed=self.bullet_speed, color1=ORANGE, color2=RED, rotation=self.rotation
            )
        elif self.current_attack == 1:
            # Cross pattern
            bullets = BulletPattern.cross_pattern(
                self.x, self.y, speed=self.bullet_speed * 1.2,
                color=ORANGE, thickness=4 + self.phase
            )
        else:
            # Aimed spiral
            bullets = BulletPattern.spiral_pattern(
                self.x, self.y, num_bullets=18 + self.phase * 4,
                speed=self.bullet_speed * 1.1, color=RED, rotation=self.rotation
            )
            bullets += BulletPattern.aimed_spread(
                self.x, self.y, player.x, player.y,
                num_bullets=3, spread=0.15, speed=self.bullet_speed * 1.3, color=YELLOW
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a massive super pizza with many toppings"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Extra large pizza base
        pygame.draw.circle(screen, (210, 180, 100), (int(self.x), int(self.y)), int(self.size), 0)
        
        # Cheese layer
        pygame.draw.circle(screen, (255, 220, 130), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
        
        # Crust edge
        pygame.draw.circle(screen, (210, 180, 100), (int(self.x), int(self.y)), int(self.size), 3)
        
        # Red sauce
        pygame.draw.circle(screen, (220, 80, 60), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Many different toppings - pepperoni, mushrooms, etc
        num_toppings = 20 + self.phase * 5
        for i in range(num_toppings):
            angle = self.rotation + i * math.pi * 2 / num_toppings
            topping_dist = self.size * (0.2 + (i % 4) * 0.18)
            top_x = self.x + math.cos(angle) * topping_dist
            top_y = self.y + math.sin(angle) * topping_dist
            
            # Different toppings
            if i % 3 == 0:
                # Pepperoni
                topping_size = int(6 + abs(math.sin(time_offset * 2 + i)) * 3)
                pygame.draw.circle(screen, (200, 40, 40), (int(top_x), int(top_y)), topping_size)
                pygame.draw.circle(screen, (255, 100, 80), (int(top_x), int(top_y)), topping_size - 1)
            elif i % 3 == 1:
                # Mushroom (brown)
                topping_size = int(5 + abs(math.sin(time_offset * 1.5 + i)) * 2)
                pygame.draw.circle(screen, (150, 100, 50), (int(top_x), int(top_y)), topping_size)
            else:
                # Green pepper
                pygame.draw.circle(screen, (100, 150, 100), (int(top_x), int(top_y)), 4)
        
        # Health bar
        bar_width = 280
        bar_height = 25
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 50)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (40, 20, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class IcedPizzaQueen(Boss):
    """Boss 5: Iced pizza queen - geometric ice design"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "ICED PIZZA QUEEN")
        self.color = (100, 200, 255)
        self.attack_cooldown = 1875
        self.rotation = 0
    
    def update_movement(self, dt):
        self.rotation += dt * 0.0008
        # Slow, minimal movement
        self.target_x = PLAYABLE_AREA_WIDTH / 2 + math.sin(self.movement_timer * 0.0008) * 100
        self.target_y = 200
        
        self.x += (self.target_x - self.x) * 0.008
        self.y += (self.target_y - self.y) * 0.008
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 2
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Dense circle patterns
            for i in range(3):
                bullets += BulletPattern.circle_pattern(
                    self.x, self.y, num_bullets=20,
                    speed=self.bullet_speed * (0.6 + i * 0.2),
                    color=self.color, offset_angle=self.rotation + i * 0.2
                )
        else:
            # Snowflake pattern (6-way symmetry)
            for i in range(6):
                angle = i * math.pi / 3 + self.rotation
                for j in range(3):
                    bullets.append(Bullet(
                        self.x, self.y, angle + j * 0.1 - 0.1,
                        self.bullet_speed * 0.8, self.color
                    ))
        
        return bullets
    
    def draw(self, screen):
        """Draw as an iced pizza with elegant design"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Ornate frozen pizza
        pygame.draw.circle(screen, (220, 240, 250), (int(self.x), int(self.y)), int(self.size), 0)
        pygame.draw.circle(screen, (240, 245, 255), (int(self.x), int(self.y)), int(self.size * 0.92), 0)
        pygame.draw.circle(screen, (180, 220, 245), (int(self.x), int(self.y)), int(self.size), 2)
        
        # Icy sauce base
        pygame.draw.circle(screen, (200, 210, 240), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Elegant snowflake pattern (6-way symmetry)
        for i in range(6):
            angle = self.rotation + i * math.pi / 3
            # Decorative ice lines
            for j in range(3):
                radius = self.size * (0.4 + j * 0.15)
                ex = self.x + math.cos(angle) * radius
                ey = self.y + math.sin(angle) * radius
                pygame.draw.line(screen, (100, 180, 255), (int(self.x), int(self.y)), (int(ex), int(ey)), 2)
            
            # Ice crystal toppings at points
            px = self.x + math.cos(angle) * self.size * 0.75
            py = self.y + math.sin(angle) * self.size * 0.75
            pygame.draw.circle(screen, (200, 240, 255), (int(px), int(py)), 8)
            pygame.draw.circle(screen, (100, 200, 255), (int(px), int(py)), 8, 2)
        
        # Pulsing frozen center
        core = int(self.size * 0.25 * (1 + abs(math.sin(time_offset * 2)) * 0.3))
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), core)
        
        # Health bar  
        bar_width = 250
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y + self.size + 30)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (20, 40, 60), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class CrispyBakerMaster(Boss):
    """Boss 6: Fast crispy baker - erratic dashing attacks"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "CRISPY BAKER MASTER")
        self.color = YELLOW
        self.attack_cooldown = 900
        self.dash_timer = 0
        self.dash_duration = 0
    
    def update_movement(self, dt):
        self.dash_timer += dt
        
        if self.dash_timer > 3000:
            # Quick dash
            self.dash_timer = 0
            self.dash_duration = 300
            self.target_x = self.rng.randint(100, PLAYABLE_AREA_WIDTH - 100)
        
        if self.dash_duration > 0:
            self.dash_duration -= dt
            self.x += (self.target_x - self.x) * 0.3
        else:
            # Erratic movement
            self.target_y = 200
            self.x += (self.target_x - self.x) * 0.015
            self.y += (self.target_y - self.y) * 0.015
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Lightning bolts (aimed spreads)
            for i in range(3):
                bullets += BulletPattern.aimed_spread(
                    self.x, self.y, player.x, player.y,
                    num_bullets=3, spread=0.2 + i * 0.1,
                    speed=self.bullet_speed * (1.2 + i * 0.1), color=YELLOW
                )
        elif self.current_attack == 1:
            # Random burst
            bullets = BulletPattern.random_burst(
                self.x, self.y, num_bullets=20 + self.phase * 5,
                min_speed=self.bullet_speed * 0.8, max_speed=self.bullet_speed * 1.8,
                color=YELLOW, rng=self.rng
            )
        else:
            # Wave patterns in multiple directions
            for angle in [0, math.pi/2, math.pi, -math.pi/2]:
                bullets += BulletPattern.wave_pattern(
                    self.x, self.y, angle, num_bullets=6,
                    speed=self.bullet_speed * 1.1, color=YELLOW
                )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a crispy golden pizza"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Golden crispy crust
        pygame.draw.circle(screen, (220, 180, 80), (int(self.x), int(self.y)), int(self.size), 0)
        pygame.draw.circle(screen, (255, 200, 100), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
        pygame.draw.circle(screen, (210, 160, 60), (int(self.x), int(self.y)), int(self.size), 3)
        
        # Golden cheese topping
        pygame.draw.circle(screen, (255, 220, 130), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Crispy pepperoni - golden red
        num_pepperoni = 10
        for i in range(num_pepperoni):
            angle = time_offset * 3 + i * math.pi * 2 / num_pepperoni
            pep_dist = self.size * (0.35 + (i % 2) * 0.25)
            pep_x = self.x + math.cos(angle) * pep_dist
            pep_y = self.y + math.sin(angle) * pep_dist
            pep_size = int(8 + abs(math.sin(time_offset * 4 + i)) * 3)
            pygame.draw.circle(screen, (220, 100, 60), (int(pep_x), int(pep_y)), pep_size)
            pygame.draw.circle(screen, (255, 140, 100), (int(pep_x), int(pep_y)), pep_size - 2)
        
        # Dash effect glow when sprinting
        if self.dash_duration > 0:
            dash_alpha = int(150 * (self.dash_duration / 300))
            dash_surf = pygame.Surface((int(self.size * 2.5), int(self.size * 2.5)), pygame.SRCALPHA)
            pygame.draw.circle(dash_surf, (255, 220, 0, dash_alpha), (int(self.size * 1.25), int(self.size * 1.25)), int(self.size * 0.8))
            screen.blit(dash_surf, (int(self.x - self.size * 1.25), int(self.y - self.size * 1.25)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Health bar
        bar_width = 240
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 40)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (30, 30, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class ShadowChefPhantom(Boss):
    """Boss 7: Sneaky shadow pizza chef - teleporting with surprise attacks"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "SHADOW PIZZA CHEF")
        self.color = (80, 0, 80)
        self.attack_cooldown = 1500  # Reduced from 2000
        self.teleport_timer = 0
        self.is_visible = True
    
    def update_movement(self, dt):
        self.teleport_timer += dt
        
        if self.teleport_timer > 4000:
            # Teleport
            self.teleport_timer = 0
            self.x = self.rng.randint(100, SCREEN_WIDTH - 100)
            self.y = self.rng.randint(100, 250)
            self.is_visible = False
        
        if self.teleport_timer > 500:
            self.is_visible = True
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        if not self.is_visible:
            return []
        
        bullets = []
        
        if self.current_attack == 0:
            # Spiral from current position
            bullets = BulletPattern.spiral_pattern(
                self.x, self.y, num_bullets=20 + self.phase * 4,
                speed=self.bullet_speed, color=self.color, rotation=self.movement_timer * 0.001
            )
        elif self.current_attack == 1:
            # Circle explosion
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=24 + self.phase * 4,
                speed=self.bullet_speed * 1.1, color=PURPLE
            )
        else:
            # Homing + aimed
            bullets = BulletPattern.homing_bullets(
                self.x, self.y, num_bullets=5 + self.phase,
                speed=self.bullet_speed * 0.7, color=GREEN
            )
            bullets += BulletPattern.aimed_spread(
                self.x, self.y, player.x, player.y,
                num_bullets=5, spread=0.25, speed=self.bullet_speed, color=self.color
            )
        
        return bullets
    
    def draw(self, screen):
        if not self.is_visible:
            # Draw faint shadow pizza
            pygame.draw.circle(screen, (100, 80, 100), (int(self.x), int(self.y)), int(self.size), 0)
            pygame.draw.circle(screen, (120, 100, 120), (int(self.x), int(self.y)), int(self.size * 0.9), 0)
        else:
            # Dark shadow pizza with ghostly appearance
            pygame.draw.circle(screen, (80, 60, 80), (int(self.x), int(self.y)), int(self.size), 0)
            pygame.draw.circle(screen, (120, 100, 120), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
            pygame.draw.circle(screen, (80, 60, 80), (int(self.x), int(self.y)), int(self.size), 3)
            
            # Dark sauce
            pygame.draw.circle(screen, (100, 50, 80), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
            
            # Shadow pepperoni
            import math
            time_offset = pygame.time.get_ticks() * 0.001
            num_pepperoni = 8
            for i in range(num_pepperoni):
                angle = time_offset * 2 + i * math.pi * 2 / num_pepperoni
                pep_dist = self.size * (0.3 + (i % 2) * 0.2)
                pep_x = self.x + math.cos(angle) * pep_dist
                pep_y = self.y + math.sin(angle) * pep_dist
                pygame.draw.circle(screen, (150, 40, 80), (int(pep_x), int(pep_y)), 6)
            
            # Health bar
            bar_width = 250
            bar_height = 20
            bar_x = int(self.x - bar_width / 2)
            bar_y = int(self.y - self.size - 40)
            health_width = bar_width * (self.health / self.max_health)
            health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
            pygame.draw.rect(screen, (30, 10, 30), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class PrismaPizza(Boss):
    """Boss 8: Geometric pizza patterns"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "PRISMA PIZZA")
        self.color = (200, 100, 255)
        self.attack_cooldown = 1425  # Reduced from 1900
        self.rotation = 0
    
    def update_movement(self, dt):
        self.rotation += dt * 0.0012
        # Square movement pattern
        cycle = (self.movement_timer * 0.0003) % 4
        if cycle < 1:
            self.target_x = 150
            self.target_y = 180
        elif cycle < 2:
            self.target_x = PLAYABLE_AREA_WIDTH - 150
            self.target_y = 180
        elif cycle < 3:
            self.target_x = PLAYABLE_AREA_WIDTH - 150
            self.target_y = 280
        else:
            self.target_x = 150
            self.target_y = 280
        
        self.x += (self.target_x - self.x) * 0.015
        self.y += (self.target_y - self.y) * 0.015
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 3
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Square pattern
            for angle in [0, math.pi/2, math.pi, -math.pi/2]:
                for i in range(4 + self.phase):
                    offset = (i - 2) * 0.1
                    bullets.append(Bullet(
                        self.x, self.y, angle + offset,
                        self.bullet_speed, self.color
                    ))
        elif self.current_attack == 1:
            # Rotating cross
            bullets = BulletPattern.cross_pattern(
                self.x, self.y, speed=self.bullet_speed,
                color=self.color, thickness=4 + self.phase
            )
            # Add rotated cross
            for angle in [math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4]:
                for i in range(3):
                    offset = (i - 1) * 0.08
                    bullets.append(Bullet(
                        self.x, self.y, angle + offset,
                        self.bullet_speed, PURPLE
                    ))
        else:
            # Hexagon pattern
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=6,
                speed=self.bullet_speed * 1.2, color=self.color, offset_angle=self.rotation
            )
            bullets += BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=12,
                speed=self.bullet_speed * 0.8, color=PURPLE, offset_angle=-self.rotation
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a prismatic multi-colored pizza"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Base crust
        pygame.draw.circle(screen, (180, 140, 100), (int(self.x), int(self.y)), int(self.size), 0)
        pygame.draw.circle(screen, (210, 180, 130), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
        pygame.draw.circle(screen, (180, 140, 100), (int(self.x), int(self.y)), int(self.size), 3)
        
        # Prismatic sauce sections - rotating quadrants
        for i in range(4):
            angle_start = self.rotation + i * math.pi / 2
            angle_end = self.rotation + (i + 1) * math.pi / 2
            
            # Different colored sauce sections
            colors = [(220, 80, 60), (200, 200, 100), (100, 150, 220), (200, 100, 200)]
            
            # Draw slice sector
            points = [(int(self.x), int(self.y))]
            steps = 20
            for j in range(steps + 1):
                angle = angle_start + (angle_end - angle_start) * j / steps
                px = self.x + math.cos(angle) * self.size * 0.8
                py = self.y + math.sin(angle) * self.size * 0.8
                points.append((int(px), int(py)))
            pygame.draw.polygon(screen, colors[i], points)
        
        # Prismatic cheese spots
        for i in range(8):
            angle = self.rotation + i * math.pi / 4
            cheese_x = self.x + math.cos(angle) * self.size * 0.5
            cheese_y = self.y + math.sin(angle) * self.size * 0.5
            cheese_colors = [(255, 255, 100), (255, 200, 150), (200, 255, 150), (150, 255, 200)]
            pygame.draw.circle(screen, cheese_colors[i % 4], (int(cheese_x), int(cheese_y)), 8)
        
        # Pulsing prismatic core
        core = int(self.size * 0.3 * (1 + abs(math.sin(time_offset * 3)) * 0.3))
        core_color = (200, 100, 255)
        pygame.draw.circle(screen, core_color, (int(self.x), int(self.y)), core)
        
        # Health bar
        bar_width = 250
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 40)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class ChaosChefNightmare(Boss):
    """Boss 9: Chaotic pizza chef nightmare - unpredictable"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "CHAOS PIZZA CHEF")
        self.color = (150, 0, 0)
        self.attack_cooldown = 1050  # Reduced from 1400
    
    def update_movement(self, dt):
        # Chaotic movement
        if self.movement_timer % 2000 < dt:
            self.target_x = self.rng.randint(80, PLAYABLE_AREA_WIDTH - 80)
            self.target_y = self.rng.randint(150, 300)
        
        self.x += (self.target_x - self.x) * 0.025
        self.y += (self.target_y - self.y) * 0.025
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 4
    
    def attack(self, player):
        bullets = []
        
        attack_choice = self.rng.randint(0, 3 + self.phase)
        
        if attack_choice == 0:
            bullets = BulletPattern.random_burst(
                self.x, self.y, num_bullets=25 + self.phase * 5,
                min_speed=self.bullet_speed * 0.5, max_speed=self.bullet_speed * 1.5,
                color=self.color, rng=self.rng
            )
        elif attack_choice == 1:
            bullets = BulletPattern.spiral_pattern(
                self.x, self.y, num_bullets=22,
                speed=self.bullet_speed, color=RED, rotation=self.rng.random() * math.pi * 2
            )
        elif attack_choice == 2:
            bullets = BulletPattern.aimed_spread(
                self.x, self.y, player.x, player.y,
                num_bullets=7 + self.phase, spread=0.4,
                speed=self.bullet_speed * 1.2, color=ORANGE
            )
        else:
            # Mix of everything
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=16, speed=self.bullet_speed, color=self.color
            )
            bullets += BulletPattern.homing_bullets(
                self.x, self.y, num_bullets=3, speed=self.bullet_speed * 0.6, color=GREEN
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as a chaotic swirling pizza with dark red chaos"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Chaotic base
        pygame.draw.circle(screen, (120, 60, 60), (int(self.x), int(self.y)), int(self.size), 0)
        pygame.draw.circle(screen, (180, 80, 80), (int(self.x), int(self.y)), int(self.size * 0.95), 0)
        pygame.draw.circle(screen, (100, 40, 40), (int(self.x), int(self.y)), int(self.size), 3)
        
        # Swirling chaotic sauce
        pygame.draw.circle(screen, (150, 50, 50), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Chaotic pepperoni in random positions
        num_pepperoni = 12 + self.phase * 2
        for i in range(num_pepperoni):
            angle = time_offset * 5 + i * math.pi * 2 / num_pepperoni + self.rng.random() * 0.5
            pep_dist = self.size * (0.25 + (i % 3) * 0.2)
            pep_x = self.x + math.cos(angle) * pep_dist
            pep_y = self.y + math.sin(angle) * pep_dist
            pep_size = int(5 + abs(math.sin(time_offset * 3 + i)) * 3)
            pygame.draw.circle(screen, (200, 30, 30), (int(pep_x), int(pep_y)), pep_size)
            pygame.draw.circle(screen, (255, 80, 80), (int(pep_x), int(pep_y)), max(1, pep_size - 1))
        
        # Chaotic center swirl
        core = int(self.size * 0.3 * (0.8 + abs(math.sin(time_offset * 4)) * 0.4))
        pygame.draw.circle(screen, (255, 100, 100), (int(self.x), int(self.y)), core)
        
        # Health bar
        bar_width = 250
        bar_height = 20
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 40)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.5 else (ORANGE if self.health / self.max_health > 0.25 else RED)
        pygame.draw.rect(screen, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class AncientPizzaMaster(Boss):
    """Boss 10: Ancient pizza master - final boss with complex patterns"""
    def __init__(self, x, y, stage_num, rng):
        super().__init__(x, y, stage_num, rng, "ANCIENT PIZZA MASTER")
        self.health *= 1.5  # Extra health for final boss
        self.max_health = self.health
        self.color = (255, 50, 150)
        self.attack_cooldown = 1275  # Reduced from 1700
        self.rotation = 0
        self.max_phases = 4
    
    def update_movement(self, dt):
        self.rotation += dt * 0.0015
        # Complex movement pattern
        angle1 = self.movement_timer * 0.001
        angle2 = self.movement_timer * 0.0015
        self.target_x = PLAYABLE_AREA_WIDTH / 2 + math.cos(angle1) * 150 + math.sin(angle2) * 80
        self.target_y = 220 + math.sin(angle1) * 40
        
        self.x += (self.target_x - self.x) * 0.015
        self.y += (self.target_y - self.y) * 0.015
        
        # Constrain to playable area
        margin = self.size + 20
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
    
    def get_num_attacks(self):
        return 5
    
    def attack(self, player):
        bullets = []
        
        if self.current_attack == 0:
            # Multi-layer spiral
            bullets = BulletPattern.double_spiral(
                self.x, self.y, num_bullets=30 + self.phase * 5,
                speed=self.bullet_speed, color1=self.color, color2=PURPLE, rotation=self.rotation
            )
        elif self.current_attack == 1:
            # Dense circle patterns
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=24 + self.phase * 4,
                speed=self.bullet_speed, color=self.color, offset_angle=self.rotation
            )
            bullets += BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=16,
                speed=self.bullet_speed * 0.6, color=PINK, offset_angle=-self.rotation * 1.5
            )
        elif self.current_attack == 2:
            # Aimed barrage
            for i in range(4 + self.phase):
                bullets += BulletPattern.aimed_spread(
                    self.x, self.y, player.x, player.y,
                    num_bullets=3, spread=0.15 + i * 0.05,
                    speed=self.bullet_speed * (0.9 + i * 0.1), color=ORANGE
                )
        elif self.current_attack == 3:
            # Homing + spiral
            bullets = BulletPattern.homing_bullets(
                self.x, self.y, num_bullets=6 + self.phase,
                speed=self.bullet_speed * 0.7, color=GREEN
            )
            bullets += BulletPattern.spiral_pattern(
                self.x, self.y, num_bullets=25,
                speed=self.bullet_speed * 1.1, color=self.color, rotation=self.rotation
            )
        else:
            # Ultimate attack - combination
            bullets = BulletPattern.circle_pattern(
                self.x, self.y, num_bullets=20, speed=self.bullet_speed * 1.2, color=RED
            )
            bullets += BulletPattern.cross_pattern(
                self.x, self.y, speed=self.bullet_speed, color=YELLOW, thickness=5
            )
            bullets += BulletPattern.homing_bullets(
                self.x, self.y, num_bullets=4, speed=self.bullet_speed * 0.6, color=GREEN
            )
        
        return bullets
    
    def draw(self, screen):
        """Draw as the ultimate legendary ancient pizza with all ingredients"""
        import math
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Legendary golden crust
        pygame.draw.circle(screen, (230, 200, 120), (int(self.x), int(self.y)), int(self.size), 0)
        pygame.draw.circle(screen, (255, 230, 150), (int(self.x), int(self.y)), int(self.size * 0.97), 0)
        pygame.draw.circle(screen, (200, 160, 80), (int(self.x), int(self.y)), int(self.size), 4)
        
        # Premium cheese
        pygame.draw.circle(screen, (255, 235, 140), (int(self.x), int(self.y)), int(self.size * 0.9), 0)
        
        # Rich red sauce
        pygame.draw.circle(screen, (200, 60, 40), (int(self.x), int(self.y)), int(self.size * 0.85), 0)
        
        # Legendary toppings - all the good stuff
        num_toppings = 25 + self.phase * 5
        for i in range(num_toppings):
            angle = self.rotation + i * math.pi * 2 / num_toppings
            topping_dist = self.size * (0.15 + (i % 5) * 0.14)
            top_x = self.x + math.cos(angle) * topping_dist
            top_y = self.y + math.sin(angle) * topping_dist
            
            # Premium toppings
            if i % 5 == 0:
                # Pepperoni
                topping_size = int(8 + abs(math.sin(time_offset * 2 + i)) * 3)
                pygame.draw.circle(screen, (180, 30, 30), (int(top_x), int(top_y)), topping_size)
                pygame.draw.circle(screen, (255, 100, 80), (int(top_x), int(top_y)), topping_size - 1)
            elif i % 5 == 1:
                # Mushroom
                pygame.draw.circle(screen, (120, 80, 40), (int(top_x), int(top_y)), 5)
            elif i % 5 == 2:
                # Green pepper
                pygame.draw.circle(screen, (80, 180, 80), (int(top_x), int(top_y)), 4)
            elif i % 5 == 3:
                # Black olive
                pygame.draw.circle(screen, (50, 50, 50), (int(top_x), int(top_y)), 4)
                pygame.draw.circle(screen, (100, 100, 100), (int(top_x), int(top_y)), 2)
            else:
                # Onion
                pygame.draw.circle(screen, (200, 180, 120), (int(top_x), int(top_y)), 4)
        
        # Legendary glowing core
        core = int(self.size * 0.35 * (1 + abs(math.sin(time_offset * 3)) * 0.3))
        pygame.draw.circle(screen, (255, 180, 80), (int(self.x), int(self.y)), core)
        pygame.draw.circle(screen, (255, 220, 150), (int(self.x), int(self.y)), int(core * 0.6))
        
        # Health bar - Grand style
        bar_width = 300
        bar_height = 30
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 50)
        health_width = bar_width * (self.health / self.max_health)
        health_color = NEON_GREEN if self.health / self.max_health > 0.6 else (ORANGE if self.health / self.max_health > 0.3 else RED)
        pygame.draw.rect(screen, (30, 20, 10), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, (255, 200, 100), (bar_x, bar_y, bar_width, bar_height), 3)


# Boss pool - all available bosses (Pizza themed!)
BOSS_CLASSES = [
    InfernoOven,
    PepperoniSerpent,
    FreezPizzaMaker,
    MegaPizzaTitan,
    IcedPizzaQueen,
    CrispyBakerMaster,
    ShadowChefPhantom,
    PrismaPizza,
    ChaosChefNightmare,
    AncientPizzaMaster
]


def create_boss(stage_num, rng):
    """Create a boss for the given stage using seeded randomization"""
    boss_class = rng.choice(BOSS_CLASSES)
    return boss_class(PLAYABLE_AREA_WIDTH / 2, -100, stage_num, rng)
