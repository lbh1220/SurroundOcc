# AirSim数据集转SurroundOcc格式工具

这个工具用于将你的AirSim数据集转换为SurroundOcc项目所需的pkl格式。

## 主要功能

1. **数据完整性检查**：自动检查每个时间戳下的6个相机图像和occupancy ground truth文件是否存在
2. **格式转换**：将AirSim数据结构转换为与nuScenes兼容的格式
3. **相机配置管理**：支持自定义相机内外参配置
4. **Token生成**：自动生成所需的UUID token用于样本索引

## 使用方法

### 1. 生成相机配置模板

首先生成一个相机配置模板文件，方便你根据实际的AirSim配置进行修改：

```bash
cd ~/Projects/SurroundOcc

# 激活conda环境
conda activate surroundocc

# 生成相机配置模板
python tools/create_airsim_infos_pkl.py --save_config_template tools/airsim_camera_config.json
```

### 2. 修改相机配置（重要）

打开生成的 `tools/airsim_camera_config.json` 文件，根据你的实际AirSim相机配置进行修改：

```json
{
  "CAM_FRONT": {
    "sensor2ego_translation": [1.7, 0.0, 1.5],
    "sensor2ego_rotation": [0.5, -0.5, 0.5, -0.5],
    "cam_intrinsic": [
      [1266.417203046554, 0.0, 640.0],
      [0.0, 1266.417203046554, 360.0],
      [0.0, 0.0, 1.0]
    ]
  },
  // ... 其他5个相机的配置
}
```

**配置说明：**
- `sensor2ego_translation`: 相机相对于车体中心的位置 [x, y, z]（米）
- `sensor2ego_rotation`: 相机相对于车体的旋转四元数 [x, y, z, w]
- `cam_intrinsic`: 相机内参矩阵 3x3，格式为 [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]

### 3. 生成pkl文件

```bash
# 为你的数据集生成pkl文件
python tools/create_airsim_infos_pkl.py \
    --dataset_root airsim_data_sample \
    --output_pkl data/airsim_infos_val.pkl \
    --camera_config tools/airsim_camera_config.json
```

**参数说明：**
- `--dataset_root`: AirSim数据集根目录
- `--output_pkl`: 输出的pkl文件路径
- `--camera_config`: 相机配置文件路径（可选，不指定则使用默认配置）

## 数据要求

### 数据集结构
```
airsim_data_sample/
├── Drone1/
│   ├── trajectory_0001/
│   │   ├── data.csv                 # 车辆状态数据
│   │   ├── CAM_FRONT/
│   │   │   ├── 1000000.png
│   │   │   ├── 1000001.png
│   │   │   └── ...
│   │   ├── CAM_FRONT_LEFT/
│   │   ├── CAM_FRONT_RIGHT/
│   │   ├── CAM_BACK/
│   │   ├── CAM_BACK_LEFT/
│   │   ├── CAM_BACK_RIGHT/
│   │   └── OCCUPANCY_GT/
│   │       ├── 1000000.npy
│   │       ├── 1000001.npy
│   │       └── ...
│   └── trajectory_0002/
│       └── ...
└── Drone2/
    └── ...
```

### data.csv格式要求
CSV文件必须包含以下列：
- `timestamp`: 时间戳（整数）
- `x`, `y`, `z`: 车辆位置（世界坐标系）
- `qx`, `qy`, `qz`, `qw`: 车辆姿态四元数

### 数据完整性要求
对于每个时间戳，必须同时存在：
1. 6个相机的图像文件：`{timestamp}.png`
2. 对应的occupancy ground truth文件：`{timestamp}.npy`

脚本会自动跳过不完整的样本。

## 输出格式

生成的pkl文件包含以下结构：

```python
{
    'infos': [
        {
            'token': 'unique_uuid',
            'scene_token': 'trajectory_name',
            'timestamp': 1000000,
            'frame_idx': 0,
            'prev': 'previous_sample_token',
            'next': 'next_sample_token',
            'occ_path': 'relative/path/to/occupancy.npy',
            'cams': {
                'CAM_FRONT': {
                    'data_path': 'relative/path/to/image.png',
                    'cam_intrinsic': [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
                    'sensor2ego_translation': [x, y, z],
                    'sensor2ego_rotation': [x, y, z, w],
                    'sensor2lidar_rotation': [[...], [...], [...]],
                    'sensor2lidar_translation': [x, y, z],
                    # ... 其他字段
                },
                # ... 其他5个相机
            },
            'ego2global_translation': [x, y, z],
            'ego2global_rotation': [x, y, z, w],
            # ... 其他兼容性字段
        },
        # ... 更多样本
    ],
    'metadata': {
        'version': 'airsim_v1.0',
        'dataset_root': 'airsim_data_sample',
        'total_samples': 100,
        'camera_configs': { ... }
    }
}
```

## 关键点说明

### 1. Token的作用
- **sample token**: 每个样本的唯一标识符
- **scene token**: 同一trajectory内样本共享相同的scene token
- **prev/next token**: 用于链接时序上相邻的样本

### 2. 坐标系转换
- **AirSim世界坐标** → **vehicle坐标系**：通过data.csv中的位置和姿态
- **相机坐标系** → **vehicle坐标系**：通过相机配置的外参
- **LiDAR坐标系**：假设与vehicle坐标系重合（可在脚本中修改）

### 3. 兼容性处理
- 生成的pkl文件完全兼容SurroundOcc的数据格式
- 为不需要的字段（如gt_boxes等）填充空值
- 保持与nuScenes数据集相同的字段结构

## 使用示例

完整的使用流程：

```bash
# 1. 激活环境
conda activate surroundocc

# 2. 生成相机配置模板
python tools/create_airsim_infos_pkl.py --save_config_template tools/airsim_camera_config.json

# 3. 编辑相机配置文件（根据你的实际AirSim设置）
# 使用文本编辑器修改 tools/airsim_camera_config.json

# 4. 生成pkl文件
python tools/create_airsim_infos_pkl.py \
    --dataset_root airsim_data_sample \
    --output_pkl data/airsim_infos_val.pkl \
    --camera_config tools/airsim_camera_config.json

# 5. 验证生成的pkl文件
python tools/analyze_pickle_structure.py data/airsim_infos_val.pkl

# 6. 提取一个样本查看
python tools/save_sample_to_json.py data/airsim_infos_val.pkl airsim_sample_0.json 0
```

## 故障排除

### 常见问题

1. **缺少依赖包**：
   ```bash
   conda install pandas scipy
   ```

2. **数据不完整**：
   检查控制台输出，脚本会显示缺失的文件

3. **相机配置错误**：
   确认相机内外参与你的AirSim设置匹配

4. **路径问题**：
   确保数据集结构与要求的格式一致

### 调试技巧

1. **检查数据完整性**：
   ```bash
   # 查看有多少样本被跳过
   python tools/create_airsim_infos_pkl.py ... | grep "Skipping"
   ```

2. **验证生成结果**：
   ```bash
   # 分析pkl文件结构
   python tools/analyze_pickle_structure.py data/airsim_infos_val.pkl
   ```

3. **查看样本数据**：
   ```bash
   # 提取第一个样本到JSON文件
   python tools/save_sample_to_json.py data/airsim_infos_val.pkl sample_0.json 0
   ```

生成pkl文件后，你就可以将其用于SurroundOcc的测试了！ 