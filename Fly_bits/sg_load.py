__author__ = 'j.smith'

from epics import *
from Tkinter import *

sg1 = PV('16TEST1:SGMenu:name1')
sg2 = PV('16TEST1:SGMenu:name2')
sg3 = PV('16TEST1:SGMenu:name3')
load1 = PV('16TEST1:SGMenu:loadConfig1.PROC')
load2 = PV('16TEST1:SGMenu:loadConfig2.PROC')
load3 = PV('16TEST1:SGMenu:loadConfig3.PROC')

def sg1_write():
    sg1.put('clear_all')
    load1.put(1)

def sg2_write():
    sg1.put('XPS_master_2Dec2015')
    load1.put(1)

def sg3_write():
    sg1.put('clear_all')
    load1.put(1)
    sg1.put('step_master_20Nov2015')
    load1.put(1)


root = Tk()
button1 = Button(root, text='load1', command=sg1_write)
button1.pack()
button2 = Button(root, text='load2', command=sg2_write)
button2.pack()
button3 = Button(root, text='load3', command=sg3_write)
button3.pack()

root.mainloop()