"""
Player class for the bullet hell game
"""
import pygame
import math
from config import *
from bullet import PlayerBullet
import sprites

class Player:
    """Player character"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.hitbox_size = PLAYER_HITBOX_SIZE
        self.speed = PLAYER_SPEED
        self.sprint_speed = PLAYER_SPEED * 1.8  # 80% faster than normal
        self.slow_speed = PLAYER_SLOW_SPEED
        self.phase_through = False  # Phasing through objects while sprinting
        self.phase_time = 0  # Duration of phasing effect
        self.phase_charge = 100  # Phase meter (0-100)
        self.phase_max = 100
        self.phase_deplete_rate = 60  # Points per second when phasing
        self.phase_regen_rate = 40  # Points per second when not phasing
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.shoot_cooldown = 0
        self.damage_multiplier = 1.0
        self.invincible_time = 0
        self.shield = False
        self.power_level = 1
        self.weapon_style = 'normal'  # Current weapon style
        self.style_timer = 0  # For burst fire timing
        
        # Trick tracking
        self.position_history = []  # Track positions for trick detection
        self.border_touched = {'top': False, 'bottom': False, 'left': False, 'right': False}
        self.trick_cooldown = 0
        
        # Stats for scoring
        self.shots_fired = 0
        self.damage_taken = 0
        
        # Ultimate ability system
        self.ultimate_charge = 0
        self.ultimate_max = 100
        self.ultimate_active = False
        self.ultimate_duration = 0
        self.ultimate_type = 'laser_grid'  # or 'clone'
        
        # ABILITY system (risk/reward activated abilities)
        self.ability_charge = 0
        self.ability_max = 100
        self.ability_active = False
        self.ability_duration = 0
        self.ability_type = 'berserker'  # Start with berserker
        self.glass_cannon_triggered = False  # Track if glass cannon was used this ability activation
        
        # Combo system
        self.combo = 0
        self.combo_multiplier = 1.0
        
        # Graze system  
        self.graze_count = 0
        self.grazed_bullets = set()  # Track which bullets were grazed
        
        # Sprite animation
        self.animation_timer = 0
        self.is_moving = False
        
        # Sprite cache for optimization (avoid per-frame scaling)
        self.sprite_cache = {}  # Cache scaled sprites by health state
        self.last_health_state = None
        
    def update(self, dt, keys):
        """Update player state"""
        # Reduce invincibility timer
        if self.invincible_time > 0:
            self.invincible_time = max(0, self.invincible_time - dt)
        
        # Update phase through duration
        if self.phase_through:
            self.phase_time -= dt
            # Deplete phase charge
            self.phase_charge = max(0, self.phase_charge - (self.phase_deplete_rate * dt / 1000))
            if self.phase_time <= 0 or self.phase_charge <= 0:
                self.phase_through = False
        else:
            # Regenerate phase charge when not phasing
            self.phase_charge = min(self.phase_max, self.phase_charge + (self.phase_regen_rate * dt / 1000))
        
        # Update ability duration
        if self.ability_active and self.ability_duration > 0:
            self.ability_duration = max(0, self.ability_duration - dt)
            if self.ability_duration == 0:
                self.ability_active = False
        
        # Movement - Shift=sprint (1.8x), Ctrl=slow (0.5x), normal=base speed
        if keys[pygame.K_LCTRL]:
            speed = self.slow_speed
        elif keys[pygame.K_LSHIFT] and self.phase_charge > 0:
            speed = self.sprint_speed
            self.phase_through = True  # Enable phasing while sprinting (if charge available)
            self.phase_time = 100  # 100ms of phasing per frame
        else:
            speed = self.speed
        
        dx = 0
        dy = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        
        # Track if player is moving for animation
        self.is_moving = (dx != 0 or dy != 0)
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707  # 1/sqrt(2)
            dy *= 0.707
        
        self.x += dx * speed
        self.y += dy * speed
        
        # Keep player in bounds (respecting panel areas)
        margin = self.size
        self.x = max(margin, min(PLAYABLE_AREA_WIDTH - margin, self.x))
        self.y = max(margin, min(PLAYABLE_AREA_HEIGHT - margin, self.y))
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0, self.shoot_cooldown - dt)
        
        # Update style timer
        self.style_timer += dt
        
        # Update trick cooldown
        if self.trick_cooldown > 0:
            self.trick_cooldown = max(0, self.trick_cooldown - dt)
        
        # Track position for tricks
        self.position_history.append((self.x, self.y, dt))
        # Keep only last 3 seconds of history
        total_time = sum(pos[2] for pos in self.position_history)
        while total_time > 3000 and len(self.position_history) > 10:
            removed = self.position_history.pop(0)
            total_time -= removed[2]
        
        # Track border touches for border trick
        margin = self.size + 5
        if self.x <= margin:
            self.border_touched['left'] = True
        if self.x >= PLAYABLE_AREA_WIDTH - margin:
            self.border_touched['right'] = True
        if self.y <= margin:
            self.border_touched['top'] = True
        if self.y >= PLAYABLE_AREA_HEIGHT - margin:
            self.border_touched['bottom'] = True
    
    def shoot(self):
        """Create player bullets based on current weapon style"""
        if self.shoot_cooldown > 0:
            return []
        
        bullets = []
        
        # Get bullets based on weapon style
        if self.weapon_style == 'normal':
            bullets = self._shoot_normal()
        elif self.weapon_style == 'burst':
            bullets = self._shoot_burst()
        elif self.weapon_style == 'laser':
            bullets = self._shoot_laser()
        elif self.weapon_style == 'spread':
            bullets = self._shoot_spread()
        elif self.weapon_style == 'homing':
            bullets = self._shoot_homing()
        elif self.weapon_style == 'rapid':
            bullets = self._shoot_rapid()
        
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN
        self.shots_fired += len(bullets)
        return bullets
    
    def _shoot_normal(self):
        """Normal shooting pattern"""
        bullets = []
        damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier
        
        # Basic shot pattern based on power level
        if self.power_level == 1:
            bullets.append(PlayerBullet(self.x, self.y - self.size, math.pi * 1.5, damage, 'normal'))
        elif self.power_level == 2:
            bullets.append(PlayerBullet(self.x - 5, self.y - self.size, math.pi * 1.5, damage, 'normal'))
            bullets.append(PlayerBullet(self.x + 5, self.y - self.size, math.pi * 1.5, damage, 'normal'))
        elif self.power_level >= 3:
            bullets.append(PlayerBullet(self.x, self.y - self.size, math.pi * 1.5, damage, 'normal'))
            bullets.append(PlayerBullet(self.x - 8, self.y - self.size, math.pi * 1.5 - 0.1, damage, 'normal'))
            bullets.append(PlayerBullet(self.x + 8, self.y - self.size, math.pi * 1.5 + 0.1, damage, 'normal'))
        
        if self.power_level >= 4:
            bullets.append(PlayerBullet(self.x - 15, self.y, math.pi * 1.5 - 0.2, damage * 0.7, 'normal'))
            bullets.append(PlayerBullet(self.x + 15, self.y, math.pi * 1.5 + 0.2, damage * 0.7, 'normal'))
        
        return bullets
    
    def _shoot_burst(self):
        """Burst fire - powerful but slow"""
        bullets = []
        damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier * 3.0  # Triple damage
        
        # Fire fewer, stronger shots
        bullets.append(PlayerBullet(self.x, self.y - self.size, math.pi * 1.5, damage, 'burst'))
        
        if self.power_level >= 2:
            bullets.append(PlayerBullet(self.x - 10, self.y - self.size, math.pi * 1.5 - 0.05, damage, 'burst'))
            bullets.append(PlayerBullet(self.x + 10, self.y - self.size, math.pi * 1.5 + 0.05, damage, 'burst'))
        
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN * 3  # Much slower fire rate
        return bullets
    
    def _shoot_laser(self):
        """Laser beam - fast, piercing shots"""
        bullets = []
        damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier * 1.5
        
        # Fire a stream of fast lasers
        for i in range(2 + self.power_level):
            offset = i * 2
            bullets.append(PlayerBullet(self.x, self.y - self.size - offset, math.pi * 1.5, damage, 'laser'))
        
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN * 0.5  # Faster fire rate
        return bullets
    
    def _shoot_spread(self):
        """Spread shot - wide coverage"""
        bullets = []
        damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier * 0.8
        
        # Fire in a spread pattern
        num_bullets = 5 + self.power_level
        spread_angle = 0.6
        base_angle = math.pi * 1.5
        
        for i in range(num_bullets):
            angle = base_angle + (i - num_bullets // 2) * (spread_angle / num_bullets)
            bullets.append(PlayerBullet(self.x, self.y - self.size, angle, damage, 'normal'))
        
        return bullets
    
    def _shoot_homing(self):
        """Homing missiles - track enemies"""
        bullets = []
        damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier * 1.2
        
        # Fire homing missiles
        bullets.append(PlayerBullet(self.x, self.y - self.size, math.pi * 1.5, damage, 'homing'))
        
        if self.power_level >= 2:
            bullets.append(PlayerBullet(self.x - 10, self.y, math.pi * 1.5 - 0.3, damage, 'homing'))
            bullets.append(PlayerBullet(self.x + 10, self.y, math.pi * 1.5 + 0.3, damage, 'homing'))
        
        if self.power_level >= 4:
            bullets.append(PlayerBullet(self.x - 5, self.y - 5, math.pi * 1.5, damage, 'homing'))
            bullets.append(PlayerBullet(self.x + 5, self.y - 5, math.pi * 1.5, damage, 'homing'))
        
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN * 1.5  # Slightly slower
        return bullets
    
    def _shoot_rapid(self):
        """Rapid fire - many weak shots"""
        bullets = []
        damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier * 0.6
        
        # Fire rapid shots
        bullets.append(PlayerBullet(self.x, self.y - self.size, math.pi * 1.5, damage, 'rapid'))
        
        if self.power_level >= 2:
            bullets.append(PlayerBullet(self.x - 3, self.y - self.size, math.pi * 1.5, damage, 'rapid'))
            bullets.append(PlayerBullet(self.x + 3, self.y - self.size, math.pi * 1.5, damage, 'rapid'))
        
        if self.power_level >= 3:
            bullets.append(PlayerBullet(self.x - 6, self.y, math.pi * 1.5 - 0.05, damage, 'rapid'))
            bullets.append(PlayerBullet(self.x + 6, self.y, math.pi * 1.5 + 0.05, damage, 'rapid'))
        
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN * 0.3  # Very fast fire rate
        return bullets
    
    def take_damage(self, damage):
        """Take damage"""
        if self.invincible_time > 0:
            return False
        
        # Invincible ability grants damage immunity
        if self.ability_active and self.ability_type == 'invincible':
            return False
        
        if self.shield:
            self.shield = False
            # Reset combo on shield break
            self.combo = 0
            self.update_combo_multiplier()
            return False
        
        self.health -= damage
        self.damage_taken += damage
        
        # Reset combo on damage
        self.combo = 0
        self.update_combo_multiplier()
        
        # Check if dead
        if self.health <= 0:
            self.health = 0
            return True  # Dead
        else:
            self.invincible_time = PLAYER_INVINCIBILITY_TIME
            return False  # Damaged but alive
    
    def heal(self, amount):
        """Heal player"""
        self.health = min(self.max_health, self.health + amount)

    
    def add_power(self):
        """Increase power level"""
        self.power_level = min(4, self.power_level + 1)
    
    def add_damage_boost(self):
        """Increase damage multiplier"""
        self.damage_multiplier = min(3.0, self.damage_multiplier + 0.5)
    
    def add_shield(self):
        """Add shield"""
        self.shield = True
    
    def switch_style(self):
        """Switch to next weapon style"""
        styles = ['normal', 'burst', 'laser', 'spread', 'homing', 'rapid']
        current_index = styles.index(self.weapon_style)
        self.weapon_style = styles[(current_index + 1) % len(styles)]
        return self.weapon_style
    
    def switch_ultimate_type(self):
        """Switch to next ultimate type"""
        ultimate_types = ['laser_grid', 'clone', 'fullscreen_laser']
        current_index = ultimate_types.index(self.ultimate_type)
        self.ultimate_type = ultimate_types[(current_index + 1) % len(ultimate_types)]
        return self.ultimate_type
    
    def switch_ability_type(self, new_ability=None):
        """Switch ability type (via powerup pickup or cycle)"""
        if new_ability:
            self.ability_type = new_ability
        else:
            ability_types = ['berserker', 'glass_cannon', 'invincible']
            current_index = ability_types.index(self.ability_type)
            self.ability_type = ability_types[(current_index + 1) % len(ability_types)]
        return self.ability_type
    
    def activate_ability(self):
        """Activate current ability"""
        if self.ability_charge >= self.ability_max and not self.ability_active:
            self.ability_active = True
            self.ability_charge = 0
            self.glass_cannon_triggered = False  # Reset glass cannon trigger
            
            if self.ability_type == 'berserker':
                self.ability_duration = 5000  # 5 seconds
            elif self.ability_type == 'glass_cannon':
                self.ability_duration = 8000  # 8 seconds
                # Reduce health to 20 HP immediately
                self.health = 20
                self.glass_cannon_triggered = True
            elif self.ability_type == 'invincible':
                self.ability_duration = 10000  # 10 seconds (shield effect)
            
            return True
        return False
    
    def get_ability_damage_multiplier(self):
        """Get damage multiplier from ability"""
        if not self.ability_active:
            return 1.0
        
        if self.ability_type == 'berserker':
            # More damage at lower health
            health_ratio = self.health / self.max_health
            if health_ratio < 0.3:
                return 2.5
            elif health_ratio < 0.5:
                return 2.0
            else:
                return 1.5
        elif self.ability_type == 'glass_cannon':
            return 3.0
        elif self.ability_type == 'invincible':
            return 1.0
        
        return 1.0
    
    def check_tricks(self):
        """Check if player performed any tricks"""
        if self.trick_cooldown > 0 or len(self.position_history) < 20:
            return None
        
        # Check for border trace (touched all 4 sides recently)
        if all(self.border_touched.values()):
            self.border_touched = {'top': False, 'bottom': False, 'left': False, 'right': False}
            self.trick_cooldown = 5000  # 5 second cooldown
            return 'border_trace'
        
        # Check for loop-de-loop (circular motion)
        if len(self.position_history) >= 30:
            positions = [(p[0], p[1]) for p in self.position_history[-30:]]
            if self._detect_loop(positions):
                self.trick_cooldown = 3000
                return 'loop'
        
        # Check for helix (zigzag pattern)
        if len(self.position_history) >= 25:
            positions = [(p[0], p[1]) for p in self.position_history[-25:]]
            if self._detect_helix(positions):
                self.trick_cooldown = 3000
                return 'helix'
        
        # Check for spiral
        if len(self.position_history) >= 35:
            positions = [(p[0], p[1]) for p in self.position_history[-35:]]
            if self._detect_spiral(positions):
                self.trick_cooldown = 3000
                return 'spiral'
        
        # Check for wall dancer
        if len(self.position_history) >= 20:
            positions = [(p[0], p[1]) for p in self.position_history[-20:]]
            if self._detect_wall_dancer(positions):
                self.trick_cooldown = 3000
                return 'wall_dancer'
        
        # Check for counter-clockwise loop
        if len(self.position_history) >= 30:
            positions = [(p[0], p[1]) for p in self.position_history[-30:]]
            if self._detect_counter_loop(positions):
                self.trick_cooldown = 3000
                return 'counter_loop'
        
        return None
    
    def _detect_loop(self, positions):
        """Detect if positions form a loop"""
        if len(positions) < 20:
            return False
        
        # Calculate center
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        
        # Check if points are roughly circular around center
        distances = [((p[0] - cx)**2 + (p[1] - cy)**2)**0.5 for p in positions]
        avg_dist = sum(distances) / len(distances)
        
        # Must have reasonable radius
        if avg_dist < 30 or avg_dist > 150:
            return False
        
        # Check variance in distance (should be low for circle)
        variance = sum((d - avg_dist)**2 for d in distances) / len(distances)
        return variance < avg_dist * 0.3
    
    def _detect_helix(self, positions):
        """Detect zigzag/helix pattern"""
        if len(positions) < 20:
            return False
        
        # Count direction changes
        direction_changes = 0
        for i in range(2, len(positions)):
            dx1 = positions[i-1][0] - positions[i-2][0]
            dx2 = positions[i][0] - positions[i-1][0]
            
            # Direction change in x
            if (dx1 > 0 and dx2 < 0) or (dx1 < 0 and dx2 > 0):
                direction_changes += 1
        
        # Helix should have multiple direction changes
        return direction_changes >= 4
    
    def _detect_spiral(self, positions):
        """Detect spiral pattern (expanding or contracting circles)"""
        if len(positions) < 30:
            return False
        
        # Check if moving in expanding/contracting circles
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        
        # Calculate distances from center
        distances = [((p[0] - cx)**2 + (p[1] - cy)**2)**0.5 for p in positions]
        
        # Spiral should show increasing or decreasing distance trend
        if len(distances) >= 2:
            # Check first half vs second half
            first_half_avg = sum(distances[:len(distances)//2]) / (len(distances)//2)
            second_half_avg = sum(distances[len(distances)//2:]) / (len(distances) - len(distances)//2)
            
            # Spiral expands or contracts significantly
            ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
            return ratio > 1.3 or ratio < 0.7
        
        return False
    
    def _detect_wall_dancer(self, positions):
        """Detect touching left/right walls alternately"""
        if len(positions) < 15:
            return False
        
        wall_touches = {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        
        for pos in positions[-15:]:
            if pos[0] < 20:
                wall_touches['left'] += 1
            elif pos[0] > PLAYABLE_AREA_WIDTH - 20:
                wall_touches['right'] += 1
            if pos[1] < 50:
                wall_touches['top'] += 1
            elif pos[1] > PLAYABLE_AREA_HEIGHT - 20:
                wall_touches['bottom'] += 1
        
        # Wall dancer should alternate between walls
        left_right_touches = wall_touches['left'] + wall_touches['right']
        return left_right_touches >= 4  # At least 4 touches on left/right walls
    
    def _detect_counter_loop(self, positions):
        """Detect counter-clockwise circular motion"""
        if len(positions) < 25:
            return False
        
        # Calculate center
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        
        # Check if points form a circle
        distances = [((p[0] - cx)**2 + (p[1] - cy)**2)**0.5 for p in positions]
        avg_dist = sum(distances) / len(distances)
        
        if avg_dist < 30 or avg_dist > 150:
            return False
        
        # Check variance (should be low for circle)
        variance = sum((d - avg_dist)**2 for d in distances) / len(distances)
        if variance > avg_dist * 0.3:
            return False
        
        # Check for counter-clockwise motion using cross products
        ccw_count = 0
        for i in range(1, len(positions) - 1):
            p1 = positions[i-1]
            p2 = positions[i]
            p3 = positions[i+1]
            
            # Cross product tells us direction
            cross = (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])
            if cross > 0:  # Counter-clockwise
                ccw_count += 1
        
        # More than 50% counter-clockwise motion
        return ccw_count > len(positions) * 0.4
    
    def draw(self, screen):
        """Draw the player with sprites"""
        # Get sprite loader
        if sprites.sprite_loader is None:
            return
        
        loader = sprites.sprite_loader
        
        # Calculate health percentage for damage state
        health_percent = self.health / self.max_health
        health_state = max(0, min(3, int((1 - health_percent) * 4)))  # 0-3 states
        
        # Get appropriate ship sprite based on health
        ship_sprite = loader.get_player_sprite(health_percent)
        engine_sprite = loader.get_player_engine(self.is_moving)
        
        # Flashing effect when invincible
        if self.invincible_time > 0 and int(self.invincible_time / 100) % 2 == 0:
            alpha = 128
        else:
            alpha = 255
        
        if ship_sprite:
            # Use cached sprite if available and health state hasn't changed
            if health_state == self.last_health_state and 'ship' in self.sprite_cache and alpha == 255:
                scaled_ship = self.sprite_cache['ship']
            else:
                # Scale sprite to larger size (4x the original size)
                scaled_ship = pygame.transform.scale(ship_sprite, (int(self.size * 4), int(self.size * 4)))
                self.sprite_cache['ship'] = scaled_ship
                self.last_health_state = health_state
            
            # Apply alpha for invincibility flash
            if alpha < 255:
                scaled_ship = scaled_ship.copy()
                scaled_ship.set_alpha(alpha)
            
            # Draw ship
            ship_rect = scaled_ship.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(scaled_ship, ship_rect)
        else:
            # Fallback to geometric drawing if sprites not loaded
            pygame.draw.circle(screen, NEON_BLUE, (int(self.x), int(self.y)), self.size)
        

        
        # Draw shield with sprite if available
        if self.shield:
            shield_sprite = loader.get_shield_sprite('round')
            if shield_sprite:
                # Animate shield rotation
                time_offset = pygame.time.get_ticks() * 0.002
                rotated = pygame.transform.rotate(shield_sprite, time_offset * 50)
                scaled_shield = pygame.transform.scale(rotated, (int(self.size * 9), int(self.size * 9)))
                scaled_shield.set_alpha(180)
                shield_rect = scaled_shield.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(scaled_shield, shield_rect)
            else:
                # Fallback hexagonal shield
                shield_points = []
                time_offset = pygame.time.get_ticks() * 0.003
                for i in range(6):
                    angle = i * (math.pi / 3) - time_offset * 2
                    shield_points.append((
                        self.x + math.cos(angle) * self.size * 2.5,
                        self.y + math.sin(angle) * self.size * 2.5
                    ))
                pygame.draw.polygon(screen, (0, 255, 255, 80), shield_points)
                pygame.draw.polygon(screen, CYAN, shield_points, 3)
        
        # Draw invincibility shield for invincible ability
        if self.ability_active and self.ability_type == 'invincible':
            shield_sprite = loader.get_shield_sprite('invincibility')
            if shield_sprite:
                time_offset = pygame.time.get_ticks() * 0.001
                rotated = pygame.transform.rotate(shield_sprite, -time_offset * 30)
                scaled = pygame.transform.scale(rotated, (int(self.size * 9), int(self.size * 9)))
                scaled.set_alpha(200)
                rect = scaled.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(scaled, rect)
        
        # Draw berserker aura effect
        if self.ability_active and self.ability_type == 'berserker':
            time_offset = pygame.time.get_ticks() * 0.005
            aura_size = int(self.size * 4 + math.sin(time_offset) * self.size)
            aura_surface = pygame.Surface((aura_size * 2, aura_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surface, (255, 50, 0, 80), (aura_size, aura_size), aura_size)
            screen.blit(aura_surface, (int(self.x - aura_size), int(self.y - aura_size)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Draw glass cannon purple aura
        if self.ability_active and self.ability_type == 'glass_cannon':
            time_offset = pygame.time.get_ticks() * 0.004
            pulse = abs(math.sin(time_offset)) * 0.5 + 0.5
            aura_size = int(self.size * 3.5 * pulse)
            aura_surface = pygame.Surface((aura_size * 2, aura_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surface, (255, 100, 255, 100), (aura_size, aura_size), aura_size)
            screen.blit(aura_surface, (int(self.x - aura_size), int(self.y - aura_size)), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def get_hitbox(self):
        """Get hitbox for collision detection"""
        return pygame.Rect(
            self.x - self.hitbox_size,
            self.y - self.hitbox_size,
            self.hitbox_size * 2,
            self.hitbox_size * 2
        )
    
    def is_alive(self):
        """Check if player is alive"""
        return self.health > 0
    
    def clear_powerups(self):
        """Clear all powerups (called when boss spawns)"""
        self.damage_multiplier = 1.0
        self.shield = False
        self.speed = PLAYER_SPEED
        self.slow_speed = PLAYER_SLOW_SPEED
        self.weapon_style = 'normal'
        # Keep power level but reset to minimum
        self.power_level = max(1, self.power_level - 1)
    
    def increment_combo(self):
        """Increment combo on kill"""
        self.combo += 1
        self.update_combo_multiplier()
    
    def update_combo_multiplier(self):
        """Update multiplier based on combo count"""
        # Find which tier the combo is in
        for i in range(len(COMBO_THRESHOLDS) - 1, -1, -1):
            if self.combo >= COMBO_THRESHOLDS[i]:
                self.combo_multiplier = COMBO_MULTIPLIERS[i]
                break
    
    def get_effective_damage(self):
        """Get effective damage with all modifiers"""
        base_damage = PLAYER_BULLET_DAMAGE * self.damage_multiplier
        
        # Apply ability damage multiplier
        base_damage *= self.get_ability_damage_multiplier()
        
        return base_damage
