from epics import *

def pv_read():
    if 0 == 0:
        alpha = pv.get()
        print caget(alpha)

        print caget(pv.get())


pv = PV('16TEST1:scan1.R1PV')

print caget(caget('16TEST1:scan1.R1PV'))

print caget(pv.get())

pv_read()
