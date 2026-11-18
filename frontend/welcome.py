
import pygame
import subprocess
import sys
from pathlib import Path

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

WIDTH = 960
HEIGHT = 700
FPS = 60

FRONTEND_DIR = Path(__file__).resolve().parent
LOGIN_PATH = FRONTEND_DIR / "login.py"

# Colors - match login.py and register.py
BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)
BUTTON = (51, 65, 85)
SELECTED = (37, 99, 235)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
CYAN = (103, 232, 249)
GREEN = (74, 222, 128)
RED = (248, 113, 113)

# Start button controls
START_KEYS = (
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_5,
    pygame.K_KP5,
    pygame.K_SPACE
)


# ----------------------------------------
# WELCOME SCREEN
# ----------------------------------------

class WelcomeScreen:

    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "IUP Arcade - Welcome"
        )

        self.clock = pygame.time.Clock()

        # Fonts
        self.title_font = pygame.font.SysFont(
            "arial", 72, bold=True
        )

        self.subtitle_font = pygame.font.SysFont(
            "arial", 30, bold=True
        )

        self.font = pygame.font.SysFont(
            "arial", 26, bold=True
        )

        self.small_font = pygame.font.SysFont(
            "arial", 20
        )

        # Program state
        self.running = True
        self.start_requested = False

        self.message = ""
        self.message_color = RED

        # Animation
        self.animation_timer = 0
        self.show_start_text = True

        # Start button
        self.start_button = pygame.Rect(
            WIDTH // 2 - 180,
            400,
            360,
            85
        )

        # Initialize connected USB joysticks
        self.joysticks = []

        for index in range(
            pygame.joystick.get_count()
        ):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks.append(joystick)

    # ------------------------------------
    # DRAW TEXT
    # ------------------------------------

    def draw_text(
        self,
        text,
        font,
        color,
        center
    ):
        surface = font.render(
            text,
            True,
            color
        )

        rect = surface.get_rect(
            center=center
        )

        self.screen.blit(
            surface,
            rect
        )

    # ------------------------------------
    # DRAW BACKGROUND
    # ------------------------------------

    def draw_background(self):
        self.screen.fill(BACKGROUND)

        # Decorative border
        border_rect = pygame.Rect(
            35,
            35,
            WIDTH - 70,
            HEIGHT - 70
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            border_rect,
            3,
            border_radius=15
        )

        # Decorative horizontal lines
        pygame.draw.line(
            self.screen,
            CYAN,
            (130, 230),
            (830, 230),
            2
        )

        pygame.draw.line(
            self.screen,
            CYAN,
            (130, 550),
            (830, 550),
            2
        )

    # ------------------------------------
    # DRAW TITLE
    # ------------------------------------

    def draw_title(self):
        self.draw_text(
            "WELCOME TO",
            self.subtitle_font,
            WHITE,
            (WIDTH // 2, 140)
        )

        self.draw_text(
            "IUP ARCADE",
            self.title_font,
            CYAN,
            (WIDTH // 2, 195)
        )

        self.draw_text(
            "YOUR RETRO GAMING EXPERIENCE",
            self.small_font,
            GRAY,
            (WIDTH // 2, 275)
        )

    # ------------------------------------
    # DRAW START BUTTON
    # ------------------------------------

    def draw_start_button(self):
        # Button background
        pygame.draw.rect(
            self.screen,
            SELECTED,
            self.start_button,
            border_radius=12
        )

        # Button outline
        pygame.draw.rect(
            self.screen,
            CYAN,
            self.start_button,
            3,
            border_radius=12
        )

        # Blinking text
        if self.show_start_text:
            self.draw_text(
                "PRESS START",
                self.subtitle_font,
                WHITE,
                self.start_button.center
            )

    # ------------------------------------
    # DRAW INSTRUCTIONS
    # ------------------------------------

    def draw_instructions(self):
        self.draw_text(
            "Press 5, Enter, or Click to Start",
            self.small_font,
            GRAY,
            (WIDTH // 2, 520)
        )

        self.draw_text(
            "Powered by Raspberry Pi 5",
            self.small_font,
            CYAN,
            (WIDTH // 2, 590)
        )

        self.draw_text(
            "ESC - Exit Arcade",
            self.small_font,
            GRAY,
            (WIDTH // 2, 650)
        )

    # ------------------------------------
    # DRAW SCREEN
    # ------------------------------------

    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_start_button()
        self.draw_instructions()

        if self.message:
            self.draw_text(
                self.message,
                self.small_font,
                self.message_color,
                (WIDTH // 2, 365)
            )

        pygame.display.flip()

    # ------------------------------------
    # ANIMATION
    # ------------------------------------

    def update_animation(self):
        current_time = pygame.time.get_ticks()

        if current_time - self.animation_timer >= 600:
            self.show_start_text = (
                not self.show_start_text
            )

            self.animation_timer = current_time

    # ------------------------------------
    # START ARCADE
    # ------------------------------------

    def start_arcade(self):
        if not LOGIN_PATH.exists():
            self.message = "Error: login.py not found!"
            self.message_color = RED
            return

        self.start_requested = True
        self.running = False

    # ------------------------------------
    # EVENT HANDLING
    # ------------------------------------

    def handle_events(self):
        for event in pygame.event.get():

            # Close window
            if event.type == pygame.QUIT:
                self.running = False

            # Keyboard controls
            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key in START_KEYS:
                    self.start_arcade()

            # Mouse controls
            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if self.start_button.collidepoint(
                        event.pos
                    ):
                        self.start_arcade()

            # USB joystick button
            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button == 0:
                    self.start_arcade()

    # ------------------------------------
    # MAIN LOOP
    # ------------------------------------

    def run(self):
        while self.running:
            self.handle_events()
            self.update_animation()
            self.draw()

            self.clock.tick(FPS)

        pygame.quit()

        # Launch login after closing welcome screen
        if self.start_requested:
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(LOGIN_PATH)
                    ],
                    check=True
                )

            except subprocess.CalledProcessError:
                print(
                    "Error: The login program failed."
                )

            except OSError as error:
                print(
                    f"Could not launch login: {error}"
                )


# ----------------------------------------
# MAIN
# ----------------------------------------

if __name__ == "__main__":
    welcome = WelcomeScreen()
    welcome.run()
    sys.exit(0)

