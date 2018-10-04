__author__ = 'j.smith'

'''
A GUI for creating, reading, and graphing flyscan (1d or 2d) files
'''

# import necessary modules
from Tkinter import *
from tkMessageBox import *
from tkFileDialog import *
import tkFont
import os.path
from shutil import copyfile
from epics import *
from epics.devices import Struck
import numpy as np
from math import cos, sin, radians, pi, sqrt
from scipy import exp, integrate
from scipy.optimize import curve_fit
# ###import fabio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import ftplib
import socket
import XPS_Q8_drivers


# define classes
class ExpConfigure:
    """
    ExpConfigure used to specify endstation and stage stack

    This pops up when the program is first started, and cannot be called
    again.  User must close and restart software to choose an alternate
    configuration.  Window can be bypassed by commenting *in* a line below,
    contained in the program start section.
    """

    def __init__(self, master):
        # set up frames
        self.config_window = Toplevel(master)
        self.config_window.title('Select endstation')
        self.config_window.geometry('250x320')
        self.frame_stages = Frame(self.config_window)
        self.frame_stages.grid(row=0, column=0, pady=10)

        # define variables for stack choice and custom config
        self.stack_choice = StringVar()
        self.stack_choice.set(NONE)
        # note custom config not currently available for Diptera
        self.use_file = BooleanVar()
        self.use_file.set(0)

        # set up list to make buttons
        # ###master stack list###
        # ###stack_list = [
        # ###    ('BMB Laue Table', 'BMBLT'),
        # ###    ('BMB PEC Table', 'BMBPEC'),
        # ###    ('BMD High Precision', 'BMDHP'),
        # ###    ('BMD High Load', 'BMDHL'),
        # ###    ('IDB GP High Precision', 'GPHP'),
        # ###    ('IDB GP High Load', 'GPHL'),
        # ###    ('IDB Laser Heating Table', 'IDBLH'),
        # ###    ('IDD Spectroscopy', 'IDD')]

        # working stack_list
        stack_list = [
            ('BMB Laue Table', 'BMB'),
            ('BMD High Load', 'BMDHL'),
            ('IDB GP High Precision', 'GPHP'),
            ('IDB GP High Load', 'GPHL'),
            ('IDB Laser Heating Table', 'IDBLH'),
            ('IDD Spectroscopy', 'IDD'),
            ('Test', 'TEST')]

        # make radio buttons for stages using lists
        for stacks, designation in stack_list:
            self.motor_buttons = Radiobutton(self.frame_stages, text=stacks,
                                             variable=self.stack_choice,
                                             value=designation)
            self.motor_buttons.grid(sticky='w', padx=50, pady=5)

        # make option for custom config file
        # ###self.custom_button = Radiobutton(self.config_window,
        # ###                                 text='Load custom configuration from file',
        # ###                                 variable=self.use_file, value=1)
        # ###self.custom_button.grid(row=3, column=0, columnspan=2, pady=5)

        # make column headings
        # ###self.stack_head = Label(self.config_window, text='Select one set of stages')
        # ###self.stack_head.grid(row=0, column=0, pady=5)

        # make confirmation and custom config buttons
        self.confirm_choice = Button(self.config_window, text='Confirm choice',
                                     command=self.confirm_choices)
        self.confirm_choice.grid(row=4, column=0, columnspan=2, pady=10)
        # ###self.or_label = Label(self.config_window, text='-----OR-----')
        # ###self.or_label.grid(row=2, column=0, columnspan=2, pady=5)

    def confirm_choices(self):
        """
        Destroy window, pass control back to root to define devices
        """
        stack = self.stack_choice.get()
        # valid list below created January 2016
        valid_list = ['BMB', 'BMDHL', 'GPHP', 'GPHL', 'IDBLH', 'IDD', 'TEST']
        if stack not in valid_list:
            showerror('Under Development',
                      'Those stages are not yet available, program will exit')
            close_quit()
        else:
            self.config_window.destroy()


class CoreData:
    """
    Core data that will be repeatedly used and modified for plotting
    """
    def __init__(self):

        # create default/dummy arrays
        self.FLY = np.linspace(-0.045, 0.045, 10)
        self.STP = np.linspace(-0.05, 0.05, 11)
        self.TIM = np.ones((11, 10))
        self.FOE = np.ones((11, 10))
        self.REF = np.ones((11, 10))
        self.RMD = np.ones((11, 10))
        self.BSD = np.ones((11, 10))
        self.SCA = np.ones((11, 10))
        # create default/dummy plot position lines
        self.h_min = plt.axhline(-.25)
        self.h_max = plt.axhline(.25)
        self.h_mid = plt.axhline(0, ls='--', c='r')
        self.v_min = plt.axvline(-.25)
        self.v_max = plt.axvline(.25)
        self.v_mid = plt.axvline(0, ls='--', c='r')
        self.dhls = []
        self.dvls = []
        # define dimension and specify default
        self.dimension = 11
        # plot flag that cannot be turned off (for now), meaning primary data always plotted
        self.plot_flag = IntVar()
        self.plot_flag.set(1)


class ScanBox:
    def __init__(self, master, label):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.flag = IntVar()
        self.axis = StringVar()
        self.rel_min = DoubleVar()
        self.step_size = DoubleVar()
        self.rel_max = DoubleVar()
        self.npts = IntVar()
        if label == 'Fly axis':
            self.axis.set(fly_list[0])
            self.flag.set(1)
        elif label == 'Step axis':
            self.axis.set(step_list[1])
            self.flag.set(0)
        self.rel_min.set('%.3f' % -.10)
        self.step_size.set('%.4f' % .004)
        self.rel_max.set('%.3f' % .10)
        self.npts.set(51)
        if label == 'Step axis':
            self.scan_directory = StringVar()
            self.scan_no = StringVar()
            self.scan_directory.set('Select directory before scan')
            self.scan_no.set('001')
            # make a placeholder for custom stages
            self.mCustom = ''

        # set up trace on stage selections
        self.axis.trace('w', self.axis_validate)

        # make column headings
        if label == 'Fly axis':
            self.head_area = Label(self.frame, text='SCAN CONTROL')
            self.head_area.grid(row=0, column=0, columnspan=2, pady=5, sticky='w')
            self.head_axis = Label(self.frame, text='Stage')
            self.head_axis.grid(row=0, column=2)
            self.head_min = Label(self.frame, text='Rel. min.')
            self.head_min.grid(row=0, column=3)
            self.head_size = Label(self.frame, text='Step size')
            self.head_size.grid(row=0, column=4)
            self.head_max = Label(self.frame, text='Rel. max.')
            self.head_max.grid(row=0, column=5)
            self.head_step = Label(self.frame, text='Points')
            self.head_step.grid(row=0, column=6)

        # define and place scan control widgets
        self.checkbutton_flag = Checkbutton(self.frame, variable=self.flag)
        self.checkbutton_flag.grid(row=1, column=0)
        if label == 'Fly axis':
            # hide fly_axis.flag from user, may still implement in future
            self.checkbutton_flag.config(state=DISABLED)
            self.led = Canvas(self.frame, height=25, width=25)
            self.led.grid(row=1, column=0)
            self.led.create_oval(5, 5, 20, 20, fill='green', disabledfill='red')
        self.label_stage = Label(self.frame, text=label, width=10)
        self.label_stage.grid(row=1, column=1, padx=5, pady=5)
        if label == 'Fly axis':
            self.stage_menu = OptionMenu(self.frame, self.axis, *fly_list)
        elif label == 'Step axis':
            self.stage_menu = OptionMenu(self.frame, self.axis, *step_list)
        self.stage_menu.config(width=17)
        self.stage_menu.grid(row=1, column=2, padx=5)
        self.stage_menu.bind('<FocusOut>', self.axis_validate)
        self.stage_menu.bind('<Return>', self.axis_validate)
        self.entry_min = Entry(self.frame, textvariable=self.rel_min, width=8)
        self.entry_min.grid(row=1, column=3, padx=5)
        self.entry_min.bind('<FocusOut>', self.min_validate)
        self.entry_min.bind('<Return>', self.min_validate)
        self.label_step_size = Label(self.frame, textvariable=self.step_size,
                                     relief=SUNKEN, width=8)
        self.label_step_size.grid(row=1, column=4, padx=5)
        self.entry_max = Entry(self.frame, textvariable=self.rel_max, width=8)
        self.entry_max.grid(row=1, column=5, padx=5)
        self.entry_max.bind('<FocusOut>', self.max_validate)
        self.entry_max.bind('<Return>', self.max_validate)
        self.entry_npts = Entry(self.frame, textvariable=self.npts,
                                width=8)
        self.entry_npts.grid(row=1, column=6, padx=5)
        self.entry_npts.bind('<FocusOut>', self.npts_validate)
        self.entry_npts.bind('<Return>', self.npts_validate)

        # define and place file control widgets
        if label == 'Step axis':
            self.label_scan_label = Label(self.frame, text='Scan directory')
            self.label_scan_label.grid(row=2, column=0, columnspan=2, pady=10)
            self.label_scan_directory = Label(self.frame, width=28,
                                              textvariable=self.scan_directory,
                                              relief=SUNKEN, anchor='w')
            self.label_scan_directory.grid(row=2, column=2, columnspan=2,
                                           padx=5, pady=10)
            self.label_file_label = Label(self.frame, text='Scan no.')
            self.label_file_label.grid(row=2, column=4, padx=5, pady=10)
            self.label_scan_no = Label(self.frame, textvariable=self.scan_no,
                                       relief=SUNKEN, width=6)
            self.label_scan_no.grid(row=2, column=5, padx=5, pady=10)
            self.button_browse = Button(self.frame, text='Browse',
                                        command=self.choose_directory)
            self.button_browse.grid(row=2, column=6)

    def choose_directory(self):
        current_directory = self.scan_directory.get()
        if os.path.exists(current_directory):
            user_dir = askdirectory(initialdir=current_directory,
                                    title='Select a user directory')
        else:
            user_dir = askdirectory(title='Select a user directory')
        if user_dir and os.path.exists(user_dir):
            win_path = os.path.normpath(user_dir)
            new_directory = win_path + '\\'
            prefix = new_directory + 'fScan_'
            index = '001'
            full_filename = prefix + index + '.npz'
            if not os.path.isfile(full_filename):
                pass
            else:
                # fast way to find the next file
                for each in range(4, -1, -1):
                    while os.path.isfile(full_filename):
                        incremented_index = str(int(index) + 10**each)
                        index = incremented_index.zfill(3)
                        full_filename = prefix + index + '.npz'
                    new_index = str(int(index) - 10**each)
                    index = new_index.zfill(3)
                    full_filename = prefix + index + '.npz'
                final_index = str(int(index) + 1).zfill(3)
                index = final_index
                overwrite_warn()
            return self.scan_directory.set(new_directory), self.scan_no.set(index)
        else:
            self.scan_directory.set(current_directory)
            if user_dir:
                path_warn()

    def set_directory(self):
        # called only on program start
        # autofill routine for scan location in zeon
        year = time.strftime('%Y')
        month = time.strftime('%m')
        if int(month) < 5:
            run = '1'
        elif int(month) > 8:
            run = '3'
        else:
            run = '2'
        folder = year + '-' + run
        stack = config.stack_choice.get()
        if stack == 'BMB':
            zeon_prefix = 'BMB TBD'
        elif stack == 'BMDHL':
            zeon_prefix = 'Y:\\saveData\\16bmd\\'
        elif stack == 'GPHL' or stack == 'GPHP' or stack == 'IDBLH':
            zeon_prefix = 'W:\\16idb\\'
        elif stack == 'IDD':
            zeon_prefix = 'IDD TBD'
        else:
            # stack is test
            zeon_prefix = 'W:\\16Test1\\'
        # user_dir should have normal run designation, e.g., 2015-1
        user_dir = zeon_prefix + folder
        if os.path.exists(user_dir):
            win_path = os.path.normpath(user_dir)
            new_directory = win_path + '\\'
            prefix = new_directory + 'fScan_'
            index = '001'
            full_filename = prefix + index + '.npz'
            if not os.path.isfile(full_filename):
                pass
            else:
                # fast way to find the next file
                for each in range(4, -1, -1):
                    while os.path.isfile(full_filename):
                        incremented_index = str(int(index) + 10**each)
                        index = incremented_index.zfill(3)
                        full_filename = prefix + index + '.npz'
                    new_index = str(int(index) - 10**each)
                    index = new_index.zfill(3)
                    full_filename = prefix + index + '.npz'
                final_index = str(int(index) + 1).zfill(3)
                index = final_index
                overwrite_warn()
            return self.scan_directory.set(new_directory), self.scan_no.set(index)

    def calc_size(self):
        # should be called on every position validation
        i = self.rel_min.get()
        f = self.rel_max.get()
        p = self.npts.get()
        size = (f - i) / (p - 1)
        if self == fly_axis:
            msize = size*10000
            # print msize
            quotient = divmod(msize, 5)
            # print quotient
            if quotient[0] >= 1 and round(quotient[1], 5) == 0:
                fly_axis.flag.set(1)
                fly_axis.led.config(state=NORMAL)
                # print 'normal'
            elif quotient[0] == 0 and round(quotient[1], 0) == msize:
                fly_axis.flag.set(1)
                fly_axis.led.config(state=NORMAL)
                # print 'special'
            else:
                fly_axis.flag.set(0)
                fly_axis.led.config(state=DISABLED)
        return self.step_size.set('%.4f' % size)

    def axis_validate(self, event, *args):
        if not self.axis.get() == 'More' and not self.axis.get() == 'Custom':
            pass
        elif self.axis.get() == 'More':
            popup = Toplevel()
            xtop = root.winfo_x() + root.winfo_width() / 2 + 200
            ytop = root.winfo_y() + root.winfo_height() / 2 - 210
            popup.geometry('180x360+%d+%d' % (xtop, ytop))
            popup.title('Additional stages')
            popup.grab_set()
            label_1 = Label(popup, text='Please select a stage')
            label_1.pack(side=TOP, pady=10)
            for each in more_list:
                buttons = Radiobutton(popup, text=each, variable=self.axis,
                                      value=each, indicatoron=0, width=20,
                                      command=lambda: popup.destroy())
                buttons.pack(pady=2, ipady=1)
        elif self.axis.get() == 'Custom':
            custom_stage = StringVar()
            popup = Toplevel()
            xtop = root.winfo_x() + root.winfo_width() / 2 - 190
            ytop = root.winfo_y() + root.winfo_height() / 2 - 180
            popup.geometry('380x360+%d+%d' % (xtop, ytop))
            popup.title('Custom step stage definition')
            popup.grab_set()
            label_1 = Label(popup, text='Please enter a valid motor prefix')
            label_1.pack(side=TOP, pady=10)
            entry = Entry(popup, textvariable=custom_stage)
            entry.pack(pady=20)
            entry.bind('<Return>', lambda r: popup.destroy())
            button = Button(popup, text='OK', width=18, command=lambda: popup.destroy())
            button.pack(pady=10)
            frame_pick = Frame(popup)
            frame_pick.pack(pady=10)
            label_quickpick = Label(frame_pick, text='Quick picks')
            label_quickpick.grid(row=0, column=1, columnspan=2)
            if config.stack_choice.get() == 'BMB':
                button_200v_curve = Button(frame_pick, text='Laue KB VFM Curvature', width=20, command=lambda: custom_stage.set('16BMA:pm27'))
                button_200v_curve.grid(row=1, column=1, padx=5, pady=5)
                button_200v_elip = Button(frame_pick, text='Laue KB VFM Ellipticity', width=20, command=lambda: custom_stage.set('16BMA:pm28'))
                button_200v_elip.grid(row=2, column=1, padx=5, pady=5)
                button_100v_curve = Button(frame_pick, text='Laue KB HFM Curvature', width=20, command=lambda: custom_stage.set('16BMA:pm25'))
                button_100v_curve.grid(row=1, column=2, padx=5, pady=5)
                button_100v_elip = Button(frame_pick, text='Laue KB HFM Ellipticity', width=20, command=lambda: custom_stage.set('16BMA:pm26'))
                button_100v_elip.grid(row=2, column=2, padx=5, pady=5)
            elif config.stack_choice.get() == 'BMDHL':
                button_320v_curve = Button(frame_pick, text='Vertical Curvature', width=20, command=lambda: custom_stage.set('16BMD:pm23'))
                button_320v_curve.grid(row=1, column=1, padx=5, pady=5)
                button_320v_elip = Button(frame_pick, text='Vertical Ellipticity', width=20, command=lambda: custom_stage.set('16BMD:pm24'))
                button_320v_elip.grid(row=2, column=1, padx=5, pady=5)
                button_320h_curve = Button(frame_pick, text='Horizontal Curvature', width=20, command=lambda: custom_stage.set('16BMD:pm19'))
                button_320h_curve.grid(row=1, column=2, padx=5, pady=5)
                button_320h_elip = Button(frame_pick, text='Horizontal Ellipticity', width=20, command=lambda: custom_stage.set('16BMD:pm20'))
                button_320h_elip.grid(row=2, column=2, padx=5, pady=5)
            elif config.stack_choice.get() == ('GPHP' or 'GPHL'):
                button_320v_curve = Button(frame_pick, text='320mm VKB Curvature', width=20, command=lambda: custom_stage.set('16IDB:pm15'))
                button_320v_curve.grid(row=1, column=1, padx=5, pady=5)
                button_320v_elip = Button(frame_pick, text='320mm VKB Ellipticity', width=20, command=lambda: custom_stage.set('16IDB:pm16'))
                button_320v_elip.grid(row=2, column=1, padx=5, pady=5)
                button_320h_curve = Button(frame_pick, text='320mm HKB Curvature', width=20, command=lambda: custom_stage.set('16IDB:pm19'))
                button_320h_curve.grid(row=3, column=1, padx=5, pady=5)
                button_320h_elip = Button(frame_pick, text='320mm HKB Ellipticity', width=20, command=lambda: custom_stage.set('16IDB:pm20'))
                button_320h_elip.grid(row=4, column=1, padx=5, pady=5)
                button_200v_curve = Button(frame_pick, text='200mm VKB Curvature', width=20, command=lambda: custom_stage.set('16IDB:pm5'))
                button_200v_curve.grid(row=1, column=2, padx=5, pady=5)
                button_200v_elip = Button(frame_pick, text='200mm VKB Ellipticity', width=20, command=lambda: custom_stage.set('16IDB:pm6'))
                button_200v_elip.grid(row=2, column=2, padx=5, pady=5)
                button_100h_curve = Button(frame_pick, text='100mm HKB Curvature', width=20, command=lambda: custom_stage.set('16IDB:pm3'))
                button_100h_curve.grid(row=3, column=2, padx=5, pady=5)
                button_100h_elip = Button(frame_pick, text='100mm HKB Ellipticity', width=20, command=lambda: custom_stage.set('16IDB:pm4'))
                button_100h_elip.grid(row=4, column=2, padx=5, pady=5)
            elif config.stack_choice.get() == 'IDBLH':
                button_320v_curve = Button(frame_pick, text='LH VKB Curvature', width=20, command=lambda: custom_stage.set('16IDB:pm23'))
                button_320v_curve.grid(row=1, column=1, padx=5, pady=5)
                button_320v_elip = Button(frame_pick, text='LH VKB Ellipticity', width=20, command=lambda: custom_stage.set('16IDB:pm24'))
                button_320v_elip.grid(row=2, column=1, padx=5, pady=5)
                button_320h_curve = Button(frame_pick, text='LH HKB Curvature', width=20, command=lambda: custom_stage.set('16IDB:pm27'))
                button_320h_curve.grid(row=1, column=2, padx=5, pady=5)
                button_320h_elip = Button(frame_pick, text='LH HKB Ellipticity', width=20, command=lambda: custom_stage.set('16IDB:pm28'))
                button_320h_elip.grid(row=2, column=2, padx=5, pady=5)
            elif config.stack_choice.get() == 'IDD':
                button_320v_curve = Button(frame_pick, text='Vert Curvature', width=20, command=lambda: custom_stage.set('16IDD:pm19'))
                button_320v_curve.grid(row=1, column=1, padx=5, pady=5)
                button_320v_elip = Button(frame_pick, text='Vert Ellipticity', width=20, command=lambda: custom_stage.set('16IDD:pm20'))
                button_320v_elip.grid(row=2, column=1, padx=5, pady=5)
                button_400h_curve = Button(frame_pick, text='Horiz Curvature', width=20, command=lambda: custom_stage.set('16IDD:pm15'))
                button_400h_curve.grid(row=1, column=2, padx=5, pady=5)
                button_400h_elip = Button(frame_pick, text='Horiz Ellipticity', width=20, command=lambda: custom_stage.set('16IDD:pm16'))
                button_400h_elip.grid(row=2, column=2, padx=5, pady=5)
            entry.focus_set()
            root.wait_window(popup)
            prefix = custom_stage.get()
            try:
                self.mCustom = Motor(prefix, timeout=1.0)
            except:
                showwarning('Invalid entry',
                            'Cannot connect to %s, please try again' % prefix)
                self.axis.set(step_list[1])
                return
            name = step_axis.mCustom.description
            self.axis.set(name)

    def min_validate(self, event):
        try:
            val = self.rel_min.get()
            isinstance(val, float)
            if val < self.rel_max.get():
                self.rel_min.set('%.3f' % val)
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            forced_min = self.rel_max.get() - 0.1
            self.rel_min.set('%.3f' % forced_min)
            self.calc_size()
            invalid_entry()

    def max_validate(self, event):
        try:
            val = self.rel_max.get()
            isinstance(val, float)
            if val > self.rel_min.get():
                self.rel_max.set('%.3f' % val)
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            forced_max = self.rel_min.get() + 0.1
            self.rel_max.set('%.3f' % forced_max)
            self.calc_size()
            invalid_entry()

    def npts_validate(self, *event):
        try:
            val = self.npts.get()
            isinstance(val, int)
            if val > 1:
                self.calc_size()
            else:
                raise ValueError
        except ValueError:
            self.npts.set(11)
            self.calc_size()
            invalid_entry()


class ScanActions:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.exp_time = DoubleVar()
        self.exp_time.set('%.3f' % 0.02)

        # define and place widgets
        self.label_exp_time = Label(self.frame, text='COUNT TIME (sec)',
                                    bg='light blue', width=20)
        self.label_exp_time.grid(row=0, column=0)
        self.entry_exp_time = Entry(self.frame, textvariable=self.exp_time,
                                    width=8, bg='light blue')
        self.entry_exp_time.grid(row=0, column=1, padx=10)
        self.entry_exp_time.bind('<FocusOut>', self.exp_time_validate)
        self.entry_exp_time.bind('<Return>', self.exp_time_validate)
        self.button_start_flyscan = Button(self.frame, text='START SCAN',
                                           width=25, bg='light blue',
                                           command=self.start_scan)
        self.button_start_flyscan.grid(row=0, column=2, padx=20, pady=5)
        self.button_fly_y = Button(self.frame, text='Fly y', bg='light blue',
                                   command=self.fly_y)
        self.button_fly_y.grid(row=0, column=3, padx=3)
        self.button_fly_z = Button(self.frame, text='Fly z', bg='light blue',
                                   command=self.fly_z)
        self.button_fly_z.grid(row=0, column=4, padx=3)

    def exp_time_validate(self, event):
        # value must be float larger than 0.008 (max frequency of PILATUS)
        try:
            val = self.exp_time.get()
            isinstance(val, float)
            if val >= 0.008:
                self.exp_time.set('%.3f' % val)
            else:
                raise ValueError
        except ValueError:
            self.exp_time.set('%.3f' % 0.2)
            invalid_entry()

    def fly_y(self):
        fly_axis.axis.set(fly_list[0])
        self.start_scan()

    def fly_z(self):
        fly_axis.axis.set(fly_list[1])
        self.start_scan()

    def start_scan(self):
        t_zero = time.clock()
        abort.put(0)
        # ensure scan directory and number have been specified
        if step_axis.scan_directory.get() == 'Select directory before scan':
            showwarning('Unspecified file destination',
                        'Please select a valid scan directory and try again')
            return
        # if writing ascii file, ensure user directory exists
        if image.ascii_flag.get():
            if image.label2_user_path.cget('bg') == 'red':
                showwarning('Directory does not exist',
                            'Please select a valid folder for writing ASCII file and try again')
                return
        # generate filename and make sure it does not already exist
        prefix = step_axis.scan_directory.get() + 'fScan_'
        index = step_axis.scan_no.get()
        path = prefix + index
        full_filename = path + '.npz'
        if not os.path.isfile(full_filename):
            data.current_file.set(full_filename)
        else:
            while os.path.isfile(full_filename):
                incremented_index = str(int(index) + 1)
                index = incremented_index.zfill(3)
                path = prefix + index
                full_filename = path + '.npz'
            step_axis.scan_no.set(index)
            data.current_file.set(full_filename)
            overwrite_warn()
        # enter step stage info for centering scans
        if center.c_flag.get():
            step_axis.flag.set(1)
            step_axis.axis.set(mW.DESC)
            omega = float(center.delta_w.get())
            step_axis.rel_min.set('-' + '%.3f' % omega)
            step_axis.rel_max.set('%.3f' % omega)
            step_axis.npts.set(3)
            step_axis.calc_size()
        # prevent flying and stepping the same stage
        if step_axis.axis.get() == fly_axis.axis.get() and step_axis.flag.get():
            showwarning('Stage overworked',
                        'Stage cannot step and fly at the same time\n'
                        'Please select different stage(s) and try again')
            return
        if fly_axis.axis.get() == 'More' or step_axis.axis.get() == 'More':
            showwarning('No Stage Specified',
                        'No stage specified for one or more axes\n'
                        'Please select valid stage(s) and try again')
            return
        # double-check that npts and step size work together
        fly_axis.npts_validate()
        step_axis.npts_validate()
        if not fly_axis.flag.get():
            showwarning('Scan aborted',
                        'Modify Fly axis parameters until you have a green light')
            return
        # make sure long count times are intentional
        if self.exp_time.get() > 0.200:
            if not askyesno('Confirm long count time',
                            'Count time per point is more than 0.2 seconds.\n'
                            'Do you want to continue?'):
                return
        # write in active elements and determine dimension
        if not step_axis.flag.get():
            step_npts = 1
            v_active = 'Counts'
        else:
            step_npts = step_axis.npts.get()
            v_active = step_axis.axis.get()
        core.dimension = step_npts
        # define temporary EPICS motor devices, fly velocity, and scan endpoints
        controller, mFly, sg_input, v_max = stage_dict[fly_axis.axis.get()]
        if step_axis.axis.get() in stage_dict:
            mStep = stage_dict[step_axis.axis.get()][1]
        else:
            mStep = step_axis.mCustom
        mFly_ipos = mFly.RBV
        mStep_ipos = mStep.RBV
        perm_velo = mFly.VELO
        perm_bdst = mFly.BDST
        perm_count = self.exp_time.get()
        min_v = mFly.VBAS
        max_v = v_max
        if controller == 'MAXV':
            # must calculate user positions, etc. based on exact number of motor steps
            resolution = abs(mFly.MRES)
            micro_steps = round(fly_axis.step_size.get()/resolution)
            new_step_size = micro_steps*resolution
            temp_velo = new_step_size/self.exp_time.get()
            # must do temp_velo check here for steppers
            if min_v <= temp_velo <= max_v:
                pass
            elif temp_velo < min_v:
                max_count = float(new_step_size/min_v)
                showwarning('Velocity warning',
                            'Calculated velocity too slow for stage capabilities\n'
                            'Try a COUNT TIME less than %.3f seconds.' % max_count)
                return
            else:
                # count time is too short, auto fill for small differences
                min_count = float(new_step_size/max_v)
                if min_count <= 1.000:
                    self.exp_time.set('%.3f' % min_count)
                    self.entry_exp_time.configure(bg='red')
                    root.update_idletasks()
                    temp_velo = max_v
                else:
                    showwarning('Velocity warning',
                             'Calculated velocity exceeds stage capabilities\n'
                             'Try a COUNT TIME greater than %.3f seconds.' % min_count)
                    return
            # end temp_velo check, resume calculations for MAXV controller
            new_rel_min = fly_axis.rel_min.get()*new_step_size/fly_axis.step_size.get()
            new_rel_max = fly_axis.rel_max.get()*new_step_size/fly_axis.step_size.get()
            abs_step_plot_min = mStep_ipos + step_axis.rel_min.get()
            abs_step_plot_max = mStep_ipos + step_axis.rel_max.get()
            abs_fly_plot_min = mFly_ipos + new_rel_min + 0.5*new_step_size
            abs_fly_plot_max = mFly_ipos + new_rel_max - 0.5*new_step_size
            abs_fly_min = mFly_ipos + new_rel_min
            abs_fly_max = mFly_ipos + new_rel_max
            accl_steps = round((mFly.VBAS + temp_velo)/2*mFly.ACCL/resolution*1.25)
            accl_distance = accl_steps*resolution
            fly_zero = abs_fly_min - accl_distance
            fly_final = abs_fly_max + accl_distance
            # accl_plus_fly_steps = (abs_fly_max - fly_zero)/resolution
        elif controller == 'XPS':
            # controller must be XPS (for now)
            temp_velo = fly_axis.step_size.get()/self.exp_time.get()
            # ### 8 Dec 2016 for XPS this will be handled by a direct command to XPS ***
            # temp_velo check
            if min_v <= temp_velo <= max_v:
                pass
            else:
                min_count = float(fly_axis.step_size.get()/max_v)
                showwarning('Velocity warning',
                            'Calculated velocity exceeds stage capabilities\n'
                            'Try a COUNT TIME greater than %.3f seconds.' % min_count)
                return
            # end temp velo check, resume calculations
            # ### 8 Dec 2016 end part to edit out
            abs_step_plot_min = mStep_ipos + step_axis.rel_min.get()
            abs_step_plot_max = mStep_ipos + step_axis.rel_max.get()
            abs_fly_plot_min = mFly_ipos + fly_axis.rel_min.get() + 0.5*fly_axis.step_size.get()
            abs_fly_plot_max = mFly_ipos + fly_axis.rel_max.get() - 0.5*fly_axis.step_size.get()
            abs_fly_min = mFly_ipos + fly_axis.rel_min.get()
            abs_fly_max = mFly_ipos + fly_axis.rel_max.get()
            fly_zero = abs_fly_min - temp_velo * mW.ACCL * 1.5
            fly_final = abs_fly_max + temp_velo * mW.ACCL * 1.5
            # make trajectory and establish communication with XPS
            make_trajectory(zero=fly_zero, min=abs_fly_min, max=abs_fly_max, velo=temp_velo, motor=mFly)
            myxps = XPS_Q8_drivers.XPS()
            socketId = myxps.TCP_ConnectToServer(xps_ip, 5001, 20)
            # do temp_velo check here for XPS
            dynamics_check = myxps.MultipleAxesPVTVerification(socketId, 'M', 'traj.trj')
            print dynamics_check[0]
            if not dynamics_check[0] == 0:
                showwarning('Velocity warning',
                            'Calculated velocity exceeds stage capabilities\n'
                            'Try increasing count time (or increasing number of steps).')
                myxps.TCP_CloseSocket(socketId)
                return
        else:
            # controller must be HEX (for now)
            temp_velo = fly_axis.step_size.get() / self.exp_time.get()
            # ### 8 Dec 2016 for XPS this will be handled by a direct command to XPS ***
            # temp_velo check
            if min_v <= temp_velo <= max_v:
                pass
            else:
                min_count = float(fly_axis.step_size.get() / max_v)
                showwarning('Velocity warning',
                            'Calculated velocity exceeds stage capabilities\n'
                            'Try a COUNT TIME greater than %.3f seconds.' % min_count)
                return
            # end temp velo check, resume calculations
            # ### 8 Dec 2016 end part to edit out
            abs_step_plot_min = mStep_ipos + step_axis.rel_min.get()
            abs_step_plot_max = mStep_ipos + step_axis.rel_max.get()
            abs_fly_plot_min = mFly_ipos + fly_axis.rel_min.get() + 0.5 * fly_axis.step_size.get()
            abs_fly_plot_max = mFly_ipos + fly_axis.rel_max.get() - 0.5 * fly_axis.step_size.get()
            abs_fly_min = mFly_ipos + fly_axis.rel_min.get()
            abs_fly_max = mFly_ipos + fly_axis.rel_max.get()
            fly_zero = abs_fly_min - temp_velo * mW.ACCL * 1.5
            fly_final = abs_fly_max + temp_velo * mW.ACCL * 1.5
            # make trajectory and establish communication with A3200
            exp_time = self.exp_time.get()
            npts = fly_axis.npts.get()
            if mFly == mX:
                f_motor = 'X'
            elif mFly == mY:
                f_motor = 'Y'
            elif mFly == mZ:
                f_motor = 'Z'
            elif mFly == mW:
                f_motor = 'C'
            else:
                print 'cannot resolve mFly and f_motor'
            make_hex_fly(zero=fly_zero, min=abs_fly_min, max=abs_fly_max, velocity=temp_velo,
                         motor=f_motor, exp_time=exp_time, num_pts=npts)

        # initialize core arrays of the proper dimension
        core.FLY = np.linspace(abs_fly_plot_min, abs_fly_plot_max, fly_axis.npts.get() - 1)
        core.STP = np.linspace(abs_step_plot_min, abs_step_plot_max, step_axis.npts.get())
        core.TIM = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.FOE = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.REF = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.BSD = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.RMD = np.ones((step_npts, fly_axis.npts.get() - 1))
        # limit check
        step_zero = mStep_ipos + step_axis.rel_min.get()
        step_final = mStep_ipos + step_axis.rel_max.get()
        fll = mFly.within_limits(fly_zero)
        fhl = mFly.within_limits(fly_final)
        sll = mStep.within_limits(step_zero)
        shl = mStep.within_limits(step_final)
        limit_check = False
        if not step_axis.flag.get():
            if fll and fhl:
                limit_check = True
        else:
            if fll and fhl and sll and shl:
                limit_check = True
        if limit_check:
            pass
        else:
            showwarning('Limit Check Failed', 'One or more stage target(s) exceed limits')
            self.exp_time.set('%.3f' % perm_count)
            self.entry_exp_time.configure(bg='light blue')
            if controller == 'XPS':
                myxps.TCP_CloseSocket(socketId)
            return
        # end of pre-flight checks, scan will now proceed unless aborted
        # disable scan buttons so only one scan can be started
        # provide indication that scan is taking place
        self.button_start_flyscan.config(state=DISABLED, text='Scanning . . .')
        self.button_fly_y.config(state=DISABLED)
        self.button_fly_z.config(state=DISABLED)
        # clear plot and fields
        plt.clf()
        data.current_slice.set(1)
        data.slice_flag.set(0)
        data.index.set(1)
        center.y_minus_pos.set('')
        center.y_center_pos.set('')
        center.y_plus_pos.set('')
        center.delta_x.set('')
        center.delta_y.set('')
        center.delta_y_base.set('')
        center.absolute_x.set('')
        center.absolute_y.set('')
        center.absolute_y_base.set('')
        hax.min_pos.set('')
        hax.mid_pos.set('')
        hax.max_pos.set('')
        hax.width.set('')
        hax.delta_pos.set('')
        vax.min_pos.set('')
        vax.mid_pos.set('')
        vax.max_pos.set('')
        vax.width.set('')
        # write active stages, draw blank canvas, and update GUI
        vax.active_stage.set(v_active)
        h_active = fly_axis.axis.get()
        hax.active_stage.set(h_active)
        plt.gcf().canvas.draw()
        framePlot.update_idletasks()
        # set up softglue
        softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
        if controller == 'MAXV':
            sg_config.put('name2', 'step_master', wait=True)
            sg_config.put('loadConfig2.PROC', 1, wait=True)
            sg_config.put('loadConfig2.PROC', 1, wait=True)
            softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
            softglue.put('DnCntr-1_PRESET', accl_steps, wait=True)
            softglue.put('DivByN-1_N', micro_steps, wait=True)
        else:
            # controller must be XPS or HEX
            sg_config.put('name2', 'xps_master', wait=True)
            sg_config.put('loadConfig2.PROC', 1, wait=True)
            sg_config.put('loadConfig2.PROC', 1, wait=True)
            softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
            softglue.put('DnCntr-1_PRESET', 1, wait=True)
        softglue.put(sg_input, 'motor', wait=True)
        softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
        # enter for loop for npts flyscans
        for steps in range(step_npts):
            # for dimension > 1, give chance to abort before each pass
            if not abort.get():
                pass
            else:
                print 'scan aborted'
                break
            # make first move(s)
            if step_npts != 1:
                step_rel = step_axis.rel_min.get() + steps * step_axis.step_size.get()
                step_abs = mStep_ipos + step_rel
                mStep.move(step_abs, wait=True)
            mFly.move(fly_zero, wait=True)
            time.sleep(.25)
            # set temporary (scan) velocity and zero backlash (for MAXV only)
            if controller == 'MAXV':
                mFly.VELO = temp_velo
                mFly.BDST = 0
            # initialize struck for collection
            mcs.stop()
            mcs.ExternalMode()
            mcs.put('InputMode', 3, wait=True)
            mcs.put('OutputMode', 3, wait=True)
            mcs.put('OutputPolarity', 0, wait=True)
            mcs.put('LNEStretcherEnable', 0, wait=True)
            mcs.NuseAll = fly_axis.npts.get() - 1
            # reset softglue for fresh counting
            softglue.put('BUFFER-1_IN_Signal', '1!', wait=True)
            # initialize and arm detector if necessary
            if image.enable_flag.get():
                prefix = image.user_path.get() + image.sample_name.get() + '_'
                image_no = image.image_no.get()
                suffix = '.tif'
                first_filename = prefix + image_no + suffix
                # print first_filename
                if not os.path.isfile(first_filename):
                    pass
                else:
                    while os.path.isfile(first_filename):
                        incremented_index = str(int(image_no) + 1)
                        image_no = incremented_index.zfill(3)
                        first_filename = prefix + image_no + suffix
                    image.image_no.set(image_no)
                    overwrite_warn()
                detector.AcquirePeriod = self.exp_time.get()
                detector.AcquireTime = self.exp_time.get() - 0.003
                detector.FileName = image.sample_name.get()
                detector.TriggerMode = 2
                detector.FileNumber = int(image.image_no.get())
                detector.NumImages = fly_axis.npts.get() - 1
                detector.Acquire = 1
            # Final actions plus data collection move
            mcs.start()
            if controller == 'MAXV':
                mFly.move(fly_final, wait=True)
            elif controller == 'XPS':
                myxps.MultipleAxesPVTPulseOutputSet(socketId, 'M', 2, 3, self.exp_time.get())
                myxps.MultipleAxesPVTExecution(socketId, 'M', 'traj.trj', 1)
                # mFly.move(fly_final, wait=True)
            else:
                # controller must be HEX
                edsIP = "164.54.164.194"
                edsPORT = 8000
                MESSAGE1 = 'PROGRAM 1 LOAD "S:\\Hexfly\\fs.pgm"\n'
                MESSAGE2 = 'PROGRAM 1 START\n'

                srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                srvsock.settimeout(3)  # 3 second timeout on commands
                srvsock.connect((edsIP, edsPORT))
                srvsock.send(MESSAGE1)
                response = srvsock.recv(4096)
                print "received message:", response
                srvsock.send(MESSAGE2)
                response = srvsock.recv(4096)
                print "received message:", response
                srvsock.close()
            hex_wait = fly_axis.npts.get()*scan.exp_time.get() + 2.0
            print hex_wait
            time.sleep(hex_wait)
            print 'wait done'
            if image.enable_flag.get():
                while detector.Acquire:
                    time.sleep(0.1)
                image_number = detector.FileNumber + detector.NumImages - 1
                str_image_number = str(image_number)
                image.image_no.set(str_image_number.zfill(3))
                detector.FileNumber = int(image_number)
            # Check enough pulses received, if not, notify user and recover
            pulses = softglue.get('UpCntr-2_COUNTS')
            if pulses >= fly_axis.npts.get():
                # handle data
                stack = config.stack_choice.get()
                if stack == 'BMB':
                    TIM_ara = mcs.readmca(1)
                    FOE_ara = mcs.readmca(1)
                    REF_ara = mcs.readmca(1)
                    BSD_ara = mcs.readmca(1)
                    RMD_ara = mcs.readmca(1)
                elif stack == 'BMDHL':
                    TIM_ara = mcs.readmca(1)
                    FOE_ara = mcs.readmca(2)
                    REF_ara = mcs.readmca(2)
                    BSD_ara = mcs.readmca(3)
                    RMD_ara = mcs.readmca(3)
                elif stack == 'IDD':
                    TIM_ara = mcs.readmca(1)
                    FOE_ara = mcs.readmca(1)
                    REF_ara = mcs.readmca(5)
                    BSD_ara = mcs.readmca(1)
                    RMD_ara = mcs.readmca(7)
                else:
                    # stack belongs to IDB
                    TIM_ara = mcs.readmca(1)
                    FOE_ara = mcs.readmca(5)
                    REF_ara = mcs.readmca(4)
                    BSD_ara = mcs.readmca(6)
                    RMD_ara = mcs.readmca(3)
                # ###replace below in future
                # ###elif stack == 'GPHP' or stack == 'GPHL' or stack == 'IDBLH':
                # ###    TIM_ara = mcs.readmca(1)
                # ###    FOE_ara = mcs.readmca(5)
                # ###    REF_ara = mcs.readmca(4)
                # ###    BSD_ara = mcs.readmca(6)
                # ###    RMD_ara = mcs.readmca(3)
                TIM_ara_bit = TIM_ara[:fly_axis.npts.get() - 1]
                FOE_ara_bit = FOE_ara[:fly_axis.npts.get() - 1]
                REF_ara_bit = REF_ara[:fly_axis.npts.get() - 1]
                BSD_ara_bit = BSD_ara[:fly_axis.npts.get() - 1]
                RMD_ara_bit = RMD_ara[:fly_axis.npts.get() - 1]
                core.TIM[steps] = TIM_ara_bit
                core.FOE[steps] = FOE_ara_bit
                core.REF[steps] = REF_ara_bit
                core.BSD[steps] = BSD_ara_bit
                core.RMD[steps] = RMD_ara_bit
            else:
                # print 'moving on this time'
                showwarning('Pulse Count Error', message=('Stage failed to generate enough pulses \n'
                            'Please try the following: \n'
                            'Reduce count time, e.g., to 0.020 s\n'
                            'Increase step size, e.g., greater than 0.001\n'
                            'Ask you local contact for assistance'))
            mFly.VELO = perm_velo
            mFly.BDST = perm_bdst
            update_plot()
            # try this for not responding, possibly remove
            framePlot.update()
        # recover
        if image.enable_flag.get():
            detector.TriggerMode = 0
            detector.NumImages = 1
            image.enable_flag.set(0)
        softglue.put(sg_input, '')
        mFly.move(mFly_ipos, wait=True)
        mStep.move(mStep_ipos, wait=True)
        self.exp_time.set('%.3f' % perm_count)
        self.entry_exp_time.configure(bg='light blue')
        # only save data from successful scan
        if pulses >= fly_axis.npts.get():
            np.savez(path,
                     dim=core.dimension,
                     v_act=v_active,
                     h_act=h_active,
                     fly=core.FLY,
                     stp=core.STP,
                     tim=core.TIM,
                     foe=core.FOE,
                     ref=core.REF,
                     bsd=core.BSD,
                     rmd=core.RMD)
            new_index = str(int(index) + 1)
            step_axis.scan_no.set(new_index.zfill(3))
        if image.ascii_flag.get():
            data.save_ascii()
        step_axis.flag.set(0)
        if center.c_flag.get():
            data.current_slice.set(1)
            data.slice_flag.set(1)
            update_plot()
        if controller == 'XPS':
            myxps.TCP_CloseSocket(socketId)
        self.button_start_flyscan.config(state=NORMAL, text='START SCAN')
        self.button_fly_y.config(state=NORMAL)
        self.button_fly_z.config(state=NORMAL)
        hax.calc_difference()
        t_elapsed = time.clock() - t_zero
        print t_elapsed


class Centering:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        # instance variable and set defaults
        self.c_flag = IntVar()
        self.delta_w = DoubleVar()
        self.y_minus_pos = StringVar()
        self.y_center_pos = StringVar()
        self.y_plus_pos = StringVar()
        self.delta_x = StringVar()
        self.absolute_x = StringVar()
        self.delta_y = StringVar()
        self.absolute_y = StringVar()
        self.delta_y_base = StringVar()
        self.absolute_y_base = StringVar()
        self.delta_w.set(6.0)

        # set up trace on c_flag to verify buttons are disabled
        self.c_flag.trace('w', self.disable_move_buttons)

        # make and place column headings
        self.head_center = Label(self.frame, text='CENTERING CONTROL')
        self.head_center.grid(row=0, column=0, columnspan=2, pady=5, stick='w')
        self.head_delta_w = Label(self.frame, text=u'\u0394 \u03c9')
        self.head_delta_w.grid(row=0, column=2)
        self.head_y_minus = Label(self.frame, text=u'y at \u03c9' + '-')
        self.head_y_minus.grid(row=0, column=3)
        self.head_y_center = Label(self.frame, text=u'y at \u03c9' + '0')
        self.head_y_center.grid(row=0, column=4)
        self.head_y_plus = Label(self.frame, text=u'y at \u03c9' + '+')
        self.head_y_plus.grid(row=0, column=5)
        self.head_delta_x = Label(self.frame, text='x correction')
        self.head_delta_x.grid(row=0, column=6)
        self.head_delta_y = Label(self.frame, text='y correction')
        self.head_delta_y.grid(row=0, column=7)
        self.head_absolute_x = Label(self.frame, text='Final target position ->')
        self.head_absolute_x.grid(row=2, column=4, columnspan=2)

        # make and place widgets
        self.cbox_c_flag = Checkbutton(self.frame, text='Enable', variable=self.c_flag)
        self.cbox_c_flag.grid(row=1, column=0, padx=5, pady=5)
        self.entry_delta_w = Entry(self.frame, textvariable=self.delta_w, width=8)
        self.entry_delta_w.grid(row=1, column=2, padx=5, pady=5)
        self.entry_delta_w.bind('<FocusOut>', self.delta_w_validate)
        self.entry_delta_w.bind('<Return>', self.delta_w_validate)
        self.label_y_minus = Label(self.frame, textvariable=self.y_minus_pos, relief=SUNKEN, width=8)
        self.label_y_minus.grid(row=1, column=3, padx=5, pady=5)
        self.label_y_center = Label(self.frame, textvariable=self.y_center_pos, relief=SUNKEN, width=8)
        self.label_y_center.grid(row=1, column=4, padx=5, pady=5)
        self.label_y_plus = Label(self.frame, textvariable=self.y_plus_pos, relief=SUNKEN, width=8)
        self.label_y_plus.grid(row=1, column=5, padx=5, pady=5)
        self.label_delta_x = Label(self.frame, textvariable=self.delta_x, relief=SUNKEN, width=8)
        self.label_delta_x.grid(row=1, column=6, padx=5, pady=5)
        self.label_delta_y = Label(self.frame, textvariable=self.delta_y, relief=SUNKEN, width=8)
        self.label_delta_y.grid(row=1, column=7, padx=5, pady=5)
        self.button_absolute_x = Button(self.frame, textvariable=self.absolute_x, command=self.move_x, width=7)
        self.button_absolute_x.grid(row=2, column=6, padx=5, pady=5)
        self.button_absolute_x.config(state=DISABLED)

    def calc_deltas(self):
        if not center.y_minus_pos.get() or not center.y_center_pos.get() or not center.y_plus_pos.get():
            return
        else:
            center.button_absolute_x.config(state=NORMAL, background='green')
            staff.button_move_all.config(state=NORMAL, background='green')
            ortho_factor = cos(radians(center.delta_w.get()))
            dsx_plus = ortho_factor*(float(center.y_plus_pos.get()) - float(center.y_center_pos.get()))
            dsx_minus = ortho_factor*(float(center.y_minus_pos.get()) - float(center.y_center_pos.get()))
            delta_x = (dsx_plus - dsx_minus)/2/(sin(radians(center.delta_w.get())))
            delta_y = (dsx_plus + dsx_minus)/2/(cos(radians(center.delta_w.get()))-1)
            delta_y_base = -delta_y
            abs_x = mX.RBV + delta_x
            abs_y = mY.RBV + delta_y
            abs_base = mYbase.RBV - delta_y
            center.delta_x.set('%.4f' % delta_x)
            center.delta_y.set('%.4f' % delta_y)
            center.delta_y_base.set('%.4f' % delta_y_base)
            center.absolute_x.set('%.4f' % abs_x)
            center.absolute_y.set('%.4f' % abs_y)
            center.absolute_y_base.set('%.4f' % abs_base)

    def delta_w_validate(self, *event):
        try:
            val = self.delta_w.get()
            isinstance(val, float)
            if not val > 0:
                raise ValueError
        except ValueError:
            self.delta_w.set(6.0)
            invalid_entry()

    def move_x(self):
        try:
            abs_x = float(self.absolute_x.get())
        except ValueError:
            return
        mX.move(abs_x, wait=True)
        self.c_flag.set(0)

    def move_all(self):
        try:
            abs_x = float(self.absolute_x.get())
            abs_y = float(self.absolute_y.get())
            abs_base = float(self.absolute_y_base.get())
        except ValueError:
            return
        mX.move(abs_x, wait=True)
        mY.move(abs_y, wait=True)
        mYbase.move(abs_base, wait=True)
        self.c_flag.set(0)

    def disable_move_buttons(self, *args):
        if not self.c_flag.get():
            self.button_absolute_x.config(state=DISABLED, background='SystemButtonFace')
            staff.button_move_all.config(state=DISABLED, background='SystemButtonFace')


class Counters:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variable and set defaults
        self.ref_flag = IntVar()
        self.i_signal = StringVar()
        self.i_ref = StringVar()
        self.scale = DoubleVar()
        self.data_type = StringVar()
        self.ref_flag.set(1)
        self.i_signal.set(counter_list[0])
        self.i_ref.set(counter_list[2])
        self.scale.set(10000)
        self.data_type_list = ['Counts', 'Derivative']
        self.data_type.set(self.data_type_list[0])
        self.max_scale = IntVar()
        self.min_scale = IntVar()
        self.levels = IntVar()
        self.max_scale.set(100)
        self.min_scale.set(0)
        self.levels.set(64)

        # setup trace on relevant values
        self.ref_flag.trace('w', update_plot)
        self.i_signal.trace('w', update_plot)
        self.i_ref.trace('w', update_plot)
        self.data_type.trace('w', update_plot)

        # make column headings
        self.head_counters = Label(self.frame, text='INTENSITY CONTROL')
        self.head_counters.grid(row=0, column=0, columnspan=2, pady=5, sticky='w')
        self.head_counter = Label(self.frame, text='Active counter', width=20)
        self.head_counter.grid(row=0, column=2)
        self.head_scale = Label(self.frame, text='Scale factor')
        self.head_scale.grid(row=0, column=4)
        self.head_time = Label(self.frame, text='Data type', width=16)
        self.head_time.grid(row=0, column=5)
        self.head_2d_scaling = Label(self.frame, text='----2D scaling----')
        self.head_2d_scaling.grid(row=0, column=6, columnspan=4)

        # define and place widgets
        self.check_ref_flag = Checkbutton(self.frame, variable=self.ref_flag)
        self.check_ref_flag.grid(row=2, column=0)
        self.label_i_signal = Label(self.frame, text='I(signal)')
        self.label_i_signal.grid(row=1, column=1, padx=5, pady=5)
        self.label_i_ref = Label(self.frame, text='I(reference)')
        self.label_i_ref.grid(row=2, column=1, padx=5, pady=5)
        self.select_i_signal = OptionMenu(self.frame, self.i_signal, *counter_list)
        self.select_i_signal.grid(row=1, column=2)
        self.select_i_ref = OptionMenu(self.frame, self.i_ref, *counter_list)
        self.select_i_ref.grid(row=2, column=2)
        self.x_label = Label(self.frame, text='X')
        self.x_label.grid(row=1, rowspan=2, column=3)
        self.entry_scale = Entry(self.frame, textvariable=self.scale, width=8)
        self.entry_scale.grid(row=1, rowspan=2, column=4)
        self.entry_scale.bind('<FocusOut>', self.scale_validate)
        self.entry_scale.bind('<Return>', self.scale_validate)
        self.entry_data_type = OptionMenu(self.frame, self.data_type, *self.data_type_list)
        self.entry_data_type.grid(row=1, rowspan=2, column=5, padx=0)
        self.entry_max_scale = Entry(self.frame, textvariable=self.max_scale, width=4)
        self.entry_max_scale.grid(row=1, column=7, padx=5, pady=5)
        self.entry_max_scale.bind('<FocusOut>', self.max_scale_validate)
        self.entry_max_scale.bind('<Return>', self.max_scale_validate)
        self.button_down_max = Button(self.frame, text='<', command=self.decrement_max)
        self.button_down_max.grid(row=1, column=6, pady=5)
        self.button_up_max = Button(self.frame, text='>', command=self.increment_max)
        self.button_up_max.grid(row=1, column=8, pady=5)
        self.entry_min_scale = Entry(self.frame, textvariable=self.min_scale, width=4)
        self.entry_min_scale.grid(row=2, column=7, padx=5, pady=5)
        self.entry_min_scale.bind('<FocusOut>', self.min_scale_validate)
        self.entry_min_scale.bind('<Return>', self.min_scale_validate)
        self.button_down_min = Button(self.frame, text='<', command=self.decrement_min)
        self.button_down_min.grid(row=2, column=6, pady=5)
        self.button_up_min = Button(self.frame, text='>', command=self.increment_min)
        self.button_up_min.grid(row=2, column=8, pady=5)
        self.entry_levels = Entry(self.frame, textvariable=self.levels, width=4)
        self.entry_levels.grid(row=1, rowspan=2, column=9, padx=10, pady=5)
        self.entry_levels.bind('<FocusOut>', self.levels_validate)
        self.entry_levels.bind('<Return>', self.levels_validate)

    def scale_validate(self, event):
        # allow negative numbers for now
        try:
            val = self.scale.get()
            isinstance(val, float)
            update_plot()
        except ValueError:
            self.scale.set(1.0)
            update_plot()
            invalid_entry()

    def max_scale_validate(self, event):
        try:
            val = self.max_scale.get()
            isinstance(val, int)
            if self.min_scale.get() < val <= 100:
                update_plot()
            else:
                raise ValueError
        except ValueError:
            self.max_scale.set(100)
            update_plot()
            invalid_entry()

    def min_scale_validate(self, event):
        try:
            val = self.min_scale.get()
            isinstance(val, int)
            if 0 <= val < self.max_scale.get():
                update_plot()
            else:
                raise ValueError
        except ValueError:
            self.min_scale.set(0)
            update_plot()
            invalid_entry()

    def levels_validate(self, event):
        try:
            val = self.levels.get()
            isinstance(val, int)
            if 4 <= val <= 128:
                update_plot()
            else:
                raise ValueError
        except ValueError:
            self.levels.set(64)
            update_plot()
            invalid_entry()

    def decrement_max(self):
        old_max = self.max_scale.get()
        new_max = old_max - 1
        if new_max > self.min_scale.get():
            self.max_scale.set(new_max)
            update_plot()
        else:
            pass

    def increment_max(self):
        old_max = self.max_scale.get()
        new_max = old_max + 1
        if new_max <= 100:
            self.max_scale.set(new_max)
            update_plot()
        else:
            pass

    def decrement_min(self):
        old_min = self.min_scale.get()
        new_min = old_min - 1
        if new_min >= 0:
            self.min_scale.set(new_min)
            update_plot()
        else:
            pass

    def increment_min(self):
        old_min = self.min_scale.get()
        new_min = old_min + 1
        if new_min < self.max_scale.get():
            self.min_scale.set(new_min)
            update_plot()
        else:
            pass


class Position:
    def __init__(self, master, label):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.active_stage = StringVar()
        self.min_pos = StringVar()
        self.mid_pos = StringVar()
        self.max_pos = StringVar()
        self.delta_pos = StringVar()
        self.width = StringVar()
        self.active_stage.set('None')

        # setup trace on relevant values
        self.min_pos.trace('w', self.calc_width)
        self.max_pos.trace('w', self.calc_width)
        self.mid_pos.trace('w', self.calc_difference)

        # make column headings
        if label == 'Horizontal axis':
            self.head_position = Label(self.frame, text='POSITION CONTROL')
            self.head_position.grid(row=0, column=0, columnspan=2, pady=5, stick='w')
            self.head_axis = Label(self.frame, text='Active element')
            self.head_axis.grid(row=0, column=2)
            self.head_cursor = Label(self.frame, text='Minimum')
            self.head_cursor.grid(row=0, column=3)
            self.head_cursor = Label(self.frame, text='Center')
            self.head_cursor.grid(row=0, column=4)
            self.head_cursor = Label(self.frame, text='Maximum')
            self.head_cursor.grid(row=0, column=5)
            self.head_cursor = Label(self.frame, text='Width')
            self.head_cursor.grid(row=0, column=6)

        # make and place widgets
        self.label_position = Label(self.frame, text=label, width=15)
        self.label_position.grid(row=1, column=0, padx=5, pady=5)
        self.label_axis = Label(self.frame, textvariable=self.active_stage, relief=SUNKEN, width=20)
        self.label_axis.grid(row=1, column=2, padx=5)
        if label == 'Horizontal axis':
            self.button_min_pos = Button(self.frame, textvariable=self.min_pos, command=self.move_min, width=7, fg='blue')
            self.button_min_pos.grid(row=1, column=3, padx=6)
            self.button_mid_pos = Button(self.frame, textvariable=self.mid_pos, command=self.move_mid, width=7, fg='red')
            self.button_mid_pos.grid(row=1, column=4, padx=7)
            self.button_max_pos = Button(self.frame, textvariable=self.max_pos, command=self.move_max, width=7, fg='blue')
            self.button_max_pos.grid(row=1, column=5, padx=6)
            self.label_width = Label(self.frame, textvariable=self.width, relief=SUNKEN, width=8)
            self.label_width.grid(row=1, column=6, padx=5)
        else:
            self.label_min_pos = Label(self.frame, textvariable=self.min_pos, width=8)
            self.label_min_pos.grid(row=1, column=3, padx=5)
            self.label_mid_pos = Label(self.frame, textvariable=self.mid_pos, relief=SUNKEN, width=8, fg='red')
            self.label_mid_pos.grid(row=1, column=4, padx=5)
            self.label_max_pos = Label(self.frame, textvariable=self.max_pos, width=8)
            self.label_max_pos.grid(row=1, column=5, padx=5)
            self.label_width = Label(self.frame, textvariable=self.width, width=8)
            self.label_width.grid(row=1, column=6, padx=5)

    def calc_width(self, *args):
        if core.dimension == 1 or data.slice_flag.get():
            try:
                self.width.set(str(float(self.max_pos.get()) - float(self.min_pos.get())))
            except ValueError:
                return

    def calc_difference(self, *args):
        # avoid doing cacl during scan, as it can give temporary/incorrect result
        if scan.button_start_flyscan.cget('state') == 'disabled':
            return
        # only execute calculation for 1D scans (although could work for 2D)
        if core.dimension == 1 or data.slice_flag.get():
            try:
                final_pos = float(hax.mid_pos.get())
            except ValueError:
                return
            stage = hax.active_stage.get()
            if stage in stage_dict:
                mH = stage_dict[stage][1]
                initial_pos = mH.RBV
                difference = final_pos - initial_pos
                self.delta_pos.set('%.4f' % difference)
            else:
                return

    def move_min(self):
        if core.dimension == 1:
            try:
                val = float(hax.min_pos.get())
            except ValueError:
                return
            stage = hax.active_stage.get()
            if stage in stage_dict:
                mH = stage_dict[stage][1]
                mH.move(val, wait=True)
            else:
                return
        else:
            try:
                h_val = float(hax.min_pos.get())
                v_val = float(vax.mid_pos.get())
            except ValueError:
                return
            h_stage = hax.active_stage.get()
            v_stage = vax.active_stage.get()
            if h_stage and v_stage in stage_dict:
                mH = stage_dict[h_stage][1]
                mH.move(h_val, wait=True)
                mV = stage_dict[v_stage][1]
                if not mV == mW:
                    mV.move(v_val, wait=True)
            elif h_stage in stage_dict and not v_stage in stage_dict:
                mH = stage_dict[h_stage][1]
                mH.move(h_val, wait=True)
                mV = step_axis.mCustom
                mV.move(v_val, wait=True)
            else:
                return

    def move_mid(self):
        if core.dimension == 1:
            try:
                val = float(hax.mid_pos.get())
            except ValueError:
                return
            stage = hax.active_stage.get()
            if stage in stage_dict:
                mH = stage_dict[stage][1]
                mH.move(val, wait=True)
            else:
                return
        else:
            try:
                h_val = float(hax.mid_pos.get())
                v_val = float(vax.mid_pos.get())
            except ValueError:
                return
            h_stage = hax.active_stage.get()
            v_stage = vax.active_stage.get()
            if h_stage and v_stage in stage_dict:
                mH = stage_dict[h_stage][1]
                mH.move(h_val, wait=True)
                mV = stage_dict[v_stage][1]
                if not mV == mW:
                    mV.move(v_val, wait=True)
            elif h_stage in stage_dict and not v_stage in stage_dict:
                mH = stage_dict[h_stage][1]
                mH.move(h_val, wait=True)
                mV = step_axis.mCustom
                mV.move(v_val, wait=True)
            else:
                return

    def move_max(self):
        if core.dimension == 1:
            try:
                val = float(hax.max_pos.get())
            except ValueError:
                return
            stage = hax.active_stage.get()
            if stage in stage_dict:
                mH = stage_dict[stage][1]
                mH.move(val, wait=True)
            else:
                return
        else:
            try:
                h_val = float(hax.max_pos.get())
                v_val = float(vax.mid_pos.get())
            except ValueError:
                return
            h_stage = hax.active_stage.get()
            v_stage = vax.active_stage.get()
            if h_stage and v_stage in stage_dict:
                mH = stage_dict[h_stage][1]
                mH.move(h_val, wait=True)
                mV = stage_dict[v_stage][1]
                if not mV == mW:
                    mV.move(v_val, wait=True)
            elif h_stage in stage_dict and not v_stage in stage_dict:
                mH = stage_dict[h_stage][1]
                mH.move(h_val, wait=True)
                mV = step_axis.mCustom
                mV.move(v_val, wait=True)
            else:
                return


class DataLoad:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.current_file = StringVar()
        self.slice_flag = IntVar()
        self.current_slice = IntVar()
        self.current_slice.set(1)
        self.index = IntVar()
        self.button_load = IntVar()

        # make and place widgets
        self.head_label = Label(self.frame, text='FILE CONTROL')
        self.head_label.grid(row=0, column=0, pady=5)
        self.label_cfile = Label(self.frame, text='Current Scan File')
        self.label_cfile.grid(row=1, column=0, padx=5, pady=5)
        self.display_cfile = Label(self.frame, textvariable=self.current_file, width=40, relief=SUNKEN, anchor='w')
        self.display_cfile.grid(row=1, column=1, columnspan=4, padx=5, pady=5)
        self.button_cfile = Button(self.frame, text='Load Data', command=self.load_data, width=11)
        self.button_cfile.grid(row=1, column=5, padx=5, pady=5)
        self.button_csave = Button(self.frame, text='Save ASCII', command=self.save_ascii, width=11)
        self.button_csave.grid(row=1, column=6, padx=5, pady=5)
        self.button_downfile = Button(self.frame, text='<', command=self.decrement_file)
        self.button_downfile.grid(row=1, column=7, padx=5, pady=5)
        self.button_upfile = Button(self.frame, text='>', command=self.increment_file)
        self.button_upfile.grid(row=1, column=8, padx=5, pady=5)
        self.cbox_slice_flag = Checkbutton(self.frame, text='2D Slice',
                                           variable=self.slice_flag,
                                           command=self.activate_slice)
        self.cbox_slice_flag.grid(row=2, column=0, pady=5)
        self.label_cslice = Label(self.frame, text='Current Slice')
        self.label_cslice.grid(row=2, column=1)
        self.button_downslice = Button(self.frame, text='<', command=self.decrement_slice)
        self.button_downslice.grid(row=2, column=2, sticky='W')
        self.display_cslice = Label(self.frame, textvariable=self.current_slice, width=4, relief=SUNKEN)
        self.display_cslice.grid(row=2, column=2)
        self.button_upslice = Button(self.frame, text='>', command=self.increment_slice)
        self.button_upslice.grid(row=2, column=2, sticky='E')
        self.label_index = Label(self.frame, text='Image index')
        self.label_index.grid(row=2, column=3, columnspan=2, sticky='E')
        self.display_index = Label(self.frame, textvariable=self.index, width=5, relief=SUNKEN)
        self.display_index.grid(row=2, column=5)

    def load_data(self):
        if not self.button_load.get():
            old_data = data.current_file.get()
            if not old_data == '':
                old_dir = os.path.dirname(old_data)
                if os.path.exists(old_dir):
                    data_file = askopenfilename(initialdir=old_dir)
                else:
                    data_file = askopenfilename()
            else:
                data_file = askopenfilename()
            try:
                if os.path.isfile(data_file):
                    cdata = np.load(data_file)
                else:
                    raise IOError
            except IOError:
                path_warn()
                return
        else:
            data_file = data.current_file.get()
            cdata = np.load(data_file)
            self.button_load.set(0)
        center.c_flag.set(0)
        data.slice_flag.set(0)
        data.current_slice.set(1)
        data.index.set(1)
        center.y_minus_pos.set('')
        center.y_center_pos.set('')
        center.y_plus_pos.set('')
        center.delta_x.set('')
        center.delta_y.set('')
        hax.min_pos.set('')
        hax.mid_pos.set('')
        hax.max_pos.set('')
        hax.width.set('')
        vax.min_pos.set('')
        vax.mid_pos.set('')
        vax.max_pos.set('')
        vax.width.set('')
        dimension = cdata['dim'][()]
        h_active = cdata['h_act'][()]
        v_active = cdata['v_act'][()]
        hax.active_stage.set(h_active)
        vax.active_stage.set(v_active)
        core.FLY = cdata['fly']
        core.STP = cdata['stp']
        core.TIM = cdata['tim']
        core.FOE = cdata['foe']
        core.REF = cdata['ref']
        core.RMD = cdata['rmd']
        core.BSD = cdata['bsd']
        data.current_file.set(data_file)
        core.dimension = dimension
        cdata.close()
        update_plot()

    def save_ascii(self):
        if core.dimension == 1:
            plot_type = '1D'
            vertical = 'n/a'
        elif not data.slice_flag.get():
            plot_type = '2D'
            vertical = 'Step stage: ' + vax.active_stage.get()
        else:
            dimension = str(core.dimension)
            slice = str(data.current_slice.get())
            plot_type = '2D slice ' + slice + ' of ' + dimension
            vertical = 'Step stage: ' + vax.active_stage.get()
        horizontal = 'Fly stage: ' + hax.active_stage.get()
        header_one = 'Plot type: ' + plot_type
        base = os.path.splitext(data.current_file.get())[0]
        textpath = base + '.txt'
        textfile = open(textpath, 'a')
        textfile.write(header_one + '\n' * 2)
        if core.dimension != 1 and not data.slice_flag.get():
            np.savetxt(textfile, core.STP, fmt='%6.4f', delimiter=', ', header=vertical, footer='\n', comments='')
        np.savetxt(textfile, core.FLY, fmt='%6.4f', delimiter=', ', header=horizontal, footer='\n', comments='')
        np.savetxt(textfile, core.SCA, fmt='%.10e', delimiter=', ', header='Scaled Intensity', footer='End scan data' + '\n' * 2, comments='')
        textfile.close()
        # option to automatically copy to user directory, esp. for 2d imaging, XRDI
        # need to clean up a bit once we get path selection figured out (in SXD, too)
        if image.ascii_flag.get():
            source = textpath
            filename = os.path.basename(textpath)
            if os.path.exists(image.user_path.get()):
                destination = image.user_path.get() + filename
                copyfile(source, destination)

    def decrement_file(self):
        current_file = data.current_file.get()
        if current_file == '':
            return
        cpath, cfile = os.path.split(current_file)[0], os.path.split(current_file)[1]
        current_number = int(cfile[6:-4])
        new_file = cpath + '/fScan_' + str(current_number - 1).zfill(3) + '.npz'
        print new_file
        if os.path.isfile(new_file):
            print 'made it here'
            data.current_file.set(new_file)
            self.button_load.set(1)
            self.load_data()

    def increment_file(self):
        current_file = data.current_file.get()
        if current_file == '':
            return
        cpath, cfile = os.path.split(current_file)[0], os.path.split(current_file)[1]
        current_number = int(cfile[6:-4])
        new_file = cpath + '/fScan_' + str(current_number + 1).zfill(3) + '.npz'
        print new_file
        if os.path.isfile(new_file):
            print 'made it here'
            data.current_file.set(new_file)
            self.button_load.set(1)
            self.load_data()

    def activate_slice(self):
        if core.dimension == 1:
            pass
        else:
            update_plot()

    def increment_slice(self):
        old_slice = data.current_slice.get()
        new_slice = old_slice + 1
        if new_slice <= core.dimension and data.slice_flag.get():
            data.current_slice.set(new_slice)
            update_plot()
        else:
            pass

    def decrement_slice(self):
        old_slice = data.current_slice.get()
        new_slice = old_slice - 1
        if new_slice > 0 and data.slice_flag.get():
            data.current_slice.set(new_slice)
            update_plot()
        else:
            pass


class Actions:
    """
    Big buttons that initiate data collection
    """

    def __init__(self, master):
        """
        :param master: frame for inserting widgets
        """
        self.frame = Frame(master, padx=10, pady=5)
        self.frame.pack()

        # define variables
        # ###self.abort = IntVar()
        # ###self.abort.set(0)

        # make big font
        bigfont = tkFont.Font(size=10, weight='bold')

        # make and place widgets
        self.button_abort = Button(self.frame, text='Overlays', height=2, width=14,
                                   font=bigfont, command=self.open_overlays)
        self.button_abort.grid(row=0, column=0, padx=8, pady=20)
        self.button_more = Button(self.frame, text='Imaging', height=2, width=14,
                                  font=bigfont, command=self.open_imaging)
        self.button_more.grid(row=0, column=1, padx=8, pady=20)
        self.button_staff = Button(self.frame,
                                   text='Alignment',
                                   height=2, width=14, font=bigfont,
                                   command=self.open_staff)
        self.button_staff.grid(row=0, column=2, padx=8, pady=20)
        self.quit_button = Button(self.frame, text='Quit', height=2, width=14,
                                  font=bigfont, command=close_quit)
        self.quit_button.grid(row=0, column=3, padx=8, pady=20)

    def open_overlays(self):
        if not alloverlays.popup.winfo_viewable():
            xtop = root.winfo_x()
            ytop = root.winfo_y() + root.winfo_height() + 40
            alloverlays.popup.geometry('+%d+%d' % (xtop, ytop))
        alloverlays.popup.deiconify()

    def open_imaging(self):
        if not image.popup.winfo_viewable():
            xtop = root.winfo_x() + 652
            ytop = root.winfo_y() + root.winfo_height() + 40
            image.popup.geometry('+%d+%d' % (xtop, ytop))
        image.popup.deiconify()

    def open_staff(self):
        if not staff.popup.winfo_viewable():
            xtop = root.winfo_x() + 652
            ytop = root.winfo_y() + root.winfo_height() + 40
            staff.popup.geometry('+%d+%d' % (xtop, ytop))
        staff.popup.deiconify()


class OverlayWindow:
    def __init__(self, master):
        self.popup = Toplevel(master)
        self.popup.title('Overlay Plots')
        self.frame = Frame(self.popup, width=676, height=158, bd=5, relief=RIDGE, padx=10, pady=5)
        self.frame.pack()

        # hide window on startup
        self.popup.withdraw()


class Overlay:
    def __init__(self, master, label):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.plot_flag = IntVar()
        self.overlay_file = StringVar()
        self.overlay_slice = IntVar()
        self.overlay_slice.set(1)

        # create default/dummy arrays
        self.FLY = np.linspace(-0.045, 0.045, 10)
        self.STP = np.linspace(-0.05, 0.05, 11)
        self.TIM = np.ones((11, 10))
        self.FOE = np.ones((11, 10))
        self.REF = np.ones((11, 10))
        self.RMD = np.ones((11, 10))
        self.BSD = np.ones((11, 10))
        self.SCA = np.ones((11, 10))
        self.dimension = 11

        # Make headings
        if label == 'over1':
            self.head_label = Label(self.frame, text='OVERLAY CONTROL')
            self.head_label.grid(row=0, column=0, columnspan=2, pady=5, sticky='W')
            self.head_slice = Label(self.frame, text='Current Slice')
            self.head_slice.grid(row=0, column=2, columnspan=3)

        # make and place widgets
        self.cbox_plot_flag = Checkbutton(self.frame,
                                             variable=self.plot_flag,
                                             command=self.activate_overlay)
        self.cbox_plot_flag.grid(row=1, column=0, pady=5)
        self.label_overlay_file = Label(self.frame, textvariable=self.overlay_file,
                                        width=40, relief=SUNKEN, anchor='w')
        self.label_overlay_file.grid(row=1, column=1, columnspan=1, padx=5, pady=5)
        self.button_downslice = Button(self.frame, text='<', command=self.decrement_slice)
        self.button_downslice.grid(row=1, column=2, sticky='W')
        self.display_overlay_slice = Label(self.frame, textvariable=self.overlay_slice, width=4, relief=SUNKEN)
        self.display_overlay_slice.grid(row=1, column=3, padx=5)
        self.button_upslice = Button(self.frame, text='>', command=self.increment_slice)
        self.button_upslice.grid(row=1, column=4, sticky='E')
        self.button_overlay_file = Button(self.frame, text='Load Data', command=self.load_overlay, width=11)
        self.button_overlay_file.grid(row=1, column=6, padx=5, pady=5)
        self.button_overlay_grab = Button(self.frame, text='Grab Data', command=self.grab_data, width=11)
        self.button_overlay_grab.grid(row=1, column=7, padx=5, pady=5)

    def activate_overlay(self):
        if not self.overlay_file.get():
            self.grab_data()
        update_plot()

    def decrement_slice(self):
        old_slice = self.overlay_slice.get()
        new_slice = old_slice - 1
        if new_slice > 0 and self.plot_flag.get():
            self.overlay_slice.set(new_slice)
            update_plot()
        else:
            pass

    def increment_slice(self):
        old_slice = self.overlay_slice.get()
        new_slice = old_slice + 1
        if new_slice <= self.dimension and self.plot_flag.get():
            self.overlay_slice.set(new_slice)
            update_plot()
        else:
            pass

    def load_overlay(self):
        old_data = self.overlay_file.get()
        if not old_data == '':
            old_dir = os.path.dirname(old_data)
            if os.path.exists(old_dir):
                data_file = askopenfilename(initialdir=old_dir)
            else:
                data_file = askopenfilename()
        else:
            old_data = data.current_file.get()
            if not old_data == '':
                old_dir = os.path.dirname(old_data)
                if os.path.exists(old_dir):
                    data_file = askopenfilename(initialdir=old_dir)
                else:
                    data_file = askopenfilename()
            else:
                data_file = askopenfilename()
        try:
            if os.path.isfile(data_file):
                cdata = np.load(data_file)
            else:
                raise IOError
        except IOError:
            path_warn()
            return
        dimension = cdata['dim'][()]
        # h_active = cdata['h_act'][()]
        # v_active = cdata['v_act'][()]
        # hax.active_stage.set(h_active)
        # vax.active_stage.set(v_active)
        self.FLY = cdata['fly']
        self.STP = cdata['stp']
        self.TIM = cdata['tim']
        self.FOE = cdata['foe']
        self.REF = cdata['ref']
        self.RMD = cdata['rmd']
        self.BSD = cdata['bsd']
        self.overlay_file.set(data_file)
        self.dimension = dimension
        if self.dimension > 1:
            o_slice = divmod(self.dimension, 2)[0]
            self.overlay_slice.set(o_slice)
        else:
            self.overlay_slice.set(1)
        cdata.close()
        self.plot_flag.set(1)
        update_plot()

    def grab_data(self):
        primary_data = data.current_file.get()
        if not primary_data == '':
            data_file = primary_data
            try:
                if os.path.isfile(data_file):
                    cdata = np.load(data_file)
                else:
                    raise IOError
            except IOError:
                path_warn()
                return
            dimension = cdata['dim'][()]
            # h_active = cdata['h_act'][()]
            # v_active = cdata['v_act'][()]
            # hax.active_stage.set(h_active)
            # vax.active_stage.set(v_active)
            self.FLY = cdata['fly']
            self.STP = cdata['stp']
            self.TIM = cdata['tim']
            self.FOE = cdata['foe']
            self.REF = cdata['ref']
            self.RMD = cdata['rmd']
            self.BSD = cdata['bsd']
            self.overlay_file.set(data_file)
            self.dimension = dimension
            primary_slice = data.current_slice.get()
            self.overlay_slice.set(primary_slice)
            cdata.close()
            self.plot_flag.set(1)
            update_plot()
        else:
            showinfo('Empty Dataset', 'There is no data to grab!')


class Images:
    def __init__(self, master):
        self.popup = Toplevel(master)
        self.popup.title('X-ray Imaging Tools')
        self.frame = Frame(self.popup, width=676, height=158, bd=5, relief=RIDGE, padx=10, pady=5)
        self.frame.pack()

        # define instance variables and set defaults
        self.enable_flag = IntVar()
        self.det_path = StringVar()
        self.user_path = StringVar()
        self.sample_name = StringVar()
        self.image_no = StringVar()
        self.temp_file = StringVar()
        self.dioptas_flag = IntVar()
        self.grid_flag = IntVar()
        self.ascii_flag = IntVar()
        self.enable_flag.set(0)
        self.user_path.set('Select directory before scan')
        # self.user_path.set('Z:\\Python Analysis\\ascii\\')
        self.sample_name.set('test')
        self.image_no.set('001')

        # make column headings
        self.head_images = Label(self.frame, text='IMAGE CONTROL')
        self.head_images.grid(row=0, column=0, columnspan=2, pady=5, sticky='w')

        # make and place widgets
        self.check_image_enable = Checkbutton(self.frame, text='Enable', variable=self.enable_flag, state=DISABLED)
        self.check_image_enable.grid(row=1, rowspan=2, column=0, columnspan=2)
        self.label_det_path = Label(self.frame, text='Detector path')
        self.label_det_path.grid(row=0, column=2, padx=5, pady=5)
        self.display_det_path = Label(self.frame, textvariable=self.det_path,
                                      width=40, relief=SUNKEN, anchor='w')
        self.display_det_path.grid(row=0, column=3, columnspan=3, pady=5)
        self.label_user_path = Label(self.frame, text='User directory')
        self.label_user_path.grid(row=1, column=2, padx=5, pady=5)
        self.label2_user_path = Label(self.frame, textvariable=self.user_path,
                                      relief=SUNKEN, width=40, anchor='w')
        self.label2_user_path.grid(row=1, column=3, columnspan=3, pady=5)
        # self.entry_user_path.bind('<FocusOut>', self.user_path_validation)
        # self.entry_user_path.bind('<Return>', self.user_path_validation)
        self.label_sample_name = Label(self.frame, text='Sample name')
        self.label_sample_name.grid(row=2, column=2, padx=5, pady=5)
        self.entry_sample_name = Entry(self.frame, textvariable=self.sample_name,
                                       width=35)
        self.entry_sample_name.grid(row=2, column=3, columnspan=2, pady=5)

        self.label_image_no = Label(self.frame, text='Image No.')
        self.label_image_no.grid(row=2, column=5, pady=5)
        self.entry_image_no = Entry(self.frame, textvariable=self.image_no,
                                    width=7)
        self.entry_image_no.grid(row=2, column=6, sticky='w', padx=5, pady=5)
        self.entry_image_no.bind('<FocusOut>', self.image_no_validation)
        self.entry_image_no.bind('<Return>', self.image_no_validation)
        self.button_path_select = Button(self.frame, text='Browse',
                                         command=self.choose_directory)
        self.button_path_select.grid(row=1, column=6, padx=5)
        self.button_initialize = Button(self.frame, text='Initialize', command=self.initialize)
        self.button_initialize.grid(row=3, column=0)
        self.cbox_activate_dioptas = Checkbutton(self.frame, text='Enable Dioptas', variable=self.dioptas_flag)
        # self.cbox_activate_dioptas.grid(row=3, column=3, padx=5, pady=5)
        self.cbox_write_ascii = Checkbutton(self.frame, text='Write ASCII', variable=self.ascii_flag)
        self.cbox_write_ascii.grid(row=3, column=4, padx=5, pady=5)

        # hide window on startup
        self.popup.withdraw()

    def initialize(self):
        # keep old style for now (0117) but limit to IDB
        stack = config.stack_choice.get()
        if not (stack == 'GPHL' or stack == 'GPHP' or stack == 'IDBLH'):
            showwarning('Connection Error',
                        'Cannot connect to detector\n'
                        'Imaging not currently available at this endstation')
            hide_image()
            return
        global detector
        detector = Device('HP1M-PIL1:cam1:', detector_args)
        detector.add_callback('FilePath_RBV', callback=path_put)
        path_put()
        self.check_image_enable.configure(state=NORMAL)
        # lines below are basic framework for future implementation at other endstations
        # ###custom_detector = StringVar()
        # ###popup = Toplevel()
        # ###xtop = root.winfo_x() + root.winfo_width() / 2 - 190
        # ###ytop = root.winfo_y() + root.winfo_height() / 2 - 180
        # ###popup.geometry('380x360+%d+%d' % (xtop, ytop))
        # ###popup.title('Area detector selection')
        # ###popup.grab_set()
        # ###label_1 = Label(popup, text='Please enter a valid detector prefix')
        # ###label_1.pack(side=TOP, pady=10)
        # ###entry = Entry(popup, textvariable=custom_detector)
        # ###entry.pack(pady=20)
        # ###entry.bind('<Return>', lambda r: popup.destroy())
        # ###button = Button(popup, text='OK', width=18, command=lambda: popup.destroy())
        # ###button.pack(pady=10)
        # ###frame_pick = Frame(popup)
        # ###frame_pick.pack(pady=10)
        # ###label_quickpick = Label(frame_pick, text='Quick picks')
        # ###label_quickpick.grid(row=0, column=1, columnspan=2)
        # ###button_pilatus = Button(frame_pick, text='PILATUS 1M', width=20,
        # ###                        command=lambda: custom_detector.set('HP1M-PIL1:cam1'))
        # ###button_pilatus.grid(row=1, column=1, padx=5, pady=5)
        # ###button_perkinelmer = Button(frame_pick, text='Perkin Elmer', width=20,
        # ###                            command=lambda: custom_detector.set('16PE:cam1'))
        # ###button_perkinelmer.grid(row=2, column=1, padx=5, pady=5)
        # ###entry.focus_set()
        # ###root.wait_window(popup)
        # ###prefix = custom_detector.get()
        # ###global detector
        # ###try:
        # ###    detector = Device(prefix, detector_args)
        # ###except:
        # ###    showwarning('Invalid entry',
        # ###                'Cannot connect to that detector')
        # ###    return
        # ###stack = config.stack_choice.get()
        # ###if prefix == 'HP1M-PIL1:cam1':
        # ###    if not (stack == 'GPHL' or stack == 'GPHP' or stack == 'IDBLH'):
        # ###        print 'crazy'

    def choose_directory(self):
        user_dir = askdirectory(title='Select a user directory')
        if user_dir and os.path.exists(user_dir):
            win_path = os.path.normpath(user_dir)
            return self.user_path.set(win_path + '\\')
        else:
            path_warn()

    def user_path_validation(self, event):
        val = self.user_path.get()
        if not (os.path.exists(val)):
            path_warn()
            return
        if val.endswith('\\'):
            pass
        else:
            self.user_path.set(val + '\\')

    def image_no_validation(self, *event):
        try:
            val = self.image_no.get()
            int(val)
            self.image_no.set(val.zfill(3))
        except ValueError:
            self.image_no.set('001')
            invalid_entry()

    def send_to_dioptas(self):
        # remove in 0117 version for now (and maybe forever)
        pass
        # current_directory = self.user_path.get()
        # while not os.path.exists(current_directory):
        #     self.choose_directory()
        #     current_directory = self.user_path.get()
        # os.chdir(current_directory)
        # filename = self.sample_name.get() + '_' + str(data.index.get()).zfill(3) + '.tif'
        # full_filename = current_directory + filename
        # if not os.path.isfile(full_filename):
        #     return
        # if not self.temp_file.get() == '':
        #     old_temp = current_directory + self.temp_file.get()
        #     if os.path.isfile(old_temp):
        #         os.remove(old_temp)
        # temp_image = fabio.open(filename=filename)
        # temp_name = 'temp' + filename
        # self.temp_file.set(temp_name)
        # time.sleep(.5)
        # temp_image.write(temp_name)


class Staff:
    def __init__(self, master):
        self.popup = Toplevel(master)
        self.popup.title('Alignment Tools')

        self.frame_fit = Frame(self.popup, bd=5, relief=RIDGE, padx=12, pady=10)
        self.frame_fit.grid(row=0, column=0, columnspan=2)
        self.frame_center = Frame(self.popup, bd=5, relief=RIDGE, padx=10, pady=10)
        self.frame_center.grid(row=1, column=0)
        self.frame_zero = Frame(self.popup, bd=5, relief=RIDGE, padx=9, pady=2)
        self.frame_zero.grid(row=1, column=1)

        # define instance variables and set defaults
        self.focus_flag = IntVar()
        self.pv_a = DoubleVar()
        self.pv_x0 = DoubleVar()
        self.pv_mul = DoubleVar()
        self.pv_mur = DoubleVar()
        self.pv_wl = DoubleVar()
        self.pv_wr = DoubleVar()
        self.pv_asymmetry = DoubleVar()
        self.pv_fwhm = DoubleVar()
        self.pv_beamsize = DoubleVar()
        self.popt = np.zeros(6)
        self.pcov = np.zeros(6)
        self.area = 0
        self.err = 0
        self.area_calc = 0

        # make frame_fit headings
        self.head_label = Label(self.frame_fit, text='PSEUDO-VOIGT PARAMETERS')
        self.head_label.grid(row=0, column=0)
        self.head_area = Label(self.frame_fit, text='Area')
        self.head_area.grid(row=0, column=2)
        self.head_x0 = Label(self.frame_fit, text='Center')
        self.head_x0.grid(row=0, column=3)
        self.head_eta = Label(self.frame_fit, text=u'\u03b7')
        self.head_eta.grid(row=0, column=4)
        self.head_width = Label(self.frame_fit, text='Width')
        self.head_width.grid(row=0, column=5)
        self.head_asymmetry = Label(self.frame_fit, text='Asymmetry')
        self.head_asymmetry.grid(row=0, column=6)
        self.head_fwhm = Label(self.frame_fit, text='FWHM')
        self.head_fwhm.grid(row=0, column=7)
        self.head_fraction = Label(self.frame_fit, text='Beam fraction')
        self.head_fraction.grid(row=0, column=8)

        # define and place frame_fit widgets
        self.cbox_focus_flag = Checkbutton(self.frame_fit, text='Focus fit',
                                           variable=self.focus_flag, command=update_plot)
        self.cbox_focus_flag.grid(row=1, rowspan=2, column=0, padx=5, pady=5)
        self.label_less = Label(self.frame_fit, text='x < Center')
        self.label_less.grid(row=1, column=1)
        self.label_more = Label(self.frame_fit, text='x > Center')
        self.label_more.grid(row=2, column=1)
        self.label_pv_a = Label(self.frame_fit, textvariable=self.pv_a, width=7, relief=SUNKEN)
        self.label_pv_a.grid(row=1, rowspan=2, column=2, padx=5, pady=5)
        self.label_pv_x0 = Label(self.frame_fit, textvariable=self.pv_x0, width=7, relief=SUNKEN)
        self.label_pv_x0.grid(row=1, rowspan=2, column=3, padx=5, pady=5)
        self.label_pv_mul = Label(self.frame_fit, textvariable=self.pv_mul, width=7, relief=SUNKEN)
        self.label_pv_mul.grid(row=1, column=4, padx=5, pady=5)
        self.label_pv_mur = Label(self.frame_fit, textvariable=self.pv_mur, width=7, relief=SUNKEN)
        self.label_pv_mur.grid(row=2, column=4, padx=5, pady=5)
        self.label_pv_wl = Label(self.frame_fit, textvariable=self.pv_wl, width=7, relief=SUNKEN)
        self.label_pv_wl.grid(row=1, column=5, padx=5, pady=5)
        self.label_pv_wr = Label(self.frame_fit, textvariable=self.pv_wr, width=7, relief=SUNKEN)
        self.label_pv_wr.grid(row=2, column=5, padx=5, pady=5)
        self.label_pv_asymmetry = Label(self.frame_fit, textvariable=self.pv_asymmetry, width=7, relief=SUNKEN)
        self.label_pv_asymmetry.grid(row=1, rowspan=2, column=6, padx=5, pady=5)
        self.label_pv_fwhm = Label(self.frame_fit, textvariable=self.pv_fwhm, width=7, relief=SUNKEN)
        self.label_pv_fwhm.grid(row=1, rowspan=2, column=7, padx=5, pady=5)
        self.label_pv_beamsize = Label(self.frame_fit, textvariable=self.pv_beamsize, width=7, relief=SUNKEN)
        self.label_pv_beamsize.grid(row=1, rowspan=2, column=8, padx=5, pady=5)
        # changing baemsize from entry to label
        # ###self.label_pv_beamsize = Entry(self.frame_fit, textvariable=self.pv_beamsize, width=7)
        # ###self.label_pv_beamsize.grid(row=1, rowspan=2, column=8, padx=5, pady=5)
        # ###self.label_pv_beamsize.bind('<FocusOut>', self.find_width)
        # ###self.label_pv_beamsize.bind('<Return>', self.find_width)

        # make frame_center headings
        self.head_label = Label(self.frame_center, text='FULL CENTERING CONTROL')
        self.head_label.grid(row=0, column=0)
        self.head_cenx = Label(self.frame_center, text='Cen X')
        self.head_cenx.grid(row=0, column=2, padx=5, pady=5)
        self.head_ceny = Label(self.frame_center, text='Cen Y')
        self.head_ceny.grid(row=0, column=3, padx=5, pady=5)
        self.head_basey = Label(self.frame_center, text='Base Y')
        self.head_basey.grid(row=0, column=4, padx=5, pady=5)

        # make and place frame_center widgets
        self.label_deltas = Label(self.frame_center, text='Deltas')
        self.label_deltas.grid(row=1, column=1, padx=5, pady=5)
        self.label_del_x = Label(self.frame_center, textvariable=center.delta_x, relief=SUNKEN, width=8)
        self.label_del_x.grid(row=1, column=2, padx=5, pady=5)
        self.label_del_y = Label(self.frame_center, textvariable=center.delta_y, relief=SUNKEN, width=8)
        self.label_del_y.grid(row=1, column=3, padx=5, pady=5)
        self.label_del_base = Label(self.frame_center, textvariable=center.delta_y_base, relief=SUNKEN, width=8)
        self.label_del_base.grid(row=1, column=4, padx=5, pady=5)
        self.label_absolute = Label(self.frame_center, text='Target Positions')
        self.label_absolute.grid(row=2, column=1, padx=5, pady=5)
        self.label_abs_x = Label(self.frame_center, textvariable=center.absolute_x, relief=SUNKEN, width=8)
        self.label_abs_x.grid(row=2, column=2, padx=5, pady=5)
        self.label_abs_y = Label(self.frame_center, textvariable=center.absolute_y, relief=SUNKEN, width=8)
        self.label_abs_y.grid(row=2, column=3, padx=5, pady=5)
        self.label_abs_base = Label(self.frame_center, textvariable=center.absolute_y_base, relief=SUNKEN, width=8)
        self.label_abs_base.grid(row=2, column=4, padx=5, pady=5)
        self.button_move_all = Button(self.frame_center, text='Move All', command=center.move_all, width=12)
        self.button_move_all.grid(row=1, rowspan=2, column=5, padx=10, pady=5)

        # frame_zero widgets
        self.button_zero_x = Button(self.frame_zero, text='Re-zero x', command=lambda: self.zero_stage(mX), width=8)
        self.button_zero_x.grid(row=0, column=0, padx=10, pady=5)
        self.button_zero_y = Button(self.frame_zero, text='Re-zero y', command=lambda: self.zero_stage(mY), width=8)
        self.button_zero_y.grid(row=1, column=0, padx=10, pady=5)
        self.button_zero_z = Button(self.frame_zero, text='Re-zero z', command=lambda: self.zero_stage(mZ), width=8)
        self.button_zero_z.grid(row=2, column=0, padx=10, pady=5)

        # hide window on startup
        self.popup.withdraw()

    def calc_mixes(self):
        wl = self.pv_wl.get()
        wr = self.pv_wr.get()
        asym = (wl - wr)/(wl + wr)
        fwhm = 0.5*wl + 0.5*wr
        self.pv_asymmetry.set('%.2f' % asym)
        self.pv_fwhm.set('%.4f' % fwhm)

    def zero_stage(self, stage):
        confirm = askyesno('Confirm action', 'Are you sure you want to proceed?')
        if confirm:
            stage.SET = 1
            stage.VAL = 0
            stage.SET = 0


class DragHorizontalLines:
    lock = None

    def __init__(self, hline):
        self.hline = hline
        self.press = None
        self.y_mid = None

    def connect(self):
        self.cidpress = self.hline.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.hline.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.hline.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        if DragHorizontalLines.lock is not None:
            return
        if event.inaxes != self.hline.axes:
            return
        contains, attrd = self.hline.contains(event)
        if not contains:
            return
        y0 = self.hline.get_ydata()
        self.y_mid = core.h_mid.get_ydata()
        self.press = y0, event.xdata, event.ydata
        DragHorizontalLines.lock = self

    def on_motion(self, event):
        if self.press is None:
            return
        if event.inaxes != self.hline.axes:
            return
        y0, xpress, ypress = self.press
        dy = event.ydata - ypress
        self.hline.set_ydata(y0+dy)
        core.h_mid.set_ydata(self.y_mid+.5*dy)
        self.hline.figure.canvas.draw()

    def on_release(self, event):
        if DragHorizontalLines.lock is not self:
            return
        self.press = None
        DragHorizontalLines.lock = None
        self.hline.figure.canvas.draw()


class DragVerticalLines:
    lock = None

    def __init__(self, vline):
        self.vline = vline
        self.press = None
        self.x_mid = None

    def connect(self):
        self.cidpress = self.vline.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.vline.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.vline.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        if DragVerticalLines.lock is not None:
            return
        if event.inaxes != self.vline.axes:
            return
        contains, attrd = self.vline.contains(event)
        if not contains:
            return
        x0 = self.vline.get_xdata()
        self.x_mid = core.v_mid.get_xdata()
        self.press = x0, event.xdata, event.ydata
        DragVerticalLines.lock = self

    def on_motion(self, event):
        if self.press is None:
            return
        if event.inaxes != self.vline.axes:
            return
        x0, xpress, ypress = self.press
        dx = event.xdata - xpress
        self.vline.set_xdata(x0+dx)
        core.v_mid.set_xdata(self.x_mid+.5*dx)
        min_now = core.v_min.get_xdata()
        mid_now = core.v_mid.get_xdata()
        max_now = core.v_max.get_xdata()
        hax.min_pos.set('%.4f' % min_now[0])
        hax.mid_pos.set('%.4f' % mid_now[0])
        hax.max_pos.set('%.4f' % max_now[0])
        if center.c_flag.get() and data.slice_flag.get():
            if data.current_slice.get() == 1:
                center.y_minus_pos.set('%.4f' % mid_now[0])
            elif data.current_slice.get() == 2:
                center.y_center_pos.set('%.4f' % mid_now[0])
            elif data.current_slice.get() == 3:
                center.y_plus_pos.set('%.4f' % mid_now[0])
        self.vline.figure.canvas.draw()

    def on_release(self, event):
        if DragVerticalLines.lock is not self:
            return
        self.press = None
        DragVerticalLines.lock = None
        self.vline.figure.canvas.draw()
        min_fin = core.v_min.get_xdata()
        mid_fin = core.v_mid.get_xdata()
        max_fin = core.v_max.get_xdata()
        hax.min_pos.set('%.4f' % min_fin[0])
        hax.mid_pos.set('%.4f' % mid_fin[0])
        hax.max_pos.set('%.4f' % max_fin[0])
        # test 1d index
        yind = data.current_slice.get() - 1
        xind = np.abs(core.FLY - mid_fin[0]).argmin()
        fly_axis_length = core.FLY.shape[0]
        image_index = yind*fly_axis_length + xind + 1
        data.index.set(image_index)
        if center.c_flag.get() and data.slice_flag.get():
            if data.current_slice.get() == 1:
                center.y_minus_pos.set('%.4f' % mid_fin[0])
            elif data.current_slice.get() == 2:
                center.y_center_pos.set('%.4f' % mid_fin[0])
            elif data.current_slice.get() == 3:
                center.y_plus_pos.set('%.4f' % mid_fin[0])
            center.calc_deltas()
        if staff.focus_flag.get() and counter.data_type.get() == 'Derivative':
            if core.dimension == 1 or data.slice_flag.get():
                beamsize_integral()
                print staff.area, staff.pv_a.get()
                fraction = staff.area / staff.pv_a.get()
                staff.pv_beamsize.set('%.3f' % fraction)


def onclick(event):
    if not event.inaxes:
        return
    if core.dimension == 1 or data.slice_flag.get():
        return
    x_val = event.xdata
    y_val = event.ydata
    xind = np.abs(core.FLY - x_val).argmin()
    yind = np.abs(core.STP - y_val).argmin()
    data.current_slice.set(yind+1)
    fly_axis_length = core.FLY.shape[0]
    image_index = yind*fly_axis_length + xind + 1
    data.index.set(image_index)
    # start dioptas test
    if image.dioptas_flag.get():
        image.send_to_dioptas()
    return hax.mid_pos.set('%.4f' % x_val), vax.mid_pos.set('%.4f' % y_val)


def invalid_entry():
    # generic pop-up notification for invalid text entries
    showwarning('Invalid Entry', message='Input was reset to default value')


def path_warn():
    showwarning('Invalid Path Name',
                'Please modify selection and try again')


def overwrite_warn():
    showwarning('Overwrite Warning',
                'Scan no. and/or Image No. automatically incremented')


def confirm_action():
    askyesno('Confirm action', 'Are you sure you want to proceed?')


def close_quit():
    # add dialog box back in and indent following code after testing period
    # ##if askyesno('Quit Diptera', 'Do you want to quit?'):
    plt.close('all')
    root.destroy()
    root.quit()


def hide_staff():
    staff.popup.withdraw()
    staff.focus_flag.set(0)


def hide_image():
    image.popup.withdraw()
    image.enable_flag.set(0)


def hide_alloverlays():
    alloverlays.popup.withdraw()
    over1.plot_flag.set(0)
    over2.plot_flag.set(0)
    over3.plot_flag.set(0)
    if data.current_file.get():
        update_plot()


def piecewise_split_pv(x, a, x0, mul, mur, wl, wr):
    condlist = [x < x0, x >= x0]
    funclist = [
            lambda x: a * (mul * (2/pi) * (wl / (4*(x-x0)**2 + wl**2)) + (1 - mul) * (sqrt(4*np.log(2)) / (sqrt(pi) * wl)) * exp(-(4*np.log(2)/wl**2)*(x-x0)**2)),
            lambda x: a * (mur * (2/pi) * (wr / (4*(x-x0)**2 + wr**2)) + (1 - mur) * (sqrt(4*np.log(2)) / (sqrt(pi) * wr)) * exp(-(4*np.log(2)/wr**2)*(x-x0)**2))]
    return np.piecewise(x, condlist, funclist)


def beamsize_integral():
    t_popt = tuple(staff.popt)
    lower_bound = float(hax.min_pos.get())
    upper_bound = float(hax.max_pos.get())
    staff.area, staff.err = integrate.quad(func=piecewise_split_pv, a=lower_bound,
                                           b=upper_bound, args=t_popt)


def path_put(**kwargs):
    image.det_path.set(detector.get('FilePath_RBV', as_string=True))
    # try autofill
    result = image.det_path.get()
    if result[0:13] == '/ramdisk/Data':
        user_directory = 'P:' + result[13:]
        windows_path = os.path.normpath(user_directory) + '\\'
        image.user_path.set(windows_path)
    else:
        windows_path = 'path error'
    if not os.path.exists(windows_path):
        image.label2_user_path.config(bg='red')
    else:
        image.label2_user_path.config(bg='SystemButtonFace')


def make_trajectory(zero, min, max, velo, motor):
    if config.stack_choice.get() == 'IDBLH':
        line_a = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
        line_b = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
        line_c = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0']
    else:
        line_a = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
        line_b = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
        line_c = ['0.525', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
    if motor.get('DIR') == 0:
        sign = 1
    else:
        sign = -1
    delta_xac = sign*(min - zero)
    delta_xb = sign*(max-min)
    velo_ab = sign*(velo)
    delta_tb = delta_xb/velo_ab
    if motor == mX:
        # print 'x'
        xi = 1
        vi = 2
    elif motor == mY:
        # print 'y'
        xi = 3
        vi = 4
    elif motor == mZ:
        # print 'z'
        xi = 5
        vi = 6
    else:
        # must be w, pick correct one
        if config.stack_choice.get() == 'GPHP':
            xi = 7
            vi = 8
        else:
            xi = 9
            vi = 10
    line_a[xi] = str(delta_xac)
    line_a[vi] = str(velo_ab)
    line_b[0] = str(delta_tb)
    line_b[xi] = str(delta_xb)
    line_b[vi] = str(velo_ab)
    line_c[xi] = str(delta_xac)
    line_a = ','.join(line_a)
    line_b = ','.join(line_b)
    line_c = ','.join(line_c)
    complete_file = (line_a + '\n' + line_b + '\n' + line_c + '\n')
    # print complete_file
    traj_file = open('traj.trj', 'w')
    traj_file.write(complete_file)
    traj_file.close()
    session = ftplib.FTP(xps_ip, user='Administrator', passwd='Administrator')
    session.cwd('Public/Trajectories/')
    traj_file = open('traj.trj')
    session.storlines('STOR traj.trj', traj_file)
    traj_file.close()
    session.quit()


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
                  'LINEAR ' + motor + delta_fly + '\n'
                  '\n'
                  'LINEAR ' + motor + delta_ramp + '\n'
                  '\n'
                  'DWELL 0.3\n'
                  '\n'
                  'END PROGRAM\n')
    textpath = 'S:\\Hexfly\\fs.pgm'
    textfile = open(textpath, 'w')
    textfile.write(prog_lines)
    textfile.close()


def update_plot(*args):
    # create a list for iteration
    array_list = [core, over1, over2, over3]
    for each in array_list:
        if each.plot_flag.get():
            # fetch and locally name the arrays selected by the user
            local_dict = {
                'Beamstop diode': each.BSD,
                'Removable diode': each.RMD,
                'Hutch reference': each.REF,
                'FOE ion chamber': each.FOE,
                '50 MHz clock': each.TIM}
            signal = counter.i_signal.get()
            reference = counter.i_ref.get()
            sig_array = local_dict[signal]
            ref_array = local_dict[reference]
            # normalize if needed
            if counter.ref_flag.get():
                raw_array = np.divide(sig_array, ref_array)
            else:
                raw_array = sig_array
            # create the basic core.SCA for plotting
            each.SCA = raw_array * counter.scale.get()
            # calculate derivative here if needed
            if counter.data_type.get() == 'Derivative':
                TEMP = np.ones(each.SCA.shape)
                x_length = len(each.FLY)
                for steps in range(each.dimension):
                    for x in range(x_length):
                        if x == 0 or x == x_length - 1:
                            pass
                        else:
                            dy = each.SCA[steps][x+1] - each.SCA[steps][x-1]
                            dx = each.FLY[x+1] - each.FLY[x-1]
                            TEMP[steps][x] = dy/dx
                    TEMP[steps][0] = TEMP[steps][1]
                    TEMP[steps][x_length-1] = TEMP[steps][x_length-2]
                each.SCA = TEMP
    # select, if necessary, the indicated slice of core.SCA
    if data.slice_flag.get() and core.dimension > 1:
        index = data.current_slice.get() - 1
        core.SCA = core.SCA[index]
        step_axis_pos = core.STP[index]
        for each in array_list:
            if each == core:
                pass
            else:
                if each.plot_flag.get():
                    index = each.overlay_slice.get() - 1
                    each.SCA = each.SCA[index]
    # ###if staff.area_calc:
    # ###    x_left = float(hax.min_pos.get())
    # ###    x_right = float(hax.max_pos.get())
    # ###    x_mid = staff.pv_x0.get()
    # clear fields and plot
    hax.min_pos.set('')
    hax.mid_pos.set('')
    hax.max_pos.set('')
    hax.width.set('')
    hax.delta_pos.set('')
    vax.min_pos.set('')
    vax.mid_pos.set('')
    vax.max_pos.set('')
    vax.width.set('')
    plt.clf()
    # plot it!
    plt.xlabel('Fly axis:  ' + hax.active_stage.get())
    if core.dimension == 1 or data.slice_flag.get():
        plt.ylabel('Intensity')
        for each in array_list:
            if each.plot_flag.get():
                shp = each.FLY.shape
                each.SCA.shape = shp
        # set up Arun bars (draggable horizontal and vertical lines)
        f_min = np.amin(core.SCA)
        f_max = np.amax(core.SCA)
        f_mid = (f_max + f_min)/2
        mid_list = []
        for i in range(core.FLY.size-1):
            if not core.SCA[i] < f_mid <= core.SCA[i + 1] and not core.SCA[i + 1] < f_mid <= core.SCA[i]:
                pass
            else:
                f2, f1, x2, x1 = core.SCA[i+1], core.SCA[i], core.FLY[i+1], core.FLY[i]
                m = (f2 - f1)/(x2 - x1)
                x_mid = (f_mid - f1)/m + x1
                mid_list.append(x_mid)
        # ###if staff.area_calc:
        # ###    x_left = float(hax.min_pos.get())
        # ###    x_right = float(hax.max_pos.get())
        # ###    x_mid = staff.pv_x0.get()
        if len(mid_list) < 2:
            x_min = np.amin(core.FLY)
            x_max = np.amax(core.FLY)
            x_span = (x_max - x_min)
            x_left = x_min + x_span/4
            x_right = x_max - x_span/4
            x_mid = (x_min+x_max)/2
        else:
            x_left = mid_list[0]
            x_right = mid_list[-1]
            x_mid = (x_left + x_right)/2
        # if core.dimension == 1:
        #     vax.min_pos.set('%.4f' % f_min)
        #     vax.mid_pos.set('%.4f' % f_mid)
        #     vax.max_pos.set('%.4f' % f_max)
        if center.c_flag.get():
            if data.current_slice.get() == 1:
                center.y_minus_pos.set('%.4f' % x_mid)
            elif data.current_slice.get() == 2:
                center.y_center_pos.set('%.4f' % x_mid)
            elif data.current_slice.get() == 3:
                center.y_plus_pos.set('%.4f' % x_mid)
            center.calc_deltas()
        core.h_min = plt.axhline(f_min)
        core.h_mid = plt.axhline(f_mid, ls='--', c='r')
        core.h_max = plt.axhline(f_max)
        hax.min_pos.set('%.4f' % x_left)
        hax.mid_pos.set('%.4f' % x_mid)
        hax.max_pos.set('%.4f' % x_right)
        core.v_min = plt.axvline(x_left)
        core.v_mid = plt.axvline(x_mid, ls='--', c='r')
        core.v_max = plt.axvline(x_right)
        if core.dimension > 1:
            vax.mid_pos.set('%.4f' % step_axis_pos)
        hlist = [core.h_min, core.h_max]
        vlist = [core.v_min, core.v_max]
        core.dhls = []
        core.dvls = []
        for each in hlist:
            dhl = DragHorizontalLines(each)
            dhl.connect()
            core.dhls.append(dhl)
        for each in vlist:
            dvl = DragVerticalLines(each)
            dvl.connect()
            core.dvls.append(dvl)
        # index calculator
        yind = data.current_slice.get() - 1
        xind = np.abs(core.FLY - x_mid).argmin()
        fly_axis_length = core.FLY.shape[0]
        image_index = yind*fly_axis_length + xind + 1
        data.index.set(image_index)
        if staff.focus_flag.get() and counter.data_type.get() == 'Derivative':
            abs_values = np.abs(core.SCA)
            guess_index = np.argmax(abs_values)
            a = core.SCA[guess_index] * 0.005
            x0 = core.FLY[guess_index]
            p0 = [a, x0, 0.5, 0.5, 0.005, 0.005]
            staff.popt, pcov = curve_fit(piecewise_split_pv, core.FLY, core.SCA, p0=p0)
            staff.pv_a.set('%.2f' % staff.popt[0])
            staff.pv_x0.set('%.4f' % staff.popt[1])
            staff.pv_mul.set('%.2f' % staff.popt[2])
            staff.pv_mur.set('%.2f' % staff.popt[3])
            staff.pv_wl.set('%.4f' % staff.popt[4])
            staff.pv_wr.set('%.4f' % staff.popt[5])
            staff.calc_mixes()
            # tpopt = tuple(staff.popt)
            # lower_bound = float(hax.min_pos.get())
            # upper_bound = float(hax.max_pos.get())
            # area, err = integrate.quad(func=piecewise_split_pv, a=lower_bound,
            #                            b=upper_bound, args=tpopt)
            beamsize_integral()
            print staff.area, staff.pv_a.get()
            fraction = staff.area / staff.pv_a.get()
            staff.pv_beamsize.set('%.3f' % fraction)
        for each in array_list:
            if each.plot_flag.get():
                if counter.data_type.get() == 'Derivative':
                    plt.plot(each.FLY[1:-1], each.SCA[1:-1], marker='.', ls='-')
                    if staff.focus_flag.get():
                        plt.plot(core.FLY, piecewise_split_pv(core.FLY, *staff.popt), 'ro:')
                else:
                    plt.plot(each.FLY, each.SCA, marker='.', ls='-')
    else:
        plt.ylabel('Step axis:  ' + vax.active_stage.get())
        # intensity scaling
        area_min = np.amin(core.SCA)
        area_max = np.amax(core.SCA)
        area_range = area_max - area_min
        cf_min = area_min + area_range*counter.min_scale.get()*0.01
        cf_max = area_min + area_range*counter.max_scale.get()*0.01
        levels = counter.levels.get() + 1
        V = np.linspace(cf_min, cf_max, levels)
        # plot filled contour
        plt.contourf(core.FLY, core.STP, core.SCA, V, cmap=None)
        plt.colorbar()
        # get and display plot middle coordinates
        halfx = (plt.xlim()[1] + plt.xlim()[0])/2
        halfy = (plt.ylim()[1] + plt.ylim()[0])/2
        hax.mid_pos.set('%.4f' % halfx)
        vax.mid_pos.set('%.4f' % halfy)
        # work out indices
        xind = np.abs(core.FLY - halfx).argmin()
        yind = np.abs(core.STP - halfy).argmin()
        data.current_slice.set(yind+1)
        fly_axis_length = core.FLY.shape[0]
        image_index = yind*fly_axis_length + xind + 1
        data.index.set(image_index)
        # grid option
        if image.grid_flag.get():
            eh = plt.gca()
            eh.set_yticks(core.STP, minor=True)
            eh.set_xticks(core.FLY, minor=True)
            eh.yaxis.grid(True, which='minor')
            eh.xaxis.grid(True, which='minor')
    plt.gcf().canvas.draw()
    print 'update done'


'''
Program start
'''
root = Tk()
# root.title('Diptera')
# hide root, draw config window, wait for user input
root.withdraw()
config = ExpConfigure(root)
# line below can be commented in/out and edited for autoconfig
# config.stack_choice.set('TEST')
if not config.stack_choice.get() == NONE:
    config.config_window.destroy()
else:
    root.wait_window(config.config_window)

'''
With stack choice made, define relevant epics devices, Pvs, etc.
'''
# station-independent arg lists for epics Devices

softglue_args = ['FI1_Signal', 'FI2_Signal', 'FI3_Signal', 'FI4_Signal',
                 'FI5_Signal', 'FI6_Signal', 'FI7_Signal', 'FI8_Signal',
                 'FI9_Signal', 'FI10_Signal', 'FI11_Signal', 'FI12_Signal',
                 'FI13_Signal', 'FI14_Signal', 'FI15_Signal', 'FI16_Signal',
                 'FO17_Signal', 'FO18_Signal', 'FO19_Signal', 'FO20_Signal',
                 'FO21_Signal', 'FO22_Signal', 'FO23_Signal', 'FO24_Signal',
                 'FI25_Signal', 'FI26_Signal', 'FI27_Signal', 'FI28_Signal',
                 'FI29_Signal', 'FI30_Signal', 'FI31_Signal', 'FI32_Signal',
                 'FI33_Signal', 'FI34_Signal', 'FI35_Signal', 'FI36_Signal',
                 'FI37_Signal', 'FI38_Signal', 'FI39_Signal', 'FI40_Signal',
                 'FI41_Signal', 'FI42_Signal', 'FI43_Signal', 'FI44_Signal',
                 'FI45_Signal', 'FI46_Signal', 'FI47_Signal', 'FI48_Signal',
                 'DnCntr-1_PRESET', 'DnCntr-2_PRESET', 'DnCntr-3_PRESET', 'DnCntr-4_PRESET',
                 'UpCntr-1_COUNTS', 'UpCntr-2_COUNTS', 'UpCntr-3_COUNTS', 'UpCntr-4_COUNTS',
                 'DivByN-1_N', 'DFF-4_OUT_BI', 'BUFFER-1_IN_Signal']

sg_config_args = ['name1', 'name2', 'loadConfig1.PROC', 'loadConfig2.PROC']

detector_args = ['ShutterMode', 'ShutterControl', 'AcquireTime',
                 'AcquirePeriod', 'NumImages', 'TriggerMode',
                 'Acquire', 'DetectorState_RBV', 'FilePath_RBV',
                 'FileName', 'FileNumber', 'AutoIncrement',
                 'FullFileName_RBV']

# include option to load custom file
if config.use_file.get():
    user_config = askopenfile(mode='r', title='Please select configuration file')
    exec user_config.read()
    user_config.close()
# hard-encoded configuration options
elif config.stack_choice.get() == 'BMB':
    root.title('Diptera - BMB Laue Endstation')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('XPSBMB:m1')
    mY = Motor('XPSBMB:m2')
    mZ = Motor('XPSBMB:m3')
    mW = Motor('XPSBMB:m4')
    mYbase = Motor('XPSBMB:m5')

    # define xps ip (if needed)
    xps_ip = '164.54.164.117'

    # define any additional flyscan motors
    mPinY = Motor('16BMA:m30')
    mPinZ = Motor('16BMA:m31')

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16BMA:SIS1:')
    softglue = Device('16BMA:softGlue:', softglue_args)
    sg_config = Device('16BMA:SGMenu:', sg_config_args)
    abort = PV('16BMA:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'Sample X': ['XPS', mX, 'FI1_Signal', 1.0],
        'Sample Y': ['XPS', mY, 'FI1_Signal', 1.0],
        'Sample Z': ['XPS', mZ, 'FI1_Signal', 1.0],
        'Omega': ['XPS', mW, 'FI1_Signal', 10.0],
        'Pinhole y': ['MAXV', mPinY, 'F7_Signal', 0.25],
        'Pinhole z': ['MAXV', mPinZ, 'F8_Signal', 0.25]}

    # create lists for drop-down menus
    fly_list = ['Sample Y', 'Sample Z', 'More']
    step_list = ['Sample Y', 'Sample Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'Sample X',
        'Omega',
        'Pinhole y',
        'Pinhole z']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

elif config.stack_choice.get() == 'BMDHL':
    root.title('Diptera - BMD Endstation')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('16BMD:m38')
    mY = Motor('16BMD:m39')
    mZ = Motor('16BMD:m13')
    mW = Motor('16BMD:m37')
    mYbase = Motor('16BMD:m36')

    # define xps ip (if needed)
    # xps_ip = '164.54.164.xxx'

    # define any additional flyscan motors
    mMonoX = Motor('16BMD:m67')
    mPinY = Motor('16BMD:m33')
    mPinZ = Motor('16BMD:m54')
    # mBSY = Motor('16BMD:mxx')
    # mBSz = Motor('16BMD:mxx')

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16BMD:SIS1:')
    softglue = Device('16BMD:softGlue:', softglue_args)
    sg_config = Device('16BMD:SGMenu:', sg_config_args)
    abort = PV('16BMD:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'Sample X': ['MAXV', mX, 'FI3_Signal', 0.25],
        'Sample Y': ['MAXV', mY, 'FI4_Signal', 0.25],
        'Sample Z': ['MAXV', mZ, 'FI5_Signal', 0.020],
        'Omega': ['MAXV', mW, 'FI6_Signal', 2],
        'Pinhole y': ['MAXV', mPinY, 'FI7_Signal', 0.25],
        'Pinhole z': ['MAXV', mPinZ, 'FI8_Signal', 0.25],
        'Mono X Translation': ['MAXV', mMonoX, 'FI11_Signal', 0.2]}

    # create lists for drop-down menus
    fly_list = ['Sample Y', 'Sample Z', 'More']
    step_list = ['Sample Y', 'Sample Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'Sample X',
        'Omega',
        'Pinhole y',
        'Pinhole z',
        'Mono X Translation']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

elif config.stack_choice.get() == 'GPHP':
    root.title('Diptera - IDB General Purpose Endstaion (high precision stages)')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('XPSGP:m1')
    mY = Motor('XPSGP:m2')
    mZ = Motor('XPSGP:m3')
    mW = Motor('XPSGP:m4')
    mYbase = Motor('16IDB:m4')

    # define xps ip (if needed)
    xps_ip = '164.54.164.24'

    # define any additional flyscan motors
    mLgPinY = Motor('16IDB:m19')
    mLgPinZ = Motor('16IDB:m24')
    mSmPinY = Motor('16IDB:m17')
    mSmPinZ = Motor('16IDB:m18')
    mBSY = Motor('16IDB:m34')
    mBSZ = Motor('16IDB:m35')

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16IDB:SIS1:')
    softglue = Device('16IDB:softGlue:', softglue_args)
    sg_config = Device('16IDB:SGMenu:', sg_config_args)
    abort = PV('16IDB:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'XPS Cen X': ['XPS', mX, 'FI1_Signal', 2.0],
        'XPS Cen Y': ['XPS', mY, 'FI1_Signal', 2.0],
        'XPS Sam Z': ['XPS', mZ, 'FI1_Signal', 2.0],
        'XPS Omega': ['XPS', mW, 'FI1_Signal', 20.0],
        'GP LKB Pinhole Y': ['MAXV', mLgPinY, 'FI7_Signal', 0.3],
        'GP LKB Pinhole Z': ['MAXV', mLgPinZ, 'FI8_Signal', 0.3],
        'GP SKB Pinhole Y': ['MAXV', mSmPinY, 'FI9_Signal', 0.3],
        'GP SKB Pinhole Z': ['MAXV', mSmPinZ, 'FI10_Signal', 0.3],
        'GP Beamstop Y': ['MAXV', mBSY, 'FI11_Signal', 0.5],
        'GP Beamstop Z': ['MAXV', mBSZ, 'FI12_Signal', 0.5]}

    # create lists for drop-down menus
    fly_list = ['XPS Cen Y', 'XPS Sam Z', 'More']
    step_list = ['XPS Cen Y', 'XPS Sam Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'XPS Cen X',
        'XPS Omega',
        'GP LKB Pinhole Y',
        'GP LKB Pinhole Z',
        'GP SKB Pinhole Y',
        'GP SKB Pinhole Z',
        'GP Beamstop Y',
        'GP Beamstop Z']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

elif config.stack_choice.get() == 'GPHL':
    root.title('Diptera - IDB General Purpose Endstaion (high load stages)')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('16IDB:m31')
    mY = Motor('16IDB:m32')
    mZ = Motor('16IDB:m5')
    mW = Motor('XPSGP:m5')
    mYbase = Motor('16IDB:m4')

    # define xps ip (if needed)
    xps_ip = '164.54.164.24'

    # define any additional flyscan motors
    mLgPinY = Motor('16IDB:m19')
    mLgPinZ = Motor('16IDB:m24')
    mSmPinY = Motor('16IDB:m17')
    mSmPinZ = Motor('16IDB:m18')
    mBSY = Motor('16IDB:m34')
    mBSZ = Motor('16IDB:m35')

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16IDB:SIS1:')
    softglue = Device('16IDB:softGlue:', softglue_args)
    sg_config = Device('16IDB:SGMenu:', sg_config_args)
    abort = PV('16IDB:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'GP CEN X': ['MAXV', mX, 'FI3_Signal', 1.0],
        'GP CEN Y': ['MAXV', mY, 'FI4_Signal', 1.0],
        'GP SAM Z': ['MAXV', mZ, 'FI5_Signal', 0.025],
        'GP Omega': ['XPS', mW, 'FI1_Signal', 10.0],
        'GP LKB Pinhole Y': ['MAXV', mLgPinY, 'FI7_Signal', 0.3],
        'GP LKB Pinhole Z': ['MAXV', mLgPinZ, 'FI8_Signal', 0.3],
        'GP SKB Pinhole Y': ['MAXV', mSmPinY, 'FI9_Signal', 0.3],
        'GP SKB Pinhole Z': ['MAXV', mSmPinZ, 'FI10_Signal', 0.3],
        'GP Beamstop Y': ['MAXV', mBSY, 'FI11_Signal', 0.5],
        'GP Beamstop Z': ['MAXV', mBSZ, 'FI12_Signal', 0.5]}

    # create lists for drop-down menus
    fly_list = ['GP CEN Y', 'GP SAM Z', 'More']
    step_list = ['GP CEN Y', 'GP SAM Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'GP CEN X',
        'GP Omega',
        'GP LKB Pinhole Y',
        'GP LKB Pinhole Z',
        'GP SKB Pinhole Y',
        'GP SKB Pinhole Z',
        'GP Beamstop Y',
        'GP Beamstop Z']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

elif config.stack_choice.get() == 'IDBLH':
    root.title('Diptera - IDB Laser Heating Endstaion')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('XPSLH:m1')
    mY = Motor('XPSLH:m2')
    mZ = Motor('XPSLH:m3')
    mW = Motor('XPSLH:m4')
    mYbase = Motor('16IDB:m10')

    # define xps ip (if needed)
    xps_ip = '164.54.164.104'

    # define any additional flyscan motors
    mLgPinY = Motor('16IDB:m62')
    mLgPinZ = Motor('16IDB:m63')
    mBSY = Motor('16IDB:m67')
    mBSZ = Motor('16IDB:m68')

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16IDB:SIS1:')
    softglue = Device('16IDB:softGlue:', softglue_args)
    sg_config = Device('16IDB:SGMenu:', sg_config_args)
    abort = PV('16IDB:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'LH CEN X': ['XPS', mX, 'FI1_Signal', 2.0],
        'LH CEN Y': ['XPS', mY, 'FI1_Signal', 2.0],
        'LH SAM Z': ['XPS', mZ, 'FI1_Signal', 1.0],
        'LH OMEGA': ['XPS', mW, 'FI1_Signal', 20.0],
        'LH Pinhole Y': ['MAXV', mLgPinY, 'FI27_Signal', 0.3],
        'LH Pinhole Z': ['MAXV', mLgPinZ, 'FI28_Signal', 0.3],
        'LH Beamstop Y': ['MAXV', mBSY, 'FI29_Signal', 0.3],
        'LH Beamstop Z': ['MAXV', mBSZ, 'FI30_Signal', 0.3]}

    # create lists for drop-down menus
    fly_list = ['LH CEN Y', 'LH SAM Z', 'More']
    step_list = ['LH CEN Y', 'LH SAM Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'LH CEN X',
        'LH OMEGA',
        'LH Pinhole Y',
        'LH Pinhole Z',
        'LH Beamstop Y',
        'LH Beamstop Z']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

elif config.stack_choice.get() == 'IDD':
    root.title('Diptera ~ IDD Endstation')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('16IDD:m29')
    mY = Motor('16IDD:m19')
    mZ = Motor('16IDD:m13')
    mW = Motor('16IDD:m27')
    mYbase = Motor('16IDD:m2')

    # define xps ip (if needed)
    # xps_ip = '164.54.164.xxx'

    # define any additional flyscan motors
    mPinY = Motor('16IDD:m12')
    mPinZ = Motor('16IDD:m11')

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16IDD:SIS1:')
    softglue = Device('16IDD:softGlue:', softglue_args)
    sg_config = Device('16IDD:SGMenu:', sg_config_args)
    abort = PV('16IDD:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'Sample_X': ['MAXV', mX, 'FI3_Signal', 1.00],
        'Sample_Y': ['MAXV', mY, 'FI4_Signal', 1.00],
        'Sample_Z': ['MAXV', mZ, 'FI5_Signal', 0.90],
        'Sample_Omega': ['MAXV', mW, 'FI6_Signal', 2.5],
        'Pinhole_Y': ['MAXV', mPinY, 'FI7_Signal', 0.25],
        'Pinhole_Z': ['MAXV', mPinZ, 'FI8_Signal', 0.25]}

    # create lists for drop-down menus
    fly_list = ['Sample_Y', 'Sample_Z', 'More']
    step_list = ['Sample_Y', 'Sample_Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'Sample_X',
        'Sample_Omega',
        'Pinhole_Y',
        'Pinhole_Z']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

# ###elif config.stack_choice.get() == 'TEST':
# ###    root.title('Diptera - A real program for scanning imaginary stages')
# ###    # create objects including epics Motors, Struck, etc
# ###    # define 5-motor sample stack
# ###    mX = Motor('16TEST1:m10')
# ###    mY = Motor('16TEST1:m9')
# ###    mZ = Motor('16TEST1:m11')
# ###    mW = Motor('16TEST1:m12')
# ###    mYbase = Motor('16TEST1:m13')
# ###
# ###    # define xps ip (if needed)
# ###    # xps_ip = '164.54.164.xxx'
# ###
# ###    # define any additional flyscan motors
# ###    mT = Motor('16TEST1:m14')
# ###
# ###    # define struck, softGlue, SG_Config, and abort PV
# ###    mcs = Struck('16TEST1:SIS1:')
# ###    softglue = Device('16TEST1:softGlue:', softglue_args)
# ###    sg_config = Device('16TEST1:SGMenu:', sg_config_args)
# ###    abort = PV('16TEST1:Unidig1Bo1')
# ###
# ###    # create dictionary for valid flyscan motors
# ###    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
# ###    stage_dict = {
# ###        'TEST X': ['MAXV', mX, 'FI3_Signal', 2.0],
# ###        'TEST Y': ['MAXV', mY, 'FI4_Signal', 2.0],
# ###        'TEST Z': ['MAXV', mZ, 'FI5_Signal', 2.0],
# ###        'M12': ['MAXV', mW, 'FI6_Signal', 20.0],
# ###        'M14': ['MAXV', mT, 'FI7_Signal', 1.0]}
# ###
# ###    # create lists for drop-down menus
# ###    fly_list = ['TEST Y', 'TEST Z', 'More']
# ###    step_list = ['TEST Y', 'TEST Z', 'More', 'Custom']
# ###
# ###    # more list should contain all fly motors not included in fly_list
# ###    more_list = [
# ###        'TEST X',
# ###        'TEST W',
# ###        'M14']
# ###
# ###    # counter list same for all endstations
# ###    counter_list = [
# ###        'Beamstop diode',
# ###        'Removable diode',
# ###        'Hutch reference',
# ###        'FOE ion chamber',
# ###        '50 MHz clock']

elif config.stack_choice.get() == 'TEST':
    root.title('Diptera - A real program for scanning imaginary stages')
    # create objects including epics Motors, Struck, etc
    # define 5-motor sample stack
    mX = Motor('16HEXGP:m1')
    mY = Motor('16HEXGP:m2')
    mZ = Motor('16HEXGP:m3')
    mW = Motor('XPSGP:m4')
    mYbase = Motor('XPSGP:m5')

    # define xps ip (if needed)
    xps_ip = '164.54.164.24'
    # define hexapod ip
    hex_ip = '164.54.164.194'

    # define any additional flyscan motors
    # none

    # define struck, softGlue, SG_Config, and abort PV
    mcs = Struck('16TEST1:SIS1:')
    softglue = Device('16TEST1:softGlue:', softglue_args)
    sg_config = Device('16TEST1:SGMenu:', sg_config_args)
    abort = PV('16TEST1:Unidig1Bo1')

    # create dictionary for valid flyscan motors
    # 'NAME': [controller, designation, softGlue, VMAX (in egu/s)]
    stage_dict = {
        'GP Hex X': ['HEX', mX, 'FI2_Signal', 2.0],
        'GP Hex Y': ['HEX', mY, 'FI2_Signal', 2.0],
        'GP Hex Z': ['HEX', mZ, 'FI2_Signal', 2.0],
        'GP Large W': ['XPS', mW, 'FI3_Signal', 10.0]}

    # create lists for drop-down menus
    fly_list = ['GP Hex Y', 'GP Hex Z', 'More']
    step_list = ['GP Hex Y', 'GP Hex Z', 'More', 'Custom']

    # more list should contain all fly motors not included in fly_list
    more_list = [
        'GP Hex X',
        'GP Large W']

    # counter list same for all endstations
    counter_list = [
        'Beamstop diode',
        'Removable diode',
        'Hutch reference',
        'FOE ion chamber',
        '50 MHz clock']

# Primary frames for displaying objects
framePlot = Frame(root)
framePlot.grid(row=0, rowspan=4, column=0, sticky='n')
frameFiles = Frame(root, width=652, height=123, bd=5, relief=RIDGE, padx=10, pady=5)
frameFiles.grid(row=4, column=0, sticky='nsew')
frameScanBox = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameScanBox.grid(row=0, column=1, sticky='ew')
frameCentering = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameCentering.grid(row=1, column=1, sticky='ew')
frameIntensity = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameIntensity.grid(row=2, column=1, sticky='ew')
# frameImages = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
# frameImages.grid(row=5, column=1, sticky='nsew')
framePosition = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
framePosition.grid(row=3, column=1, sticky='nsew')
frameActions = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameActions.grid(row=4, column=1, sticky='ew')
# frameOverlays = Frame(root, width=652, bd=5, relief=RIDGE, padx=10, pady=5)
# frameOverlays.grid(row=5, column=0, sticky='ew')

# make a drawing area
fig = plt.figure(figsize=(9, 6.7))
canvas = FigureCanvasTkAgg(fig, framePlot)
canvas.get_tk_widget().grid(row=0, column=0)
toolbar = NavigationToolbar2TkAgg(canvas, framePlot)
toolbar.grid(row=1, column=0, sticky='ew')

# initialize core data
core = CoreData()

# collections of objects to put in frames above
data = DataLoad(frameFiles)
fly_axis = ScanBox(frameScanBox, label='Fly axis')
step_axis = ScanBox(frameScanBox, label='Step axis')
scan = ScanActions(frameScanBox)
center = Centering(frameCentering)
counter = Counters(frameIntensity)
hax = Position(framePosition, label='Horizontal axis')
vax = Position(framePosition, label='Vertical axis')
action = Actions(frameActions)
alloverlays = OverlayWindow(root)
over1 = Overlay(alloverlays.frame, label='over1')
over2 = Overlay(alloverlays.frame, label='over2')
over3 = Overlay(alloverlays.frame, label='over3')
image = Images(root)
staff = Staff(root)

# next eight lines are for widgets in the plot area
inner_frame = Frame(framePlot)
inner_frame.grid(row=1, column=0, sticky='s')
cbox_enable_grid = Checkbutton(inner_frame, text='Overlay 2D Grid', variable=image.grid_flag, command=update_plot)
cbox_enable_grid.grid(row=0, column=0, padx=20)
difference_text = Label(inner_frame, text='Difference')
difference_text.grid(row=0, column=1, padx=5)
difference_label = Label(inner_frame, textvariable=hax.delta_pos, relief=SUNKEN, width=8)
difference_label.grid(row=0, column=2)

# rest of the stuff (may not be the best place, but . . .)
cid = fig.canvas.mpl_connect('button_press_event', onclick)
root.protocol('WM_DELETE_WINDOW', close_quit)
staff.popup.protocol('WM_DELETE_WINDOW', hide_staff)
image.popup.protocol('WM_DELETE_WINDOW', hide_image)
alloverlays.popup.protocol('WM_DELETE_WINDOW', hide_alloverlays)
root.update_idletasks()
root.deiconify()
step_axis.set_directory()
root.mainloop()
