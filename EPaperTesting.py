from PIL import Image
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
import fitz
from gpiozero import Button
import time

# Initialize display
display = AutoEPDDisplay(vcom=-1.40, rotate='CW')
screen_width = display.width
screen_height = display.height

# Initialize buttons
try:
    forward_button = Button(5)
    back_button = Button(6)
    print("Buttons initialized successfully")
except Exception as e:
    print(f"Button setup failed: {e}")

# PDF setup
current_page = 0
doc = fitz.open("Mushoku Tensei - Jobless Reincarnation Volume-1.pdf")
needs_redraw = True

def display_pdf_page():
    global current_page
    
    if 0 <= current_page < doc.page_count:
        page = doc[current_page]
        pix = page.get_pixmap(colorspace=fitz.csGRAY)
        img = Image.frombytes('L', [pix.width, pix.height], pix.samples)
        
        # Scale to fit screen
        width_scale = screen_width / pix.width
        height_scale = screen_height / pix.height
        scale = min(width_scale, height_scale)
        new_width = int(pix.width * scale)
        new_height = int(pix.height * scale)
        img = img.resize((new_width, new_height), resample=Image.LANCZOS)
        
        # Center on canvas
        canvas = Image.new('L', (screen_width, screen_height), 255)
        x = (screen_width - img.width) // 2
        y = (screen_height - img.height) // 2
        canvas.paste(img, (x, y))
        
        # Update display
        display.frame_buf.paste(canvas, (0, 0))
        display.draw_full(constants.DisplayModes.GC16)
        print(f"Displayed page {current_page + 1} of {doc.page_count}")

def page_forward():
    global current_page, needs_redraw
    if current_page < doc.page_count - 1:
        current_page += 1
        needs_redraw = True
        print(f"Forward to page {current_page + 1}")

def page_back():
    global current_page, needs_redraw
    if current_page > 0:
        current_page -= 1
        needs_redraw = True
        print(f"Back to page {current_page + 1}")

# Assign button callbacks
forward_button.when_activated = page_forward
back_button.when_activated = page_back

# Display initial page
print("Loading first page...")
display_pdf_page()
needs_redraw = False

print("\nReady! Use buttons to navigate.")
print("Forward button (GPIO 5) = Next page")
print("Back button (GPIO 6) = Previous page")
print("Press Ctrl+C to exit\n")

# Main loop - checks for page changes
try:
    while True:
        if needs_redraw:
            display_pdf_page()
            needs_redraw = False
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nExiting...")
    doc.close()