import pygame
import fitz
import sys
from pathlib import Path
from PIL import Image

pygame.init()

dev_scale = .5
running = True
screen_height = int(1872 * dev_scale)
screen_width = int(1404 * dev_scale)

MTV1 = ("Mushoku Tensei - Jobless Reincarnation Volume-1.pdf")
BG_COLOR = (255,255,255)

screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()

pygame.display.set_caption(MTV1)
screen.fill(BG_COLOR)

page = 0
running = True
needs_redraw = True


doc = fitz.open(MTV1)


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
       




while running:
    

   
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                page = min(page + 1, doc.page_count -1)
                needs_redraw = True
            if event.key == pygame.K_DOWN:
                page = max(page - 1, 0)
                needs_redraw = True
            if event.key == pygame.K_SPACE:
                running = False
                
    if needs_redraw == True:
        display_pdf_page(MTV1, page)
        needs_redraw = False
    clock.tick(15)


pygame.quit()
                







