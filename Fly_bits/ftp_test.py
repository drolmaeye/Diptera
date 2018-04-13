import ftplib
import urllib
import os

cwd = os.getcwd()
print cwd
os.chdir('S:')
cwd = os.getcwd()
print cwd
print 'you did it!'
textpath = 'S:\\Hexfly\\fs.ab'
print textpath
textfile = open(textpath, 'w')


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
              'PSOPULSE ST1 TIME 20000, 1000 CYCLES 51\n'
              '\n'
              'PSOOUTPUT ST1 PULSE\n'
              '\n'
              'VELOCITY ON\n'
              '\n'
              'INCREMENTAL\n'
              '\n'
              'SCOPETRIG\n'
              '\n'
              'LINEAR X-0.0875 F1\n'
              '\n'
              'DWELL 0.3\n'
              '\n'
              'LINEAR X0.0375 F0.100\n'
              '\n'
              'PSOCONTROL ST1 FIRE\n'
              '\n'
              'LINEAR X0.100\n'
              '\n'
              'LINEAR X0.0375\n'
              '\n'
              'DWELL 0.5\n'
              '\n'
              'LINEAR X-0.0875 F1\n'
              '\n'
              'END PROGRAM\n')

textfile.write(prog_lines)

textfile.close()
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
