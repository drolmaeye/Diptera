import socket
# import time

edsIP = "164.54.164.194"
edsPORT = 8000
MESSAGE1='PROGRAM 1 LOAD "C:\Users\Public\Documents\Aerotech\A3200\User Files\DO_test.pgm"\n'
MESSAGE2 = 'PROGRAM 1 START\n'

srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srvsock.settimeout(3) # 3 second timeout on commands
srvsock.connect((edsIP, edsPORT))
srvsock.send(MESSAGE1)

data = srvsock.recv(4096)
print "received message:", data

srvsock.send(MESSAGE2)

data = srvsock.recv(4096)
print "received message:", data







print 'done'
srvsock.close()

# time.sleep(10)
