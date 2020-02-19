import socket
# import time

edsIP = "164.54.105.199"
edsPORT = 8000
# MESSAGE1='PROGRAM 1 LOAD "C:\Users\Public\Documents\Aerotech\A3200\User Files\DO_test.pgm"\n'
# MESSAGE2 = 'PROGRAM 1 START\n'
message0 = 'TASKSTATUS(0, DATAITEM_CoordinatedAccelerationRate)\n'
message1 = 'TASKSTATUS(1, DATAITEM_CoordinatedAccelerationRate)\n'
message2 = 'TASKSTATUS(2, DATAITEM_CoordinatedAccelerationRate)\n'
message3 = 'TASKSTATUS(3, DATAITEM_CoordinatedAccelerationRate)\n'
message4 = 'TASKSTATUS(4, DATAITEM_CoordinatedAccelerationRate)\n'

srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srvsock.settimeout(3) # 3 second timeout on commands
srvsock.connect((edsIP, edsPORT))
srvsock.send(message0)
response0 = srvsock.recv(4096)
srvsock.send(message1)
response1 = srvsock.recv(4096)
srvsock.send(message2)
response2 = srvsock.recv(4096)
srvsock.send(message3)
response3 = srvsock.recv(4096)
srvsock.send(message4)
response4 = srvsock.recv(4096)
print response0, response1, response2, response3, response4

# srvsock.send(MESSAGE2)
# data = srvsock.recv(4096)
# print "received message:", data
# print 'done'
srvsock.close()
