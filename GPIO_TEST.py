from gpiozero import Button


try:
    forward_button = Button(5)
    back_button = Button(6)
    select_button = Button(22)
    up_button = Button(27)
    down_button = Button(3)
    menu_button = Button(4)
except:
    pass

forward_button.when_activated = print("forward")
back_button.when_activated = print("backward")
up_button.when_activated = print("up")
down_button.when_activated = print("down")
select_button.when_activated = print("select")
menu_button.when_activated = print("menu")