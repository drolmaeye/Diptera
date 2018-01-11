import fabio
import numpy as np
import matplotlib.pyplot as plt

master_matrix = np.ones((41, 40))
print len(master_matrix[0])
trunk = '\\\HPCAT21\\Pilatus2\\500_500\\Data\\2017-3\\HPCAT\\SollerVolume\\1x1box_c\\'
index = 0
for steps in range(41):
    for fly in range(40):
        index = steps*40 + fly + 1
        branch = '1x1mm_box_c_' + str(index).zfill(3) + '.tif'
        image_path = trunk + branch
        current_image = fabio.open(image_path)
        intensity_sum = 0
        for each in range(424, 619):
            intensity_sum += sum(current_image.data[each])
        master_matrix[steps, fly] = intensity_sum
        print index

plt.contourf(master_matrix)
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
