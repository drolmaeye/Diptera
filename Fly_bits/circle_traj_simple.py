from math import cos, sin, radians, pi, sqrt
import ftplib
import XPS_Q8_drivers

r = 12.5
cv = 12.5
total_time = 2*pi*r/cv
print total_time
segment_time = total_time/4
print '%.5f' % segment_time

trj_line = ['0', '0', '0', '0', '0']




# print complete_file
# traj_file = open('circle_traj.trj', 'w')
# traj_file.write(complete_file)
# traj_file.close()
session = ftplib.FTP('164.54.105.46', user='Administrator', passwd='Administrator')
session.cwd('Public/Trajectories/')
traj_file = open('circle_traj.trj')
session.storlines('STOR circle_traj.trj', traj_file)
traj_file.close()
session.quit()
