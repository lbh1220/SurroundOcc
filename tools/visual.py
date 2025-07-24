import os, sys
import cv2, imageio
import mayavi.mlab as mlab
import numpy as np
# import torch


colors = np.array(
    [
        [0, 0, 0, 255],
        [255, 120, 50, 255],  # barrier              orangey
        [255, 192, 203, 255],  # bicycle              pink
        [255, 255, 0, 255],  # bus                  yellow
        [0, 150, 245, 255],  # car                  blue
        [0, 255, 255, 255],  # construction_vehicle cyan
        [200, 180, 0, 255],  # motorcycle           dark orange
        [255, 0, 0, 255],  # pedestrian           red
        [255, 240, 150, 255],  # traffic_cone         light yellow
        [135, 60, 0, 255],  # trailer              brown
        [160, 32, 240, 255],  # truck                purple
        [255, 0, 255, 255],  # driveable_surface    dark pink
        # [175,   0,  75, 255],       # other_flat           dark red
        [139, 137, 137, 255],
        [75, 0, 75, 255],  # sidewalk             dard purple
        [150, 240, 80, 255],  # terrain              light green
        [230, 230, 250, 255],  # manmade              white
        [0, 175, 0, 255],  # vegetation           green
        [0, 255, 127, 255],  # ego car              dark cyan
        [255, 99, 71, 255],
        [0, 191, 255, 255]
    ]
).astype(np.uint8)

#mlab.options.offscreen = True

voxel_size = 0.5
# pc_range = [-50, -50,  -5, 50, 50, 3]
pc_range = [-200, -200,  -100, 200, 200, 100]

visual_path = sys.argv[1]
fov_voxels = np.load(visual_path)

# Check if the data has semantic dimension (n,4) or not (n,3)
if fov_voxels.shape[1] == 3:
    # For non-semantic occupancy data (n,3), add a semantic dimension
    # Assign all occupied voxels to class 15 (manmade/building)
    semantic_labels = np.full((fov_voxels.shape[0], 1), 15, dtype=fov_voxels.dtype)
    fov_voxels = np.concatenate([fov_voxels, semantic_labels], axis=1)
    print(f"Added semantic dimension. Shape changed to: {fov_voxels.shape}")
elif fov_voxels.shape[1] == 4:
    # Already has semantic dimension, filter out empty voxels
    fov_voxels = fov_voxels[fov_voxels[..., 3] > 0]
    print(f"Using existing semantic data. Shape: {fov_voxels.shape}")
else:
    raise ValueError(f"Unexpected data shape: {fov_voxels.shape}. Expected (n,3) or (n,4)")

fov_voxels[:, :3] = (fov_voxels[:, :3] + 0.5) * voxel_size
fov_voxels[:, 0] += pc_range[0]
fov_voxels[:, 1] += pc_range[1]
fov_voxels[:, 2] += pc_range[2]


#figure = mlab.figure(size=(600, 600), bgcolor=(1, 1, 1))
figure = mlab.figure(size=(2560, 1440), bgcolor=(1, 1, 1))
# pdb.set_trace()
plt_plot_fov = mlab.points3d(
    fov_voxels[:, 0],
    fov_voxels[:, 1],
    fov_voxels[:, 2],
    fov_voxels[:, 3],
    colormap="viridis",
    scale_factor=voxel_size - 0.05*voxel_size,
    mode="cube",
    opacity=1.0,
    vmin=0,
    vmax=19,
)


plt_plot_fov.glyph.scale_mode = "scale_by_vector"
plt_plot_fov.module_manager.scalar_lut_manager.lut.table = colors


#mlab.savefig('temp/mayavi.png')
mlab.show()
