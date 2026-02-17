"""
Main game file for the Touhou-inspired bullet hell game
"""
import pygame
import sys
import math
import json
import os
try:
    import pyperclip
except ImportError:
    pyperclip = None
from config import *
from utils import SeededRandom
from player import Player
from enemy import spawn_enemy
from boss import create_boss
from powerup import spawn_powerup
from ui import UI, ParticleSystem
from audio import create_audio_system
from sprites import init_sprites


class Clone:
    """Clone entity that mirrors player appearance and fires bullets"""
    def __init__(self, x, y, size, color, lifetime=8000):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.lifetime = lifetime  # milliseconds
        self.spawn_time = pygame.time.get_ticks()
        self.alpha = 180
        self.shoot_cooldown = 100  # milliseconds between shots - faster shooting
        self.shoot_timer = 0
        self.sprite_cache = {}
    
    def update(self, dt):
        """Update clone lifetime"""
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.lifetime:
            return False
        
        # Fade out in last 500ms
        fade_start = self.lifetime - 500
        if elapsed > fade_start:
            fade_progress = (elapsed - fade_start) / 500.0
            self.alpha = int(255 * (1.0 - fade_progress))
        
        # Update shoot timer
        self.shoot_timer += dt
        
        return True
    
    def shoot(self, enemies=None):
        """Return bullets if ready to shoot (fires at nearest enemy)"""
        from bullet import PlayerBullet
        import math
        from utils import angle_to, distance
        
        if self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0
            
            # Find nearest enemy to shoot at
            if enemies and len(enemies) > 0:
                nearest_enemy = None
                min_distance = float('inf')
                
                for enemy in enemies:
                    dist = distance((self.x, self.y), (enemy.x, enemy.y))
                    if dist < min_distance:
                        min_distance = dist
                        nearest_enemy = enemy
                
                # If found an enemy, shoot at it
                if nearest_enemy:
                    angle = angle_to((self.x, self.y), (nearest_enemy.x, nearest_enemy.y))
                    bullet = PlayerBullet(self.x, self.y, angle, PLAYER_BULLET_DAMAGE)
                    return [bullet]
            
            # If no enemies, shoot straight up
            bullet = PlayerBullet(self.x, self.y, math.pi * 1.5, PLAYER_BULLET_DAMAGE)
            return [bullet]
        
        return []
    
    def draw(self, screen):
        """Draw the clone with same sprite as player"""
        if self.alpha <= 0:
            return
        
        # Use player sprite
        import sprites
        if sprites.sprite_loader:
            loader = sprites.sprite_loader
            ship_sprite = loader.get_player_sprite(1.0)  # Full health sprite
            
            if ship_sprite:
                # Cache scaled sprite
                if 'ship' not in self.sprite_cache:
                    scaled_ship = pygame.transform.scale(ship_sprite, (int(self.size * 7), int(self.size * 7)))
                    self.sprite_cache['ship'] = scaled_ship
                else:
                    scaled_ship = self.sprite_cache['ship']
                
                # Apply transparency
                ghostly_ship = scaled_ship.copy()
                ghostly_ship.set_alpha(self.alpha)
                
                ship_rect = ghostly_ship.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(ghostly_ship, ship_rect)
                return
        
        # Fallback to geometric drawing if sprites not loaded
        import math
        hex_points = []
        for i in range(6):
            angle = i * (math.pi / 3)
            hex_points.append((
                self.x + math.cos(angle) * self.size,
                self.y + math.sin(angle) * self.size
            ))
        
        # Draw with alpha
        hex_color = tuple(int(c * 0.7) for c in self.color[:3])
        pygame.draw.polygon(screen, hex_color, hex_points)
        pygame.draw.polygon(screen, self.color, hex_points, 2)


class Game:
    """Main game class"""
    def load_backgrounds(self):
        """Load and composite background images - one for each stage"""
        import os
        
        backgrounds = []
        
        # Define nebula colors to cycle through stages
        nebula_types = [
            ("Blue Nebula", 1),
            ("Green Nebula", 1),
            ("Purple Nebula", 1),
            ("Blue Nebula", 2),
            ("Green Nebula", 2),
            ("Purple Nebula", 2)
        ]
        
        # Create composite for each stage
        for i, (nebula_type, starfield_num) in enumerate(nebula_types):
            composite = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
            composite.fill((5, 5, 15))  # Dark space background
            
            # Load starfield
            starfield_path = f"backgrounds/Large 1024x1024/Starfields/Starfield_{starfield_num:02d}-1024x1024.png"
            if os.path.exists(starfield_path):
                starfield = pygame.image.load(starfield_path).convert_alpha()
                starfield = pygame.transform.scale(starfield, (SCREEN_WIDTH, SCREEN_HEIGHT))
                composite.blit(starfield, (0, 0))
            
            # Load nebula
            nebula_num = (i % 3) + 1  # Cycle through nebula variations
            nebula_path = f"backgrounds/Large 1024x1024/{nebula_type}/{nebula_type.replace(' ', '_')}_{nebula_num:02d}-1024x1024.png"
            if os.path.exists(nebula_path):
                nebula = pygame.image.load(nebula_path).convert_alpha()
                nebula = pygame.transform.scale(nebula, (SCREEN_WIDTH, SCREEN_HEIGHT))
                composite.blit(nebula, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
            
            backgrounds.append(composite)
        
        return backgrounds
    
    def load_statistics(self):
        """Load run statistics from file"""
        try:
            if os.path.exists('stats.json'):
                with open('stats.json', 'r') as f:
                    loaded_stats = json.load(f)
                    # Update with loaded stats
                    self.run_stats.update(loaded_stats)
        except:
            pass  # Use default stats if loading fails
    
    def save_statistics(self):
        """Save run statistics to file"""
        try:
            with open('stats.json', 'w') as f:
                json.dump(self.run_stats, f, indent=2)
        except:
            pass  # Silently fail if we can't save
    
    def __init__(self):
        pygame.init()
        
        # Get monitor info for fullscreen
        info = pygame.display.Info()
        monitor_width = info.current_w
        monitor_height = info.current_h
        
        # Calculate scaling to fit monitor while maintaining aspect ratio
        aspect_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        
        # Try to fit width-wise
        scaled_width = monitor_width
        scaled_height = int(monitor_width / aspect_ratio)
        
        # If height is too large, fit height-wise instead
        if scaled_height > monitor_height:
            scaled_height = monitor_height
            scaled_width = int(monitor_height * aspect_ratio)
        
        self.display_width = scaled_width
        self.display_height = scaled_height
        self.screen = pygame.display.set_mode((monitor_width, monitor_height), pygame.FULLSCREEN)
        
        # Surface to render game to (maintains 800x1000 ratio)
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("PIESTACK")
        
        # Load and set game icon
        try:
            icon = pygame.image.load('game_icon.png')
            pygame.display.set_icon(icon)
        except:
            pass  # Silently fail if icon not found
        
        self.clock = pygame.time.Clock()
        self.is_fullscreen = True
        
        # Screen shake effect
        self.screen_shake = 0
        self.screen_shake_intensity = 0
        
        # Game state
        self.state = "menu"  # menu, playing, game_over, paused
        self.running = True
        
        # Seeded random number generator
        self.rng = SeededRandom()
        
        # Game systems
        self.ui = UI()
        self.particle_system = ParticleSystem()
        self.audio = create_audio_system()
        self.sprite_loader = init_sprites()
        
        # Game objects
        self.player = None
        self.enemies = []
        self.boss = None
        self.player_bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.clones = []  # Clone entities for clone ultimate ability
        
        # Load stage backgrounds (one for each stage)
        self.backgrounds = self.load_backgrounds()
        
        # Game statistics
        self.score = 0
        self.high_score = 0
        self.stage = 1
        self.wave = 1
        self.kills = 0
        self.deaths = 0
        self.recent_score_events = []  # Track recent score events for display
        
        # Statistics tracking (for progression display)
        self.run_stats = {
            'total_kills': 0,
            'total_grazes': 0,
            'best_combo': 0,
            'best_score': 0,
            'best_stage': 1,
            'total_runs': 0
        }
        self.load_statistics()
        
        # Graze effect tracking
        self.graze_effects = []  # Visual effects for grazes
        
        # Ultimate visual effects
        self.laser_grid_time = 0
        self.fullscreen_laser_time = 0
        
        # Timers
        self.wave_timer = 0
        self.spawn_timer = 0
        self.spawn_rate = 1500  # milliseconds between enemy spawns (balanced for stage 1)
        self.death_screen_timer = 0
        
        # Ultimate unlock display
        self.ultimate_unlock_message = None
        self.ultimate_unlock_time = 0
        
        # Input handling
        self.input_text = ""
        self.waiting_for_seed_input = False
    
    def reset_game(self):
        """Reset game to initial state"""
        # Copy seed to clipboard when starting game
        if pyperclip:
            try:
                pyperclip.copy(str(self.rng.get_seed()))
            except:
                pass  # Silently ignore if clipboard copy fails
        
        self.player = Player(SCREEN_WIDTH / 2, GAME_AREA_HEIGHT - 100)
        self.enemies = []
        self.boss = None
        self.player_bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.clones = []  # Clear clones
        
        self.score = 0
        self.stage = 1
        self.wave = 1
        self.kills = 0
        self.recent_score_events = []  # Clear score events
        self.ui.falling_numbers = []  # Clear falling numbers from game over screen
        
        # Show stage intro
        self.ui.show_stage_intro(self.stage)
    
    def start_new_stage(self):
        """Start a new stage"""
        self.stage += 1
        self.wave = 1
        self.wave_timer = 0
        self.spawn_timer = 0
        
        # Clear bullets and enemies
        self.enemy_bullets.clear()
        self.enemies.clear()
        
        # Update spawn rate based on difficulty
        self.spawn_rate = int(1500 * (DIFFICULTY_SCALING['spawn_rate'] ** (self.stage - 1)))
        self.spawn_rate = max(300, self.spawn_rate)  # Reasonable minimum spawn rate
        
        # Show stage intro
        self.ui.show_stage_intro(self.stage)
        
        # Stage complete bonus
        self.score += SCORE_STAGE_COMPLETE
    
    def spawn_boss(self):
        """Spawn boss for current stage"""
        # Spawn boss in center of screen for dramatic effect
        self.boss = create_boss(self.stage, self.rng)
        self.boss.x = SCREEN_WIDTH / 2
        self.boss.y = GAME_AREA_HEIGHT / 2
        self.boss.target_x = self.boss.x
        self.boss.target_y = self.boss.y
        self.enemies.clear()  # Clear remaining enemies
        
        # Boss dispels all player powerups!
        self.player.clear_powerups()
        self.ui.show_message("Boss Appears! Powerups Dispelled!", 3000)
        
        self.ui.show_stage_intro(self.stage, self.boss.name)
    
    def update_menu(self, dt, events):
        """Update menu state"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.waiting_for_seed_input:
                    if event.key == pygame.K_RETURN:
                        # Try to parse seed
                        try:
                            seed = int(self.input_text) if self.input_text else None
                            if seed is not None:
                                self.rng.set_seed(seed)
                        except ValueError:
                            pass
                        self.input_text = ""
                        self.waiting_for_seed_input = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.input_text = ""
                        self.waiting_for_seed_input = False
                    elif event.unicode.isdigit() and len(self.input_text) < 10:
                        self.input_text += event.unicode
                else:
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = "playing"
                    elif event.key == pygame.K_s:
                        self.waiting_for_seed_input = True
                        self.input_text = str(self.rng.get_seed())
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
    
    def update_playing(self, dt):
        """Update playing state"""
        keys = pygame.key.get_pressed()
        
        # Update player
        self.player.update(dt, keys)
        
        # Update clones (they follow player position with slight delay)
        for clone in self.clones[:]:
            if not clone.update(dt):
                self.clones.remove(clone)
            else:
                # Clones follow player with slight offset
                clone.x = self.player.x + (clone.x - self.player.x) * 0.95
                clone.y = self.player.y + (clone.y - self.player.y) * 0.95
                
                # Clones fire bullets at enemies
                clone_bullets = clone.shoot(self.enemies)
                if clone_bullets:
                    self.player_bullets.extend(clone_bullets)
        
        # Check for tricks
        trick = self.player.check_tricks()
        if trick:
            self.score += SCORE_TRICK
            trick_names = {
                'loop': 'Loop-de-Loop!',
                'helix': 'Helix Maneuver!',
                'border_trace': 'Border Master!',
                'spiral': 'Spiral Vortex!',
                'wall_dancer': 'Wall Dancer!',
                'counter_loop': 'Reverse Spin!',
                'zigzag': 'Zigzag Master!',
                'dash_pattern': 'Dash Pattern!'
            }
            trick_name = trick_names.get(trick, 'Trick!')
            self.ui.show_message(f"{trick_name} +{SCORE_TRICK}", 2000)
            self.ui.add_score_popup(f"+{SCORE_TRICK}", YELLOW, self.player.x, self.player.y)
            self.ui.add_score_event('trick', SCORE_TRICK)
            self.recent_score_events.append(('trick', SCORE_TRICK, YELLOW))
            self.audio.play_sound('powerup')
        
        # Player shooting
        if keys[pygame.K_z] or keys[pygame.K_SPACE]:
            new_bullets = self.player.shoot()
            if new_bullets:
                self.player_bullets.extend(new_bullets)
                self.audio.play_sound('player_shoot')
                # Check if any bullets trigger screen shake (laser)
                for bullet in new_bullets:
                    if hasattr(bullet, 'triggers_screen_shake') and bullet.triggers_screen_shake:
                        self.activate_screen_shake(duration=15, intensity=12)
                        break  # Only shake once per shot
        
        # Update player bullets
        for bullet in self.player_bullets[:]:
            # Find nearest enemy for homing bullets
            target = None
            if bullet.homing:
                min_dist = float('inf')
                # Check boss first
                if self.boss:
                    dist = ((bullet.x - self.boss.x)**2 + (bullet.y - self.boss.y)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        target = self.boss
                # Check enemies
                for enemy in self.enemies:
                    dist = ((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        target = enemy
            
            bullet.update(dt, target)
            if bullet.is_off_screen():
                self.player_bullets.remove(bullet)
        
        # Update enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet.update(dt, self.player)
            if bullet.is_off_screen():
                self.enemy_bullets.remove(bullet)
        
        # Update power-ups
        for powerup in self.powerups[:]:
            powerup.update(dt)
            if powerup.is_off_screen():
                self.powerups.remove(powerup)
            elif powerup.get_rect().colliderect(self.player.get_hitbox()):
                message = powerup.apply(self.player)
                self.score += SCORE_POWERUP_COLLECT
                self.ui.add_score_popup(f"+{SCORE_POWERUP_COLLECT}", GREEN, powerup.x, powerup.y)
                self.ui.add_score_event('powerup', SCORE_POWERUP_COLLECT)
                self.recent_score_events.append(('powerup', SCORE_POWERUP_COLLECT, GREEN))
                self.powerups.remove(powerup)
                self.audio.play_sound('powerup')
        
        # Boss logic
        if self.boss:
            if not self.boss.is_intro:
                new_bullets = self.boss.update(dt, self.player)
                self.enemy_bullets.extend(new_bullets)
                
                # Boss periodically drops powerups
                if self.boss.should_drop_powerup():
                    powerup = spawn_powerup(self.boss.x + self.rng.randint(-40, 40), 
                                          self.boss.y + 50, self.rng)
                    if powerup:
                        self.powerups.append(powerup)
                        self.ui.show_message("Boss dropped a powerup!", 1500)
            else:
                self.boss.update(dt, self.player)
            
            # Check player bullet collisions with boss
            for bullet in self.player_bullets[:]:
                if bullet.get_rect().colliderect(self.boss.get_rect()):
                    if self.boss.take_damage(bullet.damage):
        # Boss defeated
                        # MASSIVE boss death explosions with intensity scaling
                        self.particle_system.add_explosion(
                            self.boss.x, self.boss.y, self.boss.color, 50, 2.5
                        )
                        self.particle_system.add_explosion(
                            self.boss.x, self.boss.y, WHITE, 80, 2.0
                        )
                        self.particle_system.add_explosion(
                            self.boss.x, self.boss.y, NEON_PINK, 60, 1.8
                        )
                        # HUGE screen shake for boss death
                        self.activate_screen_shake(duration=30, intensity=25)
                        
                        boss_score = SCORE_BOSS_KILL * self.stage
                        self.score += boss_score
                        self.ui.add_score_popup(f"+{boss_score}", ORANGE, self.boss.x, self.boss.y)
                        self.ui.add_score_event('boss', boss_score)
                        self.recent_score_events.append(('boss', boss_score, ORANGE))
                        self.audio.play_sound('enemy_death')
                        
                        # Drop some powerups
                        for i in range(3):
                            powerup = spawn_powerup(
                                self.boss.x + (i - 1) * 30, self.boss.y, self.rng
                            )
                            if powerup:
                                self.powerups.append(powerup)
                        
                        # Boss gives less ultimate charge (5% instead of 10%)
                        self.player.ultimate_charge = min(self.player.ultimate_max,
                                                         self.player.ultimate_charge + 5)
                        
                        self.boss = None
                        self.start_new_stage()
                    else:
                        # Add ultimate charge on boss hit (reduced to 1%)
                        self.player.ultimate_charge = min(self.player.ultimate_max,
                                                         self.player.ultimate_charge + 1)
                        self.particle_system.add_hit_effect(
                            bullet.x, bullet.y, self.boss.color
                        )
                        # Boss hit sounds pitch up too
                        boss_pitch = 1.0 + (self.player.combo_multiplier - 1.0) * 0.1
                        self.audio.play_sound('boss_hit', boss_pitch)
                    
                    self.player_bullets.remove(bullet)
                    break
        else:
            # Normal wave logic
            self.wave_timer += dt
            self.spawn_timer += dt
            
            # Spawn enemies (with wave-based and stage-based difficulty)
            # Increase spawn rate and enemy count as waves and stages progress
            stage_multiplier = DIFFICULTY_SCALING['enemy_count'] ** (self.stage - 1)
            max_enemies = int(ENEMIES_PER_WAVE * stage_multiplier) + (self.wave - 1) * 2
            max_enemies = min(max_enemies, MAX_ENEMIES_ON_SCREEN)
            current_enemy_count = len(self.enemies)
            
            if self.spawn_timer >= self.spawn_rate and current_enemy_count < max_enemies:
                enemy = spawn_enemy(self.stage, self.rng, self.wave, current_enemy_count)
                self.enemies.append(enemy)
                self.spawn_timer = 0
            
            # Update enemies
            for enemy in self.enemies[:]:
                new_bullets = enemy.update(dt, self.player)
                self.enemy_bullets.extend(new_bullets)
                
                # Check player bullet collisions
                for bullet in self.player_bullets[:]:
                    if bullet.get_rect().colliderect(enemy.get_rect()):
                        if enemy.take_damage(bullet.damage):
                            # Enemy defeated
                            self.particle_system.add_explosion(
                                enemy.x, enemy.y, enemy.color, 20
                            )
                            
                            # Store old combo to check for milestone
                            old_combo = self.player.combo
                            
                            # Increment combo
                            self.player.increment_combo()
                            
                            # Check for combo milestone
                            for threshold in COMBO_THRESHOLDS[1:]:  # Skip 0
                                if old_combo < threshold <= self.player.combo:
                                    # Hit a new combo tier!
                                    self.particle_system.add_explosion(self.player.x, self.player.y, YELLOW, 40)
                                    self.ui.show_message(f"COMBO x{self.player.combo_multiplier:.1f}!", 1500)
                                    self.activate_screen_shake(duration=10, intensity=8)
                                    break
                            
                            # Apply combo multiplier to score
                            enemy_score = int(SCORE_ENEMY_KILL * self.player.combo_multiplier)
                            self.score += enemy_score
                            
                            # Show multiplier in popup if > 1x
                            if self.player.combo_multiplier > 1.0:
                                self.ui.add_score_popup(f"+{enemy_score} x{self.player.combo_multiplier:.1f}", YELLOW, enemy.x, enemy.y)
                            else:
                                self.ui.add_score_popup(f"+{enemy_score}", WHITE, enemy.x, enemy.y)
                            
                            self.ui.add_score_event('enemy', enemy_score)
                            self.recent_score_events.append(('enemy', enemy_score, WHITE))
                            self.kills += 1
                            
                            # Update best combo stat
                            if self.player.combo > self.run_stats['best_combo']:
                                self.run_stats['best_combo'] = self.player.combo
                            
                            self.enemies.remove(enemy)
                            # Higher pitched sound with higher combo
                            pitch = 1.0 + (self.player.combo_multiplier - 1.0) * 0.15
                            self.audio.play_sound('enemy_death', pitch)
                            
                            # Charge ultimate (2% per enemy - harder to get)
                            self.player.ultimate_charge = min(self.player.ultimate_max, 
                                                             self.player.ultimate_charge + 2)
                            
                            # Charge ability (8% per enemy - easier to get)
                            self.player.ability_charge = min(self.player.ability_max,
                                                            self.player.ability_charge + 8)
                            
                            # Spawn power-up
                            powerup = spawn_powerup(enemy.x, enemy.y, self.rng)
                            if powerup:
                                self.powerups.append(powerup)
                        else:
                            self.particle_system.add_hit_effect(
                                bullet.x, bullet.y, enemy.color
                            )
                            # Slightly higher pitch for hits during combos
                            hit_pitch = 1.0 + (self.player.combo_multiplier - 1.0) * 0.08
                            self.audio.play_sound('enemy_hit', hit_pitch)
                        
                        self.player_bullets.remove(bullet)
                        break
            
            # Check if wave is complete
            if self.wave_timer >= WAVE_DURATION:
                self.wave += 1
                self.wave_timer = 0
                
                # Speed up spawn rate as waves progress
                wave_progress = (self.wave - 1) / WAVES_PER_STAGE
                self.spawn_rate = int(1500 * (DIFFICULTY_SCALING['spawn_rate'] ** (self.stage - 1)) * (1 - wave_progress * 0.4))
                self.spawn_rate = max(300, self.spawn_rate)  # Minimum 300ms between spawns
                
                if self.wave > WAVES_PER_STAGE:
                    # Spawn boss
                    self.spawn_boss()
        
        # Check enemy bullet collisions with player and grazing
        for bullet in self.enemy_bullets[:]:
            # Check for graze (near miss)
            bullet_id = id(bullet)
            if bullet_id not in self.player.grazed_bullets:
                dist_to_player = math.sqrt((bullet.x - self.player.x)**2 + (bullet.y - self.player.y)**2)
                
                # Graze if bullet is close but not hitting hitbox
                if dist_to_player < GRAZE_DISTANCE and dist_to_player > self.player.hitbox_size:
                    self.player.grazed_bullets.add(bullet_id)
                    self.player.graze_count += 1
                    self.run_stats['total_grazes'] += 1
                    
                    # Award graze score
                    graze_score = GRAZE_SCORE
                    self.score += graze_score
                    self.ui.add_score_popup(f"+{graze_score} GRAZE", CYAN, bullet.x, bullet.y)
                    
                    # Charge ability (2% per graze - mostly for ability)
                    self.player.ability_charge = min(self.player.ability_max,
                                                    self.player.ability_charge + 2)
                    
                    # Add visual effect
                    self.graze_effects.append({
                        'x': self.player.x,
                        'y': self.player.y,
                        'time': pygame.time.get_ticks(),
                        'angle': math.atan2(bullet.y - self.player.y, bullet.x - self.player.x)
                    })
                    
                    # Play sound (if available)
                    # self.audio.play_sound('graze')
            
            # Distance-based collision feels more consistent with small hitbox
            hit_dist = math.hypot(bullet.x - self.player.x, bullet.y - self.player.y)
            if hit_dist <= (bullet.size + self.player.hitbox_size):
                # Skip damage if player is phasing through (sprinting)
                if not self.player.phase_through:
                    if self.player.take_damage(bullet.damage):
                        self.particle_system.add_explosion(
                            self.player.x, self.player.y, WHITE, 15
                        )
                        self.audio.play_sound('player_hit')
                self.enemy_bullets.remove(bullet)
        
        # Update particles
        self.particle_system.update(dt)
        
        # Update UI animations
        self.ui.update_score_popups(dt)
        
        # Update ultimate unlock message timer
        if self.ultimate_unlock_message and self.ultimate_unlock_time > 0:
            self.ultimate_unlock_time -= dt
            if self.ultimate_unlock_time <= 0:
                self.ultimate_unlock_message = None
        
        # Check if ultimate just became available
        if self.player.ultimate_charge >= self.player.ultimate_max:
            if not hasattr(self, 'prev_ult_charge') or self.prev_ult_charge < self.player.ultimate_max:
                # Ultimate just unlocked - flash + screenshake + text display
                self.activate_screen_shake(duration=15, intensity=15)
                # Set ult display
                ult_name = {
                    'laser_grid': 'SQUARE SLICES',
                    'clone': 'CLONE RECIPE',
                    'fullscreen_laser': 'FULL OVEN'
                }.get(self.player.ultimate_type, 'ULTIMATE')
                self.ultimate_unlock_message = ult_name
                self.ultimate_unlock_time = 1500  # Show for 1.5 seconds
        
        self.prev_ult_charge = self.player.ultimate_charge
        if not self.player.is_alive():
            # Massive death explosion
            self.particle_system.add_explosion(self.player.x, self.player.y, RED, 100)
            self.particle_system.add_explosion(self.player.x, self.player.y, YELLOW, 80)
            self.particle_system.add_explosion(self.player.x, self.player.y, WHITE, 60)
            self.state = "game_over"
            self.death_screen_timer = 0
            self.deaths += 1
            if self.score > self.high_score:
                self.high_score = self.score
            
            # Update run statistics
            self.run_stats['total_kills'] += self.kills
            self.run_stats['total_grazes'] += self.player.graze_count
            self.run_stats['total_runs'] += 1
            if self.score > self.run_stats['best_score']:
                self.run_stats['best_score'] = self.score
            if self.stage > self.run_stats['best_stage']:
                self.run_stats['best_stage'] = self.stage
            
            # Save statistics
            self.save_statistics()
    
    def update_game_over(self, dt, events):
        """Update game over state"""
        self.death_screen_timer += dt
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = "menu"
                elif event.key == pygame.K_r:  # Quick restart
                    self.__init__()  # Reinitialize the game
                    self.state = "playing"
                    self.stage = 1
                    self.wave = 1
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update_paused(self, dt, events):
        """Update paused state"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.state = "playing"
    
    def draw_menu(self):
        """Draw menu"""
        self.ui.draw_menu(self.game_surface, self.rng.get_seed())
    
    def draw_playing(self):
        """Draw playing state"""
        # Draw stage-specific background (single blit - highly optimized)
        if self.backgrounds:
            # Cycle through backgrounds based on stage
            bg_index = (self.stage - 1) % len(self.backgrounds)
            self.game_surface.blit(self.backgrounds[bg_index], (0, 0))
        else:
            self.game_surface.fill((5, 5, 15))
        
        # Draw particles
        self.particle_system.draw(self.game_surface)
        
        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(self.game_surface)
        
        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            bullet.draw(self.game_surface)
        
        # Draw player bullets
        for bullet in self.player_bullets:
            bullet.draw(self.game_surface)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.game_surface)
        
        # Draw boss
        if self.boss:
            self.boss.draw(self.game_surface)
        
        # Draw clones (before player so player is on top)
        for clone in self.clones:
            clone.draw(self.game_surface)
        
        # Draw player
        if self.player:
            self.player.draw(self.game_surface)
        
        # Draw graze effects (spark lines)
        current_time = pygame.time.get_ticks()
        for graze in self.graze_effects[:]:
            elapsed = current_time - graze['time']
            if elapsed < 200:  # 200ms duration
                alpha = int(255 * (1 - elapsed / 200))
                length = 30 - elapsed / 10
                angle = graze['angle']
                end_x = graze['x'] + math.cos(angle) * length
                end_y = graze['y'] + math.sin(angle) * length
                
                # Draw spark line
                graze_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                local_start = (30, 30)
                local_end = (30 + math.cos(angle) * length, 30 + math.sin(angle) * length)
                pygame.draw.line(graze_surf, (*CYAN[:3], alpha), local_start, local_end, 2)
                self.game_surface.blit(graze_surf, (int(graze['x'] - 30), int(graze['y'] - 30)), 
                                      special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                self.graze_effects.remove(graze)
        
        # Draw score popups
        self.ui.draw_score_popups(self.game_surface)
        
        # Draw borders with combo-based pulsing effect
        border_pulse = 1.0
        border_glow_alpha = 0
        if self.player.combo > 0:
            # Pulse intensity based on combo tier
            pulse_speed = 0.005 + self.player.combo_multiplier * 0.002
            border_pulse = 1.0 + math.sin(pygame.time.get_ticks() * pulse_speed) * 0.3 * (self.player.combo_multiplier - 1.0)
            border_glow_alpha = int(30 + self.player.combo_multiplier * 20)
        
        border_width = int(3 * border_pulse)
        glow_width = border_width + 6
        
        # Combo color progression: cyan -> green -> yellow -> orange -> red
        if self.player.combo_multiplier >= 5.0:
            border_color = (255, 50, 50)  # Red
            glow_color = (255, 100, 100)
        elif self.player.combo_multiplier >= 3.0:
            border_color = (255, 150, 0)  # Orange
            glow_color = (255, 200, 100)
        elif self.player.combo_multiplier >= 2.0:
            border_color = YELLOW
            glow_color = (255, 255, 150)
        elif self.player.combo_multiplier >= 1.5:
            border_color = NEON_GREEN
            glow_color = (150, 255, 150)
        else:
            border_color = CYAN
            glow_color = (100, 255, 255)
        
        # Draw glow layer
        if border_glow_alpha > 0:
            glow_surf = pygame.Surface((PLAYABLE_AREA_WIDTH, PLAYABLE_AREA_HEIGHT), pygame.SRCALPHA)
            # Top glow
            pygame.draw.line(glow_surf, (*glow_color, border_glow_alpha), (0, 0), (PLAYABLE_AREA_WIDTH, 0), glow_width)
            # Left glow
            pygame.draw.line(glow_surf, (*glow_color, border_glow_alpha), (0, 0), (0, PLAYABLE_AREA_HEIGHT), glow_width)
            self.game_surface.blit(glow_surf, (0, 0))
        
        # Draw solid borders
        # Top border
        pygame.draw.line(self.game_surface, border_color, (0, 0), (PLAYABLE_AREA_WIDTH, 0), border_width)
        # Left border
        pygame.draw.line(self.game_surface, border_color, (0, 0), (0, PLAYABLE_AREA_HEIGHT), border_width)
        # Bottom border (between play area and bottom panel)
        pygame.draw.line(self.game_surface, NEON_BLUE, (0, BOTTOM_PANEL_START_Y), (PLAYABLE_AREA_WIDTH, BOTTOM_PANEL_START_Y), 4)
        # Right border (between play area and right panel)
        pygame.draw.line(self.game_surface, NEON_BLUE, (SIDE_PANEL_START_X, 0), (SIDE_PANEL_START_X, BOTTOM_PANEL_START_Y), 4)
        
        # Draw game area UI (health bar, etc - left side)
        self.ui.draw_player_health(self.game_surface, self.player)
        
        # Draw right-side panel with stats
        self.ui.draw_side_panel(self.game_surface, self.player, self.score, 
                               self.high_score, self.stage, self.wave, self.kills, 
                               self.recent_score_events)
        
        # Boss health bar drawn in bottom panel, removed duplicate display
        
        # Draw active powerups (bottom panel with all game info)
        self.ui.draw_active_powerups(self.game_surface, self.player, self.stage, self.wave, 
                                     self.boss, self.wave_timer)
        
        # Draw laser grid ultimate effect
        if self.laser_grid_time > 0:
            elapsed = pygame.time.get_ticks() - self.laser_grid_time
            if elapsed < 800:  # 800ms duration
                self.ui.draw_laser_grid(self.game_surface, elapsed)
            else:
                self.laser_grid_time = 0
        
        # Draw fullscreen laser ultimate effect
        if self.fullscreen_laser_time > 0:
            elapsed = pygame.time.get_ticks() - self.fullscreen_laser_time
            if elapsed < 3000:  # 3 second duration
                self.ui.draw_fullscreen_laser(self.game_surface, elapsed, self.player.x, self.player.y)
            else:
                self.fullscreen_laser_time = 0
        
        # Draw messages
        self.ui.draw_message(self.game_surface, self.clock.get_time())
        
        # Low health red tint
        health_ratio = self.player.health / self.player.max_health
        if health_ratio < 0.25:  # Red tint when below 25% health
            red_intensity = int(80 * (1 - health_ratio * 4))  # Max 80 alpha
            red_overlay = pygame.Surface((PLAYABLE_AREA_WIDTH, PLAYABLE_AREA_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(red_overlay, (255, 0, 0, red_intensity), red_overlay.get_rect())
            self.game_surface.blit(red_overlay, (0, 0))
        
        # Draw stage intro
        boss_name = self.boss.name if self.boss and self.boss.is_intro else None
        self.ui.draw_stage_intro(self.game_surface, self.stage, boss_name, self.clock.get_time())
        
        # Draw ultimate unlock message (large, transparent)
        if self.ultimate_unlock_message:
            # Fade out as time goes down
            alpha = int(100 * (self.ultimate_unlock_time / 1500))  # Max 100 alpha (transparent)
            font = pygame.font.Font(None, 140)  # Large font
            text = font.render(self.ultimate_unlock_message, True, NEON_PINK)
            text.set_alpha(alpha)
            text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, GAME_AREA_HEIGHT / 2))
            self.game_surface.blit(text, text_rect)
    
    def draw_game_over(self):
        """Draw game over state"""
        # Draw last game frame
        self.draw_playing()
        
        # Red flash effect in the first second
        if self.death_screen_timer < 1000:
            flash_intensity = int(100 * (1 - self.death_screen_timer / 1000))
            flash = pygame.Surface((SCREEN_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(flash, (255, 0, 0, flash_intensity), flash.get_rect())
            self.game_surface.blit(flash, (0, 0))
        
        # Draw game over overlay
        self.ui.draw_game_over(self.game_surface, self.score, self.stage, self.rng.get_seed(), 
                              self.deaths, self.death_screen_timer)
    
    def draw_paused(self):
        """Draw paused state"""
        self.draw_playing()
        self.ui.draw_pause(self.game_surface)
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PIESTACK")
    
    def activate_ultimate(self):
        """Activate the ultimate ability based on type"""
        if self.player.ultimate_charge < self.player.ultimate_max:
            return
        
        self.player.ultimate_charge = 0
        self.player.ultimate_active = True
        self.player.ultimate_duration = 800  # 800ms duration for visual effect
        
        laser_damage = 0  # Default no damage
        
        if self.player.ultimate_type == 'laser_grid':
            # Store grid activation time for drawing
            self.laser_grid_time = pygame.time.get_ticks()
            self.ui.show_message("ULTIMATE: GRID!", 2000)
            laser_damage = 300  # Grid does massive damage
        elif self.player.ultimate_type == 'clone':
            self.ui.show_message("ULTIMATE: CLONE!", 2000)
            # Spawn 3 clones that mirror player for 8 seconds
            for i in range(3):
                offset_x = (i - 1) * 40
                clone = Clone(self.player.x + offset_x, self.player.y, self.player.size, 
                            NEON_BLUE, lifetime=8000)
                self.clones.append(clone)
        else:  # fullscreen_laser
            self.fullscreen_laser_time = pygame.time.get_ticks()
            self.ui.show_message("ULTIMATE: LASER!", 2000)
            # IMMENSE damage for fullscreen laser
            laser_damage = 2500
        
        # Only destroy bullets and damage for fullscreen laser
        if laser_damage > 0:
            # Destroy all enemy bullets
            self.enemy_bullets.clear()
            
            # Damage all enemies and the boss
            if self.boss:
                self.boss.take_damage(laser_damage)
                self.particle_system.add_explosion(self.boss.x, self.boss.y, WHITE, 50)
            
            for enemy in self.enemies[:]:
                if enemy.take_damage(laser_damage):
                    self.particle_system.add_explosion(enemy.x, enemy.y, enemy.color, 30)
                    enemy_score = SCORE_ENEMY_KILL
                    self.score += enemy_score
                    self.ui.add_score_popup(f"+{enemy_score}", YELLOW, enemy.x, enemy.y)
                    self.ui.add_score_event('ultimate', enemy_score)
                    self.recent_score_events.append(('ultimate', enemy_score, NEON_PINK))
                    self.kills += 1
                    self.enemies.remove(enemy)
                else:
                    self.particle_system.add_explosion(enemy.x, enemy.y, CYAN, 20)
        
        # Massive screen shake
        self.activate_screen_shake(duration=20, intensity=15)
        
        # Sound effect
        self.audio.play_sound('boss_hit')
    
    def show_ability_activation(self):
        """Show visual feedback for ability activation"""
        ability_names = {
            'berserker': 'PIZZA FURY',
            'glass_cannon': 'THIN CRUST',
            'invincible': 'BRICK OVEN'
        }
        ability_name = ability_names.get(self.player.ability_type, self.player.ability_type.upper().replace('_', ' '))
        
        if self.player.ability_type == 'berserker':
            self.ui.show_message(f"ABILITY: {ability_name}!", 2000)
            # Red explosion
            self.particle_system.add_explosion(self.player.x, self.player.y, RED, 60)
        elif self.player.ability_type == 'glass_cannon':
            self.ui.show_message(f"ABILITY: {ability_name}!", 2000)
            # Purple explosion
            self.particle_system.add_explosion(self.player.x, self.player.y, PURPLE, 60)
        elif self.player.ability_type == 'invincible':
            self.ui.show_message(f"ABILITY: {ability_name}!", 2000)
            # Green/cyan shield effect
            self.particle_system.add_explosion(self.player.x, self.player.y, NEON_GREEN, 60)
        
        # Screen shake
        self.activate_screen_shake(duration=15, intensity=10)
        
        # Sound effect
        self.audio.play_sound('powerup')
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(FPS)
            
            # Event handling
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.state == "playing":
                        self.state = "menu"
                    elif event.key == pygame.K_p and self.state == "playing":
                        self.state = "paused"
                    elif event.key == pygame.K_x and self.state == "playing":
                        # X key - activate ultimate if charged
                        if self.player.ultimate_charge >= self.player.ultimate_max:
                            self.activate_ultimate()
                    elif event.key == pygame.K_c and self.state == "playing":
                        # C key - activate ability if charged
                        if self.player.activate_ability():
                            self.show_ability_activation()
            
            # Update based on state
            if self.state == "menu":
                self.update_menu(dt, events)
                self.draw_menu()
            elif self.state == "playing":
                self.update_playing(dt)
                self.draw_playing()
            elif self.state == "game_over":
                self.update_game_over(dt, events)
                self.draw_game_over()
            elif self.state == "paused":
                self.update_paused(dt, events)
                self.draw_paused()
            
            # Update display
            self.render_to_screen()
        
        pygame.quit()
        sys.exit()
    
    def render_to_screen(self):
        """Render game surface to screen with proper fullscreen scaling and shake"""
        # Clear actual screen with black (for letterboxing)
        self.screen.fill(BLACK)
        
        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake > 0:
            import random as rand
            shake_offset_x = rand.randint(-int(self.screen_shake_intensity), int(self.screen_shake_intensity))
            shake_offset_y = rand.randint(-int(self.screen_shake_intensity), int(self.screen_shake_intensity))
            self.screen_shake -= 1
        
        # Calculate center position for letterboxing
        offset_x = (self.screen.get_width() - self.display_width) // 2 + shake_offset_x
        offset_y = (self.screen.get_height() - self.display_height) // 2 + shake_offset_y
        
        # Scale game surface to fit screen while maintaining aspect ratio
        scaled = pygame.transform.scale(self.game_surface, (self.display_width, self.display_height))
        self.screen.blit(scaled, (offset_x, offset_y))
        
        pygame.display.flip()
    
    def activate_screen_shake(self, duration=10, intensity=8):
        """Activate screen shake effect"""
        self.screen_shake = duration
        self.screen_shake_intensity = intensity


def main():
    """Main entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
