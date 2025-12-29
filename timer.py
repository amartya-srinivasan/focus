import pygame
import sys
import time
import os
import cv2
import numpy as np
import music_player
import website_blocker
import subprocess
import platform
import json
import math
import threading

# Database connection function
def get_database_connection():
    """Create a database connection using saved config"""
    try:
        config_file = "mysql_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                mysql_config = json.load(f)
        else:
            mysql_config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'focus_app',
                'port': 3306
            }
        
        from database import Database
        return Database(mysql_config)
    except Exception as e:  
        print(f"Database connection error: {e}")
        return None
    
# Initialize pygame
pygame.init()

# Screen dimensions - fullscreen
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Focus Timer")

# ===== IMPROVED COLOR SCHEME (matches AnalyticsDashboard) =====
BACKGROUND = (25, 25, 50)           # Deep blue background
PANEL_BG = (40, 40, 80)             # Lighter blue panels
DARK_PANEL = (30, 30, 60)           # Darker panels
TEXT_COLOR = (255, 255, 255)        # White text
HIGHLIGHT = (100, 200, 255)         # Light blue highlights
ACCENT_GOLD = (255, 215, 0)         # Gold accents
ACCENT_SILVER = (192, 192, 192)     # Silver accents

# Status colors
SUCCESS_GREEN = (100, 200, 150)     # Softer green
WARNING_ORANGE = (255, 180, 100)    # Warm orange
PAUSE_YELLOW = (255, 220, 100)      # Soft yellow
DANGER_RED = (255, 100, 100)        # Softer red

# UI colors
BUTTON_PRIMARY = (70, 130, 180)     # Blue buttons
BUTTON_HOVER = (100, 160, 210)      # Lighter blue on hover
BUTTON_SUCCESS = (80, 180, 120)     # Green for start
BUTTON_DANGER = (200, 80, 80)       # Red for stop
INPUT_BG = (40, 40, 60)             # Input backgrounds
BORDER_COLOR = (100, 100, 150)      # Subtle borders
SHADOW_COLOR = (15, 15, 30)         # Shadow color

# Todo list colors
TODO_BG = (35, 35, 65, 230)         # Semi-transparent
TODO_ITEM_BG = (45, 45, 75)         # Individual items
TODO_HOVER = (60, 60, 90)           # Hover state
TODO_COMPLETED = (50, 80, 60)       # Completed items

# ===== IMPROVED FONTS (all Times New Roman for consistency) =====
timer_font = pygame.font.SysFont("timesnewroman", 140, bold=True)
header_font = pygame.font.SysFont("timesnewroman", 48, bold=True)
text_font = pygame.font.SysFont("timesnewroman", 24)
small_font = pygame.font.SysFont("timesnewroman", 18)
tiny_font = pygame.font.SysFont("timesnewroman", 14)
button_font = pygame.font.SysFont("timesnewroman", 20, bold=True)
status_font = pygame.font.SysFont("timesnewroman", 16)
todo_font = pygame.font.SysFont("timesnewroman", 18)
todo_header_font = pygame.font.SysFont("timesnewroman", 22, bold=True)


class VideoBackground:
    def __init__(self, video_path):
        try:
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                print(f"Warning: Could not open video file {video_path}")
                self.cap = None
            self.current_frame = None
        except Exception as e:
            print(f"Error initializing video background: {e}")
            self.cap = None
        
    def get_frame(self):
        if self.cap is None:
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        
        if ret:
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Darker overlay for better readability
            overlay = np.zeros_like(frame)
            frame = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
            
            frame = np.rot90(frame)
            self.current_frame = pygame.surfarray.make_surface(frame)
        return self.current_frame
    
    def release(self):
        if self.cap:
            self.cap.release()


class VolumeControls:
    def __init__(self):
        self.visible = False
        self.dragging = False
        
        self.icon_rect = pygame.Rect(SCREEN_WIDTH - 70, 20, 50, 50)
        self.panel_rect = pygame.Rect(SCREEN_WIDTH - 200, 70, 180, 120)
        
        self.slider_rect = pygame.Rect(SCREEN_WIDTH - 190, 100, 160, 15)
        self.knob_radius = 10
        self.knob_x = self.slider_rect.x + (music_player.global_music.get_volume() * self.slider_rect.width)
        self.knob_y = self.slider_rect.y + self.slider_rect.height // 2
        
        self.prev_btn = pygame.Rect(SCREEN_WIDTH - 190, 130, 40, 30)
        self.play_pause_btn = pygame.Rect(SCREEN_WIDTH - 140, 130, 40, 30)
        self.next_btn = pygame.Rect(SCREEN_WIDTH - 90, 130, 40, 30)
        
        self.load_icons()
        self.font = pygame.font.SysFont('timesnewroman', 12)
    
    def load_icons(self):
        try:
            pause_img = pygame.image.load("assets/pause.png").convert_alpha()
            play_img = pygame.image.load("assets/play.png").convert_alpha()
            next_img = pygame.image.load("assets/next.png").convert_alpha()
            previous_img = pygame.image.load("assets/previous.png").convert_alpha()
            
            self.pause_icon = pygame.transform.scale(pause_img, (20, 20))
            self.play_icon = pygame.transform.scale(play_img, (20, 20))
            self.next_icon = pygame.transform.scale(next_img, (20, 20))
            self.previous_icon = pygame.transform.scale(previous_img, (20, 20))
            
        except Exception as e:
            print(f"Error loading icons: {e}")
            self.pause_icon = None
            self.play_icon = None
            self.next_icon = None
            self.previous_icon = None
        
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.icon_rect.collidepoint(mouse_pos):
                self.visible = not self.visible
                return True
                
            if self.visible:
                knob_rect = pygame.Rect(self.knob_x - self.knob_radius, self.knob_y - self.knob_radius,
                                      self.knob_radius * 2, self.knob_radius * 2)
                if knob_rect.collidepoint(mouse_pos) or self.slider_rect.collidepoint(mouse_pos):
                    self.dragging = True
                    self.knob_x = max(self.slider_rect.left, min(mouse_pos[0], self.slider_rect.right))
                    volume = (self.knob_x - self.slider_rect.left) / self.slider_rect.width
                    music_player.global_music.set_volume(volume)
                    return True
                    
                if self.prev_btn.collidepoint(mouse_pos):
                    music_player.global_music.previous_song()
                    return True
                elif self.play_pause_btn.collidepoint(mouse_pos):
                    music_player.global_music.toggle_play_pause()
                    return True
                elif self.next_btn.collidepoint(mouse_pos):
                    music_player.global_music.next_song()
                    return True
                    
                if not self.panel_rect.collidepoint(mouse_pos) and not self.icon_rect.collidepoint(mouse_pos):
                    self.visible = False
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.knob_x = max(self.slider_rect.left, min(event.pos[0], self.slider_rect.right))
            volume = (self.knob_x - self.slider_rect.left) / self.slider_rect.width
            music_player.global_music.set_volume(volume)
            return True
            
        return False
        
    def draw(self, screen):
        # Volume icon with improved styling
        pygame.draw.rect(screen, DARK_PANEL, self.icon_rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, self.icon_rect, 2, border_radius=8)
        
        icon_font = pygame.font.SysFont('timesnewroman', 24)
        icon_text = icon_font.render("♪", True, HIGHLIGHT)
        screen.blit(icon_text, (self.icon_rect.centerx - 8, self.icon_rect.centery - 12))
        
        if self.visible:
            # Shadow
            shadow_rect = pygame.Rect(self.panel_rect.x + 4, self.panel_rect.y + 4,
                                     self.panel_rect.width, self.panel_rect.height)
            pygame.draw.rect(screen, SHADOW_COLOR, shadow_rect, border_radius=10)
            
            # Panel
            pygame.draw.rect(screen, PANEL_BG, self.panel_rect, border_radius=10)
            pygame.draw.rect(screen, BORDER_COLOR, self.panel_rect, 2, border_radius=10)
            
            # Volume text
            volume_text = self.font.render("Volume", True, HIGHLIGHT)
            screen.blit(volume_text, (self.panel_rect.x + 10, self.panel_rect.y + 15))
            
            # Slider track
            pygame.draw.rect(screen, DARK_PANEL, self.slider_rect, border_radius=5)
            
            # Filled portion
            filled_width = self.knob_x - self.slider_rect.left
            if filled_width > 0:
                filled_rect = pygame.Rect(self.slider_rect.left, self.slider_rect.top,
                                        filled_width, self.slider_rect.height)
                pygame.draw.rect(screen, HIGHLIGHT, filled_rect, border_radius=5)
            
            # Slider knob
            pygame.draw.circle(screen, TEXT_COLOR, (int(self.knob_x), int(self.knob_y)), self.knob_radius)
            pygame.draw.circle(screen, HIGHLIGHT, (int(self.knob_x), int(self.knob_y)), self.knob_radius - 2)
            
            # Volume percentage
            volume_pct = int((self.knob_x - self.slider_rect.left) / self.slider_rect.width * 100)
            vol_text = tiny_font.render(f"{volume_pct}%", True, TEXT_COLOR)
            screen.blit(vol_text, (self.panel_rect.centerx - 15, self.panel_rect.y + 35))
            
            # Control buttons
            for btn in [self.prev_btn, self.play_pause_btn, self.next_btn]:
                pygame.draw.rect(screen, BUTTON_PRIMARY, btn, border_radius=5)
                pygame.draw.rect(screen, BORDER_COLOR, btn, 1, border_radius=5)
            
            # Icons
            if self.previous_icon:
                screen.blit(self.previous_icon, (self.prev_btn.x + 10, self.prev_btn.y + 5))
            if music_player.global_music.is_playing:
                if self.pause_icon:
                    screen.blit(self.pause_icon, (self.play_pause_btn.x + 10, self.play_pause_btn.y + 5))
            else:
                if self.play_icon:
                    screen.blit(self.play_icon, (self.play_pause_btn.x + 10, self.play_pause_btn.y + 5))
            if self.next_icon:
                screen.blit(self.next_icon, (self.next_btn.x + 10, self.next_btn.y + 5))


class Button:
    def __init__(self, x, y, width, height, text, color=BUTTON_PRIMARY, 
                 hover_color=BUTTON_HOVER, text_color=TEXT_COLOR):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        
    def draw(self, screen):
        # Shadow effect
        shadow = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 
                           self.rect.width, self.rect.height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow, border_radius=12)
        
        # Button background
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        
        # Border
        border_color = HIGHLIGHT if self.hovered else BORDER_COLOR
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=12)
        
        # Button text
        text_surface = button_font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, mouse_pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False


class TodoItem:
    def __init__(self, text, completed=False):
        self.text = text
        self.completed = completed


class TodoList:
    def __init__(self, x, y, width, height, user_id, db=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.user_id = user_id
        self.db = db  # Reuse database connection
        self.items = []
        self.input_text = ""
        self.input_active = False
        self.hovered_index = -1
        
        # Load todos from database
        self.load_todos()
        
    def load_todos(self):
        """Load todos from database"""
        try:
            if self.db:
                todos = self.db.get_todos(self.user_id)
                self.items = [TodoItem(todo['task'], todo['completed']) for todo in todos]
                print(f"Loaded {len(self.items)} todos")
        except Exception as e:
            print(f"Error loading todos: {e}")
    
    def save_todos(self):
        """Save todos to database asynchronously"""
        def _save_in_background():
            try:
                if self.db:
                    self.db.save_todos(self.user_id, [(item.text, item.completed) for item in self.items])
                    print("✓ Todos saved")
            except Exception as e:
                print(f"Error saving todos: {e}")
        
        # Run save in background thread so UI doesn't freeze
        thread = threading.Thread(target=_save_in_background, daemon=True)
        thread.start()
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEMOTION:
            # Check clear button hover
            if hasattr(self, 'clear_button_rect') and self.clear_button_rect:
                self.clear_hovered = self.clear_button_rect.collidepoint(mouse_pos)
            
            # Check item hover
            if self.rect.collidepoint(mouse_pos):
                item_height = 35
                header_height = 70
                list_y = self.rect.y + header_height + 25
                
                for i in range(len(self.items)):
                    item_y = list_y + i * item_height
                    item_rect = pygame.Rect(self.rect.x + 10, item_y, self.rect.width - 20, item_height - 5)
                    if item_rect.collidepoint(mouse_pos):
                        self.hovered_index = i
                        return
                self.hovered_index = -1
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check clear button click
            if hasattr(self, 'clear_button_rect') and self.clear_button_rect and self.clear_button_rect.collidepoint(mouse_pos):
                # Remove all completed items
                self.items = [item for item in self.items if not item.completed]
                self.save_todos()
                return
            
            if not self.rect.collidepoint(mouse_pos):
                if self.input_active:
                    self.input_active = False
                return
            
            header_height = 70
            input_y = self.rect.y + 55
            input_rect = pygame.Rect(self.rect.x + 90, input_y, self.rect.width - 180, 32)
            
            if input_rect.collidepoint(mouse_pos):
                self.input_active = True
                return
            
            # Check item clicks
            item_height = 35
            list_y = self.rect.y + header_height + 25
            
            for i, item in enumerate(self.items):
                item_y = list_y + i * item_height
                checkbox_rect = pygame.Rect(self.rect.x + 20, item_y + 10, 20, 20)
                
                if checkbox_rect.collidepoint(mouse_pos):
                    item.completed = not item.completed
                    self.save_todos()
                    return
        
        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN and self.input_text.strip():
                self.items.append(TodoItem(self.input_text.strip()))
                self.save_todos()
                self.input_text = ""
                self.input_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                self.input_text = ""
            elif len(self.input_text) < 50:
                self.input_text += event.unicode
    
    def draw(self, screen):
        # Shadow
        shadow_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, 
                                 self.rect.width, self.rect.height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow_rect, border_radius=15)
        
        # Main panel
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill(TODO_BG)
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 2, border_radius=15)
        
        # Header background
        header_height = 70
        # Draw header as rectangle (not using border_radius to avoid clipping)
        header_surface = pygame.Surface((self.rect.width - 4, header_height), pygame.SRCALPHA)
        header_surface.fill(PANEL_BG)
        screen.blit(header_surface, (self.rect.x + 2, self.rect.y + 2))
        
        # Manually draw rounded top corners
        pygame.draw.rect(screen, PANEL_BG, 
                        (self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 20),
                        border_top_left_radius=13, border_top_right_radius=13)
        
        # Title (with more padding from top)
        completed = sum(1 for item in self.items if item.completed)
        title = todo_header_font.render("TASKS", True, HIGHLIGHT)
        screen.blit(title, (self.rect.x + 25, self.rect.y + 20))
        
        # Counter (aligned with title)
        counter_text = f"{completed}/{len(self.items)}"
        counter = small_font.render(counter_text, True, ACCENT_SILVER)
        screen.blit(counter, (self.rect.right - 240, self.rect.y + 23))
        
        # Clear Completed button (if there are completed tasks)
        if completed > 0:
            clear_btn_width = 150
            clear_btn_x = self.rect.right - clear_btn_width - 15
            clear_btn_y = self.rect.y + 15
            self.clear_button_rect = pygame.Rect(clear_btn_x, clear_btn_y, clear_btn_width, 35)
            
            # Button styling
            btn_color = BUTTON_HOVER if hasattr(self, 'clear_hovered') and self.clear_hovered else BUTTON_PRIMARY
            pygame.draw.rect(screen, btn_color, self.clear_button_rect, border_radius=8)
            pygame.draw.rect(screen, BORDER_COLOR, self.clear_button_rect, 1, border_radius=8)
            
            clear_text = tiny_font.render("Clear Completed", True, TEXT_COLOR)
            text_rect = clear_text.get_rect(center=self.clear_button_rect.center)
            screen.blit(clear_text, text_rect)
        else:
            self.clear_button_rect = None
        
        # Input box (moved down a bit)
        input_y = self.rect.y + 55
        input_rect = pygame.Rect(self.rect.x + 90, input_y, self.rect.width - 180, 32)
        input_color = HIGHLIGHT if self.input_active else INPUT_BG
        pygame.draw.rect(screen, input_color, input_rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, input_rect, 1, border_radius=8)
        
        # Plus icon (aligned with input)
        plus_text = text_font.render("+", True, HIGHLIGHT)
        screen.blit(plus_text, (self.rect.x + 60, input_y + 2))
        
        # Input text or placeholder
        if self.input_active:
            input_surf = small_font.render(self.input_text + "|", True, TEXT_COLOR)
        else:
            input_surf = small_font.render(self.input_text or "Add new task...", True, ACCENT_SILVER)
        screen.blit(input_surf, (input_rect.x + 10, input_rect.y + 7))
        
        # Todo items (adjusted for new header)
        header_height = 70
        item_height = 35
        list_y = self.rect.y + header_height + 25
        visible_items = min(len(self.items), (self.rect.height - header_height - 30) // item_height)
        
        for i in range(visible_items):
            item = self.items[i]
            item_y = list_y + i * item_height
            
            # Item background
            item_rect = pygame.Rect(self.rect.x + 10, item_y, self.rect.width - 20, item_height - 5)
            if i == self.hovered_index:
                pygame.draw.rect(screen, TODO_HOVER, item_rect, border_radius=8)
            elif item.completed:
                pygame.draw.rect(screen, TODO_COMPLETED, item_rect, border_radius=8)
            else:
                pygame.draw.rect(screen, TODO_ITEM_BG, item_rect, border_radius=8)
            
            # Checkbox
            checkbox_rect = pygame.Rect(self.rect.x + 20, item_y + 10, 20, 20)
            pygame.draw.rect(screen, INPUT_BG, checkbox_rect, border_radius=4)
            pygame.draw.rect(screen, BORDER_COLOR, checkbox_rect, 2, border_radius=4)
            
            if item.completed:
                # Checkmark
                check_font = pygame.font.SysFont('timesnewroman', 18, bold=True)
                check_text = check_font.render("✓", True, SUCCESS_GREEN)
                screen.blit(check_text, (checkbox_rect.x + 3, checkbox_rect.y))
            
            # Text
            text_color = ACCENT_SILVER if item.completed else TEXT_COLOR
            text_surf = todo_font.render(item.text, True, text_color)
            if item.completed:
                # Strikethrough
                line_y = item_y + item_height // 2
                pygame.draw.line(screen, ACCENT_SILVER, 
                               (self.rect.x + 50, line_y), 
                               (self.rect.x + 50 + text_surf.get_width(), line_y), 1)
            screen.blit(text_surf, (self.rect.x + 50, item_y + 8))


class TimerApp:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.running = False
        self.paused = False
        self.remaining_seconds = 1500  # 25 minutes
        self.original_seconds = 1500
        self.start_time = 0
        
        # Database connection
        self.db = get_database_connection()
        if not self.db:
            print("⚠️ Database connection failed - running in limited mode")
        
        # Website blocking
        self.blocking_active = False
        self.blocked_sites = []
        
        # Video background
        self.video_bg = VideoBackground('snowfall.mp4')
        
        # Volume controls
        self.volume_controls = VolumeControls()
        
        # UI elements - improved styling
        self.back_button = Button(30, 30, 120, 50, "← BACK", DARK_PANEL, BUTTON_HOVER)
        
        # Timer display area
        self.timer_rect = pygame.Rect(SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2 - 140, 600, 280)
        
        # Start/Stop button - bigger and more prominent
        self.start_stop_button = Button(
            SCREEN_WIDTH//2 - 120, 
            SCREEN_HEIGHT//2 + 50,  # Moved up
            240, 
            60, 
            "START", 
            BUTTON_SUCCESS,
            BUTTON_HOVER
        )

        # Todo list (positioned below start button to avoid overlap)
        todo_width = 700
        todo_height = 280
        todo_y = SCREEN_HEIGHT//2 + 130  # Below start button with gap
        self.todo_list = TodoList(SCREEN_WIDTH//2 - todo_width//2, todo_y, 
                                  todo_width, todo_height, user_id, self.db)
        
        # Timer input
        self.timer_input = ""
        self.timer_input_active = False
        
        # Load blocked sites
        self.load_blocked_sites()
        
    def load_blocked_sites(self):
        """Load blocked sites from database and write to blocked_sites.txt"""
        try:
            if self.db:
                self.blocked_sites = self.db.get_blocked_sites(self.user_id)
                print(f"📋 Loaded {len(self.blocked_sites)} blocked sites for user {self.username}")
                
                # Write to blocked_sites.txt for website_blocker.py to use
                with open("blocked_sites.txt", "w") as f:
                    for site in self.blocked_sites:
                        f.write(site + "\n")
                print(f"✅ Written {len(self.blocked_sites)} sites to blocked_sites.txt")
            else:
                self.blocked_sites = []
                print("⚠️ No database connection - using empty blocked sites list")
        except Exception as e:
            print(f"❌ Error loading blocked sites: {e}")
            self.blocked_sites = []

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        # Handle volume controls first
        if self.volume_controls.handle_event(event):
            return True
            
        # Handle back button
        self.back_button.check_hover(mouse_pos)
        if self.back_button.is_clicked(mouse_pos, event):
            self.go_back()
            return True
            
        # Handle start/stop button
        self.start_stop_button.check_hover(mouse_pos)
        if self.start_stop_button.is_clicked(mouse_pos, event):
            if not self.running:
                self.start_timer()
            else:
                self.stop_timer()
            return True

        # Handle timer click for edit/pause/resume
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.timer_rect.collidepoint(mouse_pos):
                if not self.running:
                    self.timer_input_active = True
                    self.timer_input = f"{self.remaining_seconds//60:02d}:{self.remaining_seconds%60:02d}"
                else:
                    if not self.paused:
                        # Pausing - unblock websites
                        self.paused = True
                        self.start_stop_button.text = "RESUME"
                        self.start_stop_button.color = BUTTON_SUCCESS
                        self.deactivate_blocking()  # Unblock when paused
                    else:
                        # Resuming - re-block websites
                        self.paused = False
                        self.start_stop_button.text = "STOP"
                        self.start_stop_button.color = BUTTON_DANGER
                        self.start_time = time.time() - (self.original_seconds - self.remaining_seconds)
                        self.activate_blocking()  # Re-block when resumed
            else:
                if self.timer_input_active:
                    self.finish_editing()
                    
        # Handle timer input in edit mode
        if event.type == pygame.KEYDOWN and self.timer_input_active:
            if event.key == pygame.K_RETURN:
                self.finish_editing()
            elif event.key == pygame.K_BACKSPACE:
                self.timer_input = self.timer_input[:-1]
            elif event.key in [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
                             pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_COLON]:
                if len(self.timer_input) < 8:
                    self.timer_input += event.unicode
                    
        # Handle escape key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.timer_input_active:
                self.timer_input_active = False
            else:
                self.go_back()
            return True
            
        # Handle todo list
        self.todo_list.handle_event(event)
        
        return False
        
    def finish_editing(self):
        try:
            time_str = self.timer_input.strip()
            
            if ':' in time_str:
                minutes, seconds = map(int, time_str.split(':'))
                if seconds >= 60:
                    return
            else:
                minutes = int(time_str)
                seconds = 0
            
            if minutes < 0 or seconds < 0:
                return
                
            total_seconds = minutes * 60 + seconds
            
            if total_seconds == 0:
                return
                
            self.remaining_seconds = total_seconds
            self.original_seconds = total_seconds
            self.timer_input_active = False
            
        except ValueError:
            pass
    
    def activate_blocking(self):
        """Activate website blocking when timer starts"""
        if not self.blocking_active and self.blocked_sites:
            print("🔒 Activating website blocking...")
            success = website_blocker.block_websites()
            if success:
                self.blocking_active = True
                print("✅ Websites blocked successfully")
            else:
                print("⚠️ Website blocking failed - check admin permissions")
        
    def deactivate_blocking(self):
        """Deactivate website blocking when timer stops"""
        if self.blocking_active:
            print("🔓 Deactivating website blocking...")
            success = website_blocker.unblock_websites()
            if success:
                self.blocking_active = False
                print("✅ Websites unblocked successfully")
            else:
                print("⚠️ Website unblocking failed")

    def start_timer(self):
        if self.timer_input_active:
            self.finish_editing()
            
        self.running = True
        self.paused = False
        self.start_stop_button.text = "STOP"
        self.start_stop_button.color = BUTTON_DANGER
        self.original_seconds = self.remaining_seconds
        self.start_time = time.time()
        self.activate_blocking()
        
    def stop_timer(self):
        self.running = False
        self.paused = False
        self.start_stop_button.text = "START"
        self.start_stop_button.color = BUTTON_SUCCESS
        self.deactivate_blocking()
        
    def update_timer(self):
        if self.running and not self.paused:
            current_time = time.time()
            elapsed = current_time - self.start_time
            new_remaining = max(0, self.original_seconds - int(elapsed))
            
            if new_remaining != self.remaining_seconds:
                self.remaining_seconds = new_remaining
                
            if self.remaining_seconds <= 0:
                self.timer_finished()
                
    def timer_finished(self):
        self.running = False
        self.paused = False
        self.start_stop_button.text = "START"
        self.start_stop_button.color = BUTTON_SUCCESS
        self.deactivate_blocking()
        
        # Record study time
        study_minutes = self.original_seconds // 60
        if study_minutes > 0 and self.db:
            try:
                self.db.record_study_session(self.user_id, study_minutes)
                print(f"✅ Recorded {study_minutes} minutes for {self.username}")
            except Exception as e:
                print(f"Error recording session: {e}")
        
        # Reset timer to original time
        self.remaining_seconds = 1500
        self.original_seconds = 1500
            
    def go_back(self):
        self.deactivate_blocking()
        if hasattr(self.video_bg, 'cap'):
            self.video_bg.release()
        pygame.quit()
        # Just exit - main.py is still running and will show again
        # Restart main.py (session persists in current_user.txt)
        import subprocess
        subprocess.run([sys.executable, "main.py"])
        sys.exit()
    
    def draw_progress_ring(self, screen, center_x, center_y, radius):
        """Draw a circular progress indicator around the timer"""
        if self.running and self.original_seconds > 0:
            progress = 1 - (self.remaining_seconds / self.original_seconds)
            
            # Background circle
            pygame.draw.circle(screen, DARK_PANEL, (center_x, center_y), radius, 10)
            
            # Progress arc
            if progress > 0:
                start_angle = -math.pi / 2
                end_angle = start_angle + (2 * math.pi * progress)
                
                # Draw multiple overlapping arcs for thickness
                for i in range(10):
                    current_radius = radius - 5 + i
                    rect = pygame.Rect(center_x - current_radius, center_y - current_radius,
                                     current_radius * 2, current_radius * 2)
                    pygame.draw.arc(screen, HIGHLIGHT, rect, start_angle, end_angle, 2)
    
    def draw(self, screen):
        # Video background
        bg_frame = self.video_bg.get_frame()
        if bg_frame:
            screen.blit(bg_frame, (0, 0))
        else:
            screen.fill(BACKGROUND)
        
        # Draw back button
        self.back_button.draw(screen)
        
        # Timer label (no box behind timer)
        label_text = "FOCUS TIMER"
        label_surf = small_font.render(label_text, True, HIGHLIGHT)
        label_rect = label_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 180))
        screen.blit(label_surf, label_rect)
        
        # Progress ring (centered on timer)
        self.draw_progress_ring(screen, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80, 180)
        
        # Timer display
        if self.timer_input_active:
            timer_surf = timer_font.render(self.timer_input, True, HIGHLIGHT)
            timer_rect = timer_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            screen.blit(timer_surf, timer_rect)
            
            # Blinking cursor
            if int(time.time() * 2) % 2 == 0:
                cursor_x = timer_rect.right + 5
                cursor_y = timer_rect.centery - 30
                pygame.draw.line(screen, TEXT_COLOR, (cursor_x, cursor_y), (cursor_x, cursor_y + 60), 3)
        else:
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"
            
            timer_color = TEXT_COLOR
            if self.running:
                timer_color = PAUSE_YELLOW if self.paused else TEXT_COLOR
                
            timer_surf = timer_font.render(timer_text, True, timer_color)
            timer_rect = timer_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            screen.blit(timer_surf, timer_rect)
        
        # Percentage text
        if self.running and self.original_seconds > 0:
            progress_pct = int((1 - self.remaining_seconds / self.original_seconds) * 100)
            pct_text = tiny_font.render(f"{progress_pct}%", True, ACCENT_SILVER)
            screen.blit(pct_text, (SCREEN_WIDTH//2 - 15, SCREEN_HEIGHT//2 + 20))
            
        # Start/stop button (moved up)
        self.start_stop_button.draw(screen)

        # Status panel (moved up)
        status_panel_width = 700
        status_panel_height = 50
        status_panel_x = SCREEN_WIDTH//2 - status_panel_width//2
        status_panel_y = SCREEN_HEIGHT//2 + 120
        
        status_rect = pygame.Rect(status_panel_x, status_panel_y, status_panel_width, status_panel_height)
        pygame.draw.rect(screen, DARK_PANEL, status_rect, border_radius=10)
        pygame.draw.rect(screen, BORDER_COLOR, status_rect, 1, border_radius=10)
        
        # Status text with improved styling
        status_text = ""
        status_color = TEXT_COLOR
        if self.running:
            if self.paused:
                status_text = "PAUSED"
                status_color = PAUSE_YELLOW
                if self.blocking_active:
                    status_text += " • Websites Blocked"
            else:
                status_text = "FOCUSING"
                status_color = SUCCESS_GREEN
                if self.blocking_active:
                    status_text += " • Websites Blocked"
        else:
            if self.timer_input_active:
                status_text = "Editing timer • Press ENTER to save"
                status_color = HIGHLIGHT
            else:
                status_text = "Click timer to edit • Click START to begin"
                status_color = ACCENT_SILVER
                
        status_surf = text_font.render(status_text, True, status_color)
        status_text_rect = status_surf.get_rect(center=status_rect.center)
        screen.blit(status_surf, status_text_rect)
        
        # Draw todo list
        self.todo_list.draw(screen)
        
        # Draw volume controls
        self.volume_controls.draw(screen)
        
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            
            self.update_timer()
            self.draw(screen)
            
            pygame.display.flip()
            clock.tick(60)
        
        self.go_back()


def main():
    import sys
    
    # Check if user_id and username were passed as command line arguments
    if len(sys.argv) >= 3:
        # Called from main.py with user info - use that
        user_id = int(sys.argv[1])
        username = sys.argv[2]
        print(f"Using provided user: {username} (ID: {user_id})")
    else:
        # No arguments provided - show login (shouldn't happen normally)
        import login_screen
        print("No user provided, opening login screen...")
        user_id, username = login_screen.login_screen()
        
        if user_id is None:
            print("Login cancelled")
            pygame.quit()
            sys.exit()
            return
        
        print(f"User logged in: {username} (ID: {user_id})")
    
    # Run the timer with the user
    app = TimerApp(user_id, username)
    app.run()

if __name__ == "__main__":
    main()