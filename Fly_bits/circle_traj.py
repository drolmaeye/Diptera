from math import cos, sin, radians, pi, sqrt
import ftplib

r = 5.0
w_i = 0.0
t_total = 10.0
t_delta = t_total/360
w_dot = radians(360)/t_total

x_i = r*cos(radians(w_i))
y_i = r*sin(radians(w_i))
x_i_dot = -r*sin(radians(w_i))*w_dot
y_i_dot = r*cos(radians(w_i))*w_dot

delta_x_zero = 3.0/8 * x_i_dot
delta_y_zero = 3.0/8 * y_i_dot

x_zero = x_i - delta_x_zero
y_zero = x_i - delta_y_zero

print x_i, y_i, x_i_dot, y_i_dot, delta_x_zero, delta_y_zero, x_zero, y_zero

ramp_line = ['0.525', '0', '0', '0', '0']
ramp_line[1] = '%.5f' % delta_x_zero
ramp_line[2] = '%.5f' % x_i_dot
ramp_line[3] = '%.5f' % delta_y_zero
ramp_line[4] = '%.5f' % y_i_dot
print ramp_line
temp_line = ','.join(ramp_line)
complete_file = temp_line + '\n'

run_line = ['0', '0', '0', '0', '0']
run_line[0] = '%.5f' % t_delta


for each in range(360):
    delta_x = r*(cos(radians(each+1))-cos(radians(each)))
    delta_y = r*(sin(radians(each+1))-sin(radians(each)))
    vx_out = -r*sin(radians(each+1))*w_dot
    vy_out = r*cos(radians(each+1))*w_dot
    run_line[1] = '%.5f' % delta_x
    run_line[2] = '%.5f' % vx_out
    run_line[3] = '%.5f' % delta_y
    run_line[4] = '%.5f' % vy_out
    temp_line = ','.join(run_line)
    complete_file += temp_line + '\n'
ramp_line[4] = '0.0000'
temp_line = ','.join(ramp_line)
complete_file += temp_line + '\n'
print complete_file
