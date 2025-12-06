from PIL import Image, ImageDraw, ImageFont
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
import fitz
import sys
from pathlib import Path
from gpiozero import Button
import time

display = AutoEPDDisplay(vcom=-1.40, rotate='CW')

screen_width = display.width
screen_height = display.height

try:
    forward_button = Button(27)
    back_button = Button(17)
    select_button = Button(22)
    up_button = Button(23)
    down_button = Button(24)
    menu_button = Button(25)
except:
    pass



current_mode = "menu"
menu_redraw = True

selected_novel = 0
doc = None

dev_scale = .5
running = True



class LIGHT_NOVEL:
    def __init__(self, file_name: str, display_name: str, current_page: int):
        self.file_name = file_name
        self.display_name = display_name
        self.current_page = current_page


MTV1 = LIGHT_NOVEL("Mushoku Tensei - Jobless Reincarnation Volume-1.pdf", "Mushoku Tensei Volume 1", 0)
MTV2 = LIGHT_NOVEL("Mushoku Tensei - Jobless Reincarnation Volume-2.pdf", "Mushoku Tensei Volume 2", 0)
MTV3 = LIGHT_NOVEL("Mushoku Tensei - Jobless Reincarnation Volume-3.pdf", "Mushoku Tensei Volume 3", 0)

light_novel_list = [MTV1, MTV2, MTV3]













running = True
needs_redraw = True




def show_splash_screen():
    display.clear()
    img = Image.open("/home/noah/Documents/weeEbReader/weeEbReaderLogo.png").convert('L')
    img = img.resize((1200,1200), Image.LANCZOS)
    y = (screen_height - img.height) // 2
    x = (screen_width - img.width) // 2
    print(f"Location ({x} , {y})")
    print(f"Pasted X location: {x}")
    display.frame_buf.paste(img, (x,y))
    display.draw_full(constants.DisplayModes.GC16)
    
   
    time.sleep(5)

show_splash_screen()


def display_pdf_page():
    

    
    current_book = light_novel_list[selected_novel]
    page_num = current_book.current_page  
    filename = current_book.file_name
    doc = fitz.open(filename)


    if 0 <= page_num < doc.page_count:
        page = doc[page_num]  
        pix = page.get_pixmap(colorspace=fitz.csGRAY)
        img = Image.frombytes('L', [pix.width, pix.height], pix.samples)
        width_scale = screen_width / pix.width
        height_scale = screen_height / pix.height
        scale = min(width_scale, height_scale)
        new_width = int(pix.width * scale)
        new_height = int(pix.height * scale)
        img = img.resize((new_width, new_height), resample=Image.LANCZOS)
        canvas = Image.new('L', (screen_width, screen_height), 255)
        x = (screen_width - img.width) // 2
        y = (screen_height - img.height) // 2

        canvas.paste(img, (x,y))
        display.frame_buf.paste(canvas)
        display.draw_full(constants.DisplayModes.GC16)

display_pdf_page()