__author__ = 'j.smith'

from epics import *

motor_nine = Motor('16TEST1:m9')
buffer_two = PV('16TEST1:softGlue:BUFFER-2_IN_Signal')

time.sleep(2)
a = time.clock()
buffer_two.put('1')
b = time.clock()
motor_nine.move(0.1275, relative=True)
c = time.clock()
print b-a
print c-b
print c-a
