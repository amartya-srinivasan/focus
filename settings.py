import pygame
import sys
import json
import os
import subprocess
import threading

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h

# Colors - UNIFIED THEME (matching timer.py and analytics)
BACKGROUND = (25, 25, 50)
PANEL_BG = (40, 40, 80)
DARK_PANEL = (30, 30, 60)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT = (100, 200, 255)
ACCENT_SILVER = (192, 192, 192)
ACCENT_GOLD = (255, 215, 0)
BUTTON_PRIMARY = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_SUCCESS = (80, 180, 120)
BUTTON_DANGER = (255, 100, 100)
INPUT_BG = (40, 40, 60)
BORDER_COLOR = (100, 100, 150)
SHADOW_COLOR = (15, 15, 30)
SUCCESS_GREEN = (100, 200, 150)
ERROR_RED = (255, 100, 100)
WARNING_YELLOW = (255, 200, 0)

# Fonts - consistent with timer
title_font = pygame.font.SysFont('timesnewroman', 72, bold=True)
header_font = pygame.font.SysFont('timesnewroman', 42, bold=True)
subheader_font = pygame.font.SysFont('timesnewroman', 32, bold=True)
text_font = pygame.font.SysFont('timesnewroman', 24)
small_font = pygame.font.SysFont('timesnewroman', 20)
tiny_font = pygame.font.SysFont('timesnewroman', 18)
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

def get_current_user():
    """Get current user from file"""
    try:
        with open("current_user.txt", "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                user_id = int(lines[0].strip())
                username = lines[1].strip()
                return user_id, username
    except:
        pass
    return None, None

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

def get_blocked_sites(user_id):
    """Get user's blocked sites"""
    try:
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT website FROM blocked_sites WHERE user_id = %s ORDER BY website", (user_id,))
            sites = cursor.fetchall()
            cursor.close()
            db.connection.close()
            return [site['website'] for site in sites]
    except Exception as e:
        print(f"Error loading blocked sites: {e}")
    return []

def add_blocked_site(user_id, website):
    """Add a blocked site"""
    try:
        website = website.strip().lower()
        if not website:
            return False, "Website cannot be empty"
        
        # Remove http:// or https://
        website = website.replace('http://', '').replace('https://', '')
        website = website.replace('www.', '')
        
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor()
            
            # Check if already exists
            cursor.execute("SELECT id FROM blocked_sites WHERE user_id = %s AND website = %s", 
                          (user_id, website))
            if cursor.fetchone():
                cursor.close()
                db.connection.close()
                return False, "Website already blocked"
            
            # Try to add site
            try:
                cursor.execute("INSERT INTO blocked_sites (user_id, website) VALUES (%s, %s)", 
                              (user_id, website))
                db.connection.commit()
                cursor.close()
                db.connection.close()
                return True, "Website added successfully"
            except Exception as insert_error:
                error_msg = str(insert_error)
                cursor.close()
                db.connection.close()
                
                # Check for foreign key constraint error
                if "foreign key constraint" in error_msg.lower():
                    return False, f"User ID {user_id} not found in database. Please log in again."
                elif "1452" in error_msg:  # MySQL foreign key error code
                    return False, f"User ID {user_id} not found in database. Please log in again."
                else:
                    return False, f"Error: {error_msg}"
                    
    except Exception as e:
        print(f"Error adding blocked site: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}"
    
    return False, "Could not connect to database"

def remove_blocked_site(user_id, website):
    """Remove a blocked site"""
    try:
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor()
            cursor.execute("DELETE FROM blocked_sites WHERE user_id = %s AND website = %s", 
                          (user_id, website))
            db.connection.commit()
            cursor.close()
            return True, "Website removed successfully"
    except Exception as e:
        print(f"Error removing blocked site: {e}")
        return False, f"Error: {str(e)}"
    
    return False, "Could not connect to database"

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

def draw_input_box(screen, x, y, width, height, text, active, label=""):
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
    
    # Text - only show actual text, no placeholder here
    display_text = text
    if active and text:
        display_text = text + "|"
    elif active and not text:
        display_text = "|"
        
    if display_text:
        text_surface = text_font.render(display_text, True, TEXT_COLOR)
        screen.blit(text_surface, (x + 15, y + 12))

def settings_screen():
    """Main settings screen"""
    # Create screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Focus Timer - Settings")
    
    clock = pygame.time.Clock()
    
    # Get current user
    user_id, username = get_current_user()
    
    if not user_id:
        # No user logged in - redirect to login
        print("No user logged in! Please login first.")
        pygame.quit()
        import login_screen
        result = login_screen.login_screen()
        if result[0]:
            user_id, username = result
            pygame.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Focus Timer - Settings")
        else:
            return
    
    # Verify user exists in database
    try:
        db = get_database_connection()
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            db.connection.close()
            
            if not user_data:
                # User doesn't exist in database anymore
                print(f"User ID {user_id} not found in database!")
                pygame.quit()
                import login_screen
                result = login_screen.login_screen()
                if result[0]:
                    user_id, username = result
                    pygame.init()
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Focus Timer - Settings")
                else:
                    return
    except Exception as e:
        print(f"Error validating user: {e}")
    
    # State
    current_tab = "account"  # account, websites, database, music, about
    
    # Music tab variables
    download_url = ""
    download_url_active = False
    download_status = {"message": ""}  # Use dict so thread can modify it
    blocked_sites = get_blocked_sites(user_id)  # Load at startup, not lazily
    website_input = ""
    website_input_active = False
    message = ""
    message_color = TEXT_COLOR
    all_users_list = []  # For account switching
    user_switch_rects = []  # For click detection
    
    # UI Elements
    back_button = Button(40, 40, 140, 50, "← Back")
    
    # Tab buttons
    tab_y = 150
    tab_width = 200
    tab_height = 60
    tab_spacing = 20
    tab_x_start = SCREEN_WIDTH // 2 - (5 * tab_width + 4 * tab_spacing) // 2
    
    account_tab = Button(tab_x_start, tab_y, tab_width, tab_height, "Account")
    websites_tab = Button(tab_x_start + tab_width + tab_spacing, tab_y, tab_width, tab_height, "Websites")
    database_tab = Button(tab_x_start + 2 * (tab_width + tab_spacing), tab_y, tab_width, tab_height, "Database")
    music_tab = Button(tab_x_start + 3 * (tab_width + tab_spacing), tab_y, tab_width, tab_height, "Music")
    about_tab = Button(tab_x_start + 4 * (tab_width + tab_spacing), tab_y, tab_width, tab_height, "About")
    
    # Content area
    content_y = tab_y + tab_height + 40
    content_width = SCREEN_WIDTH - 200
    content_height = SCREEN_HEIGHT - content_y - 100
    content_x = 100
    
    # Website blocking elements
    website_input_rect = pygame.Rect(content_x + 50, content_y + 100, 400, 50)
    add_website_button = Button(content_x + 470, content_y + 100, 150, 50, "+ Add")
    
    # User management button
    manage_users_button = Button(SCREEN_WIDTH - 220, 40, 180, 50, "Manage Users")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Back button
                if back_button.is_clicked(mouse_pos, event):
                    pygame.quit()
                    subprocess.run([sys.executable, "main.py"])
                    return
                
                # Manage users button
                if manage_users_button.is_clicked(mouse_pos, event):
                    running = False  # Exit the loop first
                    pygame.quit()
                    import user_management
                    user_management.user_management_screen(first_time=False)
                    return
                
                # Tab buttons
                if account_tab.is_clicked(mouse_pos, event):
                    current_tab = "account"
                    message = ""
                    # Load users for account switching
                    all_users_list = get_all_users()
                elif websites_tab.is_clicked(mouse_pos, event):
                    current_tab = "websites"
                    message = ""
                elif database_tab.is_clicked(mouse_pos, event):
                    current_tab = "database"
                    message = ""
                elif music_tab.is_clicked(mouse_pos, event):
                    current_tab = "music"
                    print("MUSIC TAB CLICKED - current_tab is now:", current_tab)
                    message = ""
                elif about_tab.is_clicked(mouse_pos, event):
                    current_tab = "about"
                    message = ""
                
                # Account tab - user switching
                if current_tab == "account" and user_switch_rects:
                    for rect, user in user_switch_rects:
                        if rect.collidepoint(mouse_pos) and user['id'] != user_id:
                            # Switch to this user
                            try:
                                with open("current_user.txt", "w") as f:
                                    f.write(f"{user['id']}\n{user['username']}")
                                print(f"Switched to user: {user['username']}")
                                running = False  # Exit the loop
                            except Exception as e:
                                print(f"Error switching user: {e}")
                                message = "Error switching account"
                                message_color = ERROR_RED
                            break
                
                # Music tab actions
                if current_tab == "music":
                    input_y = content_y + 100
                    input_box = pygame.Rect(content_x + 50, input_y, content_width - 150, 50)
                    download_button = Button(content_x + 50, input_y + 70, 200, 50, "Download", BUTTON_SUCCESS, BUTTON_HOVER)
                    
                    # Input box click
                    if input_box.collidepoint(mouse_pos):
                        download_url_active = True
                    elif not download_button.rect.collidepoint(mouse_pos):
                        download_url_active = False
                    
                    # Download button
                    if download_button.is_clicked(mouse_pos, event):
                        if download_url.strip():
                            download_status["message"] = "Downloading..."
                            
                            def download_song():
                                # Status updates via dict
                                try:
                                    music_folder = os.path.join(os.getcwd(), "downloaded_music")
                                    if not os.path.exists(music_folder):
                                        os.makedirs(music_folder)
                                    
                                    print("="*60)
                                    print(f"DOWNLOADING: {download_url}")
                                    print(f"OUTPUT FOLDER: {music_folder}")
                                    print("="*60)
                                    
                                    # Run without capture_output so we can see real-time progress
                                    result = subprocess.run(
                                        ['spotdl', download_url, '--output', music_folder],
                                        timeout=120
                                    )
                                    
                                    print("="*60)
                                    if result.returncode == 0:
                                        download_status["message"] = "Download successful!"
                                        print("✓ DOWNLOAD COMPLETE!")
                                    else:
                                        download_status["message"] = "Download failed"
                                        print("✗ DOWNLOAD FAILED!")
                                    print("="*60)
                                except subprocess.TimeoutExpired:
                                    download_status["message"] = "Timeout (2 min limit)"
                                    print("✗ DOWNLOAD TIMEOUT!")
                                except Exception as e:
                                    download_status["message"] = "Error downloading"
                                    print(f"✗ ERROR: {e}")
                            
                            thread = threading.Thread(target=download_song, daemon=True)
                            thread.start()
                        else:
                            download_status["message"] = "Enter URL or song name"
                
                # Website blocking tab actions
                if current_tab == "websites":
                    if website_input_rect.collidepoint(mouse_pos):
                        website_input_active = True
                    else:
                        website_input_active = False
                    
                    # Add website button
                    if add_website_button.is_clicked(mouse_pos, event):
                        if website_input:
                            success, msg = add_blocked_site(user_id, website_input)
                            message = msg
                            message_color = SUCCESS_GREEN if success else ERROR_RED
                            if success:
                                website_input = ""
                                blocked_sites = get_blocked_sites(user_id)
                    
                    # Click on remove button
                    list_y = content_y + 200
                    for i, site in enumerate(blocked_sites[:15]):
                        site_rect = pygame.Rect(content_x + 50, list_y + i * 45, content_width - 150, 40)
                        remove_btn = pygame.Rect(site_rect.right + 10, site_rect.y, 60, 40)
                        
                        if remove_btn.collidepoint(mouse_pos):
                            success, msg = remove_blocked_site(user_id, site)
                            message = msg
                            message_color = SUCCESS_GREEN if success else ERROR_RED
                            if success:
                                blocked_sites = get_blocked_sites(user_id)
                            break
                            
            elif event.type == pygame.KEYDOWN:
                # Music tab input
                if current_tab == "music" and download_url_active:
                    if event.key == pygame.K_RETURN:
                        download_url_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        download_url = download_url[:-1]
                    else:
                        if len(download_url) < 200:
                            download_url += event.unicode
                
                # Website tab input
            elif event.type == pygame.KEYDOWN:
                # Music tab input
                if current_tab == "music" and download_url_active:
                    if event.key == pygame.K_RETURN:
                        download_url_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        download_url = download_url[:-1]
                    else:
                        if len(download_url) < 200:
                            download_url += event.unicode
                
                # Website tab input
                elif website_input_active:
                    if event.key == pygame.K_RETURN:
                        if website_input:
                            success, msg = add_blocked_site(user_id, website_input)
                            message = msg
                            message_color = SUCCESS_GREEN if success else ERROR_RED
                            if success:
                                website_input = ""
                                blocked_sites = get_blocked_sites(user_id)
                    elif event.key == pygame.K_BACKSPACE:
                        website_input = website_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        website_input_active = False
                    elif len(website_input) < 100:
                        website_input += event.unicode
        
        # Update hover states
        back_button.check_hover(mouse_pos)
        manage_users_button.check_hover(mouse_pos)
        account_tab.check_hover(mouse_pos)
        websites_tab.check_hover(mouse_pos)
        database_tab.check_hover(mouse_pos)
        music_tab.check_hover(mouse_pos)
        about_tab.check_hover(mouse_pos)
        if current_tab == "websites":
            add_website_button.check_hover(mouse_pos)
        
        # Skip drawing if we're exiting
        if not running:
            continue
        
        # Draw everything
        screen.fill(BACKGROUND)
        
        # Draw header
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 120)
        pygame.draw.rect(screen, DARK_PANEL, header_rect)
        
        # Title
        title = header_font.render("SETTINGS", True, HIGHLIGHT)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 35))
        
        # User info
        user_text = text_font.render(f"Logged in as: {username}", True, ACCENT_SILVER)
        screen.blit(user_text, (SCREEN_WIDTH // 2 - user_text.get_width() // 2, 90))
        
        # Draw buttons
        back_button.draw(screen)
        manage_users_button.draw(screen)
        
        # Draw tabs
        for tab in [account_tab, websites_tab, database_tab, music_tab, about_tab]:
            # Highlight active tab
            if (tab == account_tab and current_tab == "account") or \
               (tab == websites_tab and current_tab == "websites") or \
               (tab == database_tab and current_tab == "database") or \
               (tab == music_tab and current_tab == "music") or \
               (tab == about_tab and current_tab == "about"):
                # Draw active tab with highlight
                pygame.draw.rect(screen, HIGHLIGHT, tab.rect, border_radius=12)
                pygame.draw.rect(screen, BORDER_COLOR, tab.rect, 2, border_radius=12)
                text_surf = button_font.render(tab.text, True, BACKGROUND)
                screen.blit(text_surf, text_surf.get_rect(center=tab.rect.center))
            else:
                tab.draw(screen)
        
        # Draw content panel
        content_panel = pygame.Rect(content_x, content_y, content_width, content_height)
        pygame.draw.rect(screen, PANEL_BG, content_panel, border_radius=15)
        pygame.draw.rect(screen, BORDER_COLOR, content_panel, 2, border_radius=15)
        
        # Draw tab content
        if current_tab == "account":
            # Clear user switch rects for this frame
            user_switch_rects = []
            
            # Account settings
            content_title = subheader_font.render("Account Settings", True, HIGHLIGHT)
            screen.blit(content_title, (content_x + 50, content_y + 30))
            
            y_offset = content_y + 100
            
            # Current account display
            current_label = text_font.render(f"Current Account: {username}", True, TEXT_COLOR)
            screen.blit(current_label, (content_x + 50, y_offset))
            
            y_offset += 60
            
            # User ID
            id_label = text_font.render(f"User ID: {user_id}", True, ACCENT_SILVER)
            screen.blit(id_label, (content_x + 50, y_offset))
            
            y_offset += 100
            
            # Switch account section
            switch_title = text_font.render("Switch Account:", True, TEXT_COLOR)
            screen.blit(switch_title, (content_x + 50, y_offset))
            
            y_offset += 50
            
            # Get all users if not loaded
            if not all_users_list:
                all_users_list = get_all_users()
            
            # Display user buttons for switching
            for i, user in enumerate(all_users_list[:8]):  # Show up to 8 users
                user_y = y_offset + i * 55
                user_rect = pygame.Rect(content_x + 50, user_y, 350, 45)
                
                # Store rect for click detection
                user_switch_rects.append((user_rect, user))
                
                # Highlight current user
                if user['id'] == user_id:
                    pygame.draw.rect(screen, HIGHLIGHT, user_rect, border_radius=10)
                    pygame.draw.rect(screen, BORDER_COLOR, user_rect, 2, border_radius=10)
                    user_text = text_font.render(f"✓ {user['username']} (current)", True, BACKGROUND)
                    screen.blit(user_text, (user_rect.x + 15, user_rect.y + 10))
                else:
                    # Other users - clickable
                    is_hovered = user_rect.collidepoint(mouse_pos)
                    btn_color = BUTTON_HOVER if is_hovered else BUTTON_PRIMARY
                    pygame.draw.rect(screen, btn_color, user_rect, border_radius=10)
                    pygame.draw.rect(screen, BORDER_COLOR, user_rect, 2, border_radius=10)
                    user_text = text_font.render(user['username'], True, TEXT_COLOR)
                    screen.blit(user_text, (user_rect.x + 15, user_rect.y + 10))
            
            # Help text
            if len(all_users_list) > 1:
                help_y = y_offset + len(all_users_list[:8]) * 55 + 30
                help_text = small_font.render("Click on an account to switch", True, ACCENT_SILVER)
                screen.blit(help_text, (content_x + 50, help_y))
            
        elif current_tab == "websites":
            # Website blocking
            content_title = subheader_font.render("Blocked Websites", True, HIGHLIGHT)
            screen.blit(content_title, (content_x + 50, content_y + 30))
            
            # Instructions
            instr = small_font.render("Add websites to block during focus sessions:", True, ACCENT_SILVER)
            screen.blit(instr, (content_x + 50, content_y + 70))
            
            # Input field
            draw_input_box(screen, website_input_rect.x, website_input_rect.y, 
                          website_input_rect.width, website_input_rect.height, 
                          website_input, website_input_active, "")
            
            # Placeholder text only if empty AND not active
            if not website_input and not website_input_active:
                placeholder = text_font.render("e.g., youtube.com", True, ACCENT_SILVER)
                screen.blit(placeholder, (website_input_rect.x + 15, website_input_rect.y + 12))
            
            # Add button
            add_website_button.draw(screen)
            
            # List of blocked sites
            list_y = content_y + 200
            list_title = text_font.render("Currently Blocked:", True, TEXT_COLOR)
            screen.blit(list_title, (content_x + 50, list_y - 40))
            
            if blocked_sites:
                for i, site in enumerate(blocked_sites[:15]):  # Show first 15
                    site_y = list_y + i * 45
                    
                    # Site card
                    site_rect = pygame.Rect(content_x + 50, site_y, content_width - 150, 40)
                    pygame.draw.rect(screen, INPUT_BG, site_rect, border_radius=8)
                    pygame.draw.rect(screen, BORDER_COLOR, site_rect, 1, border_radius=8)
                    
                    # Site name
                    site_text = text_font.render(site, True, TEXT_COLOR)
                    screen.blit(site_text, (site_rect.x + 15, site_rect.y + 8))
                    
                    # Remove button
                    remove_btn = pygame.Rect(site_rect.right + 10, site_rect.y, 60, 40)
                    btn_color = BUTTON_DANGER if remove_btn.collidepoint(mouse_pos) else BUTTON_PRIMARY
                    pygame.draw.rect(screen, btn_color, remove_btn, border_radius=8)
                    remove_text = tiny_font.render("✕", True, TEXT_COLOR)
                    screen.blit(remove_text, (remove_btn.centerx - 6, remove_btn.centery - 8))
            else:
                no_sites = small_font.render("No blocked websites yet", True, ACCENT_SILVER)
                screen.blit(no_sites, (content_x + 50, list_y + 20))
            
            # Message
            if message:
                msg_surf = text_font.render(message, True, message_color)
                screen.blit(msg_surf, (content_x + 50, content_y + content_height - 50))
                
        elif current_tab == "database":
            # Database info
            content_title = subheader_font.render("Database Configuration", True, HIGHLIGHT)
            screen.blit(content_title, (content_x + 50, content_y + 30))
            
            y_offset = content_y + 100
            
            # Load config
            try:
                with open("mysql_config.json", 'r') as f:
                    config = json.load(f)
                
                info_items = [
                    f"Host: {config.get('host', 'N/A')}",
                    f"Database: {config.get('database', 'N/A')}",
                    f"Port: {config.get('port', 'N/A')}",
                    f"User: {config.get('user', 'N/A')}"
                ]
                
                for item in info_items:
                    item_text = text_font.render(item, True, TEXT_COLOR)
                    screen.blit(item_text, (content_x + 50, y_offset))
                    y_offset += 40
                    
            except:
                error_text = text_font.render("Could not load database config", True, ERROR_RED)
                screen.blit(error_text, (content_x + 50, y_offset))
            
            y_offset += 60
            reconfig_text = small_font.render("To reconfigure database, edit mysql_config.json", True, ACCENT_SILVER)
            screen.blit(reconfig_text, (content_x + 50, y_offset))
            
        elif current_tab == "music":
            # Music Downloads
            content_title = subheader_font.render("Music Downloads", True, HIGHLIGHT)
            screen.blit(content_title, (content_x + 50, content_y + 30))
            
            subtitle = small_font.render("Download songs using Spotify/YouTube URL or song name", True, ACCENT_SILVER)
            screen.blit(subtitle, (content_x + 50, content_y + 70))
            
            # Input box
            input_y = content_y + 120
            input_box = pygame.Rect(content_x + 50, input_y, content_width - 150, 50)
            pygame.draw.rect(screen, INPUT_BG if not download_url_active else HIGHLIGHT, input_box, border_radius=10)
            pygame.draw.rect(screen, BORDER_COLOR, input_box, 2, border_radius=10)
            
            # Input text
            if download_url:
                url_text = text_font.render(download_url, True, TEXT_COLOR)
                screen.blit(url_text, (input_box.x + 15, input_box.y + 12))
            elif not download_url_active:
                placeholder = text_font.render("Enter URL or 'Song Name - Artist'", True, ACCENT_SILVER)
                screen.blit(placeholder, (input_box.x + 15, input_box.y + 12))
            
            # Download button
            download_button = Button(content_x + 50, input_y + 70, 200, 50, "Download", BUTTON_SUCCESS, BUTTON_HOVER)
            download_button.draw(screen)
            
            # Folder info
            folder_y = input_y + 130
            folder_label = small_font.render("Download folder:", True, ACCENT_SILVER)
            screen.blit(folder_label, (content_x + 50, folder_y))
            
            music_folder = os.path.join(os.getcwd(), "downloaded_music")
            folder_path = tiny_font.render(music_folder, True, ACCENT_GOLD)
            screen.blit(folder_path, (content_x + 50, folder_y + 30))
            
            # Status message
            if download_status["message"]:
                msg_color = SUCCESS_GREEN if "success" in download_status["message"].lower() else ERROR_RED
                status = text_font.render(download_status["message"], True, msg_color)
                screen.blit(status, (content_x + 50, folder_y + 70))
            
            # Downloaded songs list
            songs_y = folder_y + 150
            songs_title = text_font.render("Downloaded Songs:", True, TEXT_COLOR)
            screen.blit(songs_title, (content_x + 50, songs_y))
            
            # Get list of songs in the music folder
            music_folder = os.path.join(os.getcwd(), "downloaded_music")
            try:
                if os.path.exists(music_folder):
                    songs = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.m4a', '.flac', '.wav'))]
                    songs.sort()
                    
                    if songs:
                        list_y = songs_y + 40
                        for i, song in enumerate(songs[:10]):  # Show first 10 songs
                            song_rect = pygame.Rect(content_x + 50, list_y + i * 35, content_width - 150, 30)
                            pygame.draw.rect(screen, INPUT_BG, song_rect, border_radius=5)
                            pygame.draw.rect(screen, BORDER_COLOR, song_rect, 1, border_radius=5)
                            
                            # Truncate long filenames
                            display_name = song if len(song) < 60 else song[:57] + "..."
                            song_text = tiny_font.render(display_name, True, TEXT_COLOR)
                            screen.blit(song_text, (song_rect.x + 10, song_rect.y + 7))
                        
                        # Show count if more than 10
                        if len(songs) > 10:
                            more_text = tiny_font.render(f"...and {len(songs) - 10} more", True, ACCENT_SILVER)
                            screen.blit(more_text, (content_x + 50, list_y + 10 * 35 + 10))
                    else:
                        no_songs = small_font.render("No songs downloaded yet", True, ACCENT_SILVER)
                        screen.blit(no_songs, (content_x + 50, songs_y + 40))
                else:
                    no_folder = small_font.render("Music folder not found", True, ACCENT_SILVER)
                    screen.blit(no_folder, (content_x + 50, songs_y + 40))
            except Exception as e:
                error_text = tiny_font.render(f"Error loading songs: {str(e)}", True, ERROR_RED)
                screen.blit(error_text, (content_x + 50, songs_y + 40))
        
        elif current_tab == "about":
            # About
            content_title = subheader_font.render("About Focus Timer", True, HIGHLIGHT)
            screen.blit(content_title, (content_x + 50, content_y + 30))
            
            y_offset = content_y + 100
            
            about_lines = [
                "Focus Timer - Productivity Application",
                "Features:",
                "• Pomodoro timer with website blocking",
                "• Task management",
                "• Analytics dashboard",
                "• Multi-user support and Music player integration",
                "Created with Python & Pygame and Developed by:",
                "Amartya Srinivasan",
                "K Shrivathsan",
                "R Vidhyuthram"
            ]
            
            for line in about_lines:
                if line.startswith("•"):
                    line_text = text_font.render(line, True, ACCENT_SILVER)
                elif line in ["Amartya Srinivasan", "K Shrivathsan", "R Vidhyuthram"]:
                    line_text = text_font.render(line, True, ACCENT_GOLD)
                else:
                    line_text = text_font.render(line, True, TEXT_COLOR)
                screen.blit(line_text, (content_x + 50, y_offset))
                y_offset += 35
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    settings_screen()