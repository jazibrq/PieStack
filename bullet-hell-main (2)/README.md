# Bullet Hell - Touhou Inspired

A challenging bullet hell game inspired by Touhou Project, featuring infinite stages, randomized bosses, and seed-based deterministic gameplay.

## Features

### Core Gameplay
- **Infinite Stages**: Progressively harder stages that scale in difficulty
- **Boss Battles**: End each stage with an epic boss fight
- **10 Unique Bosses**: Each with distinct attack patterns and multiple phases
- **Seed-Based Randomization**: Use seeds to compete with others on the exact same game
- **Skill-Based Competition**: Same seed = same enemy spawns and bosses

### Player Mechanics
- **Movement**: Smooth 8-directional movement
- **Shooting**: Auto-fire with power-up system
- **Slow Mode**: Hold Shift to slow down and see your hitbox
- **Power Levels**: Collect power-ups to increase shot strength (up to Level 4)
- **Health System**: Take hits and recover with health power-ups
- **Shield**: Temporary protection from one hit

### Bullet Patterns
- Circle patterns
- Spiral patterns
- Aimed spreads
- Wave patterns
- Homing bullets
- Cross patterns
- Random bursts
- And more complex combinations!

### Enemy Types
1. **Basic Enemy**: Simple aimed shots
2. **Circle Enemy**: 360° bullet circles
3. **Spiral Enemy**: Rotating spiral patterns
4. **Homing Enemy**: Tracking bullets
5. **Wave Enemy**: Sinusoidal wave patterns

### Boss Roster
1. **Crimson Demon**: Circle and spiral master
2. **Void Serpent**: Wave patterns and serpentine movement
3. **Celestial Guardian**: Homing bullets and random bursts
4. **Infernal Titan**: Aggressive double spirals
5. **Frozen Empress**: Dense, slow bullet walls
6. **Thunder Lord**: Fast, erratic patterns
7. **Shadow Phantom**: Teleporting surprise attacks
8. **Crystal Archon**: Geometric patterns
9. **Nightmare Beast**: Chaotic and unpredictable
10. **Eternal Overlord**: The ultimate challenge with 4 phases

### Power-Up System
- **Health**: Restore 30 HP
- **Damage**: Increase bullet damage by 50%
- **Power**: Upgrade shot pattern (up to 4 levels)
- **Shield**: Block one hit

### Difficulty Scaling
As you progress through stages:
- Enemy speed increases by 5% per stage
- Enemy health increases by 10% per stage
- Bullet speed increases by 3% per stage
- Enemy spawn rate increases by 5% per stage
- Boss health increases by 50% per stage

### Scoring System
- Enemy kill: 100 × Stage Number
- Boss kill: 5,000 × Stage Number
- Stage complete: 10,000 points
- Track your high score!

## Installation

### Requirements
- Python 3.8 or higher
- pygame
- numpy (optional, for sound effects)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install pygame numpy
```

**Note**: NumPy is optional. Without it, the game will run but sound effects will be disabled.

3. **Run the game**:
```bash
python main.py
```

## Controls

### Main Menu
- **ENTER**: Start game
- **S**: Change seed
- **ESC**: Quit game

### Gameplay
- **Arrow Keys** or **WASD**: Move
- **Z** or **SPACE**: Shoot
- **SHIFT**: Slow movement (shows hitbox)
- **P**: Pause game
- **ESC**: Return to menu

### Game Over
- **ENTER**: Return to menu
- **ESC**: Quit game

## Gameplay Tips

1. **Use Slow Mode**: Hold Shift to see your hitbox and navigate through dense bullet patterns
2. **Graze Bullets**: Get close to bullets for style points (risk vs reward)
3. **Power Up Early**: Collect power-ups to increase your firepower
4. **Learn Boss Patterns**: Each boss has predictable attack patterns - learn them!
5. **Use the Seed**: Practice with the same seed to master specific level layouts
6. **Stay Mobile**: Keep moving to avoid getting cornered
7. **Focus on Survival**: Your score means nothing if you're dead
8. **Watch Phase Transitions**: Bosses become more aggressive in later phases

## Seed System

The game uses a deterministic seed-based randomization system. This means:

- **Same Seed = Same Game**: Players using the same seed will face identical enemies, bosses, and bullet patterns
- **Fair Competition**: Compete with friends using the same seed - only skill matters
- **Practice Mode**: Use a specific seed to practice difficult sections
- **Infinite Variety**: Try different seeds for different experiences

### Using Seeds

1. From the main menu, press **S**
2. Enter your desired seed (any number)
3. Press **ENTER** to confirm
4. Start the game

Share your seed with friends to compete!

## Game Structure

### Stages
- Each stage consists of 5 waves of enemies
- After wave 5, a boss appears
- Defeating the boss starts the next stage
- Stages continue infinitely with increasing difficulty

### Waves
- 30 seconds per wave
- Up to 10 enemies per wave
- Enemy types randomized based on stage difficulty
- Spawn rate increases with stage number

### Boss Fights
- Each boss has 3-4 phases
- Boss health increases 50% per stage
- Unique attack patterns for each boss
- Phase transitions trigger visual effects

## File Structure

```
bullet-hell/
├── main.py          # Main game loop and game state management
├── config.py        # Game configuration and constants
├── utils.py         # Utility functions and seeded random
├── player.py        # Player class and mechanics
├── bullet.py        # Bullet classes and pattern generators
├── enemy.py         # Enemy classes and behaviors
├── boss.py          # Boss classes with unique patterns
├── powerup.py       # Power-up system
├── ui.py            # UI and visual effects
├── audio.py         # Audio system (requires numpy)
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Technical Details

### Performance
- Runs at 60 FPS
- Optimized bullet culling (off-screen bullets are removed)
- Efficient collision detection
- Particle system for visual effects

### Customization
Edit `config.py` to customize:
- Screen size
- Player speed and health
- Enemy spawn rates
- Difficulty scaling factors
- Score multipliers
- And much more!

## Known Limitations

1. **Audio**: Sound effects require NumPy. Without it, the game runs silently.
2. **Music**: Background music is not included. You can add your own by placing music files in the directory.
3. **Save System**: High scores are not persisted between sessions.
4. **Leaderboards**: No online leaderboard system (yet!).

## Future Enhancements

Potential features for future versions:
- [ ] Save/load high scores
- [ ] Online leaderboards
- [ ] Character selection with unique abilities
- [ ] Spell cards (screen-clearing bombs)
- [ ] Replay system
- [ ] Practice mode for specific bosses
- [ ] Additional boss mechanics
- [ ] Visual themes
- [ ] Custom bullet skins

## Credits

Inspired by:
- **Touhou Project** by ZUN
- Classic bullet hell shooters

Created as a demonstration of:
- Game development with Pygame
- Bullet pattern design
- Procedural content generation
- Seed-based randomization
- Object-oriented game architecture

## License

This project is provided as-is for educational and entertainment purposes.

## Troubleshooting

### Game won't start
- Make sure Python 3.8+ is installed
- Install pygame: `pip install pygame`
- Check that all .py files are in the same directory

### No sound
- Install numpy: `pip install numpy`
- Update pygame: `pip install --upgrade pygame`

### Game is too hard/easy
- Edit `config.py` to adjust difficulty settings
- Try different seeds for varied difficulty

### Performance issues
- Lower the FPS in `config.py`
- Reduce the number of particles in visual effects
- Close other applications

## Contributing

Feel free to fork, modify, and improve this game! Some ideas:
- Add new boss patterns
- Create new enemy types
- Improve visual effects
- Add music and better sound effects
- Implement new power-ups
- Create boss dialogue

## Have Fun!

Enjoy the bullet hell madness! Remember: dodge, weave, and survive!

Share your high scores and seeds with friends!

---

**Good luck, and may your dodging skills be legendary!**
