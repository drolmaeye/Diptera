__author__ = 'j.smith'

'''
A GUI for creating, reading, and graphing flyscan (1d or 2d) files

Devel version test for github!! 2 August 2015
'''

# import necessary modules
from Tkinter import *
from ttk import Combobox
from tkMessageBox import *
from tkFileDialog import *
import tkFont
import os.path
from epics import *
from epics.devices import Struck
import numpy as np
from math import cos, sin, radians
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg


# define classes
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
        # plot flag that cannot be turned off (for now)
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
            self.axis.set('XPS Cen Y')
            self.flag.set(1)
        elif label == 'Step axis':
            self.axis.set('XPS Sam Z')
            self.flag.set(0)
        self.rel_min.set('%.3f' % -.05)
        self.step_size.set('%.4f' % .01)
        self.rel_max.set('%.3f' % .05)
        self.npts.set(11)
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
        user_dir = askdirectory(title='Select a user directory')
        if user_dir and os.path.exists(user_dir):
            win_path = os.path.normpath(user_dir)
            new_directory = win_path + '\\'
            prefix = new_directory + 'fScan_'
            index = self.scan_no.get()
            full_filename = prefix + index + '.npz'
            if not os.path.isfile(full_filename):
                pass
            else:
                while os.path.isfile(full_filename):
                    incremented_index = str(int(index) + 1)
                    index = incremented_index.zfill(3)
                    full_filename = prefix + index + '.npz'
                overwrite_warn()
            return self.scan_directory.set(new_directory), self.scan_no.set(index)
        else:
            self.scan_directory.set(current_directory)
            path_warn()

    def calc_size(self):
        # should be called on every position validation
        i = self.rel_min.get()
        f = self.rel_max.get()
        p = self.npts.get()
        size = (f - i) / (p - 1)
        if self == fly_axis:
            msize = size*10000
            quotient = divmod(msize, 5)
            if quotient[0] > 1 and round(quotient[1], 5) == 0:
                fly_axis.flag.set(1)
                fly_axis.led.config(state=NORMAL)
            else:
                fly_axis.flag.set(0)
                fly_axis.led.config(state=DISABLED)
        return self.step_size.set('%.4f' % size)

    def axis_validate(self, event, *args):
        if self.axis.get() != 'Custom':
            pass
        else:
            custom_stage = StringVar()
            popup = Toplevel()
            xtop = root.winfo_x() + root.winfo_width() / 2 - 150
            ytop = root.winfo_y() + root.winfo_height() / 2 - 150
            popup.geometry('300x300+%d+%d' % (xtop, ytop))
            popup.title('Custom step stage definition')
            popup.grab_set()
            label_1 = Label(popup, text='Please enter a valid motor prefix')
            label_1.pack(side=TOP, pady=10)
            entry = Entry(popup, textvariable=custom_stage)
            entry.pack(pady=20)
            entry.bind('<Return>', lambda r: popup.destroy())
            button = Button(popup, text='OK', width=18, command=lambda: popup.destroy())
            button.pack(pady=10)
            entry.focus_set()
            root.wait_window(popup)
            prefix = custom_stage.get()
            try:
                self.mCustom = Motor(prefix, timeout=1.0)
            except:
                showwarning('Invalid entry',
                            'Cannot connect to %s, please try again' % prefix)
                self.axis.set('XPS Sam Z')
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
        self.exp_time.set('%.3f' % 0.2)

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

    def start_scan(self):
        pass
        action.abort.set(0)
        # ###make this a static method###
        # clear plot, position info and set dimension
        while step_axis.scan_directory.get() == 'Select directory before scan':
            step_axis.choose_directory()
        if step_axis.axis.get() == fly_axis.axis.get() and step_axis.flag.get():
            showwarning('Stage overworked',
                        'Stage cannot step and fly at the same time\n'
                        'Please select different stage(s) and try again')
            return
        fly_axis.npts_validate()
        step_axis.npts_validate()
        if not fly_axis.flag.get():
            showwarning('Scan aborted',
                        'Modify Fly axis parameters until you have a green light')
            return
        # enter step stage info for centering scans
        if center.c_flag.get():
            step_axis.flag.set(1)
            step_axis.axis.set('XPS Omega')
            omega = float(center.delta_w.get())
            step_axis.rel_min.set('-' + '%.3f' % omega)
            step_axis.rel_max.set('%.3f' % omega)
            step_axis.npts.set(3)
            step_axis.calc_size()
        plt.clf()
        # generate filename
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
        h_active = fly_axis.axis.get()
        hax.active_stage.set(h_active)
        # clear fields
        data.current_slice.set(1)
        data.slice_flag.set(0)
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
        if step_axis.flag.get():
            step_npts = step_axis.npts.get()
            v_active = step_axis.axis.get()
        else:
            step_npts = 1
            v_active = 'Counts'
        core.dimension = step_npts
        vax.active_stage.set(v_active)
        plt.gcf().canvas.draw()
        framePlot.update_idletasks()
        # define temporary EPICS motor devices, fly velocity, and scan endpoints
        mFly, mFlypco, channel = stage_dict[fly_axis.axis.get()]
        if step_axis.axis.get() in stage_dict:
            mStep = stage_dict[step_axis.axis.get()][0]
        else:
            mStep = step_axis.mCustom
        bnc.put(channel)
        mFly_ipos = mFly.RBV
        mStep_ipos = mStep.RBV
        perm_velo = mFly.VELO
        temp_velo = fly_axis.step_size.get() / self.exp_time.get()
        abs_step_plot_min = mStep_ipos + step_axis.rel_min.get()
        abs_step_plot_max = mStep_ipos + step_axis.rel_max.get()
        abs_fly_plot_min = mFly_ipos + fly_axis.rel_min.get() + 0.5*fly_axis.step_size.get()
        abs_fly_plot_max = mFly_ipos + fly_axis.rel_max.get() - 0.5*fly_axis.step_size.get()
        core.FLY = np.linspace(abs_fly_plot_min, abs_fly_plot_max, fly_axis.npts.get() - 1)
        core.STP = np.linspace(abs_step_plot_min, abs_step_plot_max, step_axis.npts.get())
        core.TIM = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.FOE = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.REF = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.BSD = np.ones((step_npts, fly_axis.npts.get() - 1))
        core.RMD = np.ones((step_npts, fly_axis.npts.get() - 1))
        abs_fly_min = mFly_ipos + fly_axis.rel_min.get()
        abs_fly_max = mFly_ipos + fly_axis.rel_max.get()
        fly_zero = abs_fly_min - temp_velo * mW.ACCL * 1.5
        fly_final = abs_fly_max + temp_velo * mW.ACCL * 1.5
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
            return
        # set up pco
        mFlypco.put('PositionCompareMode', 1, wait=True)
        mFlypco.put('PositionComparePulseWidth', 1, wait=True)
        # smallest step below, real step size after endpoints
        mFlypco.put('PositionCompareStepSize', 0.001, wait=True)
        if mFlypco.PositionCompareMaxPosition <= abs_fly_min:
            mFlypco.PositionCompareMaxPosition = abs_fly_max
            mFlypco.PositionCompareMinPosition = abs_fly_min
        else:
            mFlypco.PositionCompareMinPosition = abs_fly_min
            mFlypco.PositionCompareMaxPosition = abs_fly_max
        mFlypco.PositionCompareStepSize = fly_axis.step_size.get()
        for steps in range(step_npts):
            if step_npts != 1:
                if not action.abort.get():
                    step_rel = step_axis.rel_min.get() + steps * step_axis.step_size.get()
                    step_abs = mStep_ipos + step_rel
                    mStep.move(step_abs, wait=True)
                else:
                    mFlypco.put('PositionCompareMode', 0, wait=True)
                    mFly.move(mFly_ipos, wait=True)
                    mStep.move(mStep_ipos, wait=True)
                    showwarning('Acquisition aborted', '2D scan aborted,\nNo data saved,\nStages returnd to initial positions')
                    return
            mFly.move(fly_zero, wait=True)
            time.sleep(.25)
            mFly.VELO = temp_velo
            # initialize struck for dc_1M collection
            mcs.stop()
            mcs.ExternalMode()
            mcs.put('InputMode', 3, wait=True)
            mcs.put('OutputMode', 3, wait=True)
            mcs.put('OutputPolarity', 0, wait=True)
            mcs.put('LNEStretcherEnable', 1, wait=True)
            mcs.put('LNEOutputPolarity', 1, wait=True)
            mcs.put('LNEOutputDelay', 0, wait=True)
            mcs.put('LNEOutputWidth', 1e-6, wait=True)
            mcs.NuseAll = fly_axis.npts.get() - 1
            # initialize detector if necessary
            # ###if image.flag.get():
            # ###    prefix = image.user_path.get() + image.sample_name.get() + '_'
            # ###    image_no = image.image_no.get()
            # ###    suffix = '.tif'
            # ###    first_filename = prefix + image_no + suffix
            # ###    print first_filename
            # ###    if not os.path.isfile(first_filename):
            # ###        print "is not a file"
            # ###        pass
            # ###    else:
            # ###        while os.path.isfile(first_filename):
            # ###            incremented_index = str(int(image_no) + 1)
            # ###            image_no = incremented_index.zfill(3)
            # ###            first_filename = prefix + image_no + suffix
            # ###        image.image_no.set(image_no)
            # ###        overwrite_warn()
            # ###    detector.AcquirePeriod = scan.exp_time.get()
            # ###    detector.AcquireTime = scan.exp_time.get() - 0.003
            # ###    detector.FileName = image.sample_name.get()
            # ###    detector.TriggerMode = 2
            # ###    detector.FileNumber = image.image_no.get()
            # ###    detector.NumImages = fly_axis.npts.get() - 1
            # ###    detector.Acquire = 1
            # Final actions plus data collection move
            mcs.start()
            mFly.move(fly_final, wait=True)
            # ###if image.flag.get():
            # ###    while detector.Acquire:
            # ###        time.sleep(0.1)
            # ###    image_number = detector.FileNumber + detector.NumImages - 1
            # ###    str_image_number = str(image_number)
            # ###    image.image_no.set(str_image_number.zfill(3))
            # ###    detector.FileNumber = image_number
            # handle data
            TIM_ara = mcs.readmca(1)
            FOE_ara = mcs.readmca(5)
            REF_ara = mcs.readmca(4)
            BSD_ara = mcs.readmca(6)
            RMD_ara = mcs.readmca(3)
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
            mFly.VELO = perm_velo
            time.sleep(.25)
            update_plot()
            # try this for not responding, possibly remove
            framePlot.update()
        # recover
        # ###if image.flag.get():
        # ###    detector.TriggerMode = 0
        # ###    detector.NumImages = 1
        # ###    image.flag.set(0)
        mFlypco.put('PositionCompareMode', 0, wait=True)
        mFly.move(mFly_ipos, wait=True)
        mStep.move(mStep_ipos, wait=True)
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
        if center.c_flag.get():
            data.current_slice.set(1)
            data.slice_flag.set(1)
            update_plot()


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
        self.scale.set(1.0)
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
        #  self.button_update = Button(self.frame, text='Update plot', command=update_plot)
        # self.button_update.grid(row=1, rowspan=2, column=6, padx=0)
        self.entry_max_scale = Entry(self.frame, textvariable=self.max_scale, width=5)
        self.entry_max_scale.grid(row=1, column=6)
        self.entry_max_scale.bind('<FocusOut>', self.max_scale_validate)
        self.entry_max_scale.bind('<Return>', self.max_scale_validate)
        self.entry_min_scale = Entry(self.frame, textvariable=self.min_scale, width=5)
        self.entry_min_scale.grid(row=2, column=6)
        self.entry_min_scale.bind('<FocusOut>', self.min_scale_validate)
        self.entry_min_scale.bind('<Return>', self.min_scale_validate)
        self.entry_levels = Entry(self.frame, textvariable=self.levels, width=5)
        self.entry_levels.grid(row=1, rowspan=2, column=7)
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
            if 4 <= val < 128:
                update_plot()
            else:
                raise ValueError
        except ValueError:
            self.levels.set(64)
            update_plot()
            invalid_entry()


class Images:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.flag = IntVar()
        self.det_path = StringVar()
        self.user_path = StringVar()
        self.sample_name = StringVar()
        self.image_no = StringVar()
        self.flag.set(0)
        self.user_path.set('P:\\2015-1\\HPCAT\\SXD_test\\')
        self.sample_name.set('test')
        self.image_no.set('001')

        # make column headings
        self.head_images = Label(self.frame, text='IMAGE CONTROL')
        self.head_images.grid(row=0, column=0, columnspan=2, pady=5, sticky='w')

        # make and place widgets
        self.check_image_enable = Checkbutton(self.frame, text='Enable', variable=self.flag)
        self.check_image_enable.grid(row=1, rowspan=2, column=0, columnspan=2)
        self.label_det_path = Label(self.frame, text='Detector path')
        self.label_det_path.grid(row=0, column=2, padx=5, pady=5)
        self.display_det_path = Label(self.frame, textvariable=self.det_path,
                                      width=40, relief=SUNKEN, anchor='w')
        self.display_det_path.grid(row=0, column=3, columnspan=3, pady=5)
        self.label_user_path = Label(self.frame, text='User directory')
        self.label_user_path.grid(row=1, column=2, padx=5, pady=5)
        self.entry_user_path = Entry(self.frame, textvariable=self.user_path,
                                     width=46)
        self.entry_user_path.grid(row=1, column=3, columnspan=3, pady=5)
        self.entry_user_path.bind('<FocusOut>', self.user_path_validation)
        self.entry_user_path.bind('<Return>', self.user_path_validation)
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
        self.delta_y = StringVar()
        self.delta_w.set(2.0)

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

        # make and place widgets
        self.cbox_c_flag = Checkbutton(self.frame, text='Enable', variable=self.c_flag)
        self.cbox_c_flag.grid(row=1, column=0, padx=5, pady=5)
        self.entry_delta_w = Entry(self.frame, textvariable=self.delta_w, width=8)
        self.entry_delta_w.grid(row=1, column=2, padx=5, pady=5)
        self.label_y_minus = Label(self.frame, textvariable=self.y_minus_pos, relief=SUNKEN, width=8)
        self.label_y_minus.grid(row=1, column=3, padx=5, pady=5)
        self.label_y_center = Label(self.frame, textvariable=self.y_center_pos, relief=SUNKEN, width=8)
        self.label_y_center.grid(row=1, column=4, padx=5, pady=5)
        self.label_y_plus = Label(self.frame, textvariable=self.y_plus_pos, relief=SUNKEN, width=8)
        self.label_y_plus.grid(row=1, column=5, padx=5, pady=5)
        self.button_delta_x = Button(self.frame, textvariable=self.delta_x, command=self.move_x, width=7)
        self.button_delta_x.grid(row=1, column=6, padx=5, pady=5)
        self.button_delta_x.config(state=DISABLED)
        self.label_delta_y = Label(self.frame, textvariable=self.delta_y, relief=SUNKEN, width=8)
        self.label_delta_y.grid(row=1, column=7, padx=5, pady=5)

    def calc_deltas(self):
        if not center.y_minus_pos.get() or not center.y_center_pos.get() or not center.y_plus_pos.get():
            return
        else:
            center.button_delta_x.config(state=NORMAL, background='green')
            dsx_plus = float(center.y_plus_pos.get()) - float(center.y_center_pos.get())
            dsx_minus = float(center.y_minus_pos.get()) - float(center.y_center_pos.get())
            delta_y = (dsx_plus + dsx_minus)/2/(cos(radians(center.delta_w.get()))-1)
            delta_x = (dsx_plus - dsx_minus)/2/(sin(radians(center.delta_w.get())))
            center.delta_y.set('%.4f' % delta_y)
            center.delta_x.set('%.4f' % delta_x)

    def move_x(self):
        try:
            val = float(center.delta_x.get())
        except ValueError:
            return
        i_pos = mX.RBV
        f_pos = i_pos + val
        mX.move(f_pos, wait=True)
        center.button_delta_x.config(state=DISABLED, background='SystemButtonFace')
        center.c_flag.set(0)
        step_axis.flag.set(0)


class Position:
    def __init__(self, master, label):
        self.frame = Frame(master)
        self.frame.pack()

        # define instance variables and set defaults
        self.active_stage = StringVar()
        self.min_pos = StringVar()
        self.mid_pos = StringVar()
        self.max_pos = StringVar()
        self.width = StringVar()
        self.active_stage.set('None')

        # setup trace on relevant values
        self.min_pos.trace('w', self.calc_width)
        self.max_pos.trace('w', self.calc_width)

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
        else:
            self.label_min_pos = Label(self.frame, textvariable=self.min_pos, relief=SUNKEN, width=8)
            self.label_min_pos.grid(row=1, column=3, padx=5)
            self.label_mid_pos = Label(self.frame, textvariable=self.mid_pos, relief=SUNKEN, width=8, fg='red')
            self.label_mid_pos.grid(row=1, column=4, padx=5)
            self.label_max_pos = Label(self.frame, textvariable=self.max_pos, relief=SUNKEN, width=8)
            self.label_max_pos.grid(row=1, column=5, padx=5)
        self.label_width = Label(self.frame, textvariable=self.width, relief=SUNKEN, width=8)
        self.label_width.grid(row=1, column=6, padx=5)

    def calc_width(self, *args):
        if core.dimension == 1 or data.slice_flag.get():
            try:
                self.width.set(str(float(self.max_pos.get()) - float(self.min_pos.get())))
            except ValueError:
                return

    def move_min(self):
        try:
            val = float(hax.min_pos.get())
        except ValueError:
            return
        stage = hax.active_stage.get()
        if stage in stage_dict:
            mH = stage_dict[stage][0]
            mH.move(val, wait=True)
        else:
            return

    def move_mid(self):
        if core.dimension == 1 or data.slice_flag.get():
            try:
                val = float(hax.mid_pos.get())
            except ValueError:
                return
            stage = hax.active_stage.get()
            if stage in stage_dict:
                mH = stage_dict[stage][0]
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
                mH = stage_dict[h_stage][0]
                mH.move(h_val, wait=True)
                mV = stage_dict[v_stage][0]
                mV.move(v_val, wait=True)
            elif h_stage in stage_dict and not v_stage in stage_dict:
                mH = stage_dict[h_stage][0]
                mH.move(h_val, wait=True)
                mV = step_axis.mCustom
                mV.move(v_val, wait=True)
            else:
                return

    def move_max(self):
        try:
            val = float(hax.max_pos.get())
        except ValueError:
            return
        stage = hax.active_stage.get()
        if stage in stage_dict:
            mH = stage_dict[stage][0]
            mH.move(val, wait=True)
        else:
            return


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
        self.abort = IntVar()
        self.abort.set(0)

        # make big font
        bigfont = tkFont.Font(size=10, weight='bold')

        # make and place widgets
        self.button_abort = Button(self.frame, text='Abort',
                                   foreground='red', height=2, width=15,
                                   font=bigfont, command=self.abort)
        self.button_abort.grid(row=0, column=0, padx=5)
        self.button_staff = Button(self.frame,
                                   text='Staff',
                                   height=2, width=15, font=bigfont,
                                   command=self.open_staff)
        self.button_staff.grid(row=0, column=1, padx=5)
        self.quit_button = Button(self.frame, text='Quit', height=2, width=15,
                                  font=bigfont, command=close_quit)
        self.quit_button.grid(row=0, column=2, padx=5)

    def abort(self):
        action.abort.set(1)

    def open_staff(self):
        pass


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


def close_quit():
    # add dialog box back in and indent following code after testing period
    # ##if askyesno('Quit Diptera', 'Do you want to quit?'):
    plt.close('all')
    root.destroy()
    root.quit()


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
        for each in array_list:
            if each == core:
                pass
            else:
                if each.plot_flag.get():
                    index = each.overlay_slice.get() - 1
                    each.SCA = each.SCA[index]
    # clear fields and plot
    hax.min_pos.set('')
    hax.mid_pos.set('')
    hax.max_pos.set('')
    hax.width.set('')
    vax.min_pos.set('')
    vax.mid_pos.set('')
    vax.max_pos.set('')
    vax.width.set('')
    plt.clf()
    # plot it!
    plt.xlabel('Fly axis:  ' + fly_axis.axis.get())
    if core.dimension == 1 or data.slice_flag.get():
        plt.ylabel('Intensity')
        for each in array_list:
            if each.plot_flag.get():
                shp = each.FLY.shape
                #print shp
                #print each.SCA.shape
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
        # test autofill
        if center.c_flag.get():
            if data.current_slice.get() == 1:
                center.y_minus_pos.set('%.4f' % x_mid)
            elif data.current_slice.get() == 2:
                center.y_center_pos.set('%.4f' % x_mid)
            elif data.current_slice.get() == 3:
                center.y_plus_pos.set('%.4f' % x_mid)
            center.calc_deltas()
        # test over
        core.h_min = plt.axhline(f_min)
        core.h_mid = plt.axhline(f_mid, ls='--', c='r')
        core.h_max = plt.axhline(f_max)
        hax.min_pos.set('%.4f' % x_left)
        hax.mid_pos.set('%.4f' % x_mid)
        hax.max_pos.set('%.4f' % x_right)
        core.v_min = plt.axvline(x_left)
        core.v_mid = plt.axvline(x_mid, ls='--', c='r')
        core.v_max = plt.axvline(x_right)
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
        for each in array_list:
            if each.plot_flag.get():
                if counter.data_type.get() == 'Derivative':
                    plt.plot(each.FLY[1:-1], each.SCA[1:-1], marker='.', ls='-')
                else:
                    plt.plot(each.FLY, each.SCA, marker='.', ls='-')
    else:
        plt.ylabel('Step axis:  ' + step_axis.axis.get())
        # test intensity scaling
        area_min = np.amin(core.SCA)
        area_max = np.amax(core.SCA)
        area_range = area_max - area_min
        cf_min = area_min + area_range*counter.min_scale.get()*0.01
        cf_max = area_min + area_range*counter.max_scale.get()*0.01
        levels = counter.levels.get() + 1
        V = np.linspace(cf_min, cf_max, levels)
        # N = counter.max_scale.get()
        plt.contourf(core.FLY, core.STP, core.SCA, V)
        # plt.contourf(core.FLY, core.STP, core.SCA, 64)
        plt.colorbar()
        halfx = (plt.xlim()[1] + plt.xlim()[0])/2
        halfy = (plt.ylim()[1] + plt.ylim()[0])/2
        hax.mid_pos.set('%.4f' % halfx)
        vax.mid_pos.set('%.4f' % halfy)
        xind = np.abs(core.FLY - halfx).argmin()
        yind = np.abs(core.STP - halfy).argmin()
        data.current_slice.set(yind+1)
        fly_axis_length = core.FLY.shape[0]
        image_index = yind*fly_axis_length + xind + 1
        data.index.set(image_index)
    plt.gcf().canvas.draw()
    print 'update done'


'''
Program start
'''
root = Tk()
root.title('Diptera')

# TODO put 'create' stuff in a config dialog for various endstations
# station-independent arg lists for epics Devices
pco_args = ['PositionCompareMode', 'PositionCompareMinPosition',
            'PositionCompareMaxPosition', 'PositionCompareStepSize',
            'PositionComparePulseWidth', 'PositionCompareSettlingTime']

detector_args = ['ShutterMode', 'ShutterControl', 'AcquireTime',
                 'AcquirePeriod', 'NumImages', 'TriggerMode',
                 'Acquire', 'DetectorState_RBV', 'FilePath_RBV',
                 'FileName', 'FileNumber', 'AutoIncrement',
                 'FullFileName_RBV']

# create epics Motors, pco Devices, Struck, bnc PV, and detector Device
mX = Motor('XPSGP:m5')
mY = Motor('XPSGP:m4')
mZ = Motor('XPSGP:m3')
mW = Motor('XPSGP:m2')
mWGP = Motor('XPSGP:m1')

mXpco = Device('XPSGP:m5', pco_args)
mYpco = Device('XPSGP:m4', pco_args)
mZpco = Device('XPSGP:m3', pco_args)
mWpco = Device('XPSGP:m2', pco_args)
mWGPpco = Device('XPSGP:m1', pco_args)

mcs = Struck('16IDB:SIS1:')

bnc = PV('16IDB:cmdReply1_do_IO.AOUT')
# detector commented out for ioc protection
# #detector = Device('HP1M-PIL1:cam1:', detector_args)

# create dictionaries of valid motors, pcos, and counters
stage_dict = {
    'XPS Cen X': [mX, mXpco, 's05'],
    'XPS Cen Y': [mY, mYpco, 's04'],
    'XPS Sam Z': [mZ, mZpco, 's03'],
    'XPS Omega': [mW, mWpco, 's02'],
    'GP Omega': [mWGP, mWGPpco, 's01']}

fly_list = ['XPS Cen X', 'XPS Cen Y', 'XPS Sam Z', 'XPS Omega', 'GP Omega']
step_list = ['XPS Cen X', 'XPS Cen Y', 'XPS Sam Z', 'XPS Omega', 'GP Omega', 'Custom']

counter_list = [
    'Beamstop diode',
    'Removable diode',
    'Hutch reference',
    'FOE ion chamber',
    '50 MHz clock']

# Primary frames for displaying objects
framePlot = Frame(root)
framePlot.grid(row=0, rowspan=4, column=0)
frameScanBox = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameScanBox.grid(row=0, column=1, sticky='ew')
frameIntensity = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameIntensity.grid(row=1, column=1, sticky='ew')
frameImages = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameImages.grid(row=2, column=1, sticky='ew')
frameCentering = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameCentering.grid(row=3, column=1, sticky='ew')
framePosition = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
framePosition.grid(row=4, column=1, sticky='ew')
frameActions = Frame(root, bd=5, relief=RIDGE, padx=10, pady=10)
frameActions.grid(row=5, column=1)
frameFiles = Frame(root, width=652, height=123, bd=5, relief=RIDGE, padx=10, pady=5)
frameFiles.grid(row=4, column=0, sticky='nsew')
frameOverlays = Frame(root, bd=5, relief=RIDGE, padx=10, pady=5)
frameOverlays.grid(row=5, column=0)

# make a drawing area
fig = plt.figure(figsize=(8, 6))
canvas = FigureCanvasTkAgg(fig, framePlot)
canvas.get_tk_widget().grid(row=0, column=0)
toolbar = NavigationToolbar2TkAgg(canvas, framePlot)
toolbar.grid(row=1, column=0, sticky='ew')
quit_button = Button(framePlot, text='Quit', command=close_quit, width=15)
quit_button.grid(row=1, column=0, sticky='s')

# initialize core data
core = CoreData()


# collections of objects to put in frames above
fly_axis = ScanBox(frameScanBox, label='Fly axis')
step_axis = ScanBox(frameScanBox, label='Step axis')
scan = ScanActions(frameScanBox)
counter = Counters(frameIntensity)
image = Images(frameImages)
center = Centering(frameCentering)
hax = Position(framePosition, label='Horizontal axis')
vax = Position(framePosition, label='Vertical axis')
action = Actions(frameActions)
data = DataLoad(frameFiles)
over1 = Overlay(frameOverlays, label='over1')
over2 = Overlay(frameOverlays, label='over2')
over3 = Overlay(frameOverlays, label='over3')

# temporary!!!!
cid = fig.canvas.mpl_connect('button_press_event', onclick)
root.protocol('WM_DELETE_WINDOW', close_quit)
root.mainloop()

