"""
Utility functions for the bullet hell game
"""
import random
import math


class SeededRandom:
    """Handles deterministic randomization using seeds"""
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.rng = random.Random(self.seed)
    
    def set_seed(self, seed):
        """Set a new seed"""
        self.seed = seed
        self.rng = random.Random(self.seed)
    
    def get_seed(self):
        """Get current seed"""
        return self.seed
    
    def randint(self, a, b):
        """Generate random integer"""
        return self.rng.randint(a, b)
    
    def random(self):
        """Generate random float between 0 and 1"""
        return self.rng.random()
    
    def choice(self, seq):
        """Choose random element from sequence"""
        return self.rng.choice(seq)
    
    def uniform(self, a, b):
        """Generate random float between a and b"""
        return self.rng.uniform(a, b)
    
    def choices(self, population, weights=None, k=1):
        """Choose k elements from population with optional weights"""
        return self.rng.choices(population, weights=weights, k=k)


def distance(pos1, pos2):
    """Calculate distance between two positions"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)


def angle_to(pos1, pos2):
    """Calculate angle from pos1 to pos2"""
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.atan2(dy, dx)


def move_towards(pos, target, speed):
    """Move position towards target at given speed"""
    angle = angle_to(pos, target)
    dx = math.cos(angle) * speed
    dy = math.sin(angle) * speed
    return (pos[0] + dx, pos[1] + dy)


def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))


def lerp(a, b, t):
    """Linear interpolation between a and b"""
    return a + (b - a) * t


def normalize_vector(x, y):
    """Normalize a 2D vector"""
    length = math.sqrt(x*x + y*y)
    if length == 0:
        return 0, 0
    return x/length, y/length
