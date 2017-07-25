#!/usr/bin/env python3

from tkinter import *
from PIL import ImageTk, Image

margin = 50
screenh = 1080
screenw = 1920
bgcolor = "#ffe298"
tablebg = "#eed288"


root = Tk()
root.overrideredirect(True)
root.overrideredirect(False)
root.attributes("-fullscreen", True)
root.configure(background=bgcolor)

heading = Label(root, text="Wall of Bender", bg=bgcolor, font=("Droid Sans Mono", 120))
heading.place(x=margin, y=margin-40, anchor=NW)
credit = Label(root, text="Brought to you by Abraxas3D and Skunkwrx with thanks to AND!XOR and DEFCON Group San Diego",
	fg="#888888", bg=bgcolor, font=("Droid Sans Mono", 9))
credit.place(x=margin+18, y=170, anchor=NW)
badges_label = Label(root, text="Badges Seen", bg=bgcolor, font=("Droid Sans Mono", 50))
badges_label.place(x=margin, y=250, anchor=NW)
names_label = Label(root, text="Names", bg=bgcolor, font=("Droid Sans Mono", 50))
names_label.place(x=margin+912+margin, y=250, anchor=NW)
live_label = Label(root, text="Intercepts", bg=bgcolor, font=("Droid Sans Mono", 60))
live_label.place(x=margin+912+margin+304+margin, y=480, anchor=NW)

img = ImageTk.PhotoImage(Image.open("badge_photo.png").convert("RGBA"))
photo_panel = Label(root, image = img, borderwidth=0, bg=bgcolor)
photo_panel.place(x=screenw-margin, y=margin, anchor=NE)

badges_canvas = Canvas(root, width=912, height=680, bg=tablebg, borderwidth=0, highlightthickness=0)
badges_canvas.place(x=margin, y=350, anchor=NW)
names_canvas = Canvas(root, width=304, height=680, bg=tablebg, borderwidth=0, highlightthickness=0)
names_canvas.place(x=margin+912+margin, y=350, anchor=NW)
live_canvas = Canvas(root, width=494, height=430, bg=tablebg, borderwidth=0, highlightthickness=0)
live_canvas.place(x=screenw-margin, y=screenh-margin, anchor=SE)


root.mainloop()
