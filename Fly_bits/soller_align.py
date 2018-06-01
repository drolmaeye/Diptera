import fabio
import numpy as np
import matplotlib.pyplot as plt
from fabio import fabioimage

p = np.ones(50)
int1 = np.ones(50)
int2 = np.ones(50)
int3 = np.ones(50)
int4 = np.ones(50)
intt = np.ones(50)
# trunk = '\\\HPCAT21\\Pilatus2\\500_500\\Data\\2018-1\\HPCAT\\MCC_0418b\\aligny\\'
trunk = '\\\HPCAT21\\Pilatus2\\500_500\\Data\\2018-2\\HPCAT\\MCC\\align_yg\\'
# ###index = 0
# ###branch = 'glass_MCC_' + '001.tif'
# ###image_path = trunk + branch
# ###print image_path
# ###current_image = fabio.open(image_path)
center_x = 490
center_y = 513
xi = 700
yi = 300
delta_x = abs(xi - center_x)
delta_y = abs(yi - center_y)
y1 = yi - 20
y2 = yi + 20
y3 = yi + 2*delta_y - 20
y4 = yi + 2*delta_y + 20
x1 = xi - 2*delta_x - 20
x2 = xi - 2*delta_x + 20
x3 = xi - 20
x4 = xi +20

# #### ###for steps in range(41):
for fly in range(50):
    index = fly + 1
    branch = 'yg_b_' + str(index).zfill(3) + '.tif'
    image_path = trunk + branch
    current_image = fabio.open(image_path)
    intensity_sum = 0
    # ###for each in range(424, 619):
    # ###    intensity_sum += sum(current_image.data[each])
    roi1 = current_image.data[y1:y2, x3:x4]
    roi2 = current_image.data[y1:y2, x1:x2]
    roi3 = current_image.data[y3:y4, x1:x2]
    roi4 = current_image.data[y3:y4, x3:x4]
    roi1_s = np.sum(roi1)
    roi2_s = np.sum(roi2)
    roi3_s = np.sum(roi3)
    roi4_s = np.sum(roi4)
    roi_total = roi1_s + roi2_s + roi3_s +roi4_s
    p[fly] = (index - 1)*0.010 -0.250
    int1[fly] = roi1_s
    int2[fly] = roi2_s
    int3[fly] = roi3_s
    int4[fly] = roi4_s
    intt[fly] = roi_total
print p
print int1
print int2
print int3
print int4
print intt

# comment

plt.plot(p, int1, 'r')
plt.plot(p, int2, 'g')
plt.plot(p, int3, 'b')
plt.plot(p, int4, 'magenta')
plt.plot(p, intt, 'brown')
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

print 'still ran'
