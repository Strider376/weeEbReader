from PIL import Image, ImageDraw, ImageFont
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
import fitz
import sys
from pathlib import Path
from gpiozero import Button
import time

display = AutoEPDDisplay(vcom=-1.46, rotate='CW')

screen_width = display.width
screen_height = display.height

try:
    forward_button = Button(5)
    back_button = Button(6)
    select_button = Button(22)
    up_button = Button(27)
    down_button = Button(3)
    menu_button = Button(4)
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



def to_menu():
    global menu_redraw, current_mode
    current_mode = "menu"
    menu_redraw = True

def page_forward():
    global needs_redraw
    current_book = light_novel_list[selected_novel]
    current_book.current_page = min(current_book.current_page + 1, doc.page_count -1)
    needs_redraw = True
    print(f"Forward to Page {current_book.current_page}")

def page_back():
    global needs_redraw
    current_book = light_novel_list[selected_novel]
    current_book.current_page = max(current_book.current_page - 1, 0) 
    needs_redraw = True
    print(f"Back to page {current_book.current_page}")


def select_book():
    global doc, current_mode, needs_redraw
    book = light_novel_list[selected_novel]
    filename = book.file_name
    doc = fitz.open(filename)
    current_mode = "reading"
    needs_redraw = True

def menu_up():
    global menu_redraw, selected_novel
    selected_novel = max(selected_novel - 1, 0)
    menu_redraw = True
    

def menu_down():
    global menu_redraw, selected_novel
    selected_novel = min(selected_novel + 1, len(light_novel_list) - 1)
    menu_redraw = True
    



try:
    forward_button.when_activated = page_forward
    back_button.when_activated = page_back
    up_button.when_activated = menu_up
    down_button.when_activated = menu_down
    select_button.when_activated = select_book
    menu_button.when_activated = to_menu
    print("All Buttons Configured")
except Exception as e:
    print(f"Error: Button setup failed {e}")






def main():
    current_mode = "menu"

    show_splash_screen()

    display_pdf_page()