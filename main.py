import sys
import subprocess
import ctypes
import time
import os
import json

# Flag to skip slow checks on subsequent runs
_FIRST_RUN = not os.path.exists(".app_initialized")

def check_and_install_modules():
    """Check for required modules and install missing ones"""
    if not _FIRST_RUN:
        # Skip module check - already done in this session
        return
    
    required_modules = [
        ('pygame', 'pygame'),
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('PIL', 'pillow'),  # PIL is the module name, pillow is the package
        ('mysql.connector', 'mysql-connector-python')
    ]
    
    missing_modules = []
    
    print("🔍 Checking required modules...")
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name} is installed")
        except ImportError:
            print(f"❌ {module_name} is missing")
            missing_modules.append(package_name)
    
    if missing_modules:
        print(f"\n📦 Installing {len(missing_modules)} missing module(s)...")
        for package in missing_modules:
            try:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ Successfully installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
    else:
        print("✅ All required modules are installed")
    
    print()

# Check and install modules before anything else
check_and_install_modules()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Check if running as admin - but don't exit immediately
if _FIRST_RUN:
    if not is_admin():
        print("⚠️  WARNING: Not running as administrator")
        print("=========================================")
        print("Website blocking may not work properly.")
        print("Some features require admin privileges.")
        print()
        print("The app will start, but website blocking may fail.")
        print("To enable full functionality, run as administrator.")
        print()
        time.sleep(2)  # Give time to read the warning
        admin_warning = True
    else:
        print("✅ Running with administrator privileges")
        print("🌐 Website blocking enabled")
        admin_warning = False
else:
    # On subsequent runs, just check silently
    admin_warning = not is_admin()

# ===== MYSQL CONFIGURATION POPUP WITH PYGAME =====

# Global color constants
BUTTON_PRIMARY = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_DANGER = (200, 60, 60)

def get_mysql_config():
    """Get MySQL configuration with PyGame popup"""
    config_file = "mysql_config.json"
    
    # Check if config file exists
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print("✅ Loaded MySQL configuration from file")
                return config
        except:
            pass
    
    # First time setup - show PyGame popup
    print("Opening MySQL configuration window...")
    
    try:
        import pygame
        import cv2
        import numpy as np
        
        # Initialize PyGame for the popup
        pygame.init()
        
        # Window settings
        POPUP_WIDTH = 600
        POPUP_HEIGHT = 600
        screen = pygame.display.set_mode((POPUP_WIDTH, POPUP_HEIGHT))
        pygame.display.set_caption("MySQL Database Setup")
        
        # Colors for dark mode
        DARK_BG = (20, 20, 30)
        DARK_PANEL = (30, 30, 45)
        TEXT_COLOR = (220, 220, 220)
        HIGHLIGHT = (100, 150, 255)
        BUTTON_COLOR = (50, 100, 180)
        BUTTON_HOVER = (70, 120, 200)
        INPUT_BG = (40, 40, 60)
        INPUT_BORDER = (70, 70, 100)
        
        # Fonts
        title_font = pygame.font.SysFont('Arial', 28, bold=True)
        text_font = pygame.font.SysFont('Arial', 18)
        small_font = pygame.font.SysFont('Arial', 14)
        input_font = pygame.font.SysFont('Arial', 16)
        
        # Load video background
        try:
            video_cap = cv2.VideoCapture('snowfall.mp4')
            video_available = True
        except:
            video_available = False
            print("⚠️  Could not load video background")
        
        def get_video_frame():
            if video_available:
                ret, frame = video_cap.read()
                if not ret:
                    video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = video_cap.read()
                
                if ret:
                    # Crop and resize for square aspect ratio
                    height, width = frame.shape[:2]
                    size = min(height, width)
                    start_x = (width - size) // 2
                    start_y = (height - size) // 2
                    cropped = frame[start_y:start_y+size, start_x:start_x+size]
                    
                    # Resize to popup size
                    resized = cv2.resize(cropped, (POPUP_WIDTH, POPUP_HEIGHT))
                    
                    # Darken the video for better text visibility
                    resized = cv2.addWeighted(resized, 0.3, np.zeros_like(resized), 0.7, 0)
                    
                    # Convert to PyGame surface
                    resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    return pygame.surfarray.make_surface(resized.swapaxes(0, 1))
            return None
        
        # Input fields (database is auto-created as 'focus_app')
        input_fields = [
            {"label": "Host:", "value": "localhost", "type": "text", "active": False, "rect": None},
            {"label": "Username:", "value": "root", "type": "text", "active": False, "rect": None},
            {"label": "Password:", "value": "", "type": "password", "active": False, "rect": None},
            {"label": "Port:", "value": "3306", "type": "number", "active": False, "rect": None}
        ]
        
        # Buttons
        test_button = {"text": "Test Connection", "rect": None, "hover": False}
        save_button = {"text": "Save & Continue", "rect": None, "hover": False}
        
        # Current active input field
        active_field = None
        
        def draw_popup():
            # Get video frame
            video_frame = get_video_frame()
            if video_frame:
                screen.blit(video_frame, (0, 0))
            else:
                screen.fill(DARK_BG)
            
            # Draw semi-transparent overlay
            overlay = pygame.Surface((POPUP_WIDTH, POPUP_HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 20, 30, 200))  # Semi-transparent dark
            screen.blit(overlay, (0, 0))
            
            # Draw title
            title = title_font.render("MySQL Database Setup", True, HIGHLIGHT)
            screen.blit(title, (POPUP_WIDTH//2 - title.get_width()//2, 30))
            
            # Draw description
            desc_lines = [
                "This app needs MySQL to store your study data.",
                "Please enter your MySQL credentials below.",
                "Database 'focus_app' will be created automatically."
            ]
            
            for i, line in enumerate(desc_lines):
                desc = text_font.render(line, True, TEXT_COLOR)
                screen.blit(desc, (POPUP_WIDTH//2 - desc.get_width()//2, 80 + i*25))
            
            # Draw input fields
            field_height = 35
            field_width = 400
            start_y = 180
            
            for i, field in enumerate(input_fields):
                y_pos = start_y + i * (field_height + 15)
                
                # Draw label
                label = text_font.render(field["label"], True, TEXT_COLOR)
                screen.blit(label, (50, y_pos + 8))
                
                # Draw input box
                input_rect = pygame.Rect(200, y_pos, field_width, field_height)
                field["rect"] = input_rect
                
                # Input box background
                box_color = HIGHLIGHT if field["active"] else INPUT_BORDER
                pygame.draw.rect(screen, INPUT_BG, input_rect, border_radius=5)
                pygame.draw.rect(screen, box_color, input_rect, 2, border_radius=5)
                
                # Draw input text
                display_text = field["value"]
                if field["type"] == "password" and field["value"]:
                    display_text = "*" * len(field["value"])
                
                if display_text:
                    text_color = TEXT_COLOR
                else:
                    display_text = "Click to enter..."
                    text_color = (100, 100, 120)
                
                text_surface = input_font.render(display_text, True, text_color)
                text_x = input_rect.x + 10
                screen.blit(text_surface, (text_x, y_pos + 8))
                
                # Draw cursor if active
                if field["active"] and int(pygame.time.get_ticks() / 500) % 2 == 0:
                    cursor_x = text_x + text_surface.get_width()
                    pygame.draw.line(screen, TEXT_COLOR, 
                                   (cursor_x, y_pos + 5), 
                                   (cursor_x, y_pos + field_height - 5), 2)
            
            # Draw buttons
            button_y = start_y + len(input_fields) * (field_height + 15) + 30
            button_width = 180
            button_height = 40
            button_spacing = 30
            
            # Test button
            test_rect = pygame.Rect(POPUP_WIDTH//2 - button_width - button_spacing//2, 
                                  button_y, button_width, button_height)
            test_button["rect"] = test_rect
            
            test_color = BUTTON_HOVER if test_button["hover"] else BUTTON_COLOR
            pygame.draw.rect(screen, test_color, test_rect, border_radius=8)
            pygame.draw.rect(screen, HIGHLIGHT, test_rect, 2, border_radius=8)
            
            test_text = text_font.render(test_button["text"], True, TEXT_COLOR)
            screen.blit(test_text, (test_rect.centerx - test_text.get_width()//2,
                                  test_rect.centery - test_text.get_height()//2))
            
            # Save button
            save_rect = pygame.Rect(POPUP_WIDTH//2 + button_spacing//2, 
                                  button_y, button_width, button_height)
            save_button["rect"] = save_rect
            
            save_color = BUTTON_HOVER if save_button["hover"] else BUTTON_COLOR
            pygame.draw.rect(screen, save_color, save_rect, border_radius=8)
            pygame.draw.rect(screen, HIGHLIGHT, save_rect, 2, border_radius=8)
            
            save_text = text_font.render(save_button["text"], True, TEXT_COLOR)
            screen.blit(save_text, (save_rect.centerx - save_text.get_width()//2,
                                  save_rect.centery - save_text.get_height()//2))
            
            # Draw help text at bottom
            help_text = small_font.render("Press TAB to navigate • Press ENTER to save", True, (150, 150, 150))
            screen.blit(help_text, (POPUP_WIDTH//2 - help_text.get_width()//2, POPUP_HEIGHT - 40))
            
            pygame.display.flip()
        
        def test_mysql_connection():
            """Test MySQL connection"""
            import mysql.connector
            try:
                config = {
                    'host': input_fields[0]['value'],
                    'user': input_fields[1]['value'],
                    'password': input_fields[2]['value'],
                    'port': int(input_fields[3]['value']) if input_fields[3]['value'].isdigit() else 3306,
                    'connection_timeout': 5
                }
                print(f"Testing MySQL connection...")
                conn = mysql.connector.connect(**config)
                conn.close()
                print("Connection successful!")
                return True, "✅ MySQL OK! Database will be created."
            except mysql.connector.Error as e:
                print(f"MySQL error: {e}")
                return False, f"❌ MySQL Error: {str(e)[:100]}"
            except Exception as e:
                print(f"Connection error: {e}")
                return False, f"❌ Error: {str(e)[:100]}"
        
        
        def show_message(message, is_success=True):
            """Show a temporary message"""
            message_color = (100, 200, 100) if is_success else (220, 100, 100)
            
            # Draw semi-transparent overlay
            overlay = pygame.Surface((POPUP_WIDTH, POPUP_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            # Draw message box
            box_width = 500
            box_height = 150
            box_x = (POPUP_WIDTH - box_width) // 2
            box_y = (POPUP_HEIGHT - box_height) // 2
            
            pygame.draw.rect(screen, DARK_PANEL, (box_x, box_y, box_width, box_height), border_radius=10)
            pygame.draw.rect(screen, message_color, (box_x, box_y, box_width, box_height), 2, border_radius=10)
            
            # Draw message text (split into lines if needed)
            words = message.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surface = text_font.render(test_line, True, TEXT_COLOR)
                if test_surface.get_width() < box_width - 40:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw each line
            for i, line in enumerate(lines):
                line_surface = text_font.render(line, True, TEXT_COLOR)
                screen.blit(line_surface, (box_x + (box_width - line_surface.get_width()) // 2,
                                         box_y + 30 + i * 25))
            
            # Draw continue instruction
            continue_text = small_font.render("Click anywhere to continue...", True, (150, 150, 150))
            screen.blit(continue_text, (box_x + (box_width - continue_text.get_width()) // 2,
                                      box_y + box_height - 40))
            
            pygame.display.flip()
            
            # Wait for click
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit(0)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        waiting = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        waiting = False
        
        # Main popup loop
        clock = pygame.time.Clock()
        running = True
        config_saved = False
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Update button hover states
            test_button["hover"] = test_button["rect"] and test_button["rect"].collidepoint(mouse_pos)
            save_button["hover"] = save_button["rect"] and save_button["rect"].collidepoint(mouse_pos)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    config_saved = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check input field clicks
                    clicked_field = None
                    for i, field in enumerate(input_fields):
                        if field["rect"] and field["rect"].collidepoint(mouse_pos):
                            clicked_field = i
                            break
                    
                    if clicked_field is not None:
                        # Activate clicked field
                        for i, field in enumerate(input_fields):
                            field["active"] = (i == clicked_field)
                        active_field = clicked_field
                    
                    # Check button clicks
                    elif test_button["rect"] and test_button["rect"].collidepoint(mouse_pos):
                        success, message = test_mysql_connection()
                        show_message(message, success)
                    
                    elif save_button["rect"] and save_button["rect"].collidepoint(mouse_pos):
                        success, message = test_mysql_connection()
                        if success:
                            # Save configuration
                            config = {
                                'host': input_fields[0]["value"],
                                'user': input_fields[1]["value"],
                                'password': input_fields[2]["value"],
                                'database': 'focus_app',  # Hardcoded
                                'port': int(input_fields[3]["value"]) if input_fields[3]["value"].isdigit() else 3306
                            }
                            
                            try:
                                with open(config_file, 'w') as f:
                                    json.dump(config, f)
                                print("✅ MySQL config saved!")
                                show_message("✅ Configuration saved!\n\nYou can edit mysql_config.json later.", True)
                                config_saved = True
                                running = False
                            except Exception as e:
                                show_message(f"❌ Could not save configuration:\n{e}", False)
                        else:
                            show_message(message, False)
                    
                    else:
                        # Clicked outside - deactivate all fields
                        for field in input_fields:
                            field["active"] = False
                        active_field = None
                
                elif event.type == pygame.KEYDOWN:
                    if active_field is not None:
                        field = input_fields[active_field]
                        
                        if event.key == pygame.K_RETURN:
                            # Move to next field or save
                            if active_field < len(input_fields) - 1:
                                for f in input_fields:
                                    f["active"] = False
                                input_fields[active_field + 1]["active"] = True
                                active_field += 1
                            else:
                                # Last field - trigger save
                                success, message = test_mysql_connection()
                                if success:
                                    config = {
                                        'host': input_fields[0]["value"],
                                        'user': input_fields[1]["value"],
                                        'password': input_fields[2]["value"],
                                        'database': 'focus_app',  # Hardcoded
                                        'port': int(input_fields[3]["value"]) if input_fields[3]["value"].isdigit() else 3306
                                    }
                                    
                                    try:
                                        with open(config_file, 'w') as f:
                                            json.dump(config, f)
                                        print("✅ MySQL config saved!")
                                        config_saved = True
                                        running = False
                                    except Exception as e:
                                        show_message(f"❌ Could not save: {e}", False)
                                else:
                                    show_message(message, False)
                        
                        elif event.key == pygame.K_TAB:
                            # Move to next field
                            for f in input_fields:
                                f["active"] = False
                            next_field = (active_field + 1) % len(input_fields)
                            input_fields[next_field]["active"] = True
                            active_field = next_field
                        
                        elif event.key == pygame.K_BACKSPACE:
                            field["value"] = field["value"][:-1]
                        
                        elif event.key == pygame.K_ESCAPE:
                            for f in input_fields:
                                f["active"] = False
                            active_field = None
                        
                        else:
                            # Regular character input
                            if field["type"] == "number":
                                if event.unicode.isdigit():
                                    field["value"] += event.unicode
                            else:
                                if len(field["value"]) < 50:  # Limit length
                                    field["value"] += event.unicode
            
            draw_popup()
            clock.tick(60)
        
        # Cleanup
        if video_available:
            video_cap.release()
        pygame.quit()
        
        if config_saved and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            print("❌ MySQL configuration was not saved.")
            return None
            
    except Exception as e:
        print(f"❌ Error with PyGame popup: {e}")
        return get_mysql_config_cli()

def get_mysql_config_cli():
    """Fallback to command line if PyGame fails"""
    config_file = "mysql_config.json"
    
    print("\n" + "="*50)
    print("FIRST TIME SETUP - MySQL DATABASE CONFIGURATION")
    print("="*50)
    print("\nThis app uses MySQL to store your study data.")
    print("Please enter your MySQL credentials:")
    print()
    
    host = input("MySQL Host [localhost]: ") or "localhost"
    user = input("MySQL Username [root]: ") or "root"
    password = input("MySQL Password (leave empty if none): ")
    port = input("Port [3306]: ") or "3306"
    
    print("Database 'focus_app' will be created automatically.")
    
    config = {
        'host': host,
        'user': user,
        'password': password,
        'database': 'focus_app',  # Hardcoded
        'port': int(port)
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f)
        print(f"\n✅ Configuration saved to {config_file}")
        return config
    except Exception as e:
        print(f"❌ Could not save configuration: {e}")
        return config

# Get MySQL configuration
mysql_config = get_mysql_config()
if not mysql_config:
    print("❌ Failed to configure MySQL. Exiting.")
    sys.exit(1)

print("\n" + "="*50)
print("Initializing Database...")
print("="*50)

def initialize_database_tables(config):
    '''Create database and tables if they don't exist'''
    if not _FIRST_RUN:
        return True
    
    try:
        import mysql.connector
        
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            port=config.get('port', 3306),
            connect_timeout=10,
            autocommit=True
        )
        cursor = conn.cursor()
        
        print("Creating database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS focus_app")
        print("✅ Database 'focus_app' ready")
        
        cursor.execute("USE focus_app")
        
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Users table ready")
        
        print("Creating blocked_sites table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocked_sites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                website VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ Blocked sites table ready")
        
        print("Creating todos table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                task VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ Todos table ready")
        
        print("Creating study_sessions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                subject VARCHAR(255),
                duration INT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ Study sessions table ready")
        
        print("Closing database connection...")
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        
        print("✅ Database initialization complete!\n")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except:
            pass
        return False

initialize_database_tables(mysql_config)

# Create flag file to skip checks on subsequent runs
if _FIRST_RUN:
    try:
        with open('.app_initialized', 'w') as f:
            f.write('1')
    except:
        pass



print("\n" + "="*50)
print("Starting Focus App...")
print("="*50)

# Now import the rest of the modules
import pygame
import cv2
import mysql.connector

# Import the database module
try:
    from database import Database
    # Pass the config to the Database class
    db = Database(mysql_config)
    print("✅ Database connection established")
except Exception as e:
    print(f"❌ Database error: {e}")
    print("App will run with limited functionality")
    db = None

import music_player

class Button:
    def __init__(self, x, y, width, height, text, color=None, hover_color=None, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color or BUTTON_PRIMARY
        self.hover_color = hover_color or BUTTON_HOVER
        self.text_color = text_color
        self.hovered = False
        
    def draw(self, screen, font):
        current_color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 150), self.rect, 2, border_radius=10)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class ImageButton:
    def __init__(self, x, y, width, height, image_path, hover_image_path=None):
        self.rect = pygame.Rect(x, y, width, height)
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (width, height))
            
            if hover_image_path and os.path.exists(hover_image_path):
                self.hover_image = pygame.image.load(hover_image_path).convert_alpha()
                self.hover_image = pygame.transform.scale(self.hover_image, (width, height))
            else:
                self.hover_image = self.image
        except:
            # Fallback to a simple rectangle if image fails to load
            self.image = pygame.Surface((width, height))
            self.image.fill((100, 100, 100))
            self.hover_image = pygame.Surface((width, height))
            self.hover_image.fill((150, 150, 150))
            
        self.is_hovered = False
        
    def draw(self, screen):
        if self.is_hovered:
            screen.blit(self.hover_image, self.rect)
        else:
            screen.blit(self.image, self.rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
        
    def update_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

class VolumeControls:
    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.visible = False
        self.dragging = False
        
        # Volume icon position (top right)
        self.icon_rect = pygame.Rect(screen_width - 70, 20, 50, 50)
        
        # Volume panel (appears when icon clicked)
        self.panel_rect = pygame.Rect(screen_width - 200, 70, 180, 120)
        
        # Slider
        self.slider_rect = pygame.Rect(screen_width - 190, 100, 160, 15)
        self.knob_radius = 10
        self.knob_x = self.slider_rect.x + (music_player.global_music.get_volume() * self.slider_rect.width)
        self.knob_y = self.slider_rect.y + self.slider_rect.height // 2
        
        # Music control buttons
        self.prev_btn = pygame.Rect(screen_width - 190, 130, 40, 30)
        self.play_pause_btn = pygame.Rect(screen_width - 140, 130, 40, 30)
        self.next_btn = pygame.Rect(screen_width - 90, 130, 40, 30)
        
        # Load PNG icons
        self.load_icons()
        
        self.font = pygame.font.SysFont('Arial', 12)
    
    def load_icons(self):
        """Load and resize PNG icons from assets folder"""
        try:
            # Load and resize icons
            pause_img = pygame.image.load("assets/pause.png").convert_alpha()
            play_img = pygame.image.load("assets/play.png").convert_alpha()
            next_img = pygame.image.load("assets/next.png").convert_alpha()
            previous_img = pygame.image.load("assets/previous.png").convert_alpha()
            
            # Resize to fit buttons (20x20 for 40x30 buttons)
            self.pause_icon = pygame.transform.scale(pause_img, (20, 20))
            self.play_icon = pygame.transform.scale(play_img, (20, 20))
            self.next_icon = pygame.transform.scale(next_img, (20, 20))
            self.previous_icon = pygame.transform.scale(previous_img, (20, 20))
            
        except Exception as e:
            print(f"Error loading icons: {e}")
            # Fallback to text if images fail to load
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
                # Check slider knob
                knob_rect = pygame.Rect(self.knob_x - self.knob_radius, self.knob_y - self.knob_radius,
                                      self.knob_radius * 2, self.knob_radius * 2)
                if knob_rect.collidepoint(mouse_pos):
                    self.dragging = True
                    return True
                    
                # Check music control buttons
                if self.prev_btn.collidepoint(mouse_pos):
                    music_player.global_music.previous_song()
                    return True
                elif self.play_pause_btn.collidepoint(mouse_pos):
                    music_player.global_music.toggle_play_pause()
                    return True
                elif self.next_btn.collidepoint(mouse_pos):
                    music_player.global_music.next_song()
                    return True
                    
                # Click outside panel to close
                if not self.panel_rect.collidepoint(mouse_pos):
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
        # Draw volume icon (always visible)
        pygame.draw.rect(screen, (100, 100, 100), self.icon_rect, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.icon_rect, 2, border_radius=5)
        
        # Volume icon symbol
        icon_font = pygame.font.SysFont('Arial', 20)
        icon_text = icon_font.render("♪", True, (255, 255, 255))
        screen.blit(icon_text, (self.icon_rect.centerx - 6, self.icon_rect.centery - 10))
        
        # Draw volume panel if visible
        if self.visible:
            # Panel background
            pygame.draw.rect(screen, (50, 50, 50), self.panel_rect, border_radius=8)
            pygame.draw.rect(screen, (150, 150, 150), self.panel_rect, 2, border_radius=8)
            
            # Volume text
            volume_text = self.font.render("Volume", True, (255, 255, 255))
            screen.blit(volume_text, (self.panel_rect.x + 10, self.panel_rect.y + 15))
            
            # Volume percentage
            volume_percent = int(music_player.global_music.get_volume() * 100)
            percent_text = self.font.render(f"{volume_percent}%", True, (200, 200, 200))
            screen.blit(percent_text, (self.panel_rect.right - 40, self.panel_rect.y + 15))
            
            # Slider track
            pygame.draw.rect(screen, (100, 100, 100), self.slider_rect)
            pygame.draw.rect(screen, (150, 150, 150), self.slider_rect, 1)
            
            # Slider knob
            pygame.draw.circle(screen, (100, 200, 200), (self.knob_x, self.knob_y), self.knob_radius)
            pygame.draw.circle(screen, (50, 50, 50), (self.knob_x, self.knob_y), self.knob_radius, 2)
            
            # Music control buttons
            pygame.draw.rect(screen, (100, 100, 100), self.prev_btn, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 100), self.play_pause_btn, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 100), self.next_btn, border_radius=3)
            
            # Draw icons or fallback text
            if self.previous_icon:
                screen.blit(self.previous_icon, (self.prev_btn.centerx - 10, self.prev_btn.centery - 10))
            else:
                prev_text = self.font.render("⏮", True, (255, 255, 255))
                screen.blit(prev_text, (self.prev_btn.centerx - 6, self.prev_btn.centery - 6))
            
            if music_player.global_music.is_playing():
                if self.pause_icon:
                    screen.blit(self.pause_icon, (self.play_pause_btn.centerx - 10, self.play_pause_btn.centery - 10))
                else:
                    pause_text = self.font.render("⏸", True, (255, 255, 255))
                    screen.blit(pause_text, (self.play_pause_btn.centerx - 6, self.play_pause_btn.centery - 6))
            else:
                if self.play_icon:
                    screen.blit(self.play_icon, (self.play_pause_btn.centerx - 10, self.play_pause_btn.centery - 10))
                else:
                    play_text = self.font.render("▶", True, (255, 255, 255))
                    screen.blit(play_text, (self.play_pause_btn.centerx - 6, self.play_pause_btn.centery - 6))
            
            if self.next_icon:
                screen.blit(self.next_icon, (self.next_btn.centerx - 10, self.next_btn.centery - 10))
            else:
                next_text = self.font.render("⏭", True, (255, 255, 255))
                screen.blit(next_text, (self.next_btn.centerx - 6, self.next_btn.centery - 6))

def get_current_user():
    """Get current user from file - simple implementation"""
    try:
        with open("current_user.txt", "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                user_id = int(lines[0].strip())
                username = lines[1].strip()
                return user_id, username
    except:
        pass
    return 1, "Default User"  # Fallback to default user

# In the main() function of main.py, remove the settings_button definition and drawing

def main():
    pygame.init()
    screen_width = 1000
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("FOCUS")
    clock = pygame.time.Clock()

    cap = cv2.VideoCapture('snowfall.mp4')
    
    # Volume controls
    volume_controls = VolumeControls(screen_width)
    
    # Add analytics button (top left corner)
    analytics_button = ImageButton(20, 20, 50, 50, 'Leaderboard.png')
    

    
    # Animation variables for smooth transitions
    guy_scale = 1.0  # Current scale for guy image
    guy_target_scale = 1.0  # Target scale
    focus_glow_alpha = 0  # Glow effect alpha
    fade_in_alpha = 0  # Startup fade-in
    
    font_small = pygame.font.Font("font.ttf", 20)

    def get_video_frame():
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (screen_width, screen_height))
            return pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (screen_width, screen_height))
            return pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    guy_image = pygame.image.load('guy.png').convert_alpha()
    guy_image = pygame.transform.scale(guy_image, (310, 310))
    guy_rect = guy_image.get_rect(center=(screen_width//2, screen_height//2 + 150))
    guy_hitbox = pygame.Rect(guy_rect.left, guy_rect.top + 75, guy_rect.width, guy_rect.height - 100)

    font = pygame.font.SysFont('timesnewroman', 175)
    focus_text = font.render("F O C U S", True, (255, 255, 255))
    focus_rect = focus_text.get_rect(center=(screen_width//2, screen_height//2 - 50))

    font_large = pygame.font.SysFont('timesnewroman', 200)
    focus_text_large = font_large.render("F O C U S", True, (255, 255, 255))
    focus_rect_large = focus_text_large.get_rect(center=(screen_width//2, screen_height//2 - 50))

    running = True
    focus_hover = False
    guy_hover = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Handle volume controls first
            if volume_controls.handle_event(event):
                continue
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if analytics_button.is_clicked(event.pos):
                    print("Analytics clicked")
                    pygame.quit()
                    cap.release()
                    try:
                        subprocess.run([sys.executable, "AnalyticsDashboard.py"])
                    except:
                        subprocess.run([sys.executable, "Leaderboard.py"])
                    sys.exit()  # Exit main, analytics will restart main when done
                    
                elif guy_hitbox.collidepoint(event.pos):
                    print("Guy clicked - opening settings")
                    pygame.quit()
                    cap.release()
                    subprocess.run([sys.executable, "settings.py"])
                    sys.exit()  # Exit main, settings will restart main when done
                    
                elif focus_rect.collidepoint(event.pos):
                    print("="*60)
                    print("FOCUS CLICKED")
                    print("="*60)
                    import os
                    print(f"current_user.txt exists: {os.path.exists('current_user.txt')}")
                    user_id, username = get_current_user()
                    print(f"Got user: {username} (ID: {user_id})")
                    pygame.quit()
                    cap.release()
                    subprocess.run([sys.executable, "timer.py", str(user_id), username])
                    sys.exit()  # Exit main, timer will restart main when done

        mouse_pos = pygame.mouse.get_pos()
        focus_hover = focus_rect.collidepoint(mouse_pos)
        guy_hover = guy_hitbox.collidepoint(mouse_pos)
        analytics_button.update_hover(mouse_pos)

        
        # Smooth animations
        guy_target_scale = 1.16 if guy_hover else 1.0
        guy_scale += (guy_target_scale - guy_scale) * 0.3  # Smooth interpolation
        
        focus_glow_alpha = min(255, focus_glow_alpha + 15) if focus_hover else max(0, focus_glow_alpha - 15)
        
        # Fade in on startup
        if fade_in_alpha < 255:
            fade_in_alpha = min(255, fade_in_alpha + 5)
        
        screen.fill((0, 0, 0))
        
        video_frame = get_video_frame()
        screen.blit(video_frame, (0, 0))
        
        # Draw FOCUS text with glow effect on hover
        if focus_glow_alpha > 0:
            # Create glow surface
            glow_surf = focus_text_large.copy()
            glow_surf.set_alpha(focus_glow_alpha // 2)
            screen.blit(glow_surf, focus_rect_large)
        
        if focus_hover:
            screen.blit(focus_text_large, focus_rect_large)
        else:
            screen.blit(focus_text, focus_rect)
        
        # Draw guy with smooth scaling
        current_size = int(310 * guy_scale)
        scaled_guy = pygame.transform.smoothscale(guy_image, (current_size, current_size))
        scaled_rect = scaled_guy.get_rect(center=guy_rect.center)
        screen.blit(scaled_guy, scaled_rect)
            
        # Draw volume controls
        volume_controls.draw(screen)
        
        # Draw analytics button
        analytics_button.draw(screen)
        

        
        # REMOVED: settings_button.draw(screen, font_small)

        # Fade-in overlay
        if fade_in_alpha < 255:
            fade_overlay = pygame.Surface((screen_width, screen_height))
            fade_overlay.fill((0, 0, 0))
            fade_overlay.set_alpha(255 - fade_in_alpha)
            screen.blit(fade_overlay, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)  # Increased to 60 FPS for smoother animations

    pygame.quit()
    cap.release()
    sys.exit()
if __name__ == "__main__":
    import subprocess
    import sys
    import os
    
    print("="*60)
    print("MAIN.PY STARTED")
    print("="*60)
    
    # Check if session_active.flag exists
    # If NO flag = Initial launch from batch file (delete old session, require login)
    # If flag EXISTS = Restart from timer/settings/analytics (keep session)
    
    if not os.path.exists("session_active.flag"):
        # Initial launch - clean up any old session files
        print("Initial launch - clearing old session")
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
            print("✓ Removed old current_user.txt")
        
        # Create flag to indicate session is now active
        with open("session_active.flag", "w") as f:
            f.write("1")
        
        # Open login screen
        subprocess.run([sys.executable, "login_screen.py"])
        
        # Check if user logged in
        if not os.path.exists("current_user.txt"):
            print("Login cancelled. Exiting...")
            # Clean up flag
            if os.path.exists("session_active.flag"):
                os.remove("session_active.flag")
            sys.exit(0)
    else:
        # Restart from timer/settings/analytics - keep session
        print("Restarting from subprocess - keeping session")
        if not os.path.exists("current_user.txt"):
            print("ERROR: Session lost! Requiring login...")
            subprocess.run([sys.executable, "login_screen.py"])
            if not os.path.exists("current_user.txt"):
                print("Login cancelled. Exiting...")
                sys.exit(0)
    
    # User logged in, run main app
    print("DEBUG: About to call main()")
    main()
    print("DEBUG: main() returned")
    
    # Cleanup happens on NEXT launch, not here
    
    # Cleanup happens at startup, not here (in case of Alt+F4, crash, etc.)