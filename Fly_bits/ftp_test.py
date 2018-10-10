import ftplib
import urllib
import os
import socket
import time

# ###cwd = os.getcwd()
# ###print cwd
# ###os.chdir('S:')
# ###cwd = os.getcwd()
# ###print cwd
# ###print 'you did it!'
# ###textpath = 'S:\\Hexfly\\fs.ab'
# ###print textpath
# ###textfile = open(textpath, 'w')

fly_zero = -0.0875
abs_fly_min = -0.050
abs_fly_max = 0.050
temp_velo = 0.100
mFly = 'X'
exp_time = 0.020
npts = 51
# prog = 'fly'
prog = 'dwell'


def make_hex_fly(zero, min, max, velocity, motor, exp_time, num_pts):
    delta_ramp = str(min - zero)
    delta_fly = str(max-min)
    delta_t = str(int(exp_time*1000000))
    cycles = str(num_pts)
    fly_velo = str(velocity)
    prog_lines = ('\'--------------------------------------------\n'
                  '\'------------- HexSpliceDev.ab --------------\n'
                  '\'--------------------------------------------\n'
                  '\'\n'
                  '\'This program uses a few commands to move,\n'
                  '\'Trying to check V between moves, pulse added.\n'
                  '\n'
                  'PSOCONTROL ST1 RESET\n'
                  '\n'
                  'PSOOUTPUT ST1 CONTROL 0 1\n'
                  '\n'
                  'PSOPULSE ST1 TIME ' + delta_t + ', 1000 CYCLES ' + cycles + '\n'
                  '\n'
                  'PSOOUTPUT ST1 PULSE\n'
                  '\n'
                  'VELOCITY ON\n'
                  '\n'
                  'INCREMENTAL\n'
                  '\n'
                  'SCOPETRIG\n'
                  '\n'
                  'LINEAR ' + motor + delta_ramp + ' F' + fly_velo + '\n'
                  '\n'
                  'PSOCONTROL ST1 FIRE\n'
                  '\n'
                  'LINEAR ' + mFly + delta_fly + '\n'
                  '\n'
                  'LINEAR ' + mFly + delta_ramp + '\n'
                  '\n'
                  'DWELL 0.3\n'
                  '\n'
                  'END PROGRAM\n')
    textpath = 'S:\\Hexfly\\fs.pgm'
    textfile = open(textpath, 'w')
    textfile.write(prog_lines)
    textfile.close()


def make_dwell():
    prog_lines = ('\'--------------------------------------------\n'
                  '\'------------- Dwell.ab --------------\n'
                  '\'--------------------------------------------\n'
                  '\'\n'
                  'DWELL 1.0\n'
                  '\n'
                  'DWELL 1.0\n'
                  '\n'
                  'DWELL 1.0\n'
                  '\n'
                  'END PROGRAM\n')
    textpath = 'S:\\Hexfly\\dwell.pgm'
    textfile = open(textpath, 'w')
    textfile.write(prog_lines)
    textfile.close()


if prog == 'fly':
    make_hex_fly(zero=fly_zero, min=abs_fly_min, max=abs_fly_max,
                 velocity=temp_velo, motor=mFly, exp_time=exp_time, num_pts=npts)
    MESSAGE1 = 'PROGRAM 1 LOAD "S:\\Hexfly\\fs.pgm"\n'

else:
    make_dwell()
    MESSAGE1 = 'PROGRAM 1 LOAD "S:\\Hexfly\\dwell.pgm"\n'

edsIP = "164.54.164.194"
edsPORT = 8000
# MESSAGE1='PROGRAM 1 LOAD "S:\\Hexfly\\fs.pgm"\n'
MESSAGE2 = 'PROGRAM 1 START\n'
MESSAGE3 = 'TASKSTATUS(1, DATAITEM_TaskState)\n'

srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srvsock.settimeout(3) # 3 second timeout on commands
srvsock.connect((edsIP, edsPORT))

srvsock.send(MESSAGE1)
data = srvsock.recv(4096)
print "received message:", data

srvsock.send(MESSAGE2)
data = srvsock.recv(4096)
print "received message:", data


# ###for asks in range(20):
# ###    srvsock.send(MESSAGE3)
# ###    data = srvsock.recv(4096)
# ###    print "received message:", data
# ###    # if data == '%4\n':
# ###    #     print 'run it'
# ###    if data == '%7\n':
# ###        print 'bawt it'
# ###        break
# ###    time.sleep(0.500)

# program running check
timeout = 4.0
timeout_start = time.time()
while time.time() < timeout_start + timeout:
    srvsock.send(MESSAGE3)
    data = srvsock.recv(4096)
    if data == '%7\n':
        print data, 'bawt it'
        break
    else:
        time.sleep(0.250)
        print "received message:", data
else:
    print 'timeout!!! Oh shoot!'

# ###while not data == '%7\n':
# ###    srvsock.send(MESSAGE3)
# ###    data = srvsock.recv(4096)
# ###    print "received message:", data
# ###    # if data == '%4\n':
# ###    #     print 'run it'
# ###    time.sleep(0.25)
# ###else:
# ###    print 'bawt it'

print 'done'
srvsock.close()

print 'end'

### code below is for XPS, commented out 12 April 2018 for Hex development
# ###session = ftplib.FTP('164.54.164.24', user='Administrator', passwd='Administrator')
# ###session.cwd('Public/Trajectories/')
# ###print session.pwd()
# ###line_a = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
# ###line_b = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
# ###line_c = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
# ###m = 4
# ###if m == 's01':
# ###    xi = 1
# ###    vi = 2
# ###elif m == 's02':
# ###    xi = 3
# ###    vi = 4
# ###elif m == 's03':
# ###    xi = 5
# ###    vi = 6
# ###else:
# ###    xi = 7
# ###    vi = 8
# ###line_a[xi] = '0.1'
# ###line_a[vi] = '0.1'
# ###line_b[0] = '1'
# ###line_b[xi] = '0.1'
# ###line_b[vi] = '0.1'
# ###line_c[xi] = '0.1'
# ###line_a = ','.join(line_a)
# ###line_b = ','.join(line_b)
# ###line_c = ','.join(line_c)
# ###complete_file = (line_a + '\n' + line_b + '\n' + line_c + '\n')
# ###print complete_file
# ###traj_file = open('traj.trj', 'w')
# ###traj_file.write(complete_file)
# ###traj_file.close()
# ###traj_file = open('traj.trj')
# ###session.storlines('STOR traj.trj', traj_file)
# ###traj_file.close()
# ###session.quit()
