__author__ = 'j.smith'

import pylab as plb
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import exp
import numpy as np
from math import pi, sqrt

listx = [0.7166,
         0.7176,
         0.7186,
         0.7196,
         0.7206,
         0.7216,
         0.7226,
         0.7236,
         0.7246,
         0.7256,
         0.7266,
         0.7276,
         0.7286,
         0.7296,
         0.7306,
         0.7316,
         0.7326,
         0.7336,
         0.7346,
         0.7356,
         0.7366,
         0.7376,
         0.7386,
         0.7396,
         0.7406,
         0.7416,
         0.7426,
         0.7436,
         0.7446,
         0.7456,
         0.7466,
         0.7476,
         0.7486,
         0.7496,
         0.7506,
         0.7516,
         0.7526,
         0.7536,
         0.7546,
         0.7556,
         0.7566,
         0.7576,
         0.7586,
         0.7596,
         0.7606,
         0.7616,
         0.7626,
         0.7636,
         0.7646,
         0.7656,
         0.7666,
         0.7676,
         0.7686,
         0.7696,
         0.7706,
         0.7716,
         0.7726,
         0.7736,
         0.7746,
         0.7756,
         ]
listy = [-0.11747,
         -0.11747,
         0.74437,
         -0.30313,
         -0.59784,
         -0.42265,
         -0.41671,
         0.34598,
         0.47999,
         -0.37308,
         0.29411,
         -1.17683,
         -0.54373,
         0.83736,
         -0.35899,
         -1.12083,
         -1.82499,
         0.51759,
         -0.61778,
         -3.87688,
         -2.9183,
         -8.29526,
         -14.50581,
         -20.82182,
         -33.19348,
         -47.65442,
         -68.84498,
         -87.5042,
         -99.18335,
         -111.90411,
         -117.83654,
         -103.65207,
         -83.52208,
         -68.26118,
         -54.54199,
         -39.67673,
         -23.35024,
         -14.35263,
         -8.54725,
         -5.10411,
         -3.07992,
         -1.8955,
         -1.32265,
         -1.05559,
         -0.80691,
         -0.57792,
         -0.66585,
         -0.52989,
         -0.29307,
         -0.44554,
         -0.2719,
         -0.18181,
         -0.37319,
         -0.18308,
         0.03284,
         -0.07699,
         -0.28206,
         0.22798,
         0.06173,
         0.06173,
         ]
x = np.asarray(listx)
y = np.asarray(listy)
# print x
# print y
# n = len(x)

# mean = sum(x)/n
# sigma = 1


def gausl(x,a,x0,sigmal):
    return a*exp(-(x-x0)**2/(2*sigmal**2))


def gausr(x,a,x0,sigmar):
    return a*exp(-(x-x0)**2/(2*sigmar**2))


def pv(x, y0, a, mul, mur, x0, wl, wr):
    condlist = [x < x0, x >= x0]
    funclist = [
         lambda x: y0 + a * (mul * (2/pi) * (wl / (4*(x-x0)**2 + wl**2)) + (1 - mul) * (sqrt(4*np.log(2)) / (sqrt(pi) * wl)) * exp(-(4*np.log(2)/wl**2)*(x-x0)**2)),
         lambda x: y0 + a * (mur * (2/pi) * (wr / (4*(x-x0)**2 + wr**2)) + (1 - mur) * (sqrt(4*np.log(2)) / (sqrt(pi) * wr)) * exp(-(4*np.log(2)/wr**2)*(x-x0)**2))]
    return np.piecewise(x, condlist, funclist)


def pw(x, a, x0, sigmal, sigmar):
     condlist = [x < x0, x >= x0]
     # print condlist
     funclist = [lambda x: a*exp(-(x-x0)**2/(2*sigmal**2)), lambda x: a*exp(-(x-x0)**2/(2*sigmar**2))]
     # print funclist
     return np.piecewise(x, condlist, funclist)


# popt,pcov = curve_fit(pw,x,y,p0=[1,.75,.1,.1])
# print popt

popt,pcov = curve_fit(pv, x, y, p0=[0, -1, .5, .5, .75, .008, .008])
print popt
perr = np.sqrt(np.diag(pcov))
print perr
plt.plot(x,y,'b+:',label='data')
plt.plot(x,pv(x,*popt),'ro:',label='fit')
plt.plot(x, (y-pv(x,*popt)))
plt.legend()
plt.title('Fig. 3 - Fit for Time Constant')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.show()

