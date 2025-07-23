# AirSim数据集转SurroundOcc格式说明

本文档说明如何将AirSim多相机无人机数据集转换为SurroundOcc项目所需的occupancy ground truth格式。

## 数据集要求

### 输入数据结构
你的AirSim数据集应该遵循以下结构：
```
airsim_data_sample/
├── map_cloud_resolution1.npy      # 世界坐标系下的点云文件
├── Drone1/
│   ├── 1700000000/                # 轨迹文件夹（时间戳命名）
│   │   ├── CAM_FRONT/             # 前视相机图像
│   │   ├── CAM_BACK/              # 后视相机图像
│   │   ├── CAM_LEFT/              # 左视相机图像
│   │   ├── CAM_RIGHT/             # 右视相机图像
│   │   ├── CAM_FRONT_LEFT/        # 前左相机图像
│   │   ├── CAM_FRONT_RIGHT/       # 前右相机图像
│   │   ├── data.csv               # 飞行状态数据
│   │   └── mission_info.json      # 任务信息
│   └── ...
└── Drone2/
    └── ...
```

### 必需文件

1. **map_cloud_resolution1.npy**: 
   - 世界坐标系下的点云真值
   - 格式：(N, 3) 或 (N, 4) numpy数组
   - (N, 3): [x, y, z] - 无语义标签
   - (N, 4): [x, y, z, semantic_label] - 有语义标签

2. **data.csv**: 每个轨迹必须包含以下列
   - `timestamp`: 时间戳
   - `pos_x`, `pos_y`, `pos_z`: 无人机位置
   - `quat_1`, `quat_2`, `quat_3`, `quat_4`: 无人机姿态四元数 (x,y,z,w)

## 使用方法

### 基本用法
```bash
# 进入项目根目录
cd /path/to/SurroundOcc

# 运行转换脚本
python tools/create_airsim_occupancy_gt.py --airsim-data-root /path/to/airsim_data_sample
```

### 高级用法
```bash
# 指定自定义的map cloud文件路径
python tools/create_airsim_occupancy_gt.py \
    --airsim-data-root /path/to/airsim_data_sample \
    --map-cloud-path /path/to/custom_map_cloud.npy

# 自定义点云范围和语义标签
python tools/create_airsim_occupancy_gt.py \
    --airsim-data-root /path/to/airsim_data_sample \
    --point-cloud-range -100 -100 -10 100 100 10 \
    --default-semantic-label 0

# 查看完整参数说明
python tools/create_airsim_occupancy_gt.py --help
```

### 参数说明

- `--airsim-data-root`: AirSim数据集根目录路径
- `--map-cloud-path`: map_cloud_resolution1.npy文件路径（可选）
- `--point-cloud-range`: 点云过滤范围 [x_min, y_min, z_min, x_max, y_max, z_max]
  - 默认：[-50, -50, -5.0, 50, 50, 3.0]（SurroundOcc默认范围）
- `--default-semantic-label`: 无语义标签时的默认标签值
  - 默认：29（nuScenes中的static.other类别）

## 输出结果

转换完成后，每个轨迹文件夹中会新增`OCCUPANCY_GT`目录：

```
airsim_data_sample/
└── Drone1/
    └── 1700000000/
        ├── CAM_FRONT/
        ├── CAM_BACK/
        ├── ... (其他相机文件夹)
        ├── OCCUPANCY_GT/              # 新生成的占用网格真值
        │   ├── 123.456.npy            # 按时间戳命名的.npy文件
        │   ├── 123.789.npy
        │   └── ...
        ├── data.csv
        └── mission_info.json
```

每个`.npy`文件包含该时刻在vehicle坐标系下的占用网格点云：
- 格式：(M, 4) numpy数组 
- 维度：[x, y, z, semantic_label]
- 坐标系：以vehicle为中心的坐标系
- 范围：由`--point-cloud-range`参数限定

## 坐标系说明

### 坐标变换流程
1. **世界坐标 → Vehicle坐标**：
   - 平移：点云位置 -= vehicle位置
   - 旋转：用vehicle姿态四元数的逆旋转点云
   
2. **点云过滤**：
   - 保留在`point_cloud_range`范围内的点云
   - 过滤掉vehicle周围指定范围外的点

### 坐标系对齐
- AirSim通常使用NED (North-East-Down) 或 FLU (Forward-Left-Up) 坐标系
- SurroundOcc期望vehicle坐标系（通常为Forward-Left-Up）
- 如果坐标系不匹配，可在`transform_points_to_vehicle_frame`函数中添加坐标轴转换

## 注意事项

1. **内存使用**：大型点云文件会占用较多内存，建议在有足够RAM的机器上运行

2. **处理时间**：转换时间取决于点云大小和帧数，建议先用小数据集测试

3. **坐标系验证**：建议用少量数据验证坐标变换的正确性

4. **语义标签**：
   - 如果原始点云没有语义标签，会自动添加默认标签值29
   - 可根据需要修改`--default-semantic-label`参数

## 故障排除

### 常见错误

1. **FileNotFoundError: Map cloud file not found**
   - 确保`map_cloud_resolution1.npy`文件存在
   - 或使用`--map-cloud-path`指定正确路径

2. **Missing columns in data.csv**
   - 确保data.csv包含所有必需列：timestamp, pos_x, pos_y, pos_z, quat_1~quat_4

3. **No drone directories found**
   - 确保数据集根目录包含`Drone1/`, `Drone2/`等子目录

### 验证输出

```python
import numpy as np

# 加载并检查生成的占用网格文件
occ_gt = np.load('path/to/OCCUPANCY_GT/123.456.npy')
print(f"Shape: {occ_gt.shape}")  # 应该是 (N, 4)
print(f"X range: [{occ_gt[:, 0].min():.2f}, {occ_gt[:, 0].max():.2f}]")
print(f"Y range: [{occ_gt[:, 1].min():.2f}, {occ_gt[:, 1].max():.2f}]")
print(f"Z range: [{occ_gt[:, 2].min():.2f}, {occ_gt[:, 2].max():.2f}]")
print(f"Semantic labels: {np.unique(occ_gt[:, 3])}")
```

## 下一步

转换完成后，你可以：

1. 创建自定义数据集配置文件
2. 修改相机内外参数配置
3. 运行SurroundOcc模型进行zero-shot推理

详细步骤请参考SurroundOcc项目的使用文档。 