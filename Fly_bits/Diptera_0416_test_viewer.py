
# import necessary modules
from Tkinter import *
from tkMessageBox import *
from tkFileDialog import *
import tkFont
import os.path
from epics import *
from epics.devices import Struck
import numpy as np
from math import cos, sin, radians, pi, sqrt
from scipy import exp, integrate
from scipy.optimize import curve_fit
## import fabio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# from matplotlib.patches import Circle





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
        self.circle = []
        self.dict_points = {}
        self.points = []
        # define dimension and specify default
        self.dimension = 11
        # plot flag that cannot be turned off (for now), meaning primary data always plotted
        self.plot_flag = IntVar()
        self.plot_flag.set(1)


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
        # self.button_update = Button(self.frame, text='Update plot', command=update_plot)
        # self.button_update.grid(row=1, rowspan=2, column=6, padx=0)
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
        # self.mid_pos.trace('w', self.calc_difference)

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

    def move_min(self):
        pass
        # ###if core.dimension == 1:
        # ###    try:
        # ###        val = float(hax.min_pos.get())
        # ###    except ValueError:
        # ###        return
        # ###    stage = hax.active_stage.get()
        # ###    if stage in stage_dict:
        # ###        mH = stage_dict[stage][1]
        # ###        mH.move(val, wait=True)
        # ###    else:
        # ###        return
        # ###else:
        # ###    try:
        # ###        h_val = float(hax.min_pos.get())
        # ###        v_val = float(vax.mid_pos.get())
        # ###    except ValueError:
        # ###        return
        # ###    h_stage = hax.active_stage.get()
        # ###    v_stage = vax.active_stage.get()
        # ###    if h_stage and v_stage in stage_dict:
        # ###        mH = stage_dict[h_stage][1]
        # ###        mH.move(h_val, wait=True)
        # ###        mV = stage_dict[v_stage][1]
        # ###        if not mV == mW:
        # ###            mV.move(v_val, wait=True)
        # ###    elif h_stage in stage_dict and not v_stage in stage_dict:
        # ###        mH = stage_dict[h_stage][1]
        # ###        mH.move(h_val, wait=True)
        # ###        mV = step_axis.mCustom
        # ###        mV.move(v_val, wait=True)
        # ###    else:
        # ###        return

    def move_mid(self):
        pass
        # ###if core.dimension == 1:
        # ###    try:
        # ###        val = float(hax.mid_pos.get())
        # ###    except ValueError:
        # ###        return
        # ###    stage = hax.active_stage.get()
        # ###    if stage in stage_dict:
        # ###        mH = stage_dict[stage][1]
        # ###        mH.move(val, wait=True)
        # ###    else:
        # ###        return
        # ###else:
        # ###    try:
        # ###        h_val = float(hax.mid_pos.get())
        # ###        v_val = float(vax.mid_pos.get())
        # ###    except ValueError:
        # ###        return
        # ###    h_stage = hax.active_stage.get()
        # ###    v_stage = vax.active_stage.get()
        # ###    if h_stage and v_stage in stage_dict:
        # ###        mH = stage_dict[h_stage][1]
        # ###        mH.move(h_val, wait=True)
        # ###        mV = stage_dict[v_stage][1]
        # ###        if not mV == mW:
        # ###            mV.move(v_val, wait=True)
        # ###    elif h_stage in stage_dict and not v_stage in stage_dict:
        # ###        mH = stage_dict[h_stage][1]
        # ###        mH.move(h_val, wait=True)
        # ###        mV = step_axis.mCustom
        # ###        mV.move(v_val, wait=True)
        # ###    else:
        # ###        return

    def move_max(self):
        pass
        # ###if core.dimension == 1:
        # ###    try:
        # ###        val = float(hax.max_pos.get())
        # ###    except ValueError:
        # ###        return
        # ###    stage = hax.active_stage.get()
        # ###    if stage in stage_dict:
        # ###        mH = stage_dict[stage][1]
        # ###        mH.move(val, wait=True)
        # ###    else:
        # ###        return
        # ###else:
        # ###    try:
        # ###        h_val = float(hax.max_pos.get())
        # ###        v_val = float(vax.mid_pos.get())
        # ###    except ValueError:
        # ###        return
        # ###    h_stage = hax.active_stage.get()
        # ###    v_stage = vax.active_stage.get()
        # ###    if h_stage and v_stage in stage_dict:
        # ###        mH = stage_dict[h_stage][1]
        # ###        mH.move(h_val, wait=True)
        # ###        mV = stage_dict[v_stage][1]
        # ###        if not mV == mW:
        # ###            mV.move(v_val, wait=True)
        # ###    elif h_stage in stage_dict and not v_stage in stage_dict:
        # ###        mH = stage_dict[h_stage][1]
        # ###        mH.move(h_val, wait=True)
        # ###        mV = step_axis.mCustom
        # ###        mV.move(v_val, wait=True)
        # ###    else:
        # ###        return

    # ###def calc_difference(self, *args):
    # ###    if core.dimension == 1 or data.slice_flag.get():
    # ###        try:
    # ###            final_pos = float(hax.mid_pos.get())
    # ###        except ValueError:
    # ###            return
    # ###        stage = hax.active_stage.get()
    # ###        if stage in stage_dict:
    # ###            mH = stage_dict[stage][1]
    # ###            initial_pos = mH.RBV
    # ###            difference = final_pos - initial_pos
    # ###            self.delta_pos.set('%.4f' % difference)
    # ###        else:
    # ###            return


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
        self.grid_flag = IntVar()

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
         # disabled for testing convenience only!!!
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
        #data_file = '\\\ZEON\\epics\\saveData\\16idb\\2016-1\\fScan_1653.npz'
        print data_file
        cdata = np.load(data_file)
        self.button_load.set(0)
        # center.c_flag.set(0)
        data.slice_flag.set(0)
        data.current_slice.set(1)
        data.index.set(1)
        # center.y_minus_pos.set('')
        # center.y_center_pos.set('')
        # center.y_plus_pos.set('')
        # center.delta_x.set('')
        # center.delta_y.set('')
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
        # ###if center.c_flag.get() and data.slice_flag.get():
        # ###    if data.current_slice.get() == 1:
        # ###        center.y_minus_pos.set('%.4f' % mid_now[0])
        # ###    elif data.current_slice.get() == 2:
        # ###        center.y_center_pos.set('%.4f' % mid_now[0])
        # ###    elif data.current_slice.get() == 3:
        # ###        center.y_plus_pos.set('%.4f' % mid_now[0])
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
        # ###if center.c_flag.get() and data.slice_flag.get():
        # ###    if data.current_slice.get() == 1:
        # ###        center.y_minus_pos.set('%.4f' % mid_fin[0])
        # ###    elif data.current_slice.get() == 2:
        # ###        center.y_center_pos.set('%.4f' % mid_fin[0])
        # ###    elif data.current_slice.get() == 3:
        # ###        center.y_plus_pos.set('%.4f' % mid_fin[0])
        # ###    center.calc_deltas()
        # ###if staff.focus_flag.get() and counter.data_type.get() == 'Derivative':
        # ###    if core.dimension == 1 or data.slice_flag.get():
        # ###        beamsize_integral()
        # ###        print staff.area, staff.pv_a.get()
        # ###        fraction = staff.area / staff.pv_a.get()
        # ###        staff.pv_beamsize.set('%.3f' % fraction)


class Annotate:
    def __init__(self):
        self.ax = plt.gca()
        print self.ax
        # self.rect = Rectangle((0,0), 1, 1)
        self.circ = plt.Circle((99,99), 1, alpha=0.3)
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.ax.add_artist(self.circ)
        self.press = None
        self.cidpress = self.circ.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidmove = self.circ.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cidrelease = self.circ.figure.canvas.mpl_connect('button_release_event', self.on_release)

    def on_press(self, event):
        print 'press'
        self.press = 1
        self.x0 = event.xdata
        self.y0 = event.ydata

    def on_motion(self, event):
        if self.press is None:
            return
        self.x1 = event.xdata
        self.y1 = event.ydata
        radius = ((self.x1 - self.x0)**2 + (self.y1 - self.y0)**2)**0.5
        self.circ.set_radius(radius)
        self.circ.center = self.x0, self.y0
        # ###self.rect.set_width(self.x1 - self.x0)
        # ###self.rect.set_height(self.y1 - self.y0)
        # ###self.rect.set_xy((self.x0, self.y0))
        self.ax.figure.canvas.draw()

    def on_release(self, event):
        print 'release'
        self.press = None
        self.x1 = event.xdata
        self.y1 = event.ydata
        radius = ((self.x1 - self.x0) ** 2 + (self.y1 - self.y0) ** 2) ** 0.5
        self.circ.set_radius(radius)
        self.circ.center = self.x0, self.y0
        # ###self.rect.set_width(self.x1 - self.x0)
        # ###self.rect.set_height(self.y1 - self.y0)
        # ###self.rect.set_xy((self.x0, self.y0))
        self.ax.figure.canvas.draw()
        # begin find indices inside circle
        pa_zero = time.clock()
        box_x_min = self.x0 - radius
        box_x_max = self.x0 + radius
        box_y_min = self.y0 - radius
        box_y_max = self.y0 + radius
        composite = None
        for y_points in range(len(core.STP)):
            if box_y_min < core.STP[y_points] < box_y_max:
                for x_points in range(len(core.FLY)):
                    if box_x_min < core.FLY[x_points] < box_x_max:
                        distance = ((core.STP[y_points] - self.y0)**2 + (core.FLY[x_points] - self.x0)**2)**0.5
                        if distance < radius:
                            image_index = y_points*len(core.FLY) + x_points + 1
                            trunk = '\\\HPCAT21\\Pilatus2\\500_500\\Data\\2016-1\\HPCAT\\Jesse\\'
                            branch = 'mesh_' + str(image_index).zfill(3) + '.tif'
                            image_path = trunk + branch
                            temp_image = fabio.open(image_path)
                            if not composite:
                                print 'first'
                                composite = temp_image
                            else:
                                composite.data += temp_image.data
        if composite:
            temp_name = 'composite.tif'
            composite.write(temp_name)
        pa_final = time.clock()




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
    # ###if image.dioptas_flag.get():
    # ###    image.send_to_dioptas()
    # point test
    if image_index in core.dict_points:
        print 'already there, removing'
        del core.dict_points[image_index]
    else:
        print 'we better add this!'
        core.dict_points[image_index] = (core.FLY[xind], core.STP[yind])
    core.points = core.dict_points.values()
    update_plot()
    return hax.mid_pos.set('%.4f' % x_val), vax.mid_pos.set('%.4f' % y_val)

















def invalid_entry():
    # generic pop-up notification for invalid text entries
    showwarning('Invalid Entry', message='Input was reset to default value')

def path_warn():
    showwarning('Invalid Path Name',
                'Please modify selection and try again')

def close_quit():
    # add dialog box back in and indent following code after testing period
    # ##if askyesno('Quit Diptera', 'Do you want to quit?'):
    plt.close('all')
    root.destroy()
    root.quit()


def update_plot(*args):
    # create a list for iteration
    array_list = [core]
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
        # ###if center.c_flag.get():
        # ###    if data.current_slice.get() == 1:
        # ###        center.y_minus_pos.set('%.4f' % x_mid)
        # ###    elif data.current_slice.get() == 2:
        # ###        center.y_center_pos.set('%.4f' % x_mid)
        # ###    elif data.current_slice.get() == 3:
        # ###        center.y_plus_pos.set('%.4f' % x_mid)
        # ###    center.calc_deltas()
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
        # ###if staff.focus_flag.get() and counter.data_type.get() == 'Derivative':
        # ###    abs_values = np.abs(core.SCA)
        # ###    guess_index = np.argmax(abs_values)
        # ###    a = core.SCA[guess_index] * 0.005
        # ###    x0 = core.FLY[guess_index]
        # ###    p0 = [a, x0, 0.5, 0.5, 0.005, 0.005]
        # ###    staff.popt, pcov = curve_fit(piecewise_split_pv, core.FLY, core.SCA, p0=p0)
        # ###    staff.pv_a.set('%.2f' % staff.popt[0])
        # ###    staff.pv_x0.set('%.4f' % staff.popt[1])
        # ###    staff.pv_mul.set('%.2f' % staff.popt[2])
        # ###    staff.pv_mur.set('%.2f' % staff.popt[3])
        # ###    staff.pv_wl.set('%.4f' % staff.popt[4])
        # ###    staff.pv_wr.set('%.4f' % staff.popt[5])
        # ###    staff.calc_mixes()
        # ###    # tpopt = tuple(staff.popt)
        # ###    # lower_bound = float(hax.min_pos.get())
        # ###    # upper_bound = float(hax.max_pos.get())
        # ###    # area, err = integrate.quad(func=piecewise_split_pv, a=lower_bound,
        # ###    #                            b=upper_bound, args=tpopt)
        # ###    beamsize_integral()
        # ###    print staff.area, staff.pv_a.get()
        # ###    fraction = staff.area / staff.pv_a.get()
        # ###    staff.pv_beamsize.set('%.3f' % fraction)
        for each in array_list:
            if each.plot_flag.get():
                if counter.data_type.get() == 'Derivative':
                    plt.plot(each.FLY[1:-1], each.SCA[1:-1], marker='.', ls='-')
                    # ###if staff.focus_flag.get():
                    # ###    plt.plot(core.FLY, piecewise_split_pv(core.FLY, *staff.popt), 'ro:')
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
        core.circle = []
        a = Annotate()
        core.circle.append(a)
        # grid option
        if data.grid_flag.get():
            eh = plt.gca()
            eh.set_yticks(core.STP, minor=True)
            eh.set_xticks(core.FLY, minor=True)
            eh.yaxis.grid(True, which='minor')
            eh.xaxis.grid(True, which='minor')
        if core.points:
            for each in core.points:
                plt.scatter(each[0], each[1])
        # ###if not core.points_plot:
        # ###    pass
        # ###else:
        # ###    core.points_plot.remove()
        # ###x_values = []
        # ###y_values = []
        # ###for each in core.points.keys():
        # ###    x_values.append(core.points[each][0])
        # ###    y_values.append(core.points[each][1])
        # ###print x_values
        # ###print y_values
        # ###core.points_plot = plt.scatter(x_values, y_values)
    plt.gcf().canvas.draw()
    print 'update done'

'''
Program start
'''
# filler to make it work
counter_list = [
    'Beamstop diode',
    'Removable diode',
    'Hutch reference',
    'FOE ion chamber',
    '50 MHz clock']





# end filler
root = Tk()
root.title('Diptera')
# Primary frames for displaying objects
framePlot = Frame(root)
framePlot.grid(row=0, rowspan=4, column=0, sticky='n')
frameIntensity = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
frameIntensity.grid(row=2, column=1, sticky='ew')
framePosition = Frame(root, width=595, bd=5, relief=RIDGE, padx=10, pady=10)
framePosition.grid(row=3, column=1, sticky='nsew')
frameFiles = Frame(root, width=652, height=123, bd=5, relief=RIDGE, padx=10, pady=5)
frameFiles.grid(row=4, column=0, sticky='nsew')

# make a drawing area
fig = plt.figure(figsize=(9, 6.7))
canvas = FigureCanvasTkAgg(fig, framePlot)
canvas.get_tk_widget().grid(row=0, column=0)
toolbar = NavigationToolbar2TkAgg(canvas, framePlot)
toolbar.grid(row=1, column=0, sticky='ew')

# initialize core data
core = CoreData()

# collections of objects to put in frames above
counter = Counters(frameIntensity)
hax = Position(framePosition, label='Horizontal axis')
vax = Position(framePosition, label='Vertical axis')
data = DataLoad(frameFiles)

# next eight lines are temporary home for widgets in the plot area
inner_frame = Frame(framePlot)
inner_frame.grid(row=1, column=0, sticky='s')
cbox_enable_grid = Checkbutton(inner_frame, text='Overlay 2D Grid', variable=data.grid_flag, command=update_plot)
# cbox_enable_grid = Checkbutton(inner_frame, text='Overlay 2D Grid', command=update_plot)
cbox_enable_grid.grid(row=0, column=0, padx=20)
difference_text = Label(inner_frame, text='Difference')
difference_text.grid(row=0, column=1, padx=5)
difference_label = Label(inner_frame, textvariable=hax.delta_pos, relief=SUNKEN, width=8)
difference_label.grid(row=0, column=2)
# end temporary home for widgets

cid = fig.canvas.mpl_connect('button_press_event', onclick)
root.protocol('WM_DELETE_WINDOW', close_quit)
root.update_idletasks()
root.mainloop()