import pygame
import sys
import json
import os
import hashlib
import subprocess

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Focus Timer - User Management")

# Colors (matching theme)
BACKGROUND = (25, 25, 50)
PANEL_BG = (40, 40, 80)
DARK_PANEL = (30, 30, 60)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT = (100, 200, 255)
ACCENT_SILVER = (192, 192, 192)
BUTTON_PRIMARY = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_SUCCESS = (80, 180, 120)
BUTTON_DANGER = (255, 100, 100)
INPUT_BG = (40, 40, 60)
BORDER_COLOR = (100, 100, 150)
SHADOW_COLOR = (15, 15, 30)
ERROR_RED = (255, 100, 100)
SUCCESS_GREEN = (100, 200, 150)

# Fonts
title_font = pygame.font.SysFont('timesnewroman', 72, bold=True)
header_font = pygame.font.SysFont('timesnewroman', 36, bold=True)
text_font = pygame.font.SysFont('timesnewroman', 24)
small_font = pygame.font.SysFont('timesnewroman', 20)
button_font = pygame.font.SysFont('timesnewroman', 22, bold=True)

def hash_password(password):
    '''Hash password using SHA-256'''
    return hashlib.sha256(password.encode()).hexdigest()

def get_database_connection():
    """Create a database connection"""
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

def create_user(username, password):
    """Create a new user in database with hashed password"""
    try:
        if not username or not password:
            return False, "Username and password cannot be empty"
        
        username = username.strip()
        password = password.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 4:
            return False, "Password must be at least 4 characters"
        
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                db.connection.close()
                return False, "Username already exists"
            
            # Hash password and insert
            try:
                password_hash = hash_password(password)
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                              (username, password_hash))
                db.connection.commit()
                cursor.close()
                db.connection.close()
                return True, "User created successfully!"
            except Exception as e:
                print(f"Failed to create user: {e}")
                cursor.close()
                db.connection.close()
                return False, f"Failed to create user: {str(e)[:200]}"
                
    except Exception as e:
        error_str = str(e)
        print(f"Error creating user: {error_str}")
        import traceback
        traceback.print_exc()
        
        # Provide specific error messages
        if "duplicate" in error_str.lower() or "1062" in error_str:
            return False, f"Username '{username}' already exists!"
        elif "connection" in error_str.lower() or "2003" in error_str:
            return False, "Cannot connect to MySQL. Is it running?"
        elif "access denied" in error_str.lower() or "1045" in error_str:
            return False, "MySQL credentials wrong. Check mysql_config.json"
        elif "database" in error_str.lower() and "doesn't exist" in error_str.lower():
            return False, "Database doesn't exist. Run main.py first to create it."
        else:
            return False, f"Error: {error_str[:80]}"
    
    return False, "Could not connect to database"

def get_all_users():
    """Get all users from database"""
    try:
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            cursor.close()
            db.connection.close()
            return users
    except Exception as e:
        print(f"Error loading users: {e}")
    return []

class Button:
    def __init__(self, x, y, width, height, text, color=BUTTON_PRIMARY, hover_color=BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        
    def draw(self, screen):
        # Shadow
        shadow = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 
                           self.rect.width, self.rect.height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow, border_radius=12)
        
        # Button
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 2, border_radius=12)
        
        # Text
        text_surface = button_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, mouse_pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False

def draw_input_box(screen, x, y, width, height, text, active, label="", is_password=False):
    """Draw an input box with label"""
    # Label
    if label:
        label_surf = text_font.render(label, True, TEXT_COLOR)
        screen.blit(label_surf, (x, y - 35))
    
    # Shadow
    shadow = pygame.Rect(x + 3, y + 3, width, height)
    pygame.draw.rect(screen, SHADOW_COLOR, shadow, border_radius=10)
    
    # Box
    color = HIGHLIGHT if active else INPUT_BG
    pygame.draw.rect(screen, color, (x, y, width, height), border_radius=10)
    pygame.draw.rect(screen, BORDER_COLOR, (x, y, width, height), 2, border_radius=10)
    
    # Text
    if is_password:
        display_text = "•" * len(text)
    else:
        display_text = text
        
    if active:
        display_text += "|"
        
    text_surface = text_font.render(display_text, True, TEXT_COLOR)
    screen.blit(text_surface, (x + 15, y + 12))

def user_management_screen(first_time=False):
    """User management screen for creating/managing users"""
    clock = pygame.time.Clock()
    
    # State
    username_input = ""
    password_input = ""
    username_active = False
    password_active = False
    message = ""
    message_color = TEXT_COLOR
    
    # Cache existing users
    existing_users = get_all_users()
    
    if first_time:
        message = "Welcome! Please create your first user account."
        message_color = HIGHLIGHT
    
    # Input boxes
    input_width = 400
    input_height = 50
    input_x = SCREEN_WIDTH // 2 - input_width // 2
    
    username_y = 300
    password_y = 400
    
    username_rect = pygame.Rect(input_x, username_y, input_width, input_height)
    password_rect = pygame.Rect(input_x, password_y, input_width, input_height)
    
    # Buttons
    create_button = Button(SCREEN_WIDTH // 2 - 110, 500, 220, 55, 
                          "Create User", BUTTON_SUCCESS, BUTTON_HOVER)
    
    # Back button (only if not first time)
    back_button = None
    if not first_time:
        back_button = Button(50, 50, 140, 50, "← Back")
    
    # Continue button (only if users exist)
    continue_button = None
    if existing_users:
        continue_button = Button(SCREEN_WIDTH - 200, 50, 150, 50, "Continue →")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check input clicks
                if username_rect.collidepoint(mouse_pos):
                    username_active = True
                    password_active = False
                elif password_rect.collidepoint(mouse_pos):
                    username_active = False
                    password_active = True
                else:
                    username_active = False
                    password_active = False
                
                # Check create button
                if create_button.is_clicked(mouse_pos, event):
                    success, msg = create_user(username_input, password_input)
                    message = msg
                    message_color = SUCCESS_GREEN if success else ERROR_RED
                    
                    if success:
                        username_input = ""
                        password_input = ""
                        existing_users = get_all_users()
                        if not continue_button and existing_users:
                            continue_button = Button(SCREEN_WIDTH - 200, 50, 150, 50, "Continue →")
                
                # Check back button
                if back_button and back_button.is_clicked(mouse_pos, event):
                    pygame.quit()
                    return "back"
                
                # Check continue button
                if continue_button and continue_button.is_clicked(mouse_pos, event):
                    pygame.quit()
                    subprocess.run([sys.executable, "main.py"])
                    return "continue"
                    
            elif event.type == pygame.KEYDOWN:
                if username_active:
                    if event.key == pygame.K_RETURN:
                        username_active = False
                        password_active = True
                    elif event.key == pygame.K_BACKSPACE:
                        username_input = username_input[:-1]
                    elif event.key == pygame.K_TAB:
                        username_active = False
                        password_active = True
                    elif len(username_input) < 30:
                        username_input += event.unicode
                        
                elif password_active:
                    if event.key == pygame.K_RETURN:
                        success, msg = create_user(username_input, password_input)
                        message = msg
                        message_color = SUCCESS_GREEN if success else ERROR_RED
                        
                        if success:
                            username_input = ""
                            password_input = ""
                            password_active = False
                            existing_users = get_all_users()
                            if not continue_button and existing_users:
                                continue_button = Button(SCREEN_WIDTH - 200, 50, 150, 50, "Continue →")
                    elif event.key == pygame.K_BACKSPACE:
                        password_input = password_input[:-1]
                    elif event.key == pygame.K_TAB:
                        password_active = False
                        username_active = True
                    elif len(password_input) < 30:
                        password_input += event.unicode
        
        # Update hover states
        create_button.check_hover(mouse_pos)
        if back_button:
            back_button.check_hover(mouse_pos)
        if continue_button:
            continue_button.check_hover(mouse_pos)
        
        # Draw everything
        screen.fill(BACKGROUND)
        
        # Draw buttons in header
        if back_button:
            back_button.draw(screen)
        if continue_button:
            continue_button.draw(screen)
        
        # Title
        title_text = title_font.render("USER MANAGEMENT", True, HIGHLIGHT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title_text, title_rect)
        
        # Instruction
        if first_time:
            instruction = header_font.render("Create Your First Account", True, ACCENT_SILVER)
        else:
            instruction = header_font.render("Add New User", True, ACCENT_SILVER)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(instruction, instruction_rect)
        
        # Input boxes
        draw_input_box(screen, input_x, username_y, input_width, input_height, 
                      username_input, username_active, "Username:")
        
        draw_input_box(screen, input_x, password_y, input_width, input_height, 
                      password_input, password_active, "Password:", is_password=True)
        
        # Create button
        create_button.draw(screen)
        
        # Message
        if message:
            message_surf = text_font.render(message, True, message_color)
            message_rect = message_surf.get_rect(center=(SCREEN_WIDTH // 2, 580))
            screen.blit(message_surf, message_rect)
        
        # Existing users list
        if existing_users:
            list_y = 640
            list_title = small_font.render("Existing Users:", True, ACCENT_SILVER)
            screen.blit(list_title, (SCREEN_WIDTH // 2 - 200, list_y))
            
            for i, user in enumerate(existing_users[:5]):
                user_text = small_font.render(f"• {user['username']}", True, TEXT_COLOR)
                screen.blit(user_text, (SCREEN_WIDTH // 2 - 180, list_y + 30 + i * 25))
        
        # Help text
        help_text = small_font.render("Press TAB to switch fields • ENTER to create user", True, ACCENT_SILVER)
        help_rect = help_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(help_text, help_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return None

if __name__ == "__main__":
    result = user_management_screen(first_time=True)
    print(f"Result: {result}")
    pygame.quit()
    sys.exit()