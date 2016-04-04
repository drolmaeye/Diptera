import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle

class Annotate(object):
    def __init__(self):
        self.ax = plt.gca()
        # self.rect = Rectangle((0,0), 1, 1)
        self.circ = Circle((0,0), 1, alpha=0.1)
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        # self.ax.add_patch(self.rect)
        self.ax.add_patch(self.circ)
        self.press = None
        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.ax.figure.canvas.mpl_connect('button_release_event', self.on_release)

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

a = Annotate()
plt.show()