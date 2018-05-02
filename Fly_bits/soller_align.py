import fabio
import numpy as np
import matplotlib.pyplot as plt
from fabio import fabioimage

x = np.ones(50)
y1 = np.ones(50)
y2 = np.ones(50)
y3 = np.ones(50)
y4 = np.ones(50)
yt = np.ones(50)
trunk = '\\\HPCAT21\\Pilatus2\\500_500\\Data\\2018-1\\HPCAT\\MCC_0418b\\aligny\\'
index = 0
# ###for steps in range(41):
for fly in range(50):
    index = fly + 1
    branch = 'yscan_d_' + str(index).zfill(3) + '.tif'
    image_path = trunk + branch
    current_image = fabio.open(image_path)
    intensity_sum = 0
    # ###for each in range(424, 619):
    # ###    intensity_sum += sum(current_image.data[each])
    roi1 = current_image.data[46:97, 927:968]
    roi2 = current_image.data[46:97, 14:55]
    roi3 = current_image.data[952:993, 14:55]
    roi4 = current_image.data[952:993, 927:968]
    roi1_s = np.sum(roi1)
    roi2_s = np.sum(roi2)
    roi3_s = np.sum(roi3)
    roi4_s = np.sum(roi4)
    roi_total = roi1_s + roi2_s + roi3_s +roi4_s
    x[fly] = index
    y1[fly] = roi1_s
    y2[fly] = roi2_s
    y3[fly] = roi3_s
    y4[fly] = roi4_s
    yt[fly] = roi_total
print x
print y1
print y2
print y3
print y4
print yt



plt.plot(x, y1, 'r')
plt.plot(x, y2, 'g')
plt.plot(x, y3, 'b')
plt.plot(x, y4, 'magenta')
plt.plot(x, yt, 'brown')
plt.show()


# temp_image = fabio.open(image_path)
# print len(temp_image.data[1042])
# print temp_image.data
# print temp_image.data.shape
# alpha = sum(temp_image.data[619])
# a = 0
# for each in range(424, 619):
#     b = sum(temp_image.data[each])
#     a += sum(temp_image.data[each])
