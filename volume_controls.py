import pygame
import music_player

class VolumeControls:
    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.visible = False
        self.dragging = False
        
        # Volume icon position (top right)
        self.icon_rect = pygame.Rect(screen_width - 50, 20, 30, 30)
        
        # Volume panel (appears when icon clicked)
        self.panel_rect = pygame.Rect(screen_width - 200, 60, 180, 120)
        
        # Slider
        self.slider_rect = pygame.Rect(screen_width - 190, 100, 160, 15)
        self.knob_radius = 10
        self.knob_x = self.slider_rect.x + (music_player.global_music.get_volume() * self.slider_rect.width)
        self.knob_y = self.slider_rect.y + self.slider_rect.height // 2
        
        # Buttons
        self.play_btn = pygame.Rect(screen_width - 190, 130, 50, 30)
        self.pause_btn = pygame.Rect(screen_width - 130, 130, 50, 30)
        self.stop_btn = pygame.Rect(screen_width - 70, 130, 50, 30)
        
        self.font = pygame.font.SysFont('Arial', 12)
        
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
                    
                # Check buttons
                if self.play_btn.collidepoint(mouse_pos):
                    music_player.global_music.play()
                    return True
                elif self.pause_btn.collidepoint(mouse_pos):
                    music_player.global_music.pause()
                    return True
                elif self.stop_btn.collidepoint(mouse_pos):
                    music_player.global_music.stop()
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
            
            # Control buttons
            pygame.draw.rect(screen, (0, 150, 0), self.play_btn, border_radius=3)
            pygame.draw.rect(screen, (200, 150, 0), self.pause_btn, border_radius=3)
            pygame.draw.rect(screen, (150, 0, 0), self.stop_btn, border_radius=3)
            
            # Button text
            play_text = self.font.render("Play", True, (255, 255, 255))
            pause_text = self.font.render("Pause", True, (255, 255, 255))
            stop_text = self.font.render("Stop", True, (255, 255, 255))
            
            screen.blit(play_text, (self.play_btn.x + 10, self.play_btn.y + 8))
            screen.blit(pause_text, (self.pause_btn.x + 5, self.pause_btn.y + 8))
            screen.blit(stop_text, (self.stop_btn.x + 10, self.stop_btn.y + 8))