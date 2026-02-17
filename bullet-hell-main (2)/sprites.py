"""
Sprite loading and management system
"""
import pygame
import os
from config import *

class SpriteLoader:
    """Load and manage all game sprites"""
    
    def __init__(self):
        self.player_ship = {}
        self.player_engines = {}
        self.player_weapons = {}
        self.enemy_ships = {}
        self.icons = {}
        self.shields = {}
        
        self.load_all_sprites()
    
    def load_all_sprites(self):
        """Load all game sprites"""
        try:
            self.load_player_sprites()
            self.load_enemy_sprites()
            self.load_icons()
            self.load_weapon_sprites()
            self.load_shields()
        except Exception as e:
            print(f"Warning: Could not load sprites: {e}")
    
    def load_player_sprites(self):
        """Load player ship sprites - Pizza themed"""
        base_path = "ships/player"
        
        try:
            # Load pizza player sprite
            self.player_ship['full_health'] = pygame.image.load(
                os.path.join(base_path, "player.png")
            ).convert_alpha()
            # Use same sprite for all damage states since we have single sprite
            self.player_ship['slight_damage'] = self.player_ship['full_health']
            self.player_ship['damaged'] = self.player_ship['full_health']
            self.player_ship['very_damaged'] = self.player_ship['full_health']
            
            # Use same sprite for engines
            self.player_engines['idle'] = self.player_ship['full_health']
            self.player_engines['powering'] = self.player_ship['full_health']
            
        except Exception as e:
            print(f"Could not load player sprites: {e}")
    
    def load_enemy_sprites(self):
        """Load enemy ship sprites - Pizza themed"""
        base_path = "ships/enemy"
        
        enemy_types = [
            'Scout', 'Fighter', 'Frigate', 'Bomber', 
            'Support', 'Battlecruiser', 'Dreadnought', 'Torpedo Ship'
        ]
        
        try:
            # Load single pizza enemy sprite
            enemy_sprite = pygame.image.load(
                os.path.join(base_path, "enemy.png")
            ).convert_alpha()
            
            # Use same sprite for all enemy types
            for enemy_type in enemy_types:
                self.enemy_ships[enemy_type.lower().replace(' ', '_')] = enemy_sprite
        except Exception as e:
            print(f"Could not load enemy sprites: {e}")
    
    def load_icons(self):
        """Load UI icons"""
        icon_path = "icons/PNG"
        
        for i in range(1, 21):
            try:
                self.icons[i] = pygame.image.load(
                    os.path.join(icon_path, f"{i}.png")
                ).convert_alpha()
            except Exception as e:
                print(f"Could not load icon {i}: {e}")
    
    def load_weapon_sprites(self):
        """Load weapon projectile sprites"""
        weapon_path = "ships/player/Main ship weapons/PNGs"
        
        weapon_files = {
            'auto_cannon': 'Main ship weapon - Projectile - Auto cannon bullet.png',
            'big_gun': 'Main ship weapon - Projectile - Big Space Gun.png',
            'rocket': 'Main ship weapon - Projectile - Rocket.png',
            'zapper': 'Main ship weapon - Projectile - Zapper.png'
        }
        
        for key, filename in weapon_files.items():
            try:
                self.player_weapons[key] = pygame.image.load(
                    os.path.join(weapon_path, filename)
                ).convert_alpha()
            except Exception as e:
                print(f"Could not load weapon {key}: {e}")
    
    def load_shields(self):
        """Load shield sprites"""
        shield_path = "ships/player/Main Ship/Main Ship - Shields/PNGs"
        
        try:
            self.shields['round'] = pygame.image.load(
                os.path.join(shield_path, "Main Ship - Shields - Round Shield.png")
            ).convert_alpha()
            self.shields['invincibility'] = pygame.image.load(
                os.path.join(shield_path, "Main Ship - Shields - Invincibility Shield.png")
            ).convert_alpha()
        except Exception as e:
            print(f"Could not load shields: {e}")
    
    def get_player_sprite(self, health_percent):
        """Get player sprite based on health percentage"""
        if health_percent > 0.75:
            return self.player_ship.get('full_health')
        elif health_percent > 0.5:
            return self.player_ship.get('slight_damage')
        elif health_percent > 0.25:
            return self.player_ship.get('damaged')
        else:
            return self.player_ship.get('very_damaged')
    
    def get_player_engine(self, is_moving):
        """Get player engine sprite"""
        if is_moving:
            return self.player_engines.get('powering')
        return self.player_engines.get('idle')
    
    def get_enemy_sprite(self, enemy_type):
        """Get enemy sprite by type"""
        return self.enemy_ships.get(enemy_type, None)
    
    def get_icon(self, icon_number):
        """Get icon by number"""
        return self.icons.get(icon_number, None)
    
    def get_weapon_sprite(self, weapon_type):
        """Get weapon projectile sprite"""
        return self.player_weapons.get(weapon_type, None)
    
    def get_shield_sprite(self, shield_type='round'):
        """Get shield sprite"""
        return self.shields.get(shield_type, None)

# Global sprite loader instance
sprite_loader = None

def init_sprites():
    """Initialize the global sprite loader"""
    global sprite_loader
    sprite_loader = SpriteLoader()
    return sprite_loader
