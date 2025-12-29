import pygame.mixer as mixer
import os
import threading
import glob
import yt_dlp
import random

class GlobalMusicPlayer:
    def __init__(self):
        self.music_state = "stopped"
        self.current_volume = 0.5
        self.playlist = []
        self.current_index = 0
        self.music_folder = "downloaded_music"
        
        # Callback for UI refresh
        self.on_playlist_changed = None
        
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            
        mixer.init()
        mixer.music.set_volume(self.current_volume)
        self.refresh_playlist()
        
        # Auto-play on startup if there are songs
        if self.playlist:
            self.play_random()
    
    def refresh_playlist(self):
        self.playlist = []
        audio_extensions = ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac']
        for extension in audio_extensions:
            pattern = os.path.join(self.music_folder, extension)
            self.playlist.extend(glob.glob(pattern))
        
        self.playlist.sort()
        
        # Notify UI about playlist change
        if self.on_playlist_changed:
            self.on_playlist_changed()
    
    def play_random(self):
        """Play a random song from the playlist"""
        if not self.playlist:
            return
            
        try:
            mixer.music.stop()
            # Select random song
            self.current_index = random.randint(0, len(self.playlist) - 1)
            song_path = self.playlist[self.current_index]
            
            mixer.music.load(song_path)
            mixer.music.play(-1)  # -1 means loop indefinitely
            self.music_state = "playing"
        except Exception as e:
            print(f"Play error: {e}")
    
    def download_by_name(self, song_name):
        def download():
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{self.music_folder}/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'default_search': 'ytsearch',
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([song_name])
                
                self.refresh_playlist()
                # Auto-play the newly downloaded song
                if self.playlist:
                    self.play_random()
                return True
                
            except Exception as e:
                print(f"Download error: {e}")
                return False
        
        thread = threading.Thread(target=download, daemon=True)
        thread.start()
        return True
    
    def download_from_spotify(self, search_term):
        """Search and download by song name"""
        return self.download_by_name(search_term)
    
    def play(self, index=None):
        """Play specific song or random if no index provided"""
        if not self.playlist:
            return
            
        try:
            mixer.music.stop()
            
            if index is not None and 0 <= index < len(self.playlist):
                self.current_index = index
                song_path = self.playlist[index]
            else:
                # Play random song if no specific index
                self.play_random()
                return
            
            mixer.music.load(song_path)
            mixer.music.play(-1)
            self.music_state = "playing"
        except Exception as e:
            print(f"Play error: {e}")
    
    def toggle_play_pause(self):
        """Toggle between play and pause - this is the main control method"""
        if not self.playlist:
            return
            
        if self.music_state == "playing":
            mixer.music.pause()
            self.music_state = "paused"
        elif self.music_state == "paused":
            mixer.music.unpause()
            self.music_state = "playing"
        else:  # stopped
            self.play_random()
    
    def next_song(self):
        """Play next random song"""
        if not self.playlist:
            return
        self.play_random()
    
    def previous_song(self):
        """Play previous random song"""
        if not self.playlist:
            return
        self.play_random()
    
    def set_volume(self, volume):
        self.current_volume = max(0.0, min(1.0, volume))
        mixer.music.set_volume(self.current_volume)
    
    def get_volume(self):
        return self.current_volume
    
    def remove_song(self, index):
        if 0 <= index < len(self.playlist):
            try:
                # Stop music if it's playing the song to be deleted
                if index == self.current_index and self.music_state == "playing":
                    mixer.music.stop()
                    self.music_state = "stopped"
                
                song_path = self.playlist[index]
                os.remove(song_path)
                
                self.refresh_playlist()
                
                # If songs remain, play a random one
                if self.playlist:
                    self.play_random()
                
                return True
            except Exception as e:
                print(f"Remove error: {e}")
        return False
    
    def get_current_song(self):
        if self.playlist and 0 <= self.current_index < len(self.playlist):
            return os.path.basename(self.playlist[self.current_index])
        return "No song"
    
    def get_playlist(self):
        return [os.path.basename(song) for song in self.playlist]
    
    def is_playing(self):
        """Check if music is currently playing"""
        return self.music_state == "playing"
    
    def get_play_pause_icon(self):
        """Return the appropriate icon for play/pause state"""
        return "⏸" if self.is_playing() else "▶"

# Global instance
global_music = GlobalMusicPlayer()