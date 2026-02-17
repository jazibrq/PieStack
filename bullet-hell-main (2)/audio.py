"""
Audio system for the bullet hell game
"""
import pygame


class AudioSystem:
    """Manages game audio and sound effects"""
    def __init__(self):
        self.enabled = True
        self.music_volume = 0.08  # Reduced from 0.2 - much quieter
        self.sfx_volume = 0.08   # Reduced from 0.25 - much quieter
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init()
        except:
            self.enabled = False
            print("Audio system could not be initialized")
        
        # Sound effect placeholders
        self.sounds = {}
        
        # Generate simple sound effects using pygame
        if self.enabled:
            self.create_sound_effects()
    
    def create_sound_effects(self):
        """Create simple sound effects"""
        try:
            # We'll create simple beep sounds as placeholders
            # In a full game, you'd load actual sound files
            
            # Player shoot sound
            self.sounds['player_shoot'] = self.create_beep(440, 50)
            
            # Enemy hit sound
            self.sounds['enemy_hit'] = self.create_beep(330, 100)
            
            # Player hit sound
            self.sounds['player_hit'] = self.create_beep(220, 200)
            
            # Power-up collect sound
            self.sounds['powerup'] = self.create_beep(660, 150)
            
            # Enemy death sound
            self.sounds['enemy_death'] = self.create_beep(280, 200)
            
            # Boss hit sound
            self.sounds['boss_hit'] = self.create_beep(350, 100)
            
        except Exception as e:
            print(f"Could not create sound effects: {e}")
    
    def create_beep(self, frequency, duration_ms):
        """Create a simple beep sound"""
        try:
            sample_rate = 22050
            samples = int(sample_rate * duration_ms / 1000)
            
            import numpy as np
            
            # Generate sine wave
            t = np.linspace(0, duration_ms / 1000, samples)
            wave = np.sin(2 * np.pi * frequency * t)
            
            # Apply envelope to avoid clicks
            envelope = np.ones(samples)
            fade_samples = samples // 10
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
            wave = wave * envelope
            
            # Convert to 16-bit integer
            wave = (wave * 32767).astype(np.int16)
            
            # Create stereo sound
            stereo_wave = np.zeros((samples, 2), dtype=np.int16)
            stereo_wave[:, 0] = wave
            stereo_wave[:, 1] = wave
            
            # Create pygame sound
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.set_volume(self.sfx_volume)
            
            return sound
        except:
            # If numpy is not available, return None
            return None
    
    def play_sound(self, sound_name, pitch_multiplier=1.0):
        """Play a sound effect with optional pitch shifting"""
        if not self.enabled:
            return
        
        try:
            if sound_name in self.sounds and self.sounds[sound_name]:
                # Pitch shifting by changing playback speed (if pygame supports it)
                # For now, just play normally - pitch_multiplier parameter for future use
                self.sounds[sound_name].play()
        except:
            pass
    
    def play_music(self, music_file):
        """Play background music (placeholder)"""
        if not self.enabled:
            return
        
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)  # Loop infinitely
        except:
            pass
    
    def stop_music(self):
        """Stop background music"""
        if not self.enabled:
            return
        
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except:
                pass
    
    def set_sfx_volume(self, volume):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        if self.enabled and self.sounds:
            try:
                for sound in self.sounds.values():
                    if sound:
                        sound.set_volume(self.sfx_volume)
            except:
                pass


# Simple audio system without numpy (fallback)
class SimpleAudioSystem:
    """Simple audio system that doesn't require numpy"""
    def __init__(self):
        self.enabled = False
        print("Audio system disabled (install numpy and pygame for audio support)")
    
    def play_sound(self, sound_name, pitch_multiplier=1.0):
        pass
    
    def play_music(self, music_file):
        pass
    
    def stop_music(self):
        pass
    
    def set_music_volume(self, volume):
        pass
    
    def set_sfx_volume(self, volume):
        pass


def create_audio_system():
    """Create audio system with fallback"""
    try:
        import numpy
        return AudioSystem()
    except ImportError:
        return SimpleAudioSystem()
