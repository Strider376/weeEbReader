import pygame
import fitz
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from gpiozero import Button
import time



try:
    forward_button = Button(27)
    back_button = Button(17)
except:
    pass

pygame.init()

current_mode = "menu"
menu_redraw = True


dev_scale = .5
running = True
screen_height = int(1872 * dev_scale)
screen_width = int(1404 * dev_scale)

MTV1 = ("Mushoku Tensei - Jobless Reincarnation Volume-1.pdf")
MTV2 = ("Mushoku Tensei - Jobless Reincarnation Volume-2.pdf")
MTV3 = ("Mushoku Tensei - Jobless Reincarnation Volume-3.pdf")


BG_COLOR = (255,255,255)

img = Image.new("RGB", (screen_width, screen_height), BG_COLOR)
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()

pygame.display.set_caption(MTV1)
screen.fill(BG_COLOR)

page = 0
running = True
needs_redraw = True




def show_splash_screen():
    LOGO_path = ("weeEbReaderLogo.png")
    screen.fill(BG_COLOR)
    LOGO = pygame.image.load(LOGO_path)
    width = LOGO.get_width()
    height = LOGO.get_height
    x = (screen_width- width) // 2
    y = 0
    screen.blit(LOGO, (x,y))
    pygame.display.update()
    time.sleep(3) 

show_splash_screen()



def draw_menu():
    img = Image.new("RGB", (screen_width, screen_height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(50, 200), (650, 300)], fill='red', outline='black', width=3)
    draw.rectangle([(50, 350), (650, 450)], fill='blue', outline='black', width=3)
    draw.rectangle([(50, 500), (650, 600)], fill='green', outline='black', width=3)
    pixel_data = img.tobytes()
    surface = pygame.image.fromstring(pixel_data, img.size, img.mode)

    screen.blit(surface, (0,0))
    pygame.display.update()


doc = fitz.open(MTV2)
def display_pdf_page(pdf_file, page_num=0):
    
    screen.fill(BG_COLOR)
   
    
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
       

def page_forward():
    global page, needs_redraw
    page = min(page + 1, doc.page_count -1)
    needs_redraw = True
    print(f"Forward to Page {page}")

def page_back():
    global page, needs_redraw
    page = max(page - 1, 0)
    needs_redraw = True
    print(f"Back to page {page}")

try:
    forward_button.when_activated = page_forward
    back_button.when_activated = page_back
except:
    pass




while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                page_forward()
            if event.key == pygame.K_DOWN:
                page_back()
            if event.key == pygame.K_SPACE:
                running = False

    if current_mode == "menu":
        draw_menu()
        menu_redraw = False

    elif current_mode == "reading" and needs_redraw:
        display_pdf_page(MTV2, page)
        needs_redraw = False

    clock.tick(30)
   
       


    
    clock.tick(30)


pygame.quit()
                







