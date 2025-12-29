import pygame
import sys
import subprocess
from database import Database
import datetime
import math

# Initialize pygame
pygame.init()

# Screen dimensions - fullscreen for better experience
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Study Analytics Dashboard")

# Colors - matching timer.py theme
BACKGROUND = (25, 25, 50)
PANEL_BG = (40, 40, 80)
DARK_PANEL = (30, 30, 60)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT = (100, 200, 255)
ACCENT_GOLD = (255, 215, 0)
ACCENT_SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
SUCCESS_GREEN = (100, 200, 150)
WARNING_YELLOW = (255, 200, 0)
SHADOW_COLOR = (15, 15, 30)
BORDER_COLOR = (100, 100, 150)
TODO_ITEM_BG = (45, 45, 75)  # For dropdown items

# Fonts
title_font = pygame.font.SysFont('timesnewroman', 60, bold=True)
header_font = pygame.font.SysFont('timesnewroman', 36, bold=True)
text_font = pygame.font.SysFont('timesnewroman', 24)
small_font = pygame.font.SysFont('timesnewroman', 20)
tiny_font = pygame.font.SysFont('timesnewroman', 16)
button_font = pygame.font.SysFont('timesnewroman', 20, bold=True)

# Create database instance
db = Database()

class Button:
    def __init__(self, x, y, width, height, text, color=BUTTON_COLOR, hover_color=BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, screen):
        # Shadow
        shadow = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 
                           self.rect.width, self.rect.height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow, border_radius=12)
        
        # Button
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 2, border_radius=12)
        
        text_surface = button_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
        
    def update_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

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
    return 1, "Default User"

def get_all_users():
    """Get all users from database"""
    try:
        if db and db.connection:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            cursor.close()
            return users
    except Exception as e:
        print(f"Error loading users: {e}")
    return []

def switch_user(user_id, username):
    """Switch to a different user"""
    try:
        with open("current_user.txt", "w") as f:
            f.write(f"{user_id}\n{username}\n")
        return True
    except:
        return False

def format_time(minutes):
    """Format minutes into readable time"""
    if minutes is None:
        return "0m"
    
    minutes = int(minutes)
    if minutes < 60:
        return f"{minutes}m"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {mins}m"

def get_personal_analytics(user_id):
    """Get personal analytics data from database"""
    if db.connection is None:
        print("Database connection not available")
        return None
        
    try:
        analytics = db.get_study_analytics(user_id)
        return analytics
    except Exception as e:
        print(f"Error getting analytics data: {e}")
        return None

def draw_stat_card(screen, x, y, width, height, title, value, subtitle="", icon=""):
    """Draw an improved stat card with shadow and icon"""
    # Shadow
    shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
    pygame.draw.rect(screen, SHADOW_COLOR, shadow_rect, border_radius=12)
    
    # Card background
    card_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, PANEL_BG, card_rect, border_radius=12)
    pygame.draw.rect(screen, BORDER_COLOR, card_rect, 2, border_radius=12)
    
    # Icon (if provided)
    if icon:
        icon_surface = header_font.render(icon, True, HIGHLIGHT)
        screen.blit(icon_surface, (x + 15, y + 15))
        title_x = x + 60
    else:
        title_x = x + 15
    
    # Title
    title_surface = small_font.render(title, True, HIGHLIGHT)
    screen.blit(title_surface, (title_x, y + 20))
    
    # Main value (centered)
    value_surface = header_font.render(str(value), True, TEXT_COLOR)
    value_rect = value_surface.get_rect(center=(x + width//2, y + height//2 + 10))
    screen.blit(value_surface, value_rect)
    
    # Subtitle
    if subtitle:
        subtitle_surface = tiny_font.render(subtitle, True, ACCENT_SILVER)
        screen.blit(subtitle_surface, (x + width//2 - subtitle_surface.get_width()//2, y + height - 25))

def draw_progress_bar(screen, x, y, width, height, progress, color=HIGHLIGHT):
    """Draw a horizontal progress bar"""
    # Background
    bg_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, DARK_PANEL, bg_rect, border_radius=5)
    
    # Fill
    if progress > 0:
        fill_width = int(width * min(progress, 1.0))
        fill_rect = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(screen, color, fill_rect, border_radius=5)
    
    # Border
    pygame.draw.rect(screen, BORDER_COLOR, bg_rect, 1, border_radius=5)

def draw_mini_chart(screen, x, y, width, height, data_points, color=HIGHLIGHT):
    """Draw a simple line chart"""
    if not data_points or len(data_points) < 2:
        return
    
    # Background
    chart_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, DARK_PANEL, chart_rect, border_radius=8)
    
    # Find min/max for scaling
    max_val = max(data_points) if data_points else 1
    min_val = min(data_points) if data_points else 0
    range_val = max_val - min_val if max_val != min_val else 1
    
    # Draw points and lines
    points = []
    for i, val in enumerate(data_points):
        px = x + (i / (len(data_points) - 1)) * width
        py = y + height - ((val - min_val) / range_val) * (height - 20) - 10
        points.append((int(px), int(py)))
    
    # Draw line
    if len(points) > 1:
        pygame.draw.lines(screen, color, False, points, 3)
    
    # Draw points
    for point in points:
        pygame.draw.circle(screen, color, point, 5)
        pygame.draw.circle(screen, TEXT_COLOR, point, 3)

def draw_analytics_dashboard(screen, user_id, username, analytics, all_users=None, show_user_dropdown=False):
    """Draw the enhanced analytics dashboard"""
    screen.fill(BACKGROUND)
    
    # Header section with gradient effect
    header_height = 120
    pygame.draw.rect(screen, DARK_PANEL, (0, 0, SCREEN_WIDTH, header_height))
    
    # Title (moved right to avoid overlap with back button)
    title_text = title_font.render("STUDY ANALYTICS", True, HIGHLIGHT)
    screen.blit(title_text, (200, 25))
    
    # User info (now a dropdown/clickable area)
    user_info_text = f"Student: {username}"
    user_info = text_font.render(user_info_text, True, ACCENT_SILVER)
    user_info_rect = user_info.get_rect(topleft=(200, 85))
    screen.blit(user_info, user_info_rect)
    
    # Dropdown indicator
    dropdown_arrow = tiny_font.render("▼", True, ACCENT_SILVER)
    screen.blit(dropdown_arrow, (user_info_rect.right + 10, 87))
    
    # Store clickable area for user dropdown
    global user_dropdown_rect
    user_dropdown_rect = pygame.Rect(200, 85, user_info_rect.width + 30, 25)
    
    # Draw user dropdown menu if active
    if show_user_dropdown and all_users:
        dropdown_width = 300
        dropdown_height = min(len(all_users) * 40 + 10, 400)
        dropdown_x = 200
        dropdown_y = 115
        
        # Shadow
        shadow_rect = pygame.Rect(dropdown_x + 4, dropdown_y + 4, dropdown_width, dropdown_height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow_rect, border_radius=10)
        
        # Dropdown background
        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height)
        pygame.draw.rect(screen, PANEL_BG, dropdown_rect, border_radius=10)
        pygame.draw.rect(screen, BORDER_COLOR, dropdown_rect, 2, border_radius=10)
        
        # Draw user options
        global user_option_rects
        user_option_rects = []
        
        for i, user in enumerate(all_users[:10]):  # Show max 10 users
            option_y = dropdown_y + 5 + i * 40
            option_rect = pygame.Rect(dropdown_x + 5, option_y, dropdown_width - 10, 35)
            user_option_rects.append((option_rect, user['id'], user['username']))
            
            # Highlight current user or hovered
            if user['id'] == user_id:
                pygame.draw.rect(screen, HIGHLIGHT, option_rect, border_radius=8)
                text_color = BACKGROUND
            else:
                pygame.draw.rect(screen, TODO_ITEM_BG, option_rect, border_radius=8)
                text_color = TEXT_COLOR
            
            # User name
            user_text = small_font.render(user['username'], True, text_color)
            screen.blit(user_text, (option_rect.x + 10, option_rect.y + 8))
    
    # Current date
    date_text = tiny_font.render(datetime.datetime.now().strftime("%B %d, %Y"), True, ACCENT_SILVER)
    screen.blit(date_text, (SCREEN_WIDTH - 200, 90))
    
    if not analytics or not analytics.get('records'):
        # No data state - improved
        no_data_y = SCREEN_HEIGHT // 2 - 100
        
        # Message
        no_data_text = header_font.render("No Study Data Yet", True, TEXT_COLOR)
        screen.blit(no_data_text, (SCREEN_WIDTH//2 - no_data_text.get_width()//2, no_data_y + 20))
        
        instruction = text_font.render("Start using the focus timer to track your study sessions!", True, ACCENT_SILVER)
        screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, no_data_y + 80))
        
        # Tips box
        tips_y = no_data_y + 140
        tips_width = 600
        tips_rect = pygame.Rect(SCREEN_WIDTH//2 - tips_width//2, tips_y, tips_width, 100)
        pygame.draw.rect(screen, PANEL_BG, tips_rect, border_radius=12)
        pygame.draw.rect(screen, BORDER_COLOR, tips_rect, 2, border_radius=12)
        
        tip1 = small_font.render("• Complete study sessions to see analytics", True, TEXT_COLOR)
        tip2 = small_font.render("• Rate your focus to track performance", True, TEXT_COLOR)
        screen.blit(tip1, (SCREEN_WIDTH//2 - tip1.get_width()//2, tips_y + 25))
        screen.blit(tip2, (SCREEN_WIDTH//2 - tip2.get_width()//2, tips_y + 60))
        
        return
    
    # Stats cards section
    cards_y = header_height + 30
    card_width = 280
    card_height = 140
    spacing = 30
    start_x = (SCREEN_WIDTH - (4 * card_width + 3 * spacing)) // 2
    
    # Card 1: Total Study Time
    total_time = analytics['records'].get('total_study_time', 0) or 0
    draw_stat_card(screen, start_x, cards_y, card_width, card_height, 
                   "Total Study Time", format_time(total_time), "All time", "")
    
    # Card 2: Total Sessions
    total_sessions = analytics['records'].get('total_sessions', 0) or 0
    draw_stat_card(screen, start_x + card_width + spacing, cards_y, card_width, card_height, 
                   "Study Sessions", str(total_sessions), "Completed", "")
    
    # Card 3: Average Session
    avg_session = analytics['records'].get('avg_session_length', 0) or 0
    draw_stat_card(screen, start_x + 2*(card_width + spacing), cards_y, card_width, card_height, 
                   "Avg Session", format_time(int(avg_session)), "Per session", "")
    
    # Card 4: Best Focus
    best_focus = analytics['records'].get('best_focus', 0) or 0
    focus_stars = "★" * int(best_focus) if best_focus > 0 else "—"
    draw_stat_card(screen, start_x + 3*(card_width + spacing), cards_y, card_width, card_height, 
                   "Peak Focus", focus_stars, f"{best_focus:.1f}/5" if best_focus > 0 else "Not rated", "")
    
    # Weekly trend section
    trend_y = cards_y + card_height + 40
    
    # Left side - Weekly chart
    chart_section_width = SCREEN_WIDTH // 2 - 60
    
    # Section header
    trend_header = header_font.render("Weekly Trends", True, HIGHLIGHT)
    screen.blit(trend_header, (50, trend_y))
    
    if analytics.get('weekly_data') and len(analytics['weekly_data']) > 0:
        chart_y = trend_y + 60
        chart_height = 250
        
        # Chart background panel
        chart_panel = pygame.Rect(50, chart_y, chart_section_width, chart_height + 80)
        pygame.draw.rect(screen, PANEL_BG, chart_panel, border_radius=12)
        pygame.draw.rect(screen, BORDER_COLOR, chart_panel, 2, border_radius=12)
        
        # Extract data for chart
        weekly_minutes = [week.get('total_minutes', 0) or 0 for week in analytics['weekly_data'][:6]]
        
        # Draw mini chart
        draw_mini_chart(screen, 70, chart_y + 20, chart_section_width - 40, 180, weekly_minutes)
        
        # Labels (moved up to avoid overlap)
        label_y = chart_y + 205
        for i in range(min(6, len(analytics['weekly_data']))):
            label_x = 70 + (i / 5) * (chart_section_width - 40) if len(analytics['weekly_data']) > 1 else chart_section_width // 2
            week_label = tiny_font.render(f"W{analytics['weekly_data'][i]['week']}", True, ACCENT_SILVER)
            screen.blit(week_label, (int(label_x) - 10, label_y))
        
        # Summary stats below chart (with more spacing)
        summary_y = chart_y + 250
        if len(weekly_minutes) > 0:
            avg_weekly = sum(weekly_minutes) / len(weekly_minutes)
            trend_text = tiny_font.render(f"Avg: {format_time(int(avg_weekly))}/week", True, ACCENT_SILVER)
            screen.blit(trend_text, (60, summary_y))
            
            # Trend indicator (moved down)
            if len(weekly_minutes) >= 2:
                if weekly_minutes[-1] > weekly_minutes[-2]:
                    trend_icon = "↗ Improving"
                    trend_color = SUCCESS_GREEN
                elif weekly_minutes[-1] < weekly_minutes[-2]:
                    trend_icon = "↘ Declining"
                    trend_color = WARNING_YELLOW
                else:
                    trend_icon = "→ Stable"
                    trend_color = ACCENT_SILVER
                
                trend_surf = tiny_font.render(trend_icon, True, trend_color)
                screen.blit(trend_surf, (60, summary_y + 22))
    
    # Right side - Completed Tasks
    tasks_x = SCREEN_WIDTH // 2 + 30
    tasks_header = header_font.render("Completed Tasks", True, HIGHLIGHT)
    screen.blit(tasks_header, (tasks_x, trend_y))
    
    # Tasks panel background
    tasks_panel_y = trend_y + 60
    tasks_panel_height = 420
    tasks_panel_width = SCREEN_WIDTH // 2 - 60
    tasks_panel = pygame.Rect(tasks_x, tasks_panel_y, tasks_panel_width, tasks_panel_height)
    
    # Shadow
    tasks_shadow = pygame.Rect(tasks_panel.x + 5, tasks_panel.y + 5, 
                               tasks_panel.width, tasks_panel.height)
    pygame.draw.rect(screen, SHADOW_COLOR, tasks_shadow, border_radius=12)
    
    # Panel background
    pygame.draw.rect(screen, PANEL_BG, tasks_panel, border_radius=12)
    pygame.draw.rect(screen, BORDER_COLOR, tasks_panel, 2, border_radius=12)
    
    # Get tasks from database
    completed_tasks = []
    if db and db.connection:
        try:
            cursor = db.connection.cursor(dictionary=True)
            
            # Try to get tasks with completed_at column
            try:
                query = """
                    SELECT task, completed_at 
                    FROM todos 
                    WHERE user_id = %s 
                    AND completed = 1 
                    ORDER BY id DESC
                    LIMIT 10
                """
                cursor.execute(query, (user_id,))
                completed_tasks = cursor.fetchall()
            except:
                # Fallback if completed_at doesn't exist - just get completed tasks
                query = """
                    SELECT task
                    FROM todos 
                    WHERE user_id = %s 
                    AND completed = 1 
                    ORDER BY id DESC
                    LIMIT 10
                """
                cursor.execute(query, (user_id,))
                completed_tasks = cursor.fetchall()
            
            cursor.close()
            
        except Exception as e:
            print(f"Error loading tasks: {e}")
            completed_tasks = []
    
    # Draw tasks inside panel
    if completed_tasks and len(completed_tasks) > 0:
        tasks_list_y = tasks_panel_y + 20
        
        for i, task_data in enumerate(completed_tasks[:8]):  # Show top 8
            task_y_pos = tasks_list_y + i * 48
            task_width = tasks_panel_width - 30
            
            # Task card
            task_rect = pygame.Rect(tasks_x + 15, task_y_pos, task_width, 40)
            pygame.draw.rect(screen, TODO_ITEM_BG, task_rect, border_radius=8)
            pygame.draw.rect(screen, BORDER_COLOR, task_rect, 1, border_radius=8)
            
            # Checkmark
            check_text = text_font.render("✓", True, SUCCESS_GREEN)
            screen.blit(check_text, (tasks_x + 25, task_y_pos + 8))
            
            # Task name
            task_name = task_data.get('task', 'Unknown task')
            if len(task_name) > 30:
                task_name = task_name[:30] + "..."
            name_surf = small_font.render(task_name, True, TEXT_COLOR)
            screen.blit(name_surf, (tasks_x + 55, task_y_pos + 10))
    else:
        # No completed tasks - centered message
        no_tasks_text = text_font.render("No completed tasks yet", True, ACCENT_SILVER)
        no_tasks_rect = no_tasks_text.get_rect(center=(tasks_panel.centerx, tasks_panel.centery))
        screen.blit(no_tasks_text, no_tasks_rect)
    
    # Best day insight at bottom
    insight_y = SCREEN_HEIGHT - 100
    if analytics.get('best_day') and analytics['best_day'] and analytics['best_day'].get('day_name'):
        insight_width = 700
        insight_rect = pygame.Rect(SCREEN_WIDTH//2 - insight_width//2, insight_y, insight_width, 70)
        
        # Shadow
        shadow = pygame.Rect(insight_rect.x + 4, insight_rect.y + 4, insight_rect.width, insight_rect.height)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow, border_radius=12)
        
        # Background
        pygame.draw.rect(screen, PANEL_BG, insight_rect, border_radius=12)
        pygame.draw.rect(screen, ACCENT_GOLD, insight_rect, 2, border_radius=12)
        
        # Text
        best_day = analytics['best_day']['day_name']
        insight_text = text_font.render(f"Your most productive day: {best_day}", True, ACCENT_GOLD)
        screen.blit(insight_text, (insight_rect.x + 30, insight_rect.y + 15))
        
        tip_text = tiny_font.render("Schedule important study sessions on this day for best results!", True, ACCENT_SILVER)
        screen.blit(tip_text, (insight_rect.x + 30, insight_rect.y + 45))

def main():
    # Get current user
    user_id, username = get_current_user()
    
    # Get all users for dropdown
    all_users = get_all_users()
    
    # Get analytics data
    analytics = get_personal_analytics(user_id)
    
    clock = pygame.time.Clock()
    
    # Create buttons
    back_button = Button(30, 30, 140, 50, "← Back")
    refresh_button = Button(SCREEN_WIDTH - 170, 30, 140, 50, "Refresh")
    
    # Dropdown state
    show_user_dropdown = False
    
    # Global variables for click detection
    global user_dropdown_rect, user_option_rects
    user_dropdown_rect = None
    user_option_rects = []
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.is_clicked(mouse_pos):
                    pygame.quit()
                    try:
                        subprocess.run([sys.executable, "main.py"]); sys.exit()  # Restart main
                    except Exception as e:
                        return
                elif refresh_button.is_clicked(mouse_pos):
                    analytics = get_personal_analytics(user_id)
                    all_users = get_all_users()
                
                # Check user dropdown toggle
                elif user_dropdown_rect and user_dropdown_rect.collidepoint(mouse_pos):
                    show_user_dropdown = not show_user_dropdown
                
                # Check user selection from dropdown
                elif show_user_dropdown and user_option_rects:
                    for rect, uid, uname in user_option_rects:
                        if rect.collidepoint(mouse_pos):
                            if uid != user_id:
                                # Switch user
                                if switch_user(uid, uname):
                                    user_id = uid
                                    username = uname
                                    analytics = get_personal_analytics(user_id)
                            show_user_dropdown = False
                            break
                else:
                    # Click outside dropdown - close it
                    show_user_dropdown = False
        
        # Update button hover states
        back_button.update_hover(mouse_pos)
        refresh_button.update_hover(mouse_pos)
        
        # Draw everything with error handling
        try:
            draw_analytics_dashboard(screen, user_id, username, analytics, all_users, show_user_dropdown)
            back_button.draw(screen)
            refresh_button.draw(screen)
        except Exception as e:
            # If drawing fails, show error message
            screen.fill(BACKGROUND)
            error_title = header_font.render("Error Loading Dashboard", True, WARNING_YELLOW)
            error_msg = text_font.render(str(e), True, TEXT_COLOR)
            screen.blit(error_title, (SCREEN_WIDTH//2 - error_title.get_width()//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(error_msg, (SCREEN_WIDTH//2 - error_msg.get_width()//2, SCREEN_HEIGHT//2))
            back_button.draw(screen)
            print(f"Dashboard error: {e}")
            import traceback
            traceback.print_exc()
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()