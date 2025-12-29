import pygame
import sys
import json
import os
import hashlib

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Focus Timer - Login")

# Colors (matching theme)
BACKGROUND = (25, 25, 50)
PANEL_BG = (40, 40, 80)
DARK_PANEL = (30, 30, 60)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT = (100, 200, 255)

def hash_password(password):
    '''Hash password using SHA-256'''
    return hashlib.sha256(password.encode()).hexdigest()
ACCENT_SILVER = (192, 192, 192)
BUTTON_PRIMARY = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_SUCCESS = (80, 180, 120)
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

def get_all_users():
    """Get all users from database"""
    try:
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            cursor.close()
            return users
    except Exception as e:
        print(f"Error loading users: {e}")
    return []

def verify_password(username, password):
    """Verify user password by comparing hashes"""
    try:
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            
            username = username.strip()
            password = password.strip()
            
            # Hash the input password
            input_hash = hash_password(password)
            
            # Get user and stored hash
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            cursor.close()
            db.connection.close()
            
            if not user:
                return None
            
            stored_hash = user.get('password_hash', '').strip()
            
            # Compare hashes
            if stored_hash and stored_hash == input_hash:
                return {'id': user['id'], 'username': user['username']}
            
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None
def save_current_user(user_id, username):
    """Save current user to file"""
    try:
        with open("current_user.txt", "w") as f:
            f.write(f"{user_id}\n{username}\n")
        return True
    except:
        return False

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

class UserButton:
    def __init__(self, x, y, width, height, username, user_id):
        self.rect = pygame.Rect(x, y, width, height)
        self.username = username
        self.user_id = user_id
        self.hovered = False
        self.selected = False
        
    def draw(self, screen):
        # Shadow
        shadow = pygame.Rect(self.rect.x + 3, self.rect.y + 3, 
                           self.rect.width, self.rect.height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow, border_radius=10)
        
        # Background
        if self.selected:
            color = HIGHLIGHT
            text_color = BACKGROUND
        elif self.hovered:
            color = BUTTON_HOVER
            text_color = TEXT_COLOR
        else:
            color = PANEL_BG
            text_color = TEXT_COLOR
            
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 2, border_radius=10)
        
        # Username
        text_surface = text_font.render(self.username, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, mouse_pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False

def draw_input_box(screen, x, y, width, height, text, active, is_password=False):
    """Draw an input box"""
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

def login_screen():
    """Main login screen"""
    global screen  # Declare at the start of the function
    clock = pygame.time.Clock()
    
    # Get all users
    all_users = get_all_users()
    
    if not all_users:
        # No users in database - open user management as subprocess
        print("No users found! Opening user management...")
        pygame.quit()
        import subprocess
        subprocess.run([sys.executable, "user_management.py"])
        
        # After user management, check if users were created
        all_users = get_all_users()
        if not all_users:
            # Still no users, exit
            return None
        
        # Users created, restart login screen
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Focus Timer - Login")
        return login_screen()
    
    # State
    selected_user = None
    password_input = ""
    password_active = False
    error_message = ""
    success_message = ""
    
    # Create user buttons (VERTICAL LAYOUT)
    user_buttons = []
    button_width = 400
    button_height = 55
    spacing_y = 15
    
    start_x = SCREEN_WIDTH // 2 - button_width // 2
    start_y = 280
    
    # Limit to 8 users visible (can add scrolling later if needed)
    max_visible_users = 8
    visible_users = all_users[:max_visible_users]
    
    for i, user in enumerate(visible_users):
        y = start_y + i * (button_height + spacing_y)
        user_buttons.append(UserButton(start_x, y, button_width, button_height, 
                                       user['username'], user['id']))
    
    # Password input box (positioned below user list)
    password_box_width = 400
    password_box_height = 50
    password_box_x = SCREEN_WIDTH // 2 - password_box_width // 2
    
    # Calculate position based on visible users
    num_visible = len(visible_users)
    list_height = num_visible * (button_height + spacing_y)
    password_box_y = start_y + list_height + 40
    
    password_box_rect = pygame.Rect(password_box_x, password_box_y, password_box_width, password_box_height)
    
    # Login button
    login_button = Button(SCREEN_WIDTH // 2 - 100, password_box_y + 80, 200, 55, 
                         "Login", BUTTON_SUCCESS, BUTTON_HOVER)
    
    # Add User button (bottom right)
    add_user_button = Button(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100, 180, 50,
                             "+ Add User", BUTTON_PRIMARY, BUTTON_HOVER)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check user button clicks
                for btn in user_buttons:
                    if btn.is_clicked(mouse_pos, event):
                        selected_user = (btn.user_id, btn.username)
                        # Deselect all, select clicked
                        for b in user_buttons:
                            b.selected = False
                        btn.selected = True
                        error_message = ""
                        success_message = ""
                        
                # Check password box click
                if password_box_rect.collidepoint(mouse_pos):
                    password_active = True
                else:
                    password_active = False
                    
                # Check login button
                if login_button.is_clicked(mouse_pos, event):
                    if selected_user and password_input:
                        user = verify_password(selected_user[1], password_input)
                        if user:
                            # Success!
                            save_current_user(user['id'], user['username'])
                            success_message = "Login successful!"
                            error_message = ""
                            pygame.time.wait(500)
                            return user['id'], user['username']
                        else:
                            error_message = "Incorrect password!"
                            success_message = ""
                    else:
                        error_message = "Please select a user and enter password"
                        success_message = ""
                
                # Check add user button
                if add_user_button.is_clicked(mouse_pos, event):
                    pygame.quit()
                    pygame.quit()
                    import subprocess
                    subprocess.run([sys.executable, "user_management.py"])
                    pygame.init()
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Focus Timer - Login")
                    
                    if result == "continue" or result == "back":
                        # Restart login screen
                        pygame.init()
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        pygame.display.set_caption("Focus Timer - Login")
                        return login_screen()
                    else:
                        return None, None
                        
            elif event.type == pygame.KEYDOWN and password_active:
                if event.key == pygame.K_RETURN:
                    # Try to login
                    if selected_user and password_input:
                        user = verify_password(selected_user[1], password_input)
                        if user:
                            save_current_user(user['id'], user['username'])
                            success_message = "Login successful!"
                            error_message = ""
                            pygame.time.wait(500)
                            return user['id'], user['username']
                        else:
                            error_message = "Incorrect password!"
                            success_message = ""
                elif event.key == pygame.K_BACKSPACE:
                    password_input = password_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    password_active = False
                elif len(password_input) < 30:
                    password_input += event.unicode
        
        # Update hover states
        for btn in user_buttons:
            btn.check_hover(mouse_pos)
        login_button.check_hover(mouse_pos)
        add_user_button.check_hover(mouse_pos)
        
        # Draw everything
        screen.fill(BACKGROUND)
        
        # Title
        title_text = title_font.render("FOCUS TIMER", True, HIGHLIGHT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle = header_font.render("Select Your Account", True, ACCENT_SILVER)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(subtitle, subtitle_rect)
        
        # User buttons
        for btn in user_buttons:
            btn.draw(screen)
        
        # Password label
        if selected_user:
            password_label = text_font.render(f"Password for {selected_user[1]}:", True, TEXT_COLOR)
            screen.blit(password_label, (password_box_x, password_box_y - 35))
            
            # Password input
            draw_input_box(screen, password_box_x, password_box_y, password_box_width, 
                          password_box_height, password_input, password_active, is_password=True)
            
            # Login button
            login_button.draw(screen)
        
        # Error/Success messages
        if error_message:
            error_surf = text_font.render(error_message, True, ERROR_RED)
            error_rect = error_surf.get_rect(center=(SCREEN_WIDTH // 2, password_box_y + 150))
            screen.blit(error_surf, error_rect)
            
        if success_message:
            success_surf = text_font.render(success_message, True, SUCCESS_GREEN)
            success_rect = success_surf.get_rect(center=(SCREEN_WIDTH // 2, password_box_y + 150))
            screen.blit(success_surf, success_rect)
        
        # Instructions
        if not selected_user:
            instruction = small_font.render("Click on your name to continue", True, ACCENT_SILVER)
            instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
            screen.blit(instruction, instruction_rect)
        
        # Add user button
        add_user_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    return None, None

if __name__ == "__main__":
    result = login_screen()
    
    if result and result[0] is not None:
        user_id, username = result
        print(f"Logged in as: {username} (ID: {user_id})")
    
    pygame.quit()
    sys.exit()