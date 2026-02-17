"""
Game configuration and constants for the bullet hell game
"""

# Screen settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 1500
FPS = 60

# Colors - Futuristic Sci-Fi Palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 40, 40)
GREEN = (0, 255, 150)
BLUE = (0, 150, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 105, 180)
NEON_BLUE = (0, 200, 255)
NEON_GREEN = (0, 255, 100)
NEON_PINK = (255, 0, 200)
NEON_PURPLE = (150, 0, 255)
ENERGY_BLUE = (100, 200, 255)

# Player settings
PLAYER_SPEED = 5
PLAYER_SLOW_SPEED = 2
PLAYER_SIZE = 18
PLAYER_HITBOX_SIZE = 6
PLAYER_MAX_HEALTH = 50  # Reduced from 100 to make easier to kill
PLAYER_SHOOT_COOLDOWN = 100  # milliseconds
PLAYER_BULLET_DAMAGE = 10
PLAYER_MAX_LIVES = 3
PLAYER_STARTING_LIVES = 3
PLAYER_INVINCIBILITY_TIME = 500  # Reduced from 1000ms

# Combo system
COMBO_MULTIPLIERS = [1.0, 1.5, 2.0, 3.0, 5.0]  # Multipliers at combo tiers
COMBO_THRESHOLDS = [0, 5, 15, 30, 50]  # Kills needed for each tier

# Grazing system
GRAZE_DISTANCE = 25  # Distance from player center to count as graze
GRAZE_SCORE = 5  # Points per graze
GRAZE_COOLDOWN = 150  # Milliseconds between grazes on same bullet

# Enemy settings
ENEMY_BASE_SPEED = 2
ENEMY_BASE_SIZE = 30
ENEMY_MIN_SIZE = 12  # Minimum size as more enemies spawn
ENEMY_SIZE = 30
ENEMY_HEALTH = 50
ENEMIES_PER_WAVE = 8  # Base number for stage 1 (reduced from 25 for easier start)
MAX_ENEMIES_ON_SCREEN = 25  # Maximum concurrent enemies (reduced from 50)

# Boss settings
BOSS_SIZE = 80
BOSS_BASE_HEALTH = 3000  # Balanced for stage 1 (reduced from 9000)
BOSS_HEALTH_SCALING = 1.5  # Gradual multiplier per stage

# Bullet settings
BULLET_SPEED = 5
BULLET_SIZE = 8
PLAYER_BULLET_SPEED = 10
PLAYER_BULLET_SIZE = 6

# Power-up settings
POWERUP_SIZE = 20
POWERUP_SPAWN_CHANCE = 0.65  # High chance to drop many powerups (65%)
POWERUP_TYPES = ['health', 'damage', 'speed', 'shield', 'style']
BOSS_POWERUP_DROP_INTERVAL = 8000  # Boss drops powerup every 8 seconds

# Weapon styles
WEAPON_STYLES = ['normal', 'burst', 'laser', 'spread', 'homing', 'rapid']

# Difficulty scaling
DIFFICULTY_SCALING = {
    'enemy_speed': 1.25,       # 25% increase per stage (exponential: 1.0->1.25->1.56->1.95->2.44)
    'enemy_health': 1.25,      # 25% increase per stage
    'bullet_speed': 1.25,      # 25% increase per stage
    'spawn_rate': 0.80,        # 20% faster spawning per stage
    'boss_health': 1.30,       # 30% increase per stage (bosses scale faster)
    'wave_scaling': 1.25,      # 25% increase per wave
    'enemy_count': 1.35        # 35% more enemies per stage
}

# Boss difficulty multipliers
BOSS_DAMAGE_MULTIPLIER = 1.5  # Bosses deal 50% more damage
BOSS_ATTACK_SPEED_MULTIPLIER = 1.3  # Bosses attack 30% faster

# Stage settings
WAVES_PER_STAGE = 5
WAVE_DURATION = 12000  # milliseconds (12 seconds per wave = ~60 seconds per stage)

# UI settings
UI_HEIGHT = 100
GAME_AREA_HEIGHT = SCREEN_HEIGHT - UI_HEIGHT

# Panel layout
PLAYABLE_AREA_TOP = 0  # Top border of play area
PLAYABLE_AREA_LEFT = 0  # Left border of play area
SIDE_PANEL_START_X = 915  # Where right panel begins (610 * 1.5)
BOTTOM_PANEL_START_Y = 1320  # Where bottom panel begins (880 * 1.5)
PLAYABLE_AREA_WIDTH = SIDE_PANEL_START_X  # Playable width (stops before right panel)
PLAYABLE_AREA_HEIGHT = BOTTOM_PANEL_START_Y  # Playable height (stops before bottom panel)

# Boss pool size
NUM_BOSSES = 10

# Score multipliers
SCORE_ENEMY_KILL = 100
SCORE_BOSS_KILL = 500
SCORE_STAGE_COMPLETE = 10000
SCORE_NO_DAMAGE_BONUS = 2.0
SCORE_POWERUP_COLLECT = 50
SCORE_TRICK = 200
