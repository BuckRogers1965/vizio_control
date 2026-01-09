#!/usr/bin/env python3
"""
Vizio TV Remote Control GUI
Requires: pygame, requests
Install: pip install pygame requests
"""
import warnings
import os

# 1. Quiet environment warnings immediately
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
import sys
import json
from vizio_control import VizioTV, load_config

# Initialize Pygame
pygame.init()

# Colors
BG_COLOR = (20, 20, 30)
BUTTON_COLOR = (50, 50, 70)
BUTTON_HOVER = (70, 70, 100)
BUTTON_ACTIVE = (90, 90, 130)
TEXT_COLOR = (240, 240, 250)
ACCENT_COLOR = (100, 150, 255)
POWER_ON_COLOR = (80, 200, 120)
POWER_OFF_COLOR = (200, 80, 80)
BORDER_COLOR = (80, 80, 100)

# Screen settings
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Vizio TV Remote")

# Fonts
font_large = pygame.font.Font(None, 32)
font_medium = pygame.font.Font(None, 24)
font_small = pygame.font.Font(None, 20)

class Button:
    def __init__(self, x, y, width, height, text, action, color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.color = color or BUTTON_COLOR
        self.hover = False
        self.active = False
        
    def draw(self, surface):
        color = self.color
        if self.active:
            color = BUTTON_ACTIVE
        elif self.hover:
            color = BUTTON_HOVER
            
        # Draw button with border
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 2, border_radius=8)
        
        # Draw text
        text_surface = font_medium.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.active = False
        return False

class RemoteGUI:
    def __init__(self, tv_ip):
        self.tv_ip = tv_ip
        config = load_config()
        
        if not config.get('ip') or not config.get('auth_token'):
            print("ERROR: No pairing found. Run vizio_control.py first to pair.")
            sys.exit(1)
            
        self.tv = VizioTV(tv_ip, config['auth_token'])
        self.power_state = None
        self.status_message = "Ready"
        self.buttons = []
        self.create_buttons()
        
    def create_buttons(self):
        margin = 10
        btn_width = 80
        btn_height = 50
        small_btn = 60
        
        y_pos = 20
        
        # Power button (centered, larger)
        power_btn = Button(SCREEN_WIDTH//2 + 130, y_pos, 60, 60, "P", 
                          lambda: self.execute_command("toggle"), POWER_OFF_COLOR)
        self.buttons.append(power_btn)
        
        y_pos += 80
        
        # Input/Apps row
        input_btn = Button(margin, y_pos, 110, btn_height, "INPUTS", 
                          lambda: self.show_inputs())
        apps_btn = Button(margin + 120, y_pos, 110, btn_height, "APPS", 
                         lambda: self.show_apps())
        home_btn = Button(margin + 240, y_pos, 110, btn_height, "HOME", 
                         lambda: self.execute_command("home"))
        self.buttons.extend([input_btn, apps_btn, home_btn])
        
        y_pos += btn_height + 20
        
        # D-Pad navigation
        dpad_center_x = SCREEN_WIDTH // 2
        dpad_center_y = y_pos + 60
        
        # Up
        up_btn = Button(dpad_center_x - small_btn//2, dpad_center_y - small_btn - 5, 
                       small_btn, small_btn, "▲", lambda: self.execute_command("up"))
        # Down
        down_btn = Button(dpad_center_x - small_btn//2, dpad_center_y + 5+60, 
                         small_btn, small_btn, "▼", lambda: self.execute_command("down"))
        # Left
        left_btn = Button(dpad_center_x - small_btn - small_btn//2 - 5, dpad_center_y +30 - small_btn//2, 
                         small_btn, small_btn, "◀", lambda: self.execute_command("left"))
        # Right
        right_btn = Button(dpad_center_x + small_btn//2 + 5, dpad_center_y +30 - small_btn//2, 
                          small_btn, small_btn, "▶", lambda: self.execute_command("right"))
        # OK (center)
        ok_btn = Button(dpad_center_x - small_btn//2, dpad_center_y - small_btn//2+30, 
                       small_btn, small_btn, "OK", lambda: self.execute_command("ok"), ACCENT_COLOR)
        
        self.buttons.extend([up_btn, down_btn, left_btn, right_btn, ok_btn])
        
        y_pos = dpad_center_y + small_btn + 80
        
        # Back/Exit/Menu row
        back_btn = Button(margin, y_pos, 80, btn_height, "BACK", 
                         lambda: self.execute_command("back"))
        menu_btn = Button(margin + 90, y_pos, 80, btn_height, "MENU", 
                         lambda: self.execute_command("menu"))
        exit_btn = Button(margin + 180, y_pos, 80, btn_height, "EXIT", 
                         lambda: self.execute_command("exit"))
        info_btn = Button(margin + 270, y_pos, 80, btn_height, "INFO", 
                         lambda: self.execute_command("info"))
        self.buttons.extend([back_btn, menu_btn, exit_btn, info_btn])
        
        y_pos += btn_height + 30
        
        # Volume controls
        vol_label_y = y_pos
        y_pos += 25
        
        vol_down_btn = Button(margin + 20, y_pos, 70, btn_height, "VOL-", 
                             lambda: self.execute_command("vol_down"))
        vol_up_btn = Button(margin + 100, y_pos, 70, btn_height, "VOL+", 
                           lambda: self.execute_command("vol_up"))
        mute_btn = Button(margin + 190, y_pos, 70, btn_height, "MUTE", 
                         lambda: self.execute_command("mute"))
        self.buttons.extend([vol_down_btn, vol_up_btn, mute_btn])
        
        y_pos += 45
        # Channel controls
        ch_down_btn = Button(margin + 20, y_pos + btn_height + 10, 70, btn_height, "CH-", 
                            lambda: self.execute_command("ch_down"))
        ch_up_btn = Button(margin + 100, y_pos + btn_height + 10, 70, btn_height, "CH+", 
                          lambda: self.execute_command("ch_up"))
        
        self.buttons.extend([ch_down_btn, ch_up_btn])
        
        # Store y position for labels
        self.vol_label_y = vol_label_y
        self.ch_label_y = y_pos + btn_height + 10 - 25
        
    def execute_command(self, command):
        """Execute a TV command"""
        import warnings
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        
        try:
            if command == "toggle":
                success = self.tv.power_toggle()
            elif command == "on":
                success = self.tv.power_on()
            elif command == "off":
                success = self.tv.power_off()
            elif command == "vol_up":
                success = self.tv.volume_up()
            elif command == "vol_down":
                success = self.tv.volume_down()
            elif command == "mute":
                success = self.tv.mute()
            elif command == "ch_up":
                success = self.tv.channel_up()
            elif command == "ch_down":
                success = self.tv.channel_down()
            elif command == "up":
                success = self.tv.key_up()
            elif command == "down":
                success = self.tv.key_down()
            elif command == "left":
                success = self.tv.key_left()
            elif command == "right":
                success = self.tv.key_right()
            elif command == "ok":
                success = self.tv.key_ok()
            elif command == "back":
                success = self.tv.key_back()
            elif command == "exit":
                success = self.tv.key_exit()
            elif command == "menu":
                success = self.tv.key_menu()
            elif command == "home":
                success = self.tv.key_home()
            elif command == "info":
                success = self.tv.key_info()
            else:
                success = False
                
            if success:
                self.status_message = f"✓ {command.upper()}"
            else:
                self.status_message = f"✗ Failed: {command}"
                
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            
    def show_inputs(self):
        """Show input selection dialog"""
        try:
            inputs = self.tv.get_inputs_list()
            if inputs:
                self.show_selection_dialog("Select Input", 
                    [(inp.get('CNAME', ''), inp.get('VALUE', {}).get('NAME', '') if isinstance(inp.get('VALUE'), dict) else inp.get('VALUE', '')) 
                     for inp in inputs],
                    lambda name: self.set_input(name))
        except Exception as e:
            self.status_message = f"Error getting inputs: {str(e)}"
            
    def show_apps(self):
        """Show app selection dialog"""
        apps = self.tv.list_available_apps()
        self.show_selection_dialog("Select App", 
            [(app.lower(), app) for app in apps],
            lambda name: self.launch_app(name))
            
    def set_input(self, input_name):
        """Set TV input"""
        try:
            success = self.tv.set_input(input_name)
            if success:
                self.status_message = f"✓ Input: {input_name}"
            else:
                self.status_message = f"✗ Failed to change input"
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            
    def launch_app(self, app_name):
        """Launch app"""
        try:
            success = self.tv.launch_app(app_name)
            if success:
                self.status_message = f"✓ Launched: {app_name}"
            else:
                self.status_message = f"✗ Failed to launch {app_name}"
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            
    def show_selection_dialog(self, title, items, callback):
        """Show a selection dialog"""
        dialog_running = True
        scroll_offset = 0
        item_height = 50
        visible_items = 10
        max_scroll = max(0, len(items) - visible_items)
        
        while dialog_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        dialog_running = False
                    elif event.key == pygame.K_UP:
                        scroll_offset = max(0, scroll_offset - 1)
                    elif event.key == pygame.K_DOWN:
                        scroll_offset = min(max_scroll, scroll_offset + 1)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Check if clicked outside dialog
                    if x < 50 or x > SCREEN_WIDTH - 50 or y < 100 or y > SCREEN_HEIGHT - 50:
                        dialog_running = False
                    else:
                        # Check which item was clicked
                        for i in range(scroll_offset, min(len(items), scroll_offset + visible_items)):
                            item_y = 150 + (i - scroll_offset) * item_height
                            if y >= item_y and y < item_y + item_height - 5:
                                callback(items[i][0])
                                dialog_running = False
                                break
                                
            # Draw dialog
            screen.fill(BG_COLOR)
            
            # Draw semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BG_COLOR)
            screen.blit(overlay, (0, 0))
            
            # Draw dialog box
            dialog_rect = pygame.Rect(50, 100, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200)
            pygame.draw.rect(screen, (40, 40, 60), dialog_rect, border_radius=10)
            pygame.draw.rect(screen, BORDER_COLOR, dialog_rect, 3, border_radius=10)
            
            # Draw title
            title_surface = font_large.render(title, True, TEXT_COLOR)
            screen.blit(title_surface, (70, 120))
            
            # Draw items
            for i in range(scroll_offset, min(len(items), scroll_offset + visible_items)):
                item_y = 150 + (i - scroll_offset) * item_height
                item_rect = pygame.Rect(60, item_y, SCREEN_WIDTH - 120, item_height - 5)
                
                # Check hover
                mouse_pos = pygame.mouse.get_pos()
                if item_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, BUTTON_HOVER, item_rect, border_radius=5)
                else:
                    pygame.draw.rect(screen, BUTTON_COLOR, item_rect, border_radius=5)
                    
                pygame.draw.rect(screen, BORDER_COLOR, item_rect, 1, border_radius=5)
                
                item_text = font_small.render(items[i][1], True, TEXT_COLOR)
                screen.blit(item_text, (70, item_y + 15))
                
            # Draw scroll indicators
            if scroll_offset > 0:
                scroll_text = font_small.render("▲ Scroll Up", True, ACCENT_COLOR)
                screen.blit(scroll_text, (SCREEN_WIDTH // 2 - 50, 155))
                
            if scroll_offset < max_scroll:
                scroll_text = font_small.render("▼ Scroll Down", True, ACCENT_COLOR)
                screen.blit(scroll_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 120))
                
            pygame.display.flip()
            
    def draw(self):
        """Draw the remote interface"""
        screen.fill(BG_COLOR)
        
        # Draw title
        title = font_large.render("Vizio Remote", True, TEXT_COLOR)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 5))
        
        # Draw all buttons
        for button in self.buttons:
            button.draw(screen)
            
        # Draw section labels
        vol_label = font_small.render("VOLUME", True, TEXT_COLOR)
        screen.blit(vol_label, (SCREEN_WIDTH // 2 - vol_label.get_width() // 2, self.vol_label_y))
        
        ch_label = font_small.render("CHANNEL", True, TEXT_COLOR)
        screen.blit(ch_label, (SCREEN_WIDTH // 2 - ch_label.get_width() // 2, self.ch_label_y))
        
        # Draw status message at bottom
        status_surface = font_small.render(self.status_message, True, ACCENT_COLOR)
        screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
        
    def handle_event(self, event):
        """Handle events"""
        for button in self.buttons:
            if button.handle_event(event):
                button.action()
                return True
        return False
        
    def run(self):
        """Main loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
                    
            self.draw()
            clock.tick(60)
            
        pygame.quit()

def main():
    """Main entry point"""

    config = load_config()
    
    if not config.get('ip'):
        if len(sys.argv) < 2:
            print("ERROR: No saved config. Provide IP address.")
            print("Usage: python vizio_remote_gui.py <tv_ip>")
            sys.exit(1)
        tv_ip = sys.argv[1]
    else:
        tv_ip = config['ip']
    
    # Suppress SSL warnings
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    remote = RemoteGUI(tv_ip)
    remote.run()

if __name__ == "__main__":
    main()
