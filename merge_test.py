#!./capython3
# To avoid running as root, we use a copy of the Python3 interpreter.
# Give it the needed capabilities with this command:
# sudo setcap 'cap_net_raw,cap_net_admin+eip' capython3

# Portions of the Bluetooth interaction parts of this script have been
# taken from https://stackoverflow.com/questions/23788176/finding-bluetooth-low-energy-with-python


import sys
import os
import struct
import signal
import time
import errno
from ctypes import (CDLL, get_errno)
from ctypes.util import find_library
from socket import (
    socket,
    AF_BLUETOOTH,
    SOCK_RAW,
    BTPROTO_HCI,
    SOL_HCI,
    HCI_FILTER,
)
from tkinter import *
from PIL import ImageTk, Image
from collections import deque
import threading

class BTAdapter (threading.Thread):
	def __init__(self, master, btQueue):
		threading.Thread.__init__(self)
		self.btQueue = btQueue
		
		self.stop_event = threading.Event()
		
		btlib = find_library("bluetooth")
		if not btlib:
		    raise Exception(
		        "Can't find required bluetooth libraries"
		        " (need to install bluez)"
		    )
		self.bluez = CDLL(btlib, use_errno=True)
	
		dev_id = self.bluez.hci_get_route(None)
		
		self.sock = socket(AF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI)
		if not self.sock:
		    print("Failed to open Bluetooth")
		    sys.exit(1)
		    
		self.sock.bind((dev_id,))

		err = self.bluez.hci_le_set_scan_parameters(self.sock.fileno(), 0, 0x10, 0x10, 0, 0, 1000);
		if err < 0:
		    raise Exception("Set scan parameters failed")
		    # occurs when scanning is still enabled from previous call
		
		# allows LE advertising events
		hci_filter = struct.pack(
		    "<IQH", 
		    0x00000010, 
		    0x4000000000000000, 
		    0
		)
		self.sock.setsockopt(SOL_HCI, HCI_FILTER, hci_filter)
		
		err = self.bluez.hci_le_set_scan_enable(
		    self.sock.fileno(),
		    1,  # 1 - turn on;  0 - turn off
		    0, # 0-filtering disabled, 1-filter out duplicates
		    1000  # timeout
		)
		if err < 0:
		    errnum = get_errno()
		    raise Exception("{} {}".format(
		        errno.errorcode[errnum],
		        os.strerror(errnum)
		    ))

	def stop(self):
		self.stop_event.set()
	
	def stopped(self):
		return self.stop_event.is_set()

	def clean_up(self):
		if self.sock is None:
			print("Double clean_up", flush=True)
			return
			
		err = self.bluez.hci_le_set_scan_enable(
			self.sock.fileno(),
			0,  # 1 - turn on;  0 - turn off
			0, # 0-filtering disabled, 1-filter out duplicates
			1000  # timeout
			)
		if err < 0:
			errnum = get_errno()
			print("{} {}".format(
				errno.errorcode[errnum],
				os.strerror(errnum)
				))

		self.sock.close()
		self.sock = None
		
	def run(self):
		while True:
			data = self.sock.recv(1024)
			badge_time = time.time()
			self.btQueue.appendleft((badge_time,data))
			if self.stopped():
				self.clean_up()
				break

margin = 50
tmargin = 5
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
live_text = live_canvas.create_text(tmargin, tmargin, anchor=NW, text="Nothing received yet.")
live_canvas.place(x=screenw-margin, y=screenh-margin, anchor=SE)

print("Done setting up GUI", flush=True)

def processAdvertisement(cept):
	timestamp,data = cept
	print("t=%f %d bytes" % (timestamp, len(data)), flush=True)	# non-GUI test
	live_canvas.itemconfigure(live_text, text="%f %d bytes" % (timestamp, len(data)))

btQueue = deque(maxlen=1000)
bt = BTAdapter(root, btQueue)
print("Initialized BTAdapter", flush=True)
bt.start()
print("Started BTAdapter", flush=True)

def signal_handler(signal, frame):
	bt.stop()
	print("That'll do for now.", flush=True)
	root.quit()
signal.signal(signal.SIGINT, signal_handler)

def btPoller():
	print("poll at %f" % (time.time()), flush=True)
	while True:
		try:
			intercept = btQueue.pop()
			processAdvertisement(intercept)

		except IndexError:
			print("empty", flush=True)
			break;
			
	root.after(100, btPoller)
btPoller()

print("Started btPoller at %f" % (time.time()), flush=True)

root.mainloop()
