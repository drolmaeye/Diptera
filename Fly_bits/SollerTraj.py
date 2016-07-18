__author__ = 'j.smith'

'''
Generate trajectories for soller slits at idb
'''

from math import cos, sin, radians, pi, sqrt
import ftplib
import XPS_Q8_drivers
import numpy as np


def make_soller_trajectory(theta_range, num_points, time_total, theta_naught):

    # r is offset
    r = 35.75
    delta_time = time_total/(num_points-1)
    delta_theta = theta_range/(num_points - 1)
    v_theta = theta_range/time_total
    theta_zero = theta_naught - v_theta*0.375
    x_zero = 35 + r*cos(theta_zero*pi/180)
    y_zero = r*sin(theta_zero*pi/180)
    print x_zero, y_zero, theta_zero
    delta_sx_zero = r * (cos(theta_naught * pi / 180) - cos(theta_zero * pi / 180))
    delta_sy_zero = r * (sin(theta_naught * pi / 180) - sin(theta_zero * pi / 180))
    vx_out_zero = -r*sin(theta_naught*pi/180)*v_theta*pi/180
    vy_out_zero = r*cos(theta_naught*pi/180)*v_theta*pi/180
    delta_theta_zero = v_theta*0.375
    ramp_line = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
    ramp_line[11] = '%.5f' % -delta_sx_zero
    ramp_line[12] = '%.5f' % -vx_out_zero
    ramp_line[13] = '%.5f' % delta_sy_zero
    ramp_line[14] = '%.5f' % vy_out_zero
    ramp_line[15] = '%.5f' % delta_theta_zero
    ramp_line[16] = '%.5f' % v_theta
    temp_line = ','.join(ramp_line)
    complete_file = temp_line + '\n'
    run_line = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
    run_line[0] = '%.5f' % delta_time
    run_line[15] = '%.5f' % delta_theta
    run_line[16] = '%.5f' % v_theta
    for each in range(num_points-1):
        theta_i = theta_naught + (delta_theta*each)
        theta_f = theta_i + delta_theta
        delta_sx = r*(cos(theta_f*pi/180)-cos(theta_i*pi/180))
        delta_sy = r*(sin(theta_f*pi/180)-sin(theta_i*pi/180))
        vx_out = -r*sin(theta_f*pi/180)*v_theta*pi/180
        vy_out = r*cos(theta_f*pi/180)*v_theta*pi/180
        run_line[11] = '%.5f' % -delta_sx
        run_line[12] = '%.5f' % -vx_out
        run_line[13] = '%.5f' % delta_sy
        run_line[14] = '%.5f' % vy_out
        temp_line = ','.join(run_line)
        complete_file += temp_line + '\n'
    theta_max = theta_naught + theta_range
    theta_final = theta_max + v_theta*0.375
    delta_theta_final = delta_theta_zero
    delta_sx_final = r * (cos(theta_final * pi / 180) - cos(theta_max * pi / 180))
    delta_sy_final = r * (sin(theta_final * pi / 180) - sin(theta_max * pi / 180))
    ramp_line[11] = '%.5f' % -delta_sx_final
    ramp_line[12] = '0.00000'
    ramp_line[13] = '%.5f' % delta_sy_final
    ramp_line[14] = '0.00000'
    ramp_line[15] = '%.5f' % delta_theta_final
    ramp_line[16] = '0.00000'
    temp_line = ','.join(ramp_line)
    complete_file += temp_line + '\n'
    print complete_file
    traj_file = open('soller_traj.trj', 'w')
    traj_file.write(complete_file)
    traj_file.close()
    session = ftplib.FTP('164.54.164.24', user='Administrator', passwd='Administrator')
    session.cwd('Public/Trajectories/')
    traj_file = open('soller_traj.trj')
    session.storlines('STOR soller_traj.trj', traj_file)
    traj_file.close()
    session.quit()

make_soller_trajectory(-30.0, 301, 10.0, 15)













# ###def make_trajectory(zero, min, max, velo, motor):
# ###    line_a = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
# ###    line_b = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
# ###    line_c = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
# ###    if motor.get('DIR') == 0:
# ###        sign = 1
# ###    else:
# ###        sign = -1
# ###    delta_xac = sign*(min - zero)
# ###    delta_xb = sign*(max-min)
# ###    velo_ab = sign*(velo)
# ###    delta_tb = delta_xb/velo_ab
# ###    if motor == mX:
# ###        # print 'x'
# ###        xi = 1
# ###        vi = 2
# ###    elif motor == mY:
# ###        # print 'y'
# ###        xi = 3
# ###        vi = 4
# ###    elif motor == mZ:
# ###        # print 'z'
# ###        xi = 5
# ###        vi = 6
# ###    else:
# ###        # print 'w'
# ###        xi = 7
# ###        vi = 8
# ###    line_a[xi] = str(delta_xac)
# ###    line_a[vi] = str(velo_ab)
# ###    line_b[0] = str(delta_tb)
# ###    line_b[xi] = str(delta_xb)
# ###    line_b[vi] = str(velo_ab)
# ###    line_c[xi] = str(delta_xac)
# ###    line_a = ','.join(line_a)
# ###    line_b = ','.join(line_b)
# ###    line_c = ','.join(line_c)
# ###    complete_file = (line_a + '\n' + line_b + '\n' + line_c + '\n')
# ###    # print complete_file
# ###    traj_file = open('traj.trj', 'w')
# ###    traj_file.write(complete_file)
# ###    traj_file.close()
# ###    session = ftplib.FTP(xps_ip, user='Administrator', passwd='Administrator')
# ###    session.cwd('Public/Trajectories/')
# ###    traj_file = open('traj.trj')
# ###    session.storlines('STOR traj.trj', traj_file)
# ###    traj_file.close()
# ###    session.quit()
# ###