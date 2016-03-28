import ftplib
import urllib
import os

session = ftplib.FTP('164.54.164.24', user='Administrator', passwd='Administrator')
session.cwd('Public/Trajectories/')
print session.pwd()
line_a = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
line_b = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
line_c = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
m = 4
if m == 's01':
    xi = 1
    vi = 2
elif m == 's02':
    xi = 3
    vi = 4
elif m == 's03':
    xi = 5
    vi = 6
else:
    xi = 7
    vi = 8
line_a[xi] = '0.1'
line_a[vi] = '0.1'
line_b[0] = '1'
line_b[xi] = '0.1'
line_b[vi] = '0.1'
line_c[xi] = '0.1'
line_a = ','.join(line_a)
line_b = ','.join(line_b)
line_c = ','.join(line_c)
complete_file = (line_a + '\n' + line_b + '\n' + line_c + '\n')
print complete_file
traj_file = open('traj.trj', 'w')
traj_file.write(complete_file)
traj_file.close()
traj_file = open('traj.trj')
session.storlines('STOR traj.trj', traj_file)
traj_file.close()
session.quit()
