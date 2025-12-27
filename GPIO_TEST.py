from gpiozero import Button
import signal

def on_forward():
    print("forward")

def on_back():
    print("backward")

def on_up():
    print("up")

def on_down():
    print("down")

def on_select():
    print("select")

def on_menu():
    print("menu")

try:
    forward_button = Button(5)
    back_button = Button(6)
    select_button = Button(22)
    up_button = Button(27)
    down_button = Button(3)
    menu_button = Button(4)
    
    forward_button.when_activated = on_forward
    back_button.when_activated = on_back
    up_button.when_activated = on_up
    down_button.when_activated = on_down
    select_button.when_activated = on_select
    menu_button.when_activated = on_menu
    
    print("Button test running. Press Ctrl+C to exit.")
    signal.pause()  # Wait forever until Ctrl+C
    
except KeyboardInterrupt:
    print("\nExiting...")