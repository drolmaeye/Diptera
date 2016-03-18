from epics import *
import numpy as np

mx = PV('XPSTEST:Prof1:M1Positions')
my = PV('XPSTEST:Prof1:M2Positions')
mz = PV('XPSTEST:Prof1:M3Positions')
mw = PV('XPSTEST:Prof1:M4Positions')
t = PV('XPSTEST:Prof1:Times')

xara = np.array([0.0, 0.0, 0.0])
yara = np.array([0.075, 0.2, 0.075])
zara = np.array([0.0, 0.0, 0.0])
wara = np.array([0.0, 0.0, 0.0])
tara = np.array([0.6, 1, 0.6])

mx.put(xara)
my.put(yara)
mz.put(zara)
mw.put(wara)
t.put(tara)

print mx.get()
print my.get()
print mz.get()
print mw.get()
print t.get()
