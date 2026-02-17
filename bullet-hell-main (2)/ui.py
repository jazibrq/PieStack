"""
UI and visual effects for the bullet hell game
"""
import pygame
import math
from config import *
import sprites


class Particle:
    """Visual effect particle"""
    def __init__(self, x, y, color, velocity=(0, 0), lifetime=1000):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 3
    
    def update(self, dt):
        """Update particle"""
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= dt
        self.vy += 0.1  # Gravity
    
    def draw(self, screen):
        """Draw particle"""
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = int(self.size * (self.lifetime / self.max_lifetime))
        if size > 0:
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
            screen.blit(s, (int(self.x - size), int(self.y - size)))
    
    def is_dead(self):
        """Check if particle is dead"""
        return self.lifetime <= 0


class ParticleSystem:
    """Manages visual effects"""
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, color, num_particles=20, intensity_multiplier=1.0):
        """Create explosion effect with optional intensity scaling"""
        import random
        # Scale particles and speed based on intensity
        scaled_particles = int(num_particles * intensity_multiplier)
        speed_boost = 1.0 + (intensity_multiplier - 1.0) * 0.5
        
        for _ in range(scaled_particles):
            angle = random.random() * 2 * math.pi
            speed = random.uniform(2, 8) * speed_boost
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.randint(300, 800)
            self.particles.append(Particle(x, y, color, (vx, vy), lifetime))
    
    def add_hit_effect(self, x, y, color):
        """Create hit effect"""
        import random
        for _ in range(5):
            angle = random.random() * 2 * math.pi
            speed = random.uniform(1, 3)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, color, (vx, vy), 300))
    
    def update(self, dt):
        """Update all particles"""
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.is_dead():
                self.particles.remove(particle)
        
        # Limit particle count for performance (keep newest)
        if len(self.particles) > 500:
            self.particles = self.particles[-500:]
    
    def draw(self, screen):
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(screen)


class UI:
    """Game UI"""
    def __init__(self):
        # Use simple pygame fonts for better compatibility - monospace renders cleaner
        self.font_xl = pygame.font.Font(None, 108)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 54)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 27)
        self.message_timer = 0
        self.message_text = ""
        self.stage_intro_timer = 0
        self.stage_intro_text = ""
        self.score_popups = []  # List of score popup notifications
        self.recent_scores = []  # List of recent score events for running display
        self.last_ultimate_type = None  # Track for change animation
        self.ultimate_type_change_time = 0  # Animation timer for ultimate type switch
        self.falling_numbers = []  # Raining numbers effect for game over screen
    
    def draw_game_ui(self, screen, player, score, stage, wave, high_score):
        """Draw main game UI"""
        ui_y = GAME_AREA_HEIGHT
        
        # Modern UI background with subtle gradient effect
        ui_surface = pygame.Surface((SCREEN_WIDTH, UI_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, (15, 15, 35, 200), ui_surface.get_rect())
        screen.blit(ui_surface, (0, ui_y), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Top border with neon glow
        pygame.draw.line(screen, NEON_BLUE, (0, ui_y), (SCREEN_WIDTH, ui_y), 3)
        
        # Health bar - large and prominent at bottom
        health_bar_x = 15
        health_bar_y = ui_y + 10
        health_bar_width = 400
        health_bar_height = 15
        
        health_percent = max(0, player.health / player.max_health)
        health_width = int(health_bar_width * health_percent)
        
        # Health bar color changes based on health
        if health_percent > 0.6:
            health_color = NEON_GREEN
        elif health_percent > 0.3:
            health_color = ORANGE
        else:
            health_color = RED
        
        # Simple clean health bar
        pygame.draw.rect(screen, (40, 40, 60), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        if health_width > 0:
            pygame.draw.rect(screen, health_color, (health_bar_x, health_bar_y, health_width, health_bar_height))
        pygame.draw.rect(screen, health_color, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 1)
        
        # Health text 
        health_text = self.font_tiny.render(
            f"HP {int(player.health)}/{int(player.max_health)}", True, WHITE
        )
        screen.blit(health_text, (health_bar_x + 5, health_bar_y - 20))
        
        # Center info section with modern styling
        center_x = SCREEN_WIDTH // 2
        
        # Score display
        score_text = self.font_small.render(f"Score: {score:,}", True, NEON_GREEN)
        score_rect = score_text.get_rect(center=(center_x - 50, ui_y + 12))
        screen.blit(score_text, score_rect)
        
        # Stage and wave - sleek
        stage_text = self.font_small.render(f"Stage {stage}-{wave}", True, NEON_BLUE)
        stage_rect = stage_text.get_rect(center=(center_x + 80, ui_y + 12))
        screen.blit(stage_text, stage_rect)
        
        # Right side info - modern compact layout
        right_x = SCREEN_WIDTH - 200
        
        # Power level
        power_text = self.font_tiny.render(f"Power: {player.power_level}", True, NEON_PINK)
        screen.blit(power_text, (right_x, ui_y + 10))
        
        # Weapon style indicator - modern neon style
        style_names = {
            'normal': 'Normal',
            'burst': 'Burst',
            'laser': 'Laser',
            'spread': 'Spread',
            'homing': 'Homing',
            'rapid': 'Rapid'
        }
        style_colors = {
            'normal': NEON_BLUE,
            'burst': ORANGE,
            'laser': NEON_PINK,
            'spread': NEON_GREEN,
            'homing': CYAN,
            'rapid': NEON_PURPLE
        }
        style_name = style_names.get(player.weapon_style, player.weapon_style)
        style_color = style_colors.get(player.weapon_style, WHITE)
        style_text = self.font_tiny.render(f"Weapon: {style_name}", True, style_color)
        screen.blit(style_text, (right_x, ui_y + 30))
        
        # Shield indicator (prominent)
        if player.shield:
            shield_x = SCREEN_WIDTH - 150
            shield_y = ui_y + 15
            
            # Pulsing shield icon
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            shield_size = int(20 + pulse * 5)
            
            # Draw hexagon shield
            points = []
            for i in range(6):
                angle = i * (2 * math.pi / 6)
                points.append((
                    shield_x + math.cos(angle) * shield_size,
                    shield_y + math.sin(angle) * shield_size
                ))
            pygame.draw.polygon(screen, CYAN, points, 4)
            
            # Shield text
            shield_text = self.font_small.render("SHIELD", True, CYAN)
            screen.blit(shield_text, (shield_x + 30, shield_y - 8))
    
    def add_score_popup(self, text, color, player_x, player_y):
        """Add a score popup near the player"""
        self.score_popups.append({
            'text': text,
            'color': color,
            'x': player_x,
            'y': player_y,
            'lifetime': 1500,  # 1.5 seconds
            'vy': -2  # Move upward
        })
    
    def update_score_popups(self, dt):
        """Update score popup animations"""
        for popup in self.score_popups[:]:
            popup['lifetime'] -= dt
            popup['y'] += popup['vy']
            if popup['lifetime'] <= 0:
                self.score_popups.remove(popup)
    
    def draw_score_popups(self, screen):
        """Draw score popups on screen"""
        for popup in self.score_popups:
            alpha = min(255, int(popup['lifetime'] / 1500 * 255))
            
            # Create surface with alpha - use modern font
            font = pygame.font.SysFont('segoe ui, arial', 48, bold=True)
            text = font.render(popup['text'], True, popup['color'])
            
            # Add glow effect
            glow_size = 40
            glow = pygame.Surface((text.get_width() + glow_size, text.get_height() + glow_size), pygame.SRCALPHA)
            glow_alpha = max(0, min(255, int(alpha * 0.33)))
            pygame.draw.rect(glow, (*popup['color'][:3], glow_alpha), glow.get_rect(), border_radius=10)
            screen.blit(glow, (int(popup['x'] - glow_size//2), int(popup['y'] - glow_size//2)))
            
            # Draw text
            screen.blit(text, (int(popup['x']), int(popup['y'])))
    
    def draw_message(self, screen, dt):
        """Draw temporary message"""
        if self.message_timer > 0:
            self.message_timer -= dt
            alpha = max(0, int(min(255, self.message_timer * 0.5)))
            
            text = self.font_medium.render(self.message_text, True, YELLOW)
            text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, 80))
            
            # Draw with transparency
            s = pygame.Surface((text_rect.width + 20, text_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, max(0, min(255, int(alpha * 0.5)))), s.get_rect(), border_radius=5)
            screen.blit(s, (text_rect.x - 10, text_rect.y - 5))
            
            text_surface = self.font_medium.render(self.message_text, True, YELLOW)
            screen.blit(text_surface, text_rect)
    
    def show_message(self, text, duration=2000):
        """Show a temporary message"""
        self.message_text = text
        self.message_timer = duration
    
    def draw_stage_intro(self, screen, stage_num, boss_name, dt):
        """Draw stage introduction"""
        if self.stage_intro_timer > 0:
            self.stage_intro_timer -= dt
            
            # Fade in/out effect
            if self.stage_intro_timer > 2000:
                alpha = max(0, int(255 - (self.stage_intro_timer - 2000) * 0.255))
            elif self.stage_intro_timer < 500:
                alpha = max(0, int(self.stage_intro_timer * 0.51))
            else:
                alpha = 255
            
            alpha = max(0, min(255, alpha))  # Clamp between 0-255
            
            # Semi-transparent background
            overlay = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, min(150, alpha)), overlay.get_rect())
            screen.blit(overlay, (0, 0))
            
            # Stage text
            stage_text = self.font_large.render(f"STAGE {stage_num}", True, WHITE)
            stage_rect = stage_text.get_rect(center=(SCREEN_WIDTH / 2, GAME_AREA_HEIGHT / 2 - 40))
            screen.blit(stage_text, stage_rect)
            
            # Boss name
            if boss_name:
                boss_text = self.font_medium.render(f"Boss: {boss_name}", True, RED)
                boss_rect = boss_text.get_rect(center=(SCREEN_WIDTH / 2, GAME_AREA_HEIGHT / 2 + 20))
                screen.blit(boss_text, boss_rect)
    
    def show_stage_intro(self, stage_num, boss_name=None):
        """Show stage introduction"""
        self.stage_intro_timer = 3000
        self.stage_intro_text = f"Stage {stage_num}"
    
    def draw_game_over(self, screen, score, stage, seed, deaths=0, timer=0):
        """Draw game over screen - SLOTS STYLE CELEBRATION"""
        # Animated colorful overlay (cycling colors) - SLOWER
        color_cycle = (timer * 0.0005) % 1.0
        bg_r = int(50 + 30 * math.sin(color_cycle * math.pi * 2))
        bg_g = int(30 + 20 * math.sin(color_cycle * math.pi * 2 + 2))
        bg_b = int(60 + 40 * math.sin(color_cycle * math.pi * 2 + 4))
        overlay = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (bg_r, bg_g, bg_b, 220), overlay.get_rect())
        screen.blit(overlay, (0, 0))
        
        # Generate falling numbers if list is empty or needs refresh
        if len(self.falling_numbers) < 30:
            import random
            for i in range(50):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(-500, -50)
                speed = random.uniform(1.5, 4.0)
                value = random.choice([10, 25, 50, 100, 250, 500, 1000])
                color = random.choice([YELLOW, NEON_GREEN, CYAN, WHITE, NEON_PINK])
                size = random.randint(24, 42)
                self.falling_numbers.append({'x': x, 'y': y, 'speed': speed, 'value': value, 'color': color, 'size': size})
        
        # Update and draw falling numbers
        for num in self.falling_numbers[:]:
            num['y'] += num['speed']
            if num['y'] > GAME_AREA_HEIGHT:
                self.falling_numbers.remove(num)
            else:
                num_font = pygame.font.Font(None, num['size'])
                num_text = num_font.render(f"+{num['value']}", True, num['color'])
                num_alpha = min(255, int(255 * (1 - num['y'] / GAME_AREA_HEIGHT)))
                num_text.set_alpha(num_alpha)
                screen.blit(num_text, (num['x'], num['y']))
        
        # Flashing border effect like slots machine
        border_pulse = int(timer * 0.01) % 2
        border_colors = [YELLOW, RED, NEON_PINK, NEON_GREEN, CYAN]
        border_color = border_colors[int(timer * 0.005) % len(border_colors)]
        for i in range(5):
            pygame.draw.rect(screen, border_color if border_pulse else WHITE, 
                           (i * 10, i * 10, SCREEN_WIDTH - i * 20, GAME_AREA_HEIGHT - i * 20), 8)
        
        # MASSIVE "GAME OVER" header with glow - THINNER FONT
        pulse = abs(math.sin(timer * 0.004)) * 30
        header_font = pygame.font.SysFont('segoe ui, arial', int(108 + pulse))
        header_text = header_font.render("★ GAME OVER ★", True, YELLOW)
        header_rect = header_text.get_rect(center=(SCREEN_WIDTH / 2, 140))
        
        # Rainbow glow behind text
        for i in range(8):
            glow_color = (
                int(255 * abs(math.sin(timer * 0.003 + i * 0.5))),
                int(255 * abs(math.sin(timer * 0.003 + i * 0.5 + 2))),
                int(255 * abs(math.sin(timer * 0.003 + i * 0.5 + 4)))
            )
            glow = header_font.render("★ GAME OVER ★", True, glow_color)
            glow_rect = glow.get_rect(center=(header_rect.centerx + i - 4, header_rect.centery + i - 4))
            screen.blit(glow, glow_rect)
        
        screen.blit(header_text, header_rect)
        
        # MASSIVE RANK DISPLAY - Center of attention
        rank, rank_color = self.calculate_rank(score)
        rank_y = 300
        
        # Spinning coins/decorations around rank
        for i in range(12):
            angle = (timer * 0.003 + i * math.pi / 6) % (math.pi * 2)
            radius = 180 + 20 * math.sin(timer * 0.005 + i)
            coin_x = SCREEN_WIDTH / 2 + math.cos(angle) * radius
            coin_y = rank_y + math.sin(angle) * radius
            coin_size = int(40 + 10 * abs(math.sin(timer * 0.004 + i)))
            coin_font = pygame.font.SysFont('segoe ui, arial', coin_size)
            coin = coin_font.render("◆" if i % 2 else "★", True, YELLOW if i % 2 else RED)
            coin_rect = coin.get_rect(center=(coin_x, coin_y))
            screen.blit(coin, coin_rect)
        
        # HUGE rank with multiple layers of glow - THINNER FONT
        rank_font = pygame.font.SysFont('arial, segoe ui', 320)
        
        # Outer glow layers (multiple colors)
        for layer in range(15, 0, -1):
            layer_color = (
                int(rank_color[0] * (layer / 15)),
                int(rank_color[1] * (layer / 15)),
                int(rank_color[2] * (layer / 15))
            )
            glow_rank = rank_font.render(rank, True, layer_color)
            glow_rect = glow_rank.get_rect(center=(SCREEN_WIDTH / 2 + layer // 2, rank_y + layer // 2))
            screen.blit(glow_rank, glow_rect)
        
        # Main rank text
        rank_text = rank_font.render(rank, True, rank_color)
        rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH / 2, rank_y))
        screen.blit(rank_text, rank_rect)
        
        # Flashing "RANK" label above - THINNER FONT
        flash = int(timer * 0.01) % 2
        rank_label_font = pygame.font.SysFont('segoe ui, arial', 72)
        rank_label = rank_label_font.render("★ RANK ★", True, YELLOW if flash else WHITE)
        rank_label_rect = rank_label.get_rect(center=(SCREEN_WIDTH / 2, rank_y - 140))
        screen.blit(rank_label, rank_label_rect)
        
        # Score with animated counter effect - THINNER FONT
        score_y = rank_y + 190
        score_label_font = pygame.font.SysFont('segoe ui, arial', 54)
        score_label = score_label_font.render("FINAL SCORE", True, NEON_GREEN)
        score_label_rect = score_label.get_rect(center=(SCREEN_WIDTH / 2, score_y))
        screen.blit(score_label, score_label_rect)
        
        score_font = pygame.font.SysFont('arial, segoe ui', 90)
        score_text = score_font.render(f"{score:,}", True, YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH / 2, score_y + 55))
        
        # Score glow
        score_glow = score_font.render(f"{score:,}", True, (255, 200, 0, 150))
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
            screen.blit(score_glow, (score_rect.x + offset[0], score_rect.y + offset[1]))
        screen.blit(score_text, score_rect)
        
        # Additional stats in glowing boxes
        stats_y = score_y + 140
        stats_font = self.font_small
        
        # Stage box
        stage_text = stats_font.render(f"Stage: {stage}", True, CYAN)
        stage_rect = stage_text.get_rect(center=(SCREEN_WIDTH / 2 - 150, stats_y))
        pygame.draw.rect(screen, (0, 100, 100, 200), stage_rect.inflate(20, 10))
        pygame.draw.rect(screen, CYAN, stage_rect.inflate(20, 10), 3)
        screen.blit(stage_text, stage_rect)
        
        # Deaths box
        deaths_text = stats_font.render(f"Deaths: {deaths}", True, RED)
        deaths_rect = deaths_text.get_rect(center=(SCREEN_WIDTH / 2 + 150, stats_y))
        pygame.draw.rect(screen, (100, 0, 0, 200), deaths_rect.inflate(20, 10))
        pygame.draw.rect(screen, RED, deaths_rect.inflate(20, 10), 3)
        screen.blit(deaths_text, deaths_rect)
        
        # Restart prompt with flashing effect
        pulse_alpha = abs(math.sin(timer * 0.006))
        restart_color = (
            int(100 + 155 * pulse_alpha),
            int(255 * pulse_alpha),
            int(100 + 155 * pulse_alpha)
        )
        restart_font = pygame.font.SysFont('segoe ui, arial', 48)
        restart_text = restart_font.render("PRESS ENTER TO PLAY AGAIN", True, restart_color)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, stats_y + 120))
        
        # Restart glow
        for i in range(3):
            glow = restart_font.render("PRESS ENTER TO PLAY AGAIN", True, (*restart_color, 80))
            screen.blit(glow, (restart_rect.x + i, restart_rect.y + i))
        screen.blit(restart_text, restart_rect)
        
        # ESC hint
        esc_text = self.font_tiny.render("ESC to quit", True, (150, 150, 150))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH / 2, stats_y + 165))
        screen.blit(esc_text, esc_rect)
    
    def draw_player_health(self, screen, player):
        """Draw large health display on screen"""
        # Background box for visibility
        box_width = 180
        box_height = 80
        box_x = 10
        box_y = 10
        
        # Draw dark background
        background = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(background, (0, 0, 0, 200), background.get_rect())
        screen.blit(background, (box_x, box_y))
        
        # Draw border
        pygame.draw.rect(screen, RED, (box_x, box_y, box_width, box_height), 3)
        
        # Large health counter
        health_display = self.font_xl.render(f"{int(player.health)}", True, RED)
        screen.blit(health_display, (box_x + 15, box_y + 8))
        
        # Small label
        label = self.font_small.render(f"/ {int(player.max_health)}", True, WHITE)
        screen.blit(label, (box_x + 15, box_y + 55))
    
    def draw_boss_health_bar(self, screen, boss):
        """Draw boss health bar prominently"""
        if not boss:
            return
        
        bar_width = 550  # Stop before side panel at x=620
        bar_height = 50
        bar_x = 50
        bar_y = 120  # Moved down to avoid overlapping with player health
        
        # Draw dark background box
        background = pygame.Surface((bar_width, bar_height + 50), pygame.SRCALPHA)
        pygame.draw.rect(background, (0, 0, 0, 220), background.get_rect())
        screen.blit(background, (bar_x, bar_y - 10))
        
        # Boss name and health text (above bar)
        boss_name = self.font_large.render(boss.name, True, YELLOW)
        screen.blit(boss_name, (bar_x + 15, bar_y - 5))
        
        # Health percentage
        health_percent = max(0, boss.health / boss.max_health)
        
        # Actual bar background
        pygame.draw.rect(screen, (50, 0, 0), (bar_x + 10, bar_y + 30, bar_width - 20, bar_height))
        
        # Health fill (gradient effect with color change)
        if health_percent > 0.5:
            color = (255 - int(health_percent * 100), int(health_percent * 255), 0)
        else:
            color = RED
        
        health_width = int((bar_width - 20) * health_percent)
        pygame.draw.rect(screen, color, (bar_x + 10, bar_y + 30, health_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, YELLOW, (bar_x + 10, bar_y + 30, bar_width - 20, bar_height), 3)
        
        # Health numbers
        health_text = self.font_small.render(f"{int(boss.health)}/{int(boss.max_health)}", True, WHITE)
        screen.blit(health_text, (bar_x + 15, bar_y + 35))
    
    def draw_side_panel(self, screen, player, score, high_score, stage, wave, kills, recent_events):
        """Draw right-side panel with stats and ultimate bar"""
        panel_x = SIDE_PANEL_START_X
        panel_width = SCREEN_WIDTH - SIDE_PANEL_START_X
        panel_height = BOTTOM_PANEL_START_Y
        
        # Dark panel background
        panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_bg, (10, 10, 25, 230), panel_bg.get_rect())
        screen.blit(panel_bg, (panel_x, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Panel borders - strict
        pygame.draw.line(screen, NEON_BLUE, (panel_x, 0), (panel_x, panel_height), 4)  # Left border
        pygame.draw.line(screen, CYAN, (panel_x, 0), (SCREEN_WIDTH, 0), 3)  # Top border
        pygame.draw.line(screen, NEON_GREEN, (SCREEN_WIDTH - 1, 0), (SCREEN_WIDTH - 1, panel_height), 2)  # Right border
        
        y = 15
        
        # Score section
        score_label = self.font_tiny.render("SCORE", True, NEON_GREEN)
        screen.blit(score_label, (panel_x + 10, y))
        y += 22
        
        score_text = self.font_medium.render(f"{score:,}", True, WHITE)
        score_rect = score_text.get_rect()
        if score_rect.width > panel_width - 20:
            # Scale down if too wide
            score_text = self.font_small.render(f"{score:,}", True, WHITE)
        screen.blit(score_text, (panel_x + 10, y))
        y += 35
        
        # High score
        if high_score > 0:
            hi_label = self.font_tiny.render("HIGH", True, NEON_PINK)
            screen.blit(hi_label, (panel_x + 10, y))
            y += 27
            
            hi_text = self.font_small.render(f"{high_score:,}", True, WHITE)
            hi_rect = hi_text.get_rect()
            if hi_rect.width > panel_width - 20:
                hi_text = self.font_tiny.render(f"{high_score:,}", True, WHITE)
            screen.blit(hi_text, (panel_x + 10, y))
            y += 45
        
        # Divider
        pygame.draw.line(screen, NEON_BLUE, (panel_x + 5, y), (panel_x + panel_width - 5, y), 1)
        y += 12
        
        # Combo section
        combo_label = self.font_tiny.render("COMBO", True, YELLOW)
        screen.blit(combo_label, (panel_x + 10, y))
        y += 22
        
        # Show combo with multiplier
        if player.combo > 0:
            combo_text = self.font_medium.render(f"{player.combo}", True, YELLOW)
            screen.blit(combo_text, (panel_x + 10, y))
            
            # Show multiplier
            mult_text = self.font_small.render(f"x{player.combo_multiplier:.1f}", True, NEON_GREEN)
            screen.blit(mult_text, (panel_x + 120, y + 8))
            y += 42
        else:
            no_combo = self.font_small.render("---", True, (100, 100, 100))
            screen.blit(no_combo, (panel_x + 10, y))
            y += 35
        
        # Graze counter
        graze_label = self.font_tiny.render("GRAZES", True, CYAN)
        screen.blit(graze_label, (panel_x + 10, y))
        y += 22
        
        graze_text = self.font_small.render(f"{player.graze_count}", True, CYAN)
        screen.blit(graze_text, (panel_x + 10, y))
        y += 50
        
        # Divider
        pygame.draw.line(screen, NEON_BLUE, (panel_x + 5, y), (panel_x + panel_width - 5, y), 1)
        y += 22
        
        # Stage/Wave info
        stage_text = self.font_small.render(f"Stage {stage}", True, NEON_BLUE)
        screen.blit(stage_text, (panel_x + 10, y))
        y += 38
        
        wave_text = self.font_small.render(f"Wave {wave}", True, CYAN)
        screen.blit(wave_text, (panel_x + 10, y))
        y += 38
        
        kills_text = self.font_small.render(f"Kills: {kills}", True, NEON_GREEN)
        screen.blit(kills_text, (panel_x + 10, y))
        y += 45
        
        # Divider
        pygame.draw.line(screen, NEON_BLUE, (panel_x + 5, y), (panel_x + panel_width - 5, y), 1)
        y += 22
        
        # Ultimate bar
        ultimate_label = self.font_tiny.render("ULTIMATE", True, NEON_PINK)
        screen.blit(ultimate_label, (panel_x + 10, y))
        y += 30
        
        # Ultimate bar background
        bar_width = panel_width - 20
        bar_height = 20
        bar_x = panel_x + 10
        bar_y = y
        
        pygame.draw.rect(screen, (30, 10, 40), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, NEON_PINK, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Ultimate charge fill
        charge_percent = max(0, min(1.0, player.ultimate_charge / player.ultimate_max))
        fill_width = int(bar_width * charge_percent)
        
        if player.ultimate_active:
            # Pulsing effect when active
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            fill_color = (int(255 * pulse), 0, int(255 * pulse))
        else:
            fill_color = NEON_PINK if charge_percent > 0 else (100, 50, 100)
        
        if fill_width > 0:
            pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        y += 30
        
        # Press X to activate
        if charge_percent >= 1.0:
            activate_text = self.font_tiny.render("Press X", True, NEON_GREEN)
            screen.blit(activate_text, (bar_x, y))
            y += 20
        
        # Ultimate type display
        ultimate_type_label = self.font_tiny.render("Type:", True, WHITE)
        screen.blit(ultimate_type_label, (bar_x, y))
        
        # Check if ultimate type changed
        if self.last_ultimate_type != player.ultimate_type:
            self.last_ultimate_type = player.ultimate_type
            self.ultimate_type_change_time = pygame.time.get_ticks()
        
        # Animation: flashy punch-in effect
        time_since_change = pygame.time.get_ticks() - self.ultimate_type_change_time
        if time_since_change < 300:  # 300ms animation
            # Punchout effect: scale and fade
            progress = time_since_change / 300.0
            scale = 1.0 + (1 - progress) * 0.5  # Grows then shrinks
            alpha = int(255 * (1 - progress * 0.3))  # Slight fade
            
            # Create temporary text for animation
            anim_font = pygame.font.SysFont('segoe ui, arial', int(27 * scale), bold=True)
            anim_color = (255, int(100 * (1 - progress * 0.2)), 255)
            
            if player.ultimate_type == 'laser_grid':
                ultimate_type_text = anim_font.render("SQUARE SLICES", True, anim_color)
            elif player.ultimate_type == 'clone':
                ultimate_type_text = anim_font.render("CLONE RECIPE", True, anim_color)
            else:  # fullscreen_laser
                ultimate_type_text = anim_font.render("FULL OVEN", True, anim_color)
            
            text_rect = ultimate_type_text.get_rect(topleft=(bar_x + 55, y))
            screen.blit(ultimate_type_text, text_rect)
        else:
            # Normal display
            if player.ultimate_type == 'laser_grid':
                ultimate_type_text = self.font_tiny.render("SQUARE SLICES", True, NEON_GREEN)
            elif player.ultimate_type == 'clone':
                ultimate_type_text = self.font_tiny.render("CLONE RECIPE", True, CYAN)
            else:  # fullscreen_laser
                ultimate_type_text = self.font_tiny.render("FULL OVEN", True, YELLOW)
            
            screen.blit(ultimate_type_text, (bar_x + 55, y))
        
        y += 35
        
        # ABILITY BAR - Below ultimate bar
        ability_bar_y = y
        ability_bar_height = 12
        ability_bar_width = panel_width - 40
        
        # Dark background
        pygame.draw.rect(screen, (30, 30, 50),
                        (bar_x - 2, ability_bar_y - 2, ability_bar_width + 4, ability_bar_height + 4))
        
        ability_percent = player.ability_charge / player.ability_max
        ability_width = int(ability_bar_width * ability_percent)
        
        # Ability bar color based on type
        ability_colors = {
            'berserker': (255, 50, 0),
            'glass_cannon': (255, 100, 255),
            'invincible': (100, 255, 255)
        }
        ability_color = ability_colors.get(player.ability_type, PURPLE)
        
        # Draw ability bar
        if ability_width > 0:
            pygame.draw.rect(screen, ability_color,
                            (bar_x, ability_bar_y, ability_width, ability_bar_height))
        
        # Active indicator
        if player.ability_active:
            pygame.draw.rect(screen, WHITE,
                            (bar_x, ability_bar_y, ability_bar_width, ability_bar_height), 2)
        else:
            pygame.draw.rect(screen, ability_color,
                            (bar_x, ability_bar_y, ability_bar_width, ability_bar_height), 2)
        
        # Ability label - Pizza themed names
        ability_names = {
            'berserker': 'PIZZA FURY',
            'glass_cannon': 'THIN CRUST',
            'invincible': 'BRICK OVEN'
        }
        ability_name = ability_names.get(player.ability_type, player.ability_type.upper().replace('_', ' '))
        ability_label = self.font_tiny.render("Type:", True, WHITE)
        ability_text = self.font_small.render(ability_name, True, YELLOW)
        screen.blit(ability_label, (bar_x, ability_bar_y - 20))
        screen.blit(ability_text, (bar_x + 50, ability_bar_y - 20))
        
        y += 40
        
        # PHASE METER - Shift/Sprint limit
        phase_label = self.font_tiny.render("PHASE", True, CYAN)
        screen.blit(phase_label, (panel_x + 10, y))
        y += 16
        
        # Phase bar background
        phase_bar_width = panel_width - 20
        phase_bar_height = 12
        phase_bar_x = panel_x + 10
        phase_bar_y = y
        
        pygame.draw.rect(screen, (20, 30, 40), (phase_bar_x - 2, phase_bar_y - 2, phase_bar_width + 4, phase_bar_height + 4))
        pygame.draw.rect(screen, (30, 60, 100), (phase_bar_x, phase_bar_y, phase_bar_width, phase_bar_height))
        
        # Phase charge fill
        phase_percent = max(0, min(1.0, player.phase_charge / player.phase_max))
        phase_fill_width = int(phase_bar_width * phase_percent)
        
        if phase_percent > 0:
            phase_color = CYAN if phase_percent > 0.3 else (100, 150, 200)
            pygame.draw.rect(screen, phase_color, (phase_bar_x, phase_bar_y, phase_fill_width, phase_bar_height))
        
        # Border
        pygame.draw.rect(screen, CYAN, (phase_bar_x, phase_bar_y, phase_bar_width, phase_bar_height), 1)
        
        y += 25
        
        # RANK SECTION - Large and prominent
        pygame.draw.line(screen, NEON_BLUE, (panel_x + 5, y), (panel_x + panel_width - 5, y), 2)
        y += 15
        
        rank_label = self.font_small.render("RANK", True, YELLOW)
        rank_label_rect = rank_label.get_rect(center=(panel_x + panel_width // 2, y))
        screen.blit(rank_label, rank_label_rect)
        y += 50
        
        rank, rank_color = self.calculate_rank(score)
        
        # Massive rank display with glow - THINNER FONT
        rank_font = pygame.font.SysFont('arial, segoe ui', 180)
        rank_text = rank_font.render(rank, True, rank_color)
        rank_rect = rank_text.get_rect(center=(panel_x + panel_width // 2, y))
        
        # Glow effect
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
            glow_text = rank_font.render(rank, True, (*rank_color[:3], 100))
            glow_rect = glow_text.get_rect(center=(rank_rect.centerx + offset[0], rank_rect.centery + offset[1]))
            screen.blit(glow_text, glow_rect)
        
        screen.blit(rank_text, rank_rect)
        
        # Decorative stars around rank
        star_font = pygame.font.SysFont('segoe ui, arial', 48, bold=True)
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.003))
        star_color = (int(255), int(200 + 55 * pulse), int(100))
        star_left = star_font.render("★", True, star_color)
        star_right = star_font.render("★", True, star_color)
        screen.blit(star_left, (rank_rect.left - 45, rank_rect.centery - 20))
        screen.blit(star_right, (rank_rect.right + 15, rank_rect.centery - 20))
        
        y += 120
        pygame.draw.line(screen, NEON_BLUE, (panel_x + 5, y), (panel_x + panel_width - 5, y), 2)
        y += 5
        
        # Recent events section
        y += 10
        pygame.draw.line(screen, NEON_BLUE, (panel_x + 5, y), (panel_x + panel_width - 5, y), 1)
        y += 10
        
        events_label = self.font_tiny.render("EVENTS", True, CYAN)
        screen.blit(events_label, (panel_x + 10, y))
        y += 20
        
        # Display recent score events (last 8)
        for event in recent_events[-8:]:
            event_text = self.font_tiny.render(f"+ {event[1]} {event[0]}", True, event[2])
            screen.blit(event_text, (panel_x + 10, y))
            y += 18
    
    def draw_active_powerups(self, screen, player, stage, wave, boss=None, wave_timer=0):
        """Draw comprehensive bottom info panel with game stats"""
        panel_y = BOTTOM_PANEL_START_Y
        panel_height = SCREEN_HEIGHT - BOTTOM_PANEL_START_Y
        
        # Draw dark panel background at bottom
        panel_bg = pygame.Surface((PLAYABLE_AREA_WIDTH, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_bg, (10, 10, 25, 240), panel_bg.get_rect())
        screen.blit(panel_bg, (0, panel_y), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Top border of panel - thick and strict
        pygame.draw.line(screen, NEON_BLUE, (0, panel_y), (PLAYABLE_AREA_WIDTH, panel_y), 4)
        # Left border - strict
        pygame.draw.line(screen, NEON_GREEN, (0, panel_y), (0, SCREEN_HEIGHT), 3)
        
        # Divide panel into 4 columns of info
        col_width = PLAYABLE_AREA_WIDTH / 4
        col_height = panel_height
        
        # Draw vertical dividers
        for i in range(1, 4):
            pygame.draw.line(screen, (40, 40, 80), (int(col_width * i), panel_y), 
                           (int(col_width * i), SCREEN_HEIGHT), 1)
        
        # Column 1: Health and Ability
        x = 15
        y = panel_y + 8
        
        # Health section
        health_label = self.font_tiny.render("HEALTH", True, RED)
        screen.blit(health_label, (x, y))
        
        # Health bar
        health_percent = max(0, player.health / player.max_health)
        bar_width = 60
        bar_height = 12
        
        pygame.draw.rect(screen, (30, 30, 50), (x, y + 18, bar_width, bar_height))
        health_width = int(bar_width * health_percent)
        if health_width > 0:
            health_color = NEON_GREEN if health_percent > 0.6 else (ORANGE if health_percent > 0.3 else RED)
            pygame.draw.rect(screen, health_color, (x, y + 18, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (x, y + 18, bar_width, bar_height), 1)
        
        health_text = self.font_small.render(f"{int(player.health)}/{int(player.max_health)}", True, WHITE)
        screen.blit(health_text, (x, y + 32))
        
        # Ability section
        y += 60
        ability_label = self.font_small.render("ABILITY", True, PURPLE)
        screen.blit(ability_label, (x, y))
        
        # Draw ability icon
        ability_icon_map = {
            'berserker': 9,
            'glass_cannon': 8,
            'invincible': 10
        }
        ability_icon_num = ability_icon_map.get(player.ability_type)
        if sprites.sprite_loader and ability_icon_num:
            ability_icon = sprites.sprite_loader.get_icon(ability_icon_num)
            if ability_icon:
                scaled_icon = pygame.transform.scale(ability_icon, (32, 32))
                screen.blit(scaled_icon, (x, y + 18))
        
        ability_names = {
            'berserker': 'PIZZA FURY',
            'glass_cannon': 'THIN CRUST',
            'invincible': 'BRICK OVEN'
        }
        ability_display = ability_names.get(player.ability_type, player.ability_type.upper())
        ability_text = self.font_small.render(ability_display, True, YELLOW)
        screen.blit(ability_text, (x + 36, y + 22))

        
        # Column 2: Stage and Wave
        x = int(col_width) + 15
        y = panel_y + 8
        
        # Stage section
        stage_label = self.font_small.render("STAGE", True, NEON_GREEN)
        screen.blit(stage_label, (x, y))
        stage_text = self.font_large.render(str(stage), True, NEON_GREEN)
        screen.blit(stage_text, (x, y + 24))
        
        # Wave section
        y += 72
        wave_label = self.font_small.render("WAVE", True, CYAN)
        screen.blit(wave_label, (x, y))
        wave_text = self.font_medium.render(str(wave), True, CYAN)
        screen.blit(wave_text, (x, y + 24))
        
        # Column 3: Weapon and Ultimate Type
        x = int(col_width * 2) + 15
        y = panel_y + 8
        
        # Weapon section
        weapon_label = self.font_small.render("WEAPON", True, ORANGE)
        screen.blit(weapon_label, (x, y))
        
        # Draw weapon icon above text
        weapon_icon_map = {
            'normal': 11,
            'burst': 12,
            'laser': 13,
            'spread': 14,
            'homing': 15,
            'rapid': 16
        }
        weapon_icon_num = weapon_icon_map.get(player.weapon_style)
        if sprites.sprite_loader and weapon_icon_num:
            weapon_icon = sprites.sprite_loader.get_icon(weapon_icon_num)
            if weapon_icon:
                scaled_icon = pygame.transform.scale(weapon_icon, (36, 36))
                screen.blit(scaled_icon, (x, y + 18))
        
        weapon_text = self.font_small.render(player.weapon_style[:6].upper(), True, ORANGE)
        screen.blit(weapon_text, (x + 44, y + 22))
        
        # Ultimate section
        y += 72
        ultimate_label = self.font_small.render("ULTIMATE", True, NEON_PINK)
        screen.blit(ultimate_label, (x, y))
        
        # Ultimate icon and type display
        ultimate_icon_map = {
            'laser_grid': 17,
            'clone': 18,
            'fullscreen_laser': 19
        }
        ultimate_icon_num = ultimate_icon_map.get(player.ultimate_type)
        if sprites.sprite_loader and ultimate_icon_num:
            ultimate_icon = sprites.sprite_loader.get_icon(ultimate_icon_num)
            if ultimate_icon:
                scaled_icon = pygame.transform.scale(ultimate_icon, (36, 36))
                screen.blit(scaled_icon, (x, y + 18))
        
        if player.ultimate_type == 'laser_grid':
            ult_text = self.font_small.render("SQUARE SLICES", True, NEON_GREEN)
        elif player.ultimate_type == 'clone':
            ult_text = self.font_small.render("CLONE RECIPE", True, CYAN)
        else:  # fullscreen_laser
            ult_text = self.font_small.render("FULL OVEN", True, YELLOW)
        screen.blit(ult_text, (x + 44, y + 22))
        
        # Column 4: Boss Info
        x = int(col_width * 3) + 15
        y = panel_y + 8
        
        if boss and boss.health > 0:
            boss_label = self.font_tiny.render("BOSS", True, RED)
            screen.blit(boss_label, (x, y))
            
            # Truncate boss name if too long
            boss_name = boss.name
            if len(boss_name) > 12:
                boss_name = boss_name[:12]
            
            boss_text = self.font_tiny.render(boss_name, True, RED)
            screen.blit(boss_text, (x, y + 18))
            
            # Boss health bar mini
            y += 45
            boss_health_bar_width = int(col_width) - 30
            pygame.draw.rect(screen, (50, 0, 0), (x, y, boss_health_bar_width, 8))
            if boss.health > 0:
                health_percent = max(0, boss.health / boss.max_health)
                fill_width = int(boss_health_bar_width * health_percent)
                pygame.draw.rect(screen, RED, (x, y, fill_width, 8))
            pygame.draw.rect(screen, RED, (x, y, boss_health_bar_width, 8), 1)
        else:
            status_label = self.font_tiny.render("STATUS", True, GREEN)
            screen.blit(status_label, (x, y))
            status_text = self.font_small.render("Waves...", True, GREEN)
            screen.blit(status_text, (x, y + 18))
    
    def calculate_rank(self, score):
        """Calculate SSS-F rank based on score"""
        if score >= 100000:
            return 'SSS', (255, 215, 0)  # Gold
        elif score >= 50000:
            return 'S', NEON_PINK
        elif score >= 35000:
            return 'A', NEON_GREEN
        elif score >= 20000:
            return 'B', CYAN
        elif score >= 10000:
            return 'C', NEON_BLUE
        elif score >= 5000:
            return 'D', GREEN
        elif score >= 2000:
            return 'E', YELLOW
        else:
            return 'F', RED
    
    def add_score_event(self, event_type, points):
        """Add a score event to the running list with color"""
        # Determine color based on event type
        color_map = {
            'enemy': WHITE,
            'boss': ORANGE,
            'powerup': GREEN,
            'trick': YELLOW,
            'ultimate': NEON_PINK
        }
        color = color_map.get(event_type, WHITE)
        
        # Store as tuple (type, points, color) for easy access
        self.recent_scores.append((event_type, points, color))
    
    def update_score_events(self, dt):
        """Update recent score events"""
        for event in self.recent_scores[:]:
            event['lifetime'] -= dt
            event['y_offset'] -= 1  # Move upward
            if event['lifetime'] <= 0:
                self.recent_scores.remove(event)
    
    def draw_score_list(self, screen, total_score):
        """Draw DMC-style running score list on the right side"""
        x = SCREEN_WIDTH - 280
        y = 150
        
        # Title
        title = self.font_medium.render("SCORE", True, YELLOW)
        screen.blit(title, (x, y - 40))
        
        # Draw recent score events
        for i, event in enumerate(self.recent_scores):
            alpha = min(255, int(event['lifetime'] / 3000 * 255))
            lifetime_percent = event['lifetime'] / 3000
            
            # Fade color from bright to dim
            color_intensity = int(255 * lifetime_percent)
            event_color = (255, color_intensity, 0) if event['type'] == 'enemy' else \
                         (0, 255, color_intensity) if event['type'] == 'powerup' else \
                         (255, 0, color_intensity) if event['type'] == 'boss' else \
                         (255, 255, 0)  # Trick
            
            # Event text
            event_text = f"{event['type'].upper()}: +{event['points']}"
            text_surface = self.font_small.render(event_text, True, event_color)
            
            # Position starts at the right and animates upward
            draw_y = y + i * 30 + event['y_offset']
            
            # Glow effect
            if lifetime_percent > 0.5:
                glow_size = int(5 * (lifetime_percent - 0.5) * 2)
                pygame.draw.circle(screen, (*event_color, 50), (x + 140, draw_y + 10), glow_size)
            
            screen.blit(text_surface, (x, draw_y))
        
        # Total score display
        score_text = self.font_large.render(f"{total_score:,}", True, YELLOW)
        score_rect = score_text.get_rect(bottomright=(SCREEN_WIDTH - 20, GAME_AREA_HEIGHT - 20))
        screen.blit(score_text, score_rect)
    
    def draw_logo(self, screen):
        """Draw animated PIESTACK logo with cool effects"""
        center_x = SCREEN_WIDTH / 2
        center_y = 120
        time = pygame.time.get_ticks()
        
        # Rotating hexagonal frame
        hex_radius = 85
        hex_points = []
        rotation = time * 0.0005
        for i in range(6):
            angle = i * (math.pi / 3) + rotation
            x = center_x + math.cos(angle) * hex_radius
            y = center_y + math.sin(angle) * hex_radius
            hex_points.append((x, y))
        
        # Draw outer glow rings
        for ring in range(4, 0, -1):
            ring_radius = hex_radius + ring * 8
            ring_alpha = int(40 / ring)
            ring_points = []
            for i in range(6):
                angle = i * (math.pi / 3) + rotation
                x = center_x + math.cos(angle) * ring_radius
                y = center_y + math.sin(angle) * ring_radius
                ring_points.append((x, y))
            
            glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(glow_surf, (*NEON_BLUE[:3], ring_alpha), ring_points, 3)
            screen.blit(glow_surf, (0, 0))
        
        # Main hexagonal frame
        pygame.draw.polygon(screen, NEON_BLUE, hex_points, 4)
        
        # Inner pizza logo - InfernoOven design
        pizza_size = 45
        time_offset = pygame.time.get_ticks() * 0.001
        
        # Pizza crust - golden circle
        pygame.draw.circle(screen, (210, 180, 100), (int(center_x), int(center_y)), pizza_size, 0)
        
        # Cheese layer
        pygame.draw.circle(screen, (255, 220, 130), (int(center_x), int(center_y)), int(pizza_size * 0.95), 0)
        
        # Crust edge
        pygame.draw.circle(screen, (210, 180, 100), (int(center_x), int(center_y)), pizza_size, 3)
        
        # Red sauce base
        pygame.draw.circle(screen, (220, 80, 60), (int(center_x), int(center_y)), int(pizza_size * 0.85), 0)
        
        # Pepperoni - red circles
        num_pepperoni = 8
        for i in range(num_pepperoni):
            angle = time * 0.0005 + i * math.pi * 2 / num_pepperoni
            pep_dist = pizza_size * (0.3 + (i % 2) * 0.25)
            pep_x = center_x + math.cos(angle) * pep_dist
            pep_y = center_y + math.sin(angle) * pep_dist
            pep_size = int(5 + abs(math.sin(time_offset * 2 + i)) * 2)
            pygame.draw.circle(screen, (200, 40, 40), (int(pep_x), int(pep_y)), pep_size)
            pygame.draw.circle(screen, (255, 100, 80), (int(pep_x), int(pep_y)), max(1, pep_size - 1))
        
        # Pulsing energy core
        pulse = abs(math.sin(time * 0.003))
        core_radius = int(15 + pulse * 10)
        core_color = (int(255 * pulse), int(200 * pulse), 255)
        pygame.draw.circle(screen, core_color, (int(center_x), int(center_y)), core_radius)
        pygame.draw.circle(screen, WHITE, (int(center_x), int(center_y)), core_radius, 2)
        
        # Orbiting particles
        for i in range(8):
            orbit_angle = (time * 0.002 + i * (math.pi / 4)) % (2 * math.pi)
            orbit_radius = 70
            particle_x = center_x + math.cos(orbit_angle) * orbit_radius
            particle_y = center_y + math.sin(orbit_angle) * orbit_radius
            particle_size = 3 + int(2 * abs(math.sin(orbit_angle * 2)))
            particle_color = CYAN if i % 2 == 0 else NEON_GREEN
            pygame.draw.circle(screen, particle_color, (int(particle_x), int(particle_y)), particle_size)
        
        # Title text with glow
        title_text = self.font_xl.render("PIESTACK", True, NEON_BLUE)
        title_rect = title_text.get_rect(center=(center_x, center_y + 95))
        
        # Text glow effect
        for offset in range(8, 0, -2):
            glow_alpha = int(30 * (9 - offset) / 8)
            glow_surf = pygame.Surface((title_rect.width + offset * 2, title_rect.height + offset), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*NEON_BLUE[:3], glow_alpha), glow_surf.get_rect(), border_radius=8)
            screen.blit(glow_surf, (title_rect.x - offset, title_rect.y - offset // 2))
        
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle = self.font_small.render("UNLIMITED PIZZA", True, NEON_GREEN)
        subtitle_rect = subtitle.get_rect(center=(center_x, center_y + 140))
        screen.blit(subtitle, subtitle_rect)
        
        # Decorative line
        line_y = center_y + 160
        pygame.draw.line(screen, NEON_BLUE, (200, line_y), (SCREEN_WIDTH - 200, line_y), 2)
    
    def draw_menu(self, screen, current_seed):
        """Draw main menu - sleek and minimal"""
        # Dark gradient background
        for i in range(SCREEN_HEIGHT):
            ratio = i / SCREEN_HEIGHT
            r = int(15 + ratio * 5)
            g = int(10 + ratio * 8)
            b = int(30 + ratio * 15)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        # Draw animated logo
        self.draw_logo(screen)
        
        # Main content
        y = 280
        
        # Controls header
        header = self.font_medium.render("CONTROLS", True, NEON_GREEN)
        header_rect = header.get_rect(center=(SCREEN_WIDTH / 2, y))
        screen.blit(header, header_rect)
        y += 50
        
        # Control instructions
        controls = [
            "Arrow Keys / WASD - Move",
            "Z / Space - Shoot",
            "Shift - Sprint  •  Ctrl - Slow",
            "C - Use Ability  •  X - Use Ultimate",
            "P - Pause",
        ]
        
        for control in controls:
            text = self.font_small.render(control, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, y))
            screen.blit(text, text_rect)
            y += 35
        
        y += 20
        
        # Start prompt
        y = SCREEN_HEIGHT - 120
        start_text = self.font_large.render("PRESS ENTER TO START", True, NEON_BLUE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH / 2, y))
        screen.blit(start_text, start_rect)
        
        # Footer
        y = SCREEN_HEIGHT - 50
        footer = self.font_tiny.render("Press ESC to quit", True, WHITE)
        footer_rect = footer.get_rect(center=(SCREEN_WIDTH / 2, y))
        screen.blit(footer, footer_rect)
    
    def draw_pause(self, screen):
        """Draw pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), overlay.get_rect())
        screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH / 2, GAME_AREA_HEIGHT / 2))
        screen.blit(pause_text, pause_rect)
        
        continue_text = self.font_small.render("Press P to continue", True, GREEN)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH / 2, GAME_AREA_HEIGHT / 2 + 50))
        screen.blit(continue_text, continue_rect)
    
    def draw_laser_grid(self, screen, elapsed_ms):
        """Draw the laser grid mesh effect for ultimate ability"""
        # Calculate progress (0 to 1) for animation
        progress = min(1.0, elapsed_ms / 800.0)
        
        # Pulsing effect: bright at start, fades out
        pulse = 1.0 - (progress * 0.8)
        
        # Grid parameters
        grid_spacing = 35
        line_width = 2
        base_color = (0, 200, 255)  # Cyan for laser effect
        
        # Create semi-transparent surface for the grid
        grid_surface = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
        
        # Draw vertical lines with perspective effect
        for x in range(0, SCREEN_WIDTH + grid_spacing, grid_spacing):
            # Perspective: lines closer to center are brighter
            distance_from_center = abs(x - SCREEN_WIDTH / 2)
            perspective_factor = max(0.3, 1.0 - (distance_from_center / (SCREEN_WIDTH / 2)) * 0.5)
            
            alpha = int(150 * pulse * perspective_factor)
            color = (*base_color, alpha)
            
            pygame.draw.line(grid_surface, color, (x, 0), (x, GAME_AREA_HEIGHT), line_width)
        
        # Draw horizontal lines with perspective effect
        for y in range(0, GAME_AREA_HEIGHT + grid_spacing, grid_spacing):
            # Perspective: lines closer to top are brighter (depth effect)
            perspective_factor = max(0.3, 1.0 - (y / GAME_AREA_HEIGHT) * 0.3)
            
            alpha = int(150 * pulse * perspective_factor)
            color = (*base_color, alpha)
            
            pygame.draw.line(grid_surface, color, (0, y), (SCREEN_WIDTH, y), line_width)
        
        # Add diagonal shimmer lines for extra visual interest
        for offset in range(-GAME_AREA_HEIGHT, SCREEN_WIDTH + GAME_AREA_HEIGHT, grid_spacing * 2):
            alpha = int(80 * pulse * 0.7)
            color = (100, 255, 255, alpha)  # Brighter cyan for shimmer
            
            # Diagonal lines
            pygame.draw.line(grid_surface, color, (offset, 0), (offset + GAME_AREA_HEIGHT, GAME_AREA_HEIGHT), 1)
        
        screen.blit(grid_surface, (0, 0))
        
        # Add center glow during first half of animation
        if progress < 0.5:
            glow_alpha = int(100 * (1.0 - progress * 2))
            glow_surface = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (0, 200, 255, glow_alpha), 
                             (SCREEN_WIDTH // 2, GAME_AREA_HEIGHT // 2), 150)
            screen.blit(glow_surface, (0, 0))
    
    def draw_fullscreen_laser(self, screen, elapsed_ms, player_x, player_y):
        """Draw massive laser beam from player ship upward"""
        # Calculate progress (0 to 1) for animation
        progress = min(1.0, elapsed_ms / 3000.0)  # 3 second duration
        
        # IMMENSE laser beam width
        laser_width = 280
        laser_x_start = int(player_x - laser_width / 2)
        laser_x_end = laser_x_start + laser_width
        
        # Intensity and fade
        intensity = 1.0 - (progress * 0.8)
        
        # Main yellow-white laser core (very bright)
        laser_surface = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
        
        # Outer bright yellow layer
        outer_yellow = int(255 * intensity)
        outer_alpha = int(200 * intensity)
        pygame.draw.rect(laser_surface, (outer_yellow, outer_yellow, 0, outer_alpha),
                        (laser_x_start, 0, laser_width, player_y))
        
        # White hot inner core
        inner_width = laser_width * 0.6
        inner_x_start = int(player_x - inner_width / 2)
        inner_alpha = int(255 * intensity)
        pygame.draw.rect(laser_surface, (255, 255, 200, inner_alpha),
                        (inner_x_start, 0, int(inner_width), player_y))
        
        # Pulsing energy stripes through beam
        stripe_spacing = 12
        for y in range(0, int(player_y), stripe_spacing):
            pulse = 0.7 + 0.3 * abs(math.sin(y * 0.05 + elapsed_ms * 0.01))
            stripe_alpha = int(180 * intensity * pulse)
            stripe_color = (255, int(255 * pulse), 0, stripe_alpha)
            pygame.draw.line(laser_surface, stripe_color, (laser_x_start, y), (laser_x_end, y), 2)
        
        # Glow edges
        glow_width = 15
        for i in range(glow_width):
            glow_alpha = int(100 * intensity * (1.0 - i / glow_width))
            glow_color = (255, 255, 100, glow_alpha)
            # Left glow
            pygame.draw.line(laser_surface, glow_color,
                           (laser_x_start - glow_width + i, 0),
                           (laser_x_start - glow_width + i, int(player_y)), 1)
            # Right glow
            pygame.draw.line(laser_surface, glow_color,
                           (laser_x_end + glow_width - i, 0),
                           (laser_x_end + glow_width - i, int(player_y)), 1)
        
        # Bright impact at top of beam
        if elapsed_ms < 500:
            impact_alpha = int(255 * (1.0 - elapsed_ms / 500.0))
            pygame.draw.circle(laser_surface, (255, 255, 255, impact_alpha), (int(player_x), 0), 40)
        
        screen.blit(laser_surface, (0, 0))
