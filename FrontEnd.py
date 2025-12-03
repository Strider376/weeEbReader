from PIL import Image, ImageDraw, ImageFont
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
import fitz
from pathlib import Path
import time
import threading
import tkinter as tk
from tkinter import ttk


class EinkReader:
    def __init__(self, vcom=-1.40, use_virtual_buttons=False):
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
        self.use_virtual_buttons = use_virtual_buttons
        if not use_virtual_buttons:
            self._setup_buttons()
    
    def _setup_buttons(self):
        """Initialize GPIO buttons with callbacks"""
        from gpiozero import Button
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
        if self.current_mode == "reading" and self.doc:
            book = self.library.books[self.selected_novel]
            book.current_page = min(book.current_page + 1, self.doc.page_count - 1)
            self.needs_page_redraw = True
            
    def _on_back(self):
        if self.current_mode == "reading":
            book = self.library.books[self.selected_novel]
            book.current_page = max(book.current_page - 1, 0)
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
            try:
                self.doc = fitz.open(book.file_name)
                self.current_mode = "reading"
                self.needs_page_redraw = True
            except Exception as e:
                print(f"Error opening {book.file_name}: {e}")
            
    def _on_menu(self):
        if self.current_mode == "reading":
            self.current_mode = "menu"
            self.needs_menu_redraw = True
    
    def show_splash(self):
        """Display startup logo - use GC16 for quality"""
        self.display.clear()
        
        logo_path = Path(__file__).parent / "weeEbReaderLogo.png"
        
        if logo_path.exists():
            img = Image.open(logo_path).convert('L')
            img = img.resize((1200, 1200), Image.LANCZOS)
            
            x = (self.screen_width - img.width) // 2
            y = (self.screen_height - img.height) // 2
            
            self.display.frame_buf.paste(img, (x, y))
            self.display.draw_full(constants.DisplayModes.GC16)
        else:
            print(f"Logo not found at {logo_path}")
            # Show text splash instead
            img = Image.new('L', (self.screen_width, self.screen_height), 255)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                    size=80
                )
            except:
                font = ImageFont.load_default()
            
            draw.text(
                (self.screen_width // 2 - 300, self.screen_height // 2),
                "weeEbReader",
                fill=0,
                font=font
            )
            self.display.frame_buf.paste(img, (0, 0))
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
            text_x = 150
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
        
        if not self.doc or not (0 <= page_num < self.doc.page_count):
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


class VirtualButtonController:
    """Simulates GPIO buttons using tkinter GUI"""
    def __init__(self, reader_instance):
        self.reader = reader_instance
        self.root = tk.Tk()
        self.root.title("E-ink Reader Virtual Controller")
        self.root.geometry("400x500")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Create the button interface"""
        # Title
        title = ttk.Label(
            self.root, 
            text="Virtual Button Controller",
            font=('Arial', 16, 'bold')
        )
        title.pack(pady=20)
        
        # Navigation buttons frame
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(pady=20)
        
        # Up button
        up_btn = ttk.Button(
            nav_frame,
            text="↑ UP",
            width=15,
            command=self._on_up
        )
        up_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Down button
        down_btn = ttk.Button(
            nav_frame,
            text="↓ DOWN",
            width=15,
            command=self._on_down
        )
        down_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Select button (center)
        select_btn = ttk.Button(
            nav_frame,
            text="⏎ SELECT",
            width=15,
            command=self._on_select
        )
        select_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Page navigation frame
        page_frame = ttk.Frame(self.root)
        page_frame.pack(pady=20)
        
        # Back button
        back_btn = ttk.Button(
            page_frame,
            text="◄ BACK",
            width=15,
            command=self._on_back
        )
        back_btn.pack(side=tk.LEFT, padx=10)
        
        # Forward button
        forward_btn = ttk.Button(
            page_frame,
            text="FORWARD ►",
            width=15,
            command=self._on_forward
        )
        forward_btn.pack(side=tk.LEFT, padx=10)
        
        # Menu button
        menu_btn = ttk.Button(
            self.root,
            text="☰ MENU",
            width=15,
            command=self._on_menu
        )
        menu_btn.pack(pady=20)
        
        # Status display
        self.status_label = ttk.Label(
            self.root,
            text="Mode: menu | Selected: 0",
            font=('Arial', 10),
            relief=tk.SUNKEN
        )
        self.status_label.pack(pady=10, fill=tk.X, padx=20)
        
        # Keyboard bindings
        self.root.bind('<Up>', lambda e: self._on_up())
        self.root.bind('<Down>', lambda e: self._on_down())
        self.root.bind('<Return>', lambda e: self._on_select())
        self.root.bind('<Left>', lambda e: self._on_back())
        self.root.bind('<Right>', lambda e: self._on_forward())
        self.root.bind('<Escape>', lambda e: self._on_menu())
        
        # Update status periodically
        self._update_status()
    
    def _on_up(self):
        """Simulate UP button press"""
        if self.reader.current_mode == "menu":
            self.reader.selected_novel = max(self.reader.selected_novel - 1, 0)
            self.reader.needs_menu_redraw = True
            print("Virtual: UP pressed")
    
    def _on_down(self):
        """Simulate DOWN button press"""
        if self.reader.current_mode == "menu":
            max_index = len(self.reader.library.books) - 1
            self.reader.selected_novel = min(self.reader.selected_novel + 1, max_index)
            self.reader.needs_menu_redraw = True
            print("Virtual: DOWN pressed")
    
    def _on_select(self):
        """Simulate SELECT button press"""
        if self.reader.current_mode == "menu":
            book = self.reader.library.books[self.reader.selected_novel]
            try:
                self.reader.doc = fitz.open(book.file_name)
                self.reader.current_mode = "reading"
                self.reader.needs_page_redraw = True
                print(f"Virtual: SELECT pressed - Opening {book.display_name}")
            except Exception as e:
                print(f"Error opening book: {e}")
    
    def _on_back(self):
        """Simulate BACK button press"""
        if self.reader.current_mode == "reading":
            book = self.reader.library.books[self.reader.selected_novel]
            book.current_page = max(book.current_page - 1, 0)
            self.reader.needs_page_redraw = True
            print(f"Virtual: BACK pressed - Page {book.current_page}")
    
    def _on_forward(self):
        """Simulate FORWARD button press"""
        if self.reader.current_mode == "reading":
            book = self.reader.library.books[self.reader.selected_novel]
            if self.reader.doc:
                book.current_page = min(book.current_page + 1, self.reader.doc.page_count - 1)
                self.reader.needs_page_redraw = True
                print(f"Virtual: FORWARD pressed - Page {book.current_page}")
    
    def _on_menu(self):
        """Simulate MENU button press"""
        if self.reader.current_mode == "reading":
            self.reader.current_mode = "menu"
            self.reader.needs_menu_redraw = True
            print("Virtual: MENU pressed - Returning to menu")
    
    def _update_status(self):
        """Update status display with current reader state"""
        if self.reader.current_mode == "menu":
            status = f"Mode: MENU | Selected: {self.reader.selected_novel}"
        else:
            book = self.reader.library.books[self.reader.selected_novel]
            page_count = self.reader.doc.page_count if self.reader.doc else 0
            status = f"Mode: READING | Page: {book.current_page + 1}/{page_count}"
        
        self.status_label.config(text=status)
        self.root.after(100, self._update_status)  # Update every 100ms
    
    def run(self):
        """Start the tkinter event loop"""
        self.root.mainloop()


if __name__ == "__main__":
    # Set to True to use virtual buttons, False for real GPIO
    USE_VIRTUAL_BUTTONS = True
    
    reader = EinkReader(vcom=-1.40, use_virtual_buttons=USE_VIRTUAL_BUTTONS)
    
    if USE_VIRTUAL_BUTTONS:
        # Run virtual controller in separate thread
        controller = VirtualButtonController(reader)
        reader_thread = threading.Thread(target=reader.run, daemon=True)
        reader_thread.start()
        
        # Run tkinter in main thread (required for GUI)
        controller.run()
    else:
        # Run normally with real buttons
        reader.run()