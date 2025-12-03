from PIL import Image, ImageDraw, ImageFont
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
import fitz
from pathlib import Path
from gpiozero import Button
import time
import threading

class EinkReader:
    def __init__(self, vcom=-1.40):
        # Display initialization
        self.display = AutoEPDDisplay(vcom=vcom, rotate='CW')
        self.screen_width = self.display.width
        self.screen_height = self.display.height
        
        # State management
        self.current_mode = "menu"
        self.selected_novel = 0
        self.doc = None
        self.running = True
        
        # Flags for thread-safe updates
        self.needs_menu_redraw = True
        self.needs_page_redraw = False
        
        # Books library
        self.library = BookLibrary()
        
        # Button setup
        self._setup_buttons()
        
    def _setup_buttons(self):
        """Initialize GPIO buttons with callbacks"""
        try:
            self.forward_button = Button(27)
            self.back_button = Button(17)
            self.select_button = Button(22)
            self.up_button = Button(23)
            self.down_button = Button(24)
            self.menu_button = Button(25)
            
            # Assign callbacks
            self.forward_button.when_activated = self._on_forward
            self.back_button.when_activated = self._on_back
            self.up_button.when_activated = self._on_up
            self.down_button.when_activated = self._on_down
            self.select_button.when_activated = self._on_select
            self.menu_button.when_activated = self._on_menu
            
            print("All buttons configured")
        except Exception as e:
            print(f"Button setup failed: {e}")
    
    # Button callbacks - these run in GPIO threads
    def _on_forward(self):
        if self.current_mode == "reading":
            self.needs_page_redraw = True
            
    def _on_back(self):
        if self.current_mode == "reading":
            self.needs_page_redraw = True
            
    def _on_up(self):
        if self.current_mode == "menu":
            self.selected_novel = max(self.selected_novel - 1, 0)
            self.needs_menu_redraw = True
            
    def _on_down(self):
        if self.current_mode == "menu":
            max_index = len(self.library.books) - 1
            self.selected_novel = min(self.selected_novel + 1, max_index)
            self.needs_menu_redraw = True
            
    def _on_select(self):
        if self.current_mode == "menu":
            book = self.library.books[self.selected_novel]
            self.doc = fitz.open(book.file_name)
            self.current_mode = "reading"
            self.needs_page_redraw = True
            
    def _on_menu(self):
        if self.current_mode == "reading":
            self.current_mode = "menu"
            self.needs_menu_redraw = True
    
    def show_splash(self):
        """Display startup logo - use GC16 for quality"""
        self.display.clear()
        
        logo_path = Path(__file__).parent / "weeEbReaderLogo.png"
        img = Image.open(logo_path).convert('L')
        img = img.resize((1200, 1200), Image.LANCZOS)
        
        x = (self.screen_width - img.width) // 2
        y = (self.screen_height - img.height) // 2
        
        self.display.frame_buf.paste(img, (x, y))
        self.display.draw_full(constants.DisplayModes.GC16)
        
        time.sleep(2)
    
    def draw_menu(self):
        """Draw menu screen - use DU mode for fast navigation"""
        img = Image.new('L', (self.screen_width, self.screen_height), 255)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                size=35
            )
        except:
            font = ImageFont.load_default()
        
        y_pos = 200
        for i, book in enumerate(self.library.books):
            # Highlight selected book with gray fill
            fill = 200 if i == self.selected_novel else 255
            
            draw.rectangle(
                [(50, y_pos), (self.screen_width - 50, y_pos + 100)],
                fill=fill,
                outline=0,
                width=3
            )
            
            # Center text in rectangle
            text_x = (self.screen_width - 100) // 2 - 100
            draw.text(
                (text_x, y_pos + 30),
                book.display_name,
                fill=0,
                font=font
            )
            
            y_pos += 150
        
        # Update display - DU mode for fast menu navigation
        self.display.frame_buf.paste(img, (0, 0))
        self.display.draw_partial(constants.DisplayModes.DU)
    
    def draw_page(self):
        """Render current PDF page - use GC16 for text quality"""
        book = self.library.books[self.selected_novel]
        page_num = book.current_page
        
        if not (0 <= page_num < self.doc.page_count):
            return
        
        # Render PDF page
        page = self.doc[page_num]
        pix = page.get_pixmap()
        
        # Convert to PIL Image and grayscale
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.convert('L')
        
        # Scale to fit screen
        width_scale = self.screen_width / pix.width
        height_scale = self.screen_height / pix.height
        scale = min(width_scale, height_scale)
        
        new_width = int(pix.width * scale)
        new_height = int(pix.height * scale)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Center on screen
        x = (self.screen_width - new_width) // 2
        y = (self.screen_height - new_height) // 2
        
        # Clear frame buffer and paste image
        self.display.frame_buf.paste(255, (0, 0, self.screen_width, self.screen_height))
        self.display.frame_buf.paste(img, (x, y))
        
        # GC16 mode for high-quality text rendering
        self.display.draw_full(constants.DisplayModes.GC16)
    
    def run(self):
        """Main event loop"""
        self.show_splash()
        
        while self.running:
            if self.current_mode == "menu" and self.needs_menu_redraw:
                self.draw_menu()
                self.needs_menu_redraw = False
                
            elif self.current_mode == "reading" and self.needs_page_redraw:
                self.draw_page()
                self.needs_page_redraw = False
            
            time.sleep(0.05)  # Small sleep to prevent CPU spinning


class BookLibrary:
    """Manages the collection of books"""
    def __init__(self):
        self.books = [
            LightNovel(
                "Mushoku Tensei - Jobless Reincarnation Volume-1.pdf",
                "Mushoku Tensei Volume 1",
                0
            ),
            LightNovel(
                "Mushoku Tensei - Jobless Reincarnation Volume-2.pdf",
                "Mushoku Tensei Volume 2",
                0
            ),
            LightNovel(
                "Mushoku Tensei - Jobless Reincarnation Volume-3.pdf",
                "Mushoku Tensei Volume 3",
                0
            ),
        ]


class LightNovel:
    """Represents a single book with its state"""
    def __init__(self, file_name: str, display_name: str, current_page: int):
        self.file_name = file_name
        self.display_name = display_name
        self.current_page = current_page


if __name__ == "__main__":
    reader = EinkReader(vcom=-1.40)
    reader.run()