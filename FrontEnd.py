import pygame
import fitz
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button
import time



try:
    forward_button = Button(27)
    back_button = Button(17)
    select_button = Button(22)
    up_button = Button(23)
    down_button = Button(24)
    menu_button = Button(25)
except:
    pass

pygame.init()

current_mode = "menu"
menu_redraw = True

selected_novel = 0
doc = None

dev_scale = .5
running = True
screen_height = int(1872 * dev_scale)
screen_width = int(1404 * dev_scale)


class LIGHT_NOVEL:
    def __init__(self, file_name: str, display_name: str, current_page: int):
        self.file_name = file_name
        self.display_name = display_name
        self.current_page = current_page


MTV1 = LIGHT_NOVEL("Mushoku Tensei - Jobless Reincarnation Volume-1.pdf", "Mushoku Tensei Volume 1", 0)
MTV2 = LIGHT_NOVEL("Mushoku Tensei - Jobless Reincarnation Volume-2.pdf", "Mushoku Tensei Volume 2", 0)
MTV3 = LIGHT_NOVEL("Mushoku Tensei - Jobless Reincarnation Volume-3.pdf", "Mushoku Tensei Volume 3", 0)

light_novel_list = [MTV1, MTV2, MTV3]


BG_COLOR = (255,255,255)




img = Image.new("RGB", (screen_width, screen_height), BG_COLOR)
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()

screen.fill(BG_COLOR)


running = True
needs_redraw = True




def show_splash_screen():
    LOGO_path = ("weeEbReaderLogo.png")
    screen.fill(BG_COLOR)
    LOGO = pygame.image.load(LOGO_path)
    width = LOGO.get_width()
    height = LOGO.get_height()
    x = (screen_width- width) // 2
    y = 0
    screen.blit(LOGO, (x,y))
    pygame.display.update()
    time.sleep(1.5)

show_splash_screen()



def draw_menu():
    img = Image.new("RGB", (screen_width, screen_height), BG_COLOR)
    draw = ImageDraw.Draw(img)
   
    try:
        book_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=35)
    except:
        book_title_font = ImageFont.load_default()
    y_pos = 200
    x_pos = 275
    for i, book in enumerate(light_novel_list):

        if i == selected_novel:
            fill = (100,100,255)
        else:
            fill = (255,255,255)

        draw.rectangle([(50, y_pos), (650, y_pos+100)], fill=fill,outline="black", width=3)
        current_book = (book.display_name)
        draw.text((x_pos-120,y_pos+30), current_book, fill = "Black", font=book_title_font)
        y_pos += 150

    pixel_data = img.tobytes()
    surface = pygame.image.fromstring(pixel_data, img.size, img.mode)

    screen.blit(surface, (0,0))
    pygame.display.update()



def display_pdf_page():
    

    screen.fill(BG_COLOR)
    
    current_book = light_novel_list[selected_novel]
    page_num = current_book.current_page  
    
    if 0 <= page_num < doc.page_count:
        page = doc[page_num]  
        pix = page.get_pixmap()

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        width_scale = screen_width / pix.width
        height_scale = screen_height / pix.height
        scale = min(width_scale, height_scale)
        new_width = int(pix.width*scale)
        new_height = int(pix.height*scale)
        img = img.resize((new_width,new_height), resample=Image.LANCZOS)

        pixel_data = img.tobytes()
        image_mode = img.mode
        surface = pygame.image.fromstring(pixel_data, img.size, image_mode)
        
        x = (screen_width-new_width) // 2
        y = (screen_height-new_height) // 2

        screen.blit(surface, (x,y))
        pygame.display.update()
       
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




while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and current_mode == "reading":
            if event.key == pygame.K_UP:
                page_forward()
            if event.key == pygame.K_DOWN:
                page_back()
            if event.key == pygame.K_ESCAPE:
                to_menu()
        if event.type == pygame.KEYDOWN and current_mode == "menu":
            if event.key == pygame.K_SPACE:
                running = False
            if event.key == pygame.K_RETURN:
                select_book()
            if event.key == pygame.K_UP:
                menu_up()
            if event.key == pygame.K_DOWN:
                menu_down()
                
    if current_mode == "menu" and menu_redraw:
        draw_menu()
        menu_redraw = False

    elif current_mode == "reading" and needs_redraw:
        display_pdf_page()
        needs_redraw = False

    clock.tick(30)
   
       


 


pygame.quit()
