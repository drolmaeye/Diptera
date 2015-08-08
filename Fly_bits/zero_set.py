__author__ = 'j.smith'

from epics import *

mTest = Motor('16TEST1:m1')

mTest_i = mTest.RBV
print mTest_i
mTest.SET = 1
mTest.VAL = 0
mTest.SET = 0
raw_input('press enter when ready')
mTest.SET = 1
mTest.VAL = mTest_i

mTest.SET = 0

