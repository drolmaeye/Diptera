__author__ = 'j.smith'

from epics import *
from Tkinter import *


def initialize():
    global m1
    m1 = Motor('16TEST1:m1')
    return m1


def rbv():
    print m1.get('RBV')


root = Tk()
button = Button(root, text='initialize', command=initialize)
button.pack()
button2 = Button(root, text='get RBV', command=rbv)
button2.pack()
root.mainloop()
