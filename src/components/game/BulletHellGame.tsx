import { useEffect, useRef, useCallback, useState } from 'react';

/* ============================================================
   PieStack Bullet-Hell — HTML5 Canvas Game
   Ported from the Python/Pygame original.
   Core features: player, enemies, boss, bullets, powerups,
   stages, combos, scoring, game-over → returns to lobby.
   ============================================================ */

// ─── Config ─────────────────────────────────────────────────
const GAME_W = 600;
const GAME_H = 800;
const FPS = 60;

const PLAYER_SPEED = 5;
const PLAYER_SLOW_SPEED = 2;
const PLAYER_SIZE = 14;
const PLAYER_HITBOX = 5;
const PLAYER_MAX_HP = 50;
const PLAYER_SHOOT_CD = 100;
const PLAYER_BULLET_DMG = 10;
const PLAYER_BULLET_SPEED = 10;
const PLAYER_INVULN_MS = 500;

const ENEMY_BASE_SPEED = 1.8;
const ENEMY_SIZE = 22;
const ENEMY_HP = 50;
const ENEMIES_PER_WAVE = 6;
const MAX_ENEMIES = 20;

const BOSS_SIZE = 55;
const BOSS_BASE_HP = 2500;

const BULLET_SPEED = 4;
const BULLET_SIZE = 5;

const WAVES_PER_STAGE = 5;
const WAVE_DURATION = 12000;

const POWERUP_SIZE = 14;
const POWERUP_CHANCE = 0.3;

const COMBO_THRESHOLDS = [0, 5, 15, 30, 50];
const COMBO_MULTIPLIERS = [1.0, 1.5, 2.0, 3.0, 5.0];

// Scoring
const SCORE_ENEMY = 100;
const SCORE_BOSS = 5000;
const SCORE_STAGE = 2000;
const SCORE_POWERUP = 50;

// Colors
const COL = {
  bg: '#050510',
  player: '#00c8ff',
  playerGlow: 'rgba(0,200,255,0.3)',
  enemy: '#ff2828',
  enemyCircle: '#ff6600',
  enemySpiral: '#b400ff',
  boss: '#ff00c8',
  bossGlow: 'rgba(255,0,200,0.2)',
  bullet: '#ff4444',
  playerBullet: '#00ffaa',
  powerup: '#00ff64',
  shield: '#00ffff',
  text: '#ffffff',
  hud: 'rgba(0,0,0,0.6)',
  combo: '#ffff00',
  cyan: '#00ffff',
  pink: '#ff00c8',
};

// ─── Types ──────────────────────────────────────────────────
interface Vec2 { x: number; y: number; }
interface Bullet extends Vec2 { angle: number; speed: number; size: number; damage: number; isPlayer: boolean; homing?: boolean; }
interface Enemy extends Vec2 { hp: number; maxHp: number; size: number; speed: number; color: string; shootTimer: number; shootCD: number; type: string; moveAngle: number; moveTimer: number; }
interface Boss extends Vec2 { hp: number; maxHp: number; size: number; color: string; name: string; phase: number; shootTimer: number; moveTimer: number; targetX: number; targetY: number; introTimer: number; }
interface Powerup extends Vec2 { type: string; timer: number; }
interface Particle extends Vec2 { vx: number; vy: number; life: number; maxLife: number; color: string; size: number; }
interface ScorePopup extends Vec2 { text: string; color: string; life: number; }

// ─── Utilities ──────────────────────────────────────────────
function rand(min: number, max: number) { return Math.random() * (max - min) + min; }
function randInt(min: number, max: number) { return Math.floor(rand(min, max + 1)); }
function dist(a: Vec2, b: Vec2) { return Math.hypot(a.x - b.x, a.y - b.y); }
function angleTo(a: Vec2, b: Vec2) { return Math.atan2(b.y - a.y, b.x - a.x); }
function clamp(v: number, lo: number, hi: number) { return Math.max(lo, Math.min(hi, v)); }

// ─── Game State ─────────────────────────────────────────────
interface GameState {
  status: 'playing' | 'game_over';
  player: {
    x: number; y: number; hp: number; maxHp: number;
    shootCD: number; invuln: number; shield: boolean;
    combo: number; comboMult: number; powerLevel: number;
    damageMult: number;
  };
  enemies: Enemy[];
  boss: Boss | null;
  playerBullets: Bullet[];
  enemyBullets: Bullet[];
  powerups: Powerup[];
  particles: Particle[];
  scorePopups: ScorePopup[];
  score: number;
  stage: number;
  wave: number;
  kills: number;
  waveTimer: number;
  spawnTimer: number;
  spawnRate: number;
  screenShake: number;
  shakeIntensity: number;
  message: string;
  messageTimer: number;
  stageIntroTimer: number;
}

function createInitialState(): GameState {
  return {
    status: 'playing',
    player: {
      x: GAME_W / 2, y: GAME_H - 80, hp: PLAYER_MAX_HP, maxHp: PLAYER_MAX_HP,
      shootCD: 0, invuln: 0, shield: false,
      combo: 0, comboMult: 1.0, powerLevel: 1, damageMult: 1.0,
    },
    enemies: [],
    boss: null,
    playerBullets: [],
    enemyBullets: [],
    powerups: [],
    particles: [],
    scorePopups: [],
    score: 0,
    stage: 1,
    wave: 1,
    kills: 0,
    waveTimer: 0,
    spawnTimer: 0,
    spawnRate: 1500,
    screenShake: 0,
    shakeIntensity: 0,
    message: 'STAGE 1',
    messageTimer: 2000,
    stageIntroTimer: 2000,
  };
}

// ─── Enemy Factory ──────────────────────────────────────────
function spawnEnemy(stage: number, wave: number): Enemy {
  const types = ['basic', 'circle', 'spiral'];
  const type = types[randInt(0, Math.min(types.length - 1, stage))];
  const speedMult = Math.pow(1.2, stage - 1);
  const hpMult = Math.pow(1.2, stage - 1);

  return {
    x: rand(40, GAME_W - 40),
    y: -30,
    hp: Math.floor(ENEMY_HP * hpMult),
    maxHp: Math.floor(ENEMY_HP * hpMult),
    size: ENEMY_SIZE,
    speed: ENEMY_BASE_SPEED * speedMult * (type === 'circle' ? 0.8 : 1),
    color: type === 'basic' ? COL.enemy : type === 'circle' ? COL.enemyCircle : COL.enemySpiral,
    shootTimer: rand(500, 2000),
    shootCD: type === 'spiral' ? 400 : 1200,
    type,
    moveAngle: rand(0, Math.PI * 2),
    moveTimer: 0,
  };
}

// ─── Boss Factory ───────────────────────────────────────────
const BOSS_NAMES = [
  'Margherita Menace', 'Pepperoni Punisher', 'Four Cheese Fury',
  'Calzone Crusher', 'Deep Dish Destroyer', 'Supreme Slayer',
];

function createBoss(stage: number): Boss {
  const hpMult = Math.pow(1.4, stage - 1);
  return {
    x: GAME_W / 2, y: -80,
    hp: Math.floor(BOSS_BASE_HP * hpMult),
    maxHp: Math.floor(BOSS_BASE_HP * hpMult),
    size: BOSS_SIZE + stage * 4,
    color: COL.boss,
    name: BOSS_NAMES[(stage - 1) % BOSS_NAMES.length],
    phase: 0,
    shootTimer: 0,
    moveTimer: 0,
    targetX: GAME_W / 2,
    targetY: 120,
    introTimer: 2000,
  };
}

// ─── Particles ──────────────────────────────────────────────
function addExplosion(particles: Particle[], x: number, y: number, color: string, count: number) {
  for (let i = 0; i < count; i++) {
    const angle = rand(0, Math.PI * 2);
    const speed = rand(1, 5);
    particles.push({
      x, y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: rand(300, 800),
      maxLife: 800,
      color,
      size: rand(1.5, 4),
    });
  }
}

// ─── Main Game Component ────────────────────────────────────
interface BulletHellGameProps {
  onGameOver: (score: number, stage: number, kills: number) => void;
  onExit: () => void;
}

export const BulletHellGame = ({ onGameOver, onExit }: BulletHellGameProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<GameState>(createInitialState());
  const keysRef = useRef<Set<string>>(new Set());
  const animRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const [gameOver, setGameOver] = useState(false);
  const gameOverCalledRef = useRef(false);

  // ─── Input ──────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault();
      keysRef.current.add(e.code);
      if (e.code === 'Escape') onExit();
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      keysRef.current.delete(e.code);
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [onExit]);

  // ─── Update ─────────────────────────────────────────
  const update = useCallback((dt: number) => {
    const s = stateRef.current;
    if (s.status !== 'playing') return;
    const keys = keysRef.current;
    const p = s.player;

    // Stage intro timer
    if (s.stageIntroTimer > 0) {
      s.stageIntroTimer -= dt;
      return; // Freeze during intro
    }

    // Player movement
    let speed = keys.has('ShiftLeft') || keys.has('ShiftRight') ? PLAYER_SLOW_SPEED : PLAYER_SPEED;
    let dx = 0, dy = 0;
    if (keys.has('ArrowLeft') || keys.has('KeyA')) dx -= 1;
    if (keys.has('ArrowRight') || keys.has('KeyD')) dx += 1;
    if (keys.has('ArrowUp') || keys.has('KeyW')) dy -= 1;
    if (keys.has('ArrowDown') || keys.has('KeyS')) dy += 1;
    if (dx && dy) { dx *= 0.707; dy *= 0.707; }
    p.x = clamp(p.x + dx * speed, PLAYER_SIZE, GAME_W - PLAYER_SIZE);
    p.y = clamp(p.y + dy * speed, PLAYER_SIZE, GAME_H - PLAYER_SIZE);

    // Invulnerability
    if (p.invuln > 0) p.invuln -= dt;

    // Shooting
    p.shootCD -= dt;
    if ((keys.has('KeyZ') || keys.has('Space')) && p.shootCD <= 0) {
      p.shootCD = PLAYER_SHOOT_CD;
      const dmg = PLAYER_BULLET_DMG * p.damageMult * (p.powerLevel >= 2 ? 1.2 : 1);
      s.playerBullets.push({ x: p.x, y: p.y - PLAYER_SIZE, angle: -Math.PI / 2, speed: PLAYER_BULLET_SPEED, size: 4, damage: dmg, isPlayer: true });
      if (p.powerLevel >= 2) {
        s.playerBullets.push({ x: p.x - 8, y: p.y - PLAYER_SIZE + 4, angle: -Math.PI / 2 - 0.08, speed: PLAYER_BULLET_SPEED, size: 3, damage: dmg * 0.7, isPlayer: true });
        s.playerBullets.push({ x: p.x + 8, y: p.y - PLAYER_SIZE + 4, angle: -Math.PI / 2 + 0.08, speed: PLAYER_BULLET_SPEED, size: 3, damage: dmg * 0.7, isPlayer: true });
      }
      if (p.powerLevel >= 3) {
        s.playerBullets.push({ x: p.x - 14, y: p.y, angle: -Math.PI / 2 - 0.18, speed: PLAYER_BULLET_SPEED * 0.9, size: 3, damage: dmg * 0.5, isPlayer: true });
        s.playerBullets.push({ x: p.x + 14, y: p.y, angle: -Math.PI / 2 + 0.18, speed: PLAYER_BULLET_SPEED * 0.9, size: 3, damage: dmg * 0.5, isPlayer: true });
      }
    }

    // Update player bullets
    s.playerBullets = s.playerBullets.filter(b => {
      b.x += Math.cos(b.angle) * b.speed;
      b.y += Math.sin(b.angle) * b.speed;
      return b.y > -20 && b.y < GAME_H + 20 && b.x > -20 && b.x < GAME_W + 20;
    });

    // Update enemy bullets
    s.enemyBullets = s.enemyBullets.filter(b => {
      b.x += Math.cos(b.angle) * b.speed;
      b.y += Math.sin(b.angle) * b.speed;
      return b.y > -20 && b.y < GAME_H + 20 && b.x > -20 && b.x < GAME_W + 20;
    });

    // ─── Boss Logic ───────────────────────────────────
    if (s.boss) {
      const boss = s.boss;
      if (boss.introTimer > 0) {
        boss.introTimer -= dt;
        boss.y += (boss.targetY - boss.y) * 0.03;
        return;
      }

      // Boss movement
      boss.moveTimer += dt;
      if (boss.moveTimer > 3000) {
        boss.moveTimer = 0;
        boss.targetX = rand(boss.size + 30, GAME_W - boss.size - 30);
        boss.targetY = rand(60, 200);
      }
      boss.x += (boss.targetX - boss.x) * 0.02;
      boss.y += (boss.targetY - boss.y) * 0.02;

      // Boss shooting
      boss.shootTimer += dt;
      const bossPhase = 1 - boss.hp / boss.maxHp;
      const shootInterval = Math.max(200, 800 - bossPhase * 400);

      if (boss.shootTimer >= shootInterval) {
        boss.shootTimer = 0;
        const bSpd = BULLET_SPEED * (1 + bossPhase * 0.5) * Math.pow(1.15, s.stage - 1);

        // Pattern based on phase
        if (bossPhase < 0.3) {
          // Aimed shots
          const a = angleTo(boss, p);
          for (let i = -1; i <= 1; i++) {
            s.enemyBullets.push({ x: boss.x, y: boss.y + boss.size / 2, angle: a + i * 0.15, speed: bSpd, size: BULLET_SIZE, damage: 15, isPlayer: false });
          }
        } else if (bossPhase < 0.6) {
          // Ring + aimed
          const count = 12 + s.stage * 2;
          for (let i = 0; i < count; i++) {
            const a = (i / count) * Math.PI * 2 + boss.moveTimer * 0.001;
            s.enemyBullets.push({ x: boss.x, y: boss.y, angle: a, speed: bSpd * 0.8, size: BULLET_SIZE, damage: 12, isPlayer: false });
          }
        } else {
          // Spiral + aimed
          const a = angleTo(boss, p);
          s.enemyBullets.push({ x: boss.x, y: boss.y, angle: a, speed: bSpd * 1.2, size: BULLET_SIZE + 2, damage: 20, isPlayer: false });
          const spiralCount = 8 + s.stage;
          for (let i = 0; i < spiralCount; i++) {
            const sa = (i / spiralCount) * Math.PI * 2 + performance.now() * 0.002;
            s.enemyBullets.push({ x: boss.x, y: boss.y, angle: sa, speed: bSpd * 0.7, size: BULLET_SIZE, damage: 10, isPlayer: false });
          }
        }
      }

      // Boss-bullet collision
      for (let i = s.playerBullets.length - 1; i >= 0; i--) {
        const b = s.playerBullets[i];
        if (dist(b, boss) < boss.size + b.size) {
          boss.hp -= b.damage;
          addExplosion(s.particles, b.x, b.y, COL.pink, 3);
          s.playerBullets.splice(i, 1);
          if (boss.hp <= 0) {
            // Boss defeated
            addExplosion(s.particles, boss.x, boss.y, COL.boss, 50);
            addExplosion(s.particles, boss.x, boss.y, '#ffffff', 40);
            s.screenShake = 25; s.shakeIntensity = 20;
            const bossScore = SCORE_BOSS * s.stage;
            s.score += bossScore;
            s.scorePopups.push({ x: boss.x, y: boss.y, text: `+${bossScore}`, color: COL.combo, life: 1500 });
            // Drop powerups
            for (let j = 0; j < 3; j++) {
              s.powerups.push({ x: boss.x + (j - 1) * 30, y: boss.y, type: ['health', 'damage', 'power'][j], timer: 0 });
            }
            s.boss = null;
            // Next stage
            s.stage++;
            s.wave = 1;
            s.waveTimer = 0;
            s.spawnTimer = 0;
            s.spawnRate = Math.max(400, Math.floor(1500 * Math.pow(0.85, s.stage - 1)));
            s.enemyBullets = [];
            s.enemies = [];
            s.score += SCORE_STAGE;
            s.message = `STAGE ${s.stage}`;
            s.messageTimer = 2500;
            s.stageIntroTimer = 2000;
            break;
          }
        }
      }
    } else {
      // ─── Wave / Enemy Logic ─────────────────────────
      s.waveTimer += dt;
      s.spawnTimer += dt;

      const stageScale = Math.pow(1.3, s.stage - 1);
      const maxE = Math.min(MAX_ENEMIES, Math.floor(ENEMIES_PER_WAVE * stageScale) + (s.wave - 1) * 2);

      if (s.spawnTimer >= s.spawnRate && s.enemies.length < maxE) {
        s.enemies.push(spawnEnemy(s.stage, s.wave));
        s.spawnTimer = 0;
      }

      // Update enemies
      for (let i = s.enemies.length - 1; i >= 0; i--) {
        const e = s.enemies[i];
        e.moveTimer += dt;

        // Movement based on type
        if (e.type === 'circle') {
          e.moveAngle += 0.02;
          e.x += Math.cos(e.moveAngle) * e.speed;
          e.y += e.speed * 0.5;
        } else if (e.type === 'spiral') {
          e.moveAngle += 0.03;
          e.x += Math.cos(e.moveAngle) * e.speed * 1.5;
          e.y += e.speed * 0.4;
        } else {
          e.y += e.speed;
          e.x += Math.sin(e.moveTimer * 0.002) * 0.8;
        }

        // Keep on screen
        e.x = clamp(e.x, e.size, GAME_W - e.size);

        // Remove if off bottom
        if (e.y > GAME_H + 40) { s.enemies.splice(i, 1); continue; }

        // Enemy shooting
        e.shootTimer -= dt;
        if (e.shootTimer <= 0 && e.y > 0) {
          e.shootTimer = e.shootCD;
          const eBSpd = BULLET_SPEED * Math.pow(1.15, s.stage - 1);
          if (e.type === 'spiral') {
            for (let j = 0; j < 4; j++) {
              const a = (j / 4) * Math.PI * 2 + e.moveAngle;
              s.enemyBullets.push({ x: e.x, y: e.y, angle: a, speed: eBSpd * 0.8, size: BULLET_SIZE, damage: 8, isPlayer: false });
            }
          } else {
            const a = angleTo(e, p);
            s.enemyBullets.push({ x: e.x, y: e.y + e.size / 2, angle: a, speed: eBSpd, size: BULLET_SIZE, damage: 10, isPlayer: false });
          }
        }

        // Player bullet → enemy collision
        for (let j = s.playerBullets.length - 1; j >= 0; j--) {
          const b = s.playerBullets[j];
          if (dist(b, e) < e.size + b.size) {
            e.hp -= b.damage;
            addExplosion(s.particles, b.x, b.y, e.color, 3);
            s.playerBullets.splice(j, 1);
            if (e.hp <= 0) {
              addExplosion(s.particles, e.x, e.y, e.color, 15);
              p.combo++;
              // Update combo multiplier
              for (let k = COMBO_THRESHOLDS.length - 1; k >= 0; k--) {
                if (p.combo >= COMBO_THRESHOLDS[k]) { p.comboMult = COMBO_MULTIPLIERS[k]; break; }
              }
              const enemyScore = Math.floor(SCORE_ENEMY * p.comboMult);
              s.score += enemyScore;
              s.kills++;
              const popText = p.comboMult > 1 ? `+${enemyScore} x${p.comboMult.toFixed(1)}` : `+${enemyScore}`;
              s.scorePopups.push({ x: e.x, y: e.y, text: popText, color: p.comboMult > 1 ? COL.combo : COL.text, life: 1000 });
              // Powerup drop
              if (Math.random() < POWERUP_CHANCE) {
                const types = ['health', 'damage', 'power', 'shield'];
                s.powerups.push({ x: e.x, y: e.y, type: types[randInt(0, types.length - 1)], timer: 0 });
              }
              s.enemies.splice(i, 1);
              break;
            }
          }
        }
      }

      // Wave progression
      if (s.waveTimer >= WAVE_DURATION) {
        s.wave++;
        s.waveTimer = 0;
        const waveProgress = (s.wave - 1) / WAVES_PER_STAGE;
        s.spawnRate = Math.max(300, Math.floor(1500 * Math.pow(0.85, s.stage - 1) * (1 - waveProgress * 0.4)));
        if (s.wave > WAVES_PER_STAGE) {
          // Spawn boss
          s.boss = createBoss(s.stage);
          s.enemies = [];
          s.message = BOSS_NAMES[(s.stage - 1) % BOSS_NAMES.length];
          s.messageTimer = 3000;
        }
      }
    }

    // ─── Enemy bullet → player collision ──────────────
    for (let i = s.enemyBullets.length - 1; i >= 0; i--) {
      const b = s.enemyBullets[i];
      if (dist(b, p) < PLAYER_HITBOX + b.size) {
        if (p.invuln <= 0) {
          if (p.shield) {
            p.shield = false;
            p.combo = 0; p.comboMult = 1.0;
          } else {
            p.hp -= b.damage;
            p.combo = 0; p.comboMult = 1.0;
            p.invuln = PLAYER_INVULN_MS;
            addExplosion(s.particles, p.x, p.y, '#ffffff', 12);
            s.screenShake = 8; s.shakeIntensity = 6;
          }
        }
        s.enemyBullets.splice(i, 1);
      }
    }

    // ─── Player death ─────────────────────────────────
    if (p.hp <= 0) {
      addExplosion(s.particles, p.x, p.y, COL.enemy, 50);
      addExplosion(s.particles, p.x, p.y, COL.combo, 40);
      addExplosion(s.particles, p.x, p.y, '#ffffff', 30);
      s.screenShake = 20; s.shakeIntensity = 15;
      s.status = 'game_over';
    }

    // ─── Powerups ─────────────────────────────────────
    s.powerups = s.powerups.filter(pw => {
      pw.y += 1.5;
      pw.timer += dt;
      if (pw.y > GAME_H + 20) return false;
      if (dist(pw, p) < PLAYER_SIZE + POWERUP_SIZE) {
        s.score += SCORE_POWERUP;
        s.scorePopups.push({ x: pw.x, y: pw.y, text: `+${SCORE_POWERUP}`, color: COL.powerup, life: 800 });
        if (pw.type === 'health') p.hp = Math.min(p.maxHp, p.hp + 15);
        else if (pw.type === 'damage') p.damageMult = Math.min(3, p.damageMult + 0.3);
        else if (pw.type === 'power') p.powerLevel = Math.min(4, p.powerLevel + 1);
        else if (pw.type === 'shield') p.shield = true;
        return false;
      }
      return true;
    });

    // ─── Particles ────────────────────────────────────
    s.particles = s.particles.filter(pt => {
      pt.x += pt.vx; pt.y += pt.vy;
      pt.vx *= 0.98; pt.vy *= 0.98;
      pt.life -= dt;
      return pt.life > 0;
    });

    // Score popups
    s.scorePopups = s.scorePopups.filter(sp => {
      sp.y -= 0.8;
      sp.life -= dt;
      return sp.life > 0;
    });

    // Messages
    if (s.messageTimer > 0) s.messageTimer -= dt;
    if (s.screenShake > 0) s.screenShake--;
  }, []);

  // ─── Draw ───────────────────────────────────────────
  const draw = useCallback((ctx: CanvasRenderingContext2D) => {
    const s = stateRef.current;
    const p = s.player;

    // Screen shake offset
    let shakeX = 0, shakeY = 0;
    if (s.screenShake > 0) {
      shakeX = rand(-s.shakeIntensity, s.shakeIntensity);
      shakeY = rand(-s.shakeIntensity, s.shakeIntensity);
    }
    ctx.save();
    ctx.translate(shakeX, shakeY);

    // Background
    ctx.fillStyle = COL.bg;
    ctx.fillRect(0, 0, GAME_W, GAME_H);

    // Stars
    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    for (let i = 0; i < 60; i++) {
      const sx = (i * 137.5 + performance.now() * 0.002 * (i % 3 + 1)) % GAME_W;
      const sy = (i * 83.7 + performance.now() * 0.01 * (i % 2 + 1)) % GAME_H;
      ctx.fillRect(sx, sy, i % 3 === 0 ? 2 : 1, i % 3 === 0 ? 2 : 1);
    }

    // Particles
    for (const pt of s.particles) {
      const alpha = pt.life / pt.maxLife;
      ctx.globalAlpha = alpha;
      ctx.fillStyle = pt.color;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, pt.size * alpha, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // Powerups
    for (const pw of s.powerups) {
      const pulse = 1 + Math.sin(pw.timer * 0.005) * 0.2;
      const colors: Record<string, string> = { health: '#00ff64', damage: '#ff4444', power: '#ffff00', shield: '#00ffff' };
      ctx.fillStyle = colors[pw.type] || COL.powerup;
      ctx.beginPath();
      ctx.arc(pw.x, pw.y, POWERUP_SIZE * pulse, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.stroke();
      // Icon letter
      ctx.fillStyle = '#000';
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const icons: Record<string, string> = { health: '+', damage: '!', power: 'P', shield: 'S' };
      ctx.fillText(icons[pw.type] || '?', pw.x, pw.y);
    }

    // Enemy bullets
    for (const b of s.enemyBullets) {
      ctx.fillStyle = COL.bullet;
      ctx.shadowColor = COL.bullet;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    // Player bullets
    for (const b of s.playerBullets) {
      ctx.fillStyle = COL.playerBullet;
      ctx.shadowColor = COL.playerBullet;
      ctx.shadowBlur = 4;
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    // Enemies
    for (const e of s.enemies) {
      // Glow
      ctx.fillStyle = e.color + '33';
      ctx.beginPath();
      ctx.arc(e.x, e.y, e.size * 1.4, 0, Math.PI * 2);
      ctx.fill();
      // Body
      ctx.fillStyle = e.color;
      if (e.type === 'circle') {
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.size, 0, Math.PI * 2);
        ctx.fill();
      } else if (e.type === 'spiral') {
        // Diamond shape
        ctx.beginPath();
        ctx.moveTo(e.x, e.y - e.size);
        ctx.lineTo(e.x + e.size * 0.7, e.y);
        ctx.lineTo(e.x, e.y + e.size);
        ctx.lineTo(e.x - e.size * 0.7, e.y);
        ctx.closePath();
        ctx.fill();
      } else {
        // Triangle
        ctx.beginPath();
        ctx.moveTo(e.x, e.y + e.size);
        ctx.lineTo(e.x - e.size * 0.8, e.y - e.size * 0.6);
        ctx.lineTo(e.x + e.size * 0.8, e.y - e.size * 0.6);
        ctx.closePath();
        ctx.fill();
      }
      // HP bar
      if (e.hp < e.maxHp) {
        const barW = e.size * 1.5;
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(e.x - barW / 2, e.y - e.size - 8, barW, 3);
        ctx.fillStyle = COL.powerup;
        ctx.fillRect(e.x - barW / 2, e.y - e.size - 8, barW * (e.hp / e.maxHp), 3);
      }
    }

    // Boss
    if (s.boss) {
      const boss = s.boss;
      // Glow
      ctx.fillStyle = COL.bossGlow;
      ctx.beginPath();
      ctx.arc(boss.x, boss.y, boss.size * 2, 0, Math.PI * 2);
      ctx.fill();
      // Body
      ctx.fillStyle = boss.color;
      ctx.shadowColor = boss.color;
      ctx.shadowBlur = 15;
      ctx.beginPath();
      const sides = 6;
      for (let i = 0; i < sides; i++) {
        const a = (i / sides) * Math.PI * 2 - Math.PI / 2 + performance.now() * 0.001;
        const px = boss.x + Math.cos(a) * boss.size;
        const py = boss.y + Math.sin(a) * boss.size;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.fill();
      ctx.shadowBlur = 0;
      // HP bar
      const barW = boss.size * 3;
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.fillRect(boss.x - barW / 2, boss.y - boss.size - 20, barW, 6);
      ctx.fillStyle = boss.color;
      ctx.fillRect(boss.x - barW / 2, boss.y - boss.size - 20, barW * (boss.hp / boss.maxHp), 6);
      // Name
      ctx.fillStyle = COL.text;
      ctx.font = 'bold 12px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(boss.name, boss.x, boss.y - boss.size - 26);
    }

    // Player
    if (s.status === 'playing') {
      const flicker = p.invuln > 0 && Math.floor(p.invuln / 80) % 2 === 0;
      if (!flicker) {
        // Ship glow
        ctx.fillStyle = COL.playerGlow;
        ctx.beginPath();
        ctx.arc(p.x, p.y, PLAYER_SIZE * 2, 0, Math.PI * 2);
        ctx.fill();
        // Ship body (triangle pointing up)
        ctx.fillStyle = COL.player;
        ctx.shadowColor = COL.player;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y - PLAYER_SIZE);
        ctx.lineTo(p.x - PLAYER_SIZE * 0.8, p.y + PLAYER_SIZE * 0.6);
        ctx.lineTo(p.x + PLAYER_SIZE * 0.8, p.y + PLAYER_SIZE * 0.6);
        ctx.closePath();
        ctx.fill();
        ctx.shadowBlur = 0;
        // Engine glow
        ctx.fillStyle = '#ff8800';
        ctx.beginPath();
        ctx.arc(p.x, p.y + PLAYER_SIZE * 0.6, 4 + Math.sin(performance.now() * 0.01) * 2, 0, Math.PI * 2);
        ctx.fill();
        // Hitbox dot
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(p.x, p.y, PLAYER_HITBOX, 0, Math.PI * 2);
        ctx.fill();
        // Shield
        if (p.shield) {
          ctx.strokeStyle = COL.shield;
          ctx.lineWidth = 2;
          ctx.globalAlpha = 0.5 + Math.sin(performance.now() * 0.005) * 0.2;
          ctx.beginPath();
          ctx.arc(p.x, p.y, PLAYER_SIZE * 2, 0, Math.PI * 2);
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }
    }

    // Score popups
    for (const sp of s.scorePopups) {
      ctx.globalAlpha = Math.min(1, sp.life / 300);
      ctx.fillStyle = sp.color;
      ctx.font = 'bold 14px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(sp.text, sp.x, sp.y);
    }
    ctx.globalAlpha = 1;

    // ─── HUD ─────────────────────────────────────────
    // Top bar
    ctx.fillStyle = COL.hud;
    ctx.fillRect(0, 0, GAME_W, 36);
    ctx.fillStyle = COL.text;
    ctx.font = 'bold 13px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`SCORE: ${s.score}`, 10, 24);
    ctx.textAlign = 'center';
    ctx.fillText(`STAGE ${s.stage}  WAVE ${s.wave}/${WAVES_PER_STAGE}`, GAME_W / 2, 24);
    ctx.textAlign = 'right';
    ctx.fillText(`KILLS: ${s.kills}`, GAME_W - 10, 24);

    // Health bar (bottom)
    const hpBarW = 200;
    const hpBarH = 10;
    const hpBarX = 10;
    const hpBarY = GAME_H - 20;
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(hpBarX, hpBarY, hpBarW, hpBarH);
    const hpRatio = Math.max(0, p.hp / p.maxHp);
    ctx.fillStyle = hpRatio > 0.5 ? COL.powerup : hpRatio > 0.25 ? COL.combo : COL.enemy;
    ctx.fillRect(hpBarX, hpBarY, hpBarW * hpRatio, hpBarH);
    ctx.fillStyle = COL.text;
    ctx.font = '10px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`HP: ${Math.max(0, Math.ceil(p.hp))}/${p.maxHp}`, hpBarX, hpBarY - 4);

    // Combo display
    if (p.combo > 0) {
      ctx.fillStyle = COL.combo;
      ctx.font = 'bold 11px monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`COMBO: ${p.combo} (x${p.comboMult.toFixed(1)})`, GAME_W - 10, GAME_H - 8);
    }

    // Power level
    ctx.fillStyle = COL.cyan;
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`PWR: ${p.powerLevel}  DMG: x${p.damageMult.toFixed(1)}`, GAME_W / 2, GAME_H - 8);

    // Message
    if (s.messageTimer > 0) {
      const alpha = Math.min(1, s.messageTimer / 500);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = COL.text;
      ctx.font = 'bold 28px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.shadowColor = COL.cyan;
      ctx.shadowBlur = 20;
      ctx.fillText(s.message, GAME_W / 2, GAME_H / 2 - 40);
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
      ctx.textBaseline = 'alphabetic';
    }

    // Low health tint
    if (hpRatio < 0.25 && s.status === 'playing') {
      ctx.fillStyle = `rgba(255,0,0,${0.1 * (1 - hpRatio * 4)})`;
      ctx.fillRect(0, 0, GAME_W, GAME_H);
    }

    // ─── Game Over overlay ────────────────────────────
    if (s.status === 'game_over') {
      ctx.fillStyle = 'rgba(0,0,0,0.75)';
      ctx.fillRect(0, 0, GAME_W, GAME_H);
      ctx.fillStyle = COL.enemy;
      ctx.font = 'bold 36px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('GAME OVER', GAME_W / 2, GAME_H / 2 - 60);
      ctx.fillStyle = COL.text;
      ctx.font = '18px monospace';
      ctx.fillText(`Score: ${s.score}`, GAME_W / 2, GAME_H / 2);
      ctx.fillText(`Stage: ${s.stage}  Kills: ${s.kills}`, GAME_W / 2, GAME_H / 2 + 30);
      ctx.fillStyle = COL.cyan;
      ctx.font = '14px monospace';
      ctx.fillText('Returning to lobby...', GAME_W / 2, GAME_H / 2 + 80);
      ctx.textBaseline = 'alphabetic';
    }

    ctx.restore();
  }, []);

  // ─── Game Loop ──────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    lastTimeRef.current = performance.now();
    gameOverCalledRef.current = false;

    const loop = (now: number) => {
      const rawDt = now - lastTimeRef.current;
      lastTimeRef.current = now;
      const dt = Math.min(rawDt, 50); // Cap delta to 50ms

      update(dt);
      draw(ctx);

      const s = stateRef.current;
      if (s.status === 'game_over' && !gameOverCalledRef.current) {
        gameOverCalledRef.current = true;
        setGameOver(true);
        // Delay return to lobby
        setTimeout(() => {
          onGameOver(s.score, s.stage, s.kills);
        }, 3000);
      }

      animRef.current = requestAnimationFrame(loop);
    };

    animRef.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animRef.current);
    };
  }, [update, draw, onGameOver]);

  // ─── Render ─────────────────────────────────────────
  return (
    <div className="fixed inset-0 z-[100] bg-black flex items-center justify-center">
      <canvas
        ref={canvasRef}
        width={GAME_W}
        height={GAME_H}
        className="max-h-screen max-w-full"
        style={{ imageRendering: 'pixelated' }}
        tabIndex={0}
        autoFocus
      />
      {/* Controls hint */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs text-gray-500 font-mono text-center">
        <span className="opacity-60">
          WASD/Arrows: Move &nbsp;|&nbsp; Space/Z: Shoot &nbsp;|&nbsp; Shift: Focus (slow) &nbsp;|&nbsp; ESC: Exit
        </span>
      </div>
    </div>
  );
};
