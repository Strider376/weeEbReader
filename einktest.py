"""
E-Ink PDF Reader for Waveshare 7.8" Display
Uses IT8951 controller with GregDMeyer library
"""

import fitz
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button
import time

# IT8951 imports
from IT8951 import constants
from IT8951.display import AutoEPDDisplay

# =============================================================================
# DISPLAY SETUP
# =============================================================================

# Initialize e-ink display
# Check the VCOM value on your display's flexible cable label (e.g., -2.06)
VCOM = -2.06  # UPDATE THIS to match your display!

display = AutoEPDDisplay(vcom=VCOM)

# Native resolution for 7.8" Waveshare
SCREEN_WIDTH = 1404   # Note: width/height might need swapping depending on orientation
SCREEN_HEIGHT = 1872

# Clear display on startup
display.clear()

# =============================================================================
# BUTTON SETUP
# =============================================================================

try:
    forward_button = Button(27)
    back_button = Button(17)
    select_button = Button(22)
    up_button = Button(23)
    down_button = Button(24)
    menu_button = Button(25)
    BUTTONS_AVAILABLE = True
except Exception as e:
    print(f"Button setup failed: {e}")
    BUTTONS_AVAILABLE = False

# =============================================================================
# STATE VARIABLES
# =============================================================================

current_mode = "menu"
menu_redraw = True
needs_redraw = True
selected_novel = 0
doc = None
running = True

BG_COLOR = 255  # White in grayscale (0=black, 255=white)

# =============================================================================
# BOOK DATA
# =============================================================================

class LightNovel:
    def __init__(self, file_name: str, display_name: str, current_page: int = 0):
        self.file_name = file_name
        self.display_name = display_name
        self.current_page = current_page


# Your book library
light_novel_list = [
    LightNovel("Mushoku Tensei - Jobless Reincarnation Volume-1.pdf", "Mushoku Tensei Volume 1"),
    LightNovel("Mushoku Tensei - Jobless Reincarnation Volume-2.pdf", "Mushoku Tensei Volume 2"),
    LightNovel("Mushoku Tensei - Jobless Reincarnation Volume-3.pdf", "Mushoku Tensei Volume 3"),
]

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def update_eink(image, full_refresh=False):
    """
    Push a PIL Image to the e-ink display.
    
    Args:
        image: PIL Image in mode 'L' (grayscale)
        full_refresh: True for quality (GC16), False for speed (DU)
    """
    # Ensure image is grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    # Resize if needed
    if image.size != (SCREEN_WIDTH, SCREEN_HEIGHT):
        image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
    
    # Paste to frame buffer
    display.frame_buf.paste(image, [0, 0])
    
    # Choose refresh mode
    if full_refresh:
        # GC16: Full grayscale, best for text/images, ~450ms
        display.draw_full(constants.DisplayModes.GC16)
    else:
        # DU: Fast 1-bit update, good for menus, ~260ms
        display.draw_partial(constants.DisplayModes.DU)


def show_splash_screen():
    """Display the logo on startup."""
    img = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    
    try:
        logo = Image.open("weeEbReaderLogo.png").convert("L")
        # Center the logo
        x = (SCREEN_WIDTH - logo.width) // 2
        y = (SCREEN_HEIGHT - logo.height) // 4  # Upper portion of screen
        img.paste(logo, (x, y))
    except FileNotFoundError:
        # Draw text if no logo
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        draw.text((SCREEN_WIDTH//4, SCREEN_HEIGHT//3), "E-Reader", fill=0, font=font)
    
    update_eink(img, full_refresh=True)
    time.sleep(1.5)


def draw_menu():
    """Draw the book selection menu."""
    img = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
    
    # Draw header
    draw.text((SCREEN_WIDTH//2 - 150, 80), "Library", fill=0, font=header_font)
    
    # Draw book list
    y_pos = 250
    box_width = 900
    box_height = 100
    x_start = (SCREEN_WIDTH - box_width) // 2
    
    for i, book in enumerate(light_novel_list):
        # Highlight selected book
        if i == selected_novel:
            fill_color = 180  # Light gray for selection
        else:
            fill_color = 255  # White
        
        # Draw box
        draw.rectangle(
            [(x_start, y_pos), (x_start + box_width, y_pos + box_height)],
            fill=fill_color,
            outline=0,
            width=3
        )
        
        # Draw book title (centered in box)
        text_x = x_start + 30
        text_y = y_pos + (box_height - 35) // 2
        draw.text((text_x, text_y), book.display_name, fill=0, font=title_font)
        
        # Show current page if book has been read
        if book.current_page > 0:
            page_text = f"Page {book.current_page}"
            draw.text((x_start + box_width - 150, text_y), page_text, fill=80, font=title_font)
        
        y_pos += 150
    
    # Draw navigation hints at bottom
    hint_font = title_font
    draw.text((50, SCREEN_HEIGHT - 100), "UP/DOWN: Navigate  |  SELECT: Open  |  MENU: Back", 
              fill=100, font=hint_font)
    
    update_eink(img, full_refresh=False)


def display_pdf_page():
    """Render and display the current PDF page."""
    global doc
    
    current_book = light_novel_list[selected_novel]
    page_num = current_book.current_page
    
    if doc is None or page_num >= doc.page_count:
        return
    
    # Render page
    page = doc[page_num]
    
    # Calculate zoom for best fit
    zoom = min(SCREEN_WIDTH / page.rect.width, SCREEN_HEIGHT / page.rect.height)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Convert to PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img = img.convert("L")  # Convert to grayscale
    
    # Create canvas and center the page
    canvas = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), BG_COLOR)
    x = (SCREEN_WIDTH - img.width) // 2
    y = (SCREEN_HEIGHT - img.height) // 2
    canvas.paste(img, (x, y))
    
    # Full refresh for best text quality
    update_eink(canvas, full_refresh=True)
    
    print(f"Displaying page {page_num + 1}/{doc.page_count}")


# =============================================================================
# NAVIGATION FUNCTIONS
# =============================================================================

def to_menu():
    global menu_redraw, current_mode
    current_mode = "menu"
    menu_redraw = True
    print("Returning to menu")


def page_forward():
    global needs_redraw
    if current_mode != "reading":
        return
    current_book = light_novel_list[selected_novel]
    current_book.current_page = min(current_book.current_page + 1, doc.page_count - 1)
    needs_redraw = True
    print(f"Forward to page {current_book.current_page + 1}")


def page_back():
    global needs_redraw
    if current_mode != "reading":
        return
    current_book = light_novel_list[selected_novel]
    current_book.current_page = max(current_book.current_page - 1, 0)
    needs_redraw = True
    print(f"Back to page {current_book.current_page + 1}")


def select_book():
    global doc, current_mode, needs_redraw
    if current_mode != "menu":
        return
    book = light_novel_list[selected_novel]
    try:
        doc = fitz.open(book.file_name)
        current_mode = "reading"
        needs_redraw = True
        print(f"Opened: {book.display_name}")
    except Exception as e:
        print(f"Error opening {book.file_name}: {e}")


def menu_up():
    global menu_redraw, selected_novel
    if current_mode != "menu":
        return
    selected_novel = max(selected_novel - 1, 0)
    menu_redraw = True
    print(f"Selected: {light_novel_list[selected_novel].display_name}")


def menu_down():
    global menu_redraw, selected_novel
    if current_mode != "menu":
        return
    selected_novel = min(selected_novel + 1, len(light_novel_list) - 1)
    menu_redraw = True
    print(f"Selected: {light_novel_list[selected_novel].display_name}")


# =============================================================================
# BUTTON CALLBACKS
# =============================================================================

if BUTTONS_AVAILABLE:
    forward_button.when_activated = page_forward
    back_button.when_activated = page_back
    up_button.when_activated = menu_up
    down_button.when_activated = menu_down
    select_button.when_activated = select_book
    menu_button.when_activated = to_menu
    print("All buttons configured")

# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    global running, menu_redraw, needs_redraw
    
    print("Starting E-Ink Reader...")
    print(f"Display: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"VCOM: {VCOM}")
    
    # Show splash screen
    show_splash_screen()
    
    # Initial menu draw
    draw_menu()
    menu_redraw = False
    
    print("Ready! Use buttons to navigate.")
    print("Press Ctrl+C to exit.")
    
    try:
        while running:
            # Handle menu mode
            if current_mode == "menu" and menu_redraw:
                draw_menu()
                menu_redraw = False
            
            # Handle reading mode
            elif current_mode == "reading" and needs_redraw:
                display_pdf_page()
                needs_redraw = False
            
            # E-ink doesn't need fast polling
            # Sleep to reduce CPU usage
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clear display on exit (optional)
        display.clear()
        print("Goodbye!")


if __name__ == "__main__":
    main()