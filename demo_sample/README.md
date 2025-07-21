# nuScenes 真实样本演示

## 样本信息
- Token: fd8420396768425eabec9bdddf7e64b6
- Scene: e7ef871f77f44331aefdebc24ec034b7
- Frame: 0
- Timestamp: 1533201470448696

## 数据文件
- LiDAR: ./data/nuscenes/samples/LIDAR_TOP/n015-2018-08-02-17-16-37+0800__LIDAR_TOP__1533201470448696.pcd.bin
- Occupancy: ./data/nuscenes_occ/samples/n015-2018-08-02-17-16-37+0800__LIDAR_TOP__1533201470448696.pcd.bin.npy
- Cameras: 6 个相机

## 相机配置

### CAM_FRONT
- 图像: ./data/nuscenes/samples/CAM_FRONT/n015-2018-08-02-17-16-37+0800__CAM_FRONT__1533201470412460.jpg
- 内参矩阵: (3, 3)
- 传感器到LiDAR平移: [-0.01271581  0.76880558 -0.31059456]

### CAM_FRONT_RIGHT
- 图像: ./data/nuscenes/samples/CAM_FRONT_RIGHT/n015-2018-08-02-17-16-37+0800__CAM_FRONT_RIGHT__1533201470420339.jpg
- 内参矩阵: (3, 3)
- 传感器到LiDAR平移: [ 0.49650027  0.61746215 -0.32655959]

### CAM_FRONT_LEFT
- 图像: ./data/nuscenes/samples/CAM_FRONT_LEFT/n015-2018-08-02-17-16-37+0800__CAM_FRONT_LEFT__1533201470404874.jpg
- 内参矩阵: (3, 3)
- 传感器到LiDAR平移: [-0.4917212   0.59365311 -0.31925387]

### CAM_BACK
- 图像: ./data/nuscenes/samples/CAM_BACK/n015-2018-08-02-17-16-37+0800__CAM_BACK__1533201470437525.jpg
- 内参矩阵: (3, 3)
- 传感器到LiDAR平移: [-0.00369546 -0.90757475 -0.28322187]

### CAM_BACK_LEFT
- 图像: ./data/nuscenes/samples/CAM_BACK_LEFT/n015-2018-08-02-17-16-37+0800__CAM_BACK_LEFT__1533201470447423.jpg
- 内参矩阵: (3, 3)
- 传感器到LiDAR平移: [-0.48313021  0.09925075 -0.24976868]

### CAM_BACK_RIGHT
- 图像: ./data/nuscenes/samples/CAM_BACK_RIGHT/n015-2018-08-02-17-16-37+0800__CAM_BACK_RIGHT__1533201470427893.jpg
- 内参矩阵: (3, 3)
- 传感器到LiDAR平移: [ 0.48231268  0.07918378 -0.2730718 ]

## 标注信息
- 目标数量: 37
- 类别: ['car', 'car', 'car', 'car', 'pedestrian', 'car', 'pedestrian', 'car', 'pedestrian', 'pedestrian', 'traffic_cone', 'traffic_cone', 'car', 'car', 'car', 'car', 'car', 'car', 'car', 'pedestrian', 'car', 'car', 'car', 'car', 'car', 'car', 'pedestrian', 'car', 'car', 'car', 'traffic_cone', 'car', 'pedestrian', 'pedestrian', 'car', 'pedestrian', 'car']
- 有效目标: 37/37

## 坐标变换
- LiDAR到车体平移: [0.943713, 0.0, 1.84023]
- 车体到全局平移: [249.89610931430778, 917.5522573162784, 0.0]
