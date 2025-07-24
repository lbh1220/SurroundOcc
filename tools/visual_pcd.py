import numpy as np
import matplotlib.pyplot as plt

points = np.load('/home/liang/Projects/SurroundOcc/visual_dir/1753196389.626.npy')  # (N, 3) 或 (N, 4)
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(points[:, 0], points[:, 1], points[:, 2], s=1, c=points[:, 3] if points.shape[1] > 3 else 'b')
plt.show()