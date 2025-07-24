# AirSim 多传感器数据集结构说明

本数据集用于多无人机、多传感器仿真采集，支持多种传感器类型（如RGB相机、深度相机、IMU、GPS、LiDAR等），并支持多任务轨迹采集。2024年7月起，数据集新增对全局交通（traffic）状态的存储，详见下文。

## 目录结构

```
/dataset_root/
├── Drone1/
│   ├── 1700000000/                # 每个任务/轨迹一个子文件夹，文件夹名为任务起始时间戳
│   │   ├── CAM_FRONT/             # 每个需要保存的传感器一个子文件夹，名称与配置一致
│   │   ├── CAM_FRONT_DEPTH/
│   │   ├── ...                    # 其他传感器
│   │   ├── data.csv               # 该任务ego无人机的状态数据（见下文）
│   │   ├── mission_info.json      # 任务信息
│   │   └── traffic/               # 交通状态数据（全局所有飞机）
│   │       ├── traffic_summary.json   # 交通概览与飞机静态信息
│   │       ├── UAV_001.csv            # UAV_001的完整轨迹
│   │       ├── eVTOL_002.csv          # eVTOL_002的完整轨迹
│   │       ├── ...                    # 其他飞机
│   │       └── collision_events.json  # 碰撞事件记录（可选）
│   └── ...                        # 其他任务
├── Drone2/
│   └── ...
└── ...                            # 其他无人机
```

- `traffic/` 目录下存储了该任务期间所有出现过的飞机的轨迹数据（每个飞机一个csv），以及全局交通概览和碰撞事件。

## data.csv 字段说明（ego无人机）

| 字段名         | 含义                         |
| -------------- | ---------------------------- |
| timestamp      | 时间戳（秒，浮点数，保留3位）|
| desired_vel    | 期望速度（任务参数）         |
| quat_1~quat_4  | 四元数姿态（x, y, z, w）     |
| pos_x~pos_z    | 位置（x, y, z，单位：米）    |
| vel_x~vel_z    | 速度（body系，单位：米/秒）  |
| velcmd_x~velcmd_z | 期望速度（body系，单位：米/秒）|
| is_collide     | 是否碰撞（True/False）       |

## traffic/ 目录结构与说明

### 1. traffic_summary.json
记录本次任务期间所有出现过的飞机的静态信息、数据文件索引、数量统计等。

```json
{
  "mission_info": {
    "mission_id": 12345,
    "ego_vehicle": "Drone1",
    "total_aircraft_count": 4,
    "uav_count": 2,
    "evtol_count": 2,
    "collision_events_count": 1
  },
  "aircraft_registry": {
    "UAV_001": {
      "aircraft_type": "uav",
      "radius": 1.5,
      "bbox_width": 2.0,
      "bbox_length": 2.0,
      "bbox_height": 1.0,
      "first_seen_timestamp": 1700000000.123,
      "last_seen_timestamp": 1700000300.456,
      "data_file": "UAV_001.csv",
      "total_data_points": 3000
    },
    "eVTOL_002": {
      "aircraft_type": "evtol",
      "radius": 3.0,
      "bbox_width": 4.0,
      "bbox_length": 4.0,
      "bbox_height": 2.0,
      "first_seen_timestamp": 1700000050.789,
      "last_seen_timestamp": 1700000250.123,
      "data_file": "eVTOL_002.csv",
      "total_data_points": 2000
    }
  },
  "data_format_version": "1.0"
}
```

### 2. 单个飞机轨迹csv（如 UAV_001.csv）
每个飞机一个csv文件，记录其全时序动态状态。

| timestamp | pos_x | pos_y | pos_z | quat_x | quat_y | quat_z | quat_w | vel_x | vel_y | vel_z | ang_vel_x | ang_vel_y | ang_vel_z | lin_acc_x | lin_acc_y | lin_acc_z | ang_acc_x | ang_acc_y | ang_acc_z | flight_state | has_target | target_x | target_y | target_z | has_collided | collision_object | speed | heading | airsim_timestamp |
|-----------|-------|-------|-------|--------|--------|--------|--------|-------|-------|-------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|--------------|------------|----------|----------|----------|--------------|------------------|-------|---------|------------------|
| 1700000000.123 | 10.5 | 20.3 | -15.0 | 0.0 | 0.0 | 0.0 | 1.0 | 5.0 | 0.0 | 0.0 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2 | true | 50.0 | 60.0 | -15.0 | false | "" | 5.0 | 0.0 | 1700000000.123 |

- 字段含义与AircraftState.msg一致，详见msg定义。
- timestamp为采集时刻（秒，保留3位小数），airsim_timestamp为仿真内部时钟。

### 3. collision_events.json（可选）
记录本任务期间所有检测到的碰撞事件。

```json
{
  "collision_events": [
    {
      "timestamp": 1700000150.456,
      "aircraft_name": "UAV_001",
      "collision_object": "eVTOL_002",
      "collision_position": {"x": 25.0, "y": 30.0, "z": -17.0},
      "aircraft_velocity": {"x": -3.0, "y": 2.0, "z": 0.0},
      "aircraft_type": "uav"
    }
  ],
  "total_events": 1,
  "mission_id": 12345
}
```

## 其他说明

- traffic/目录下的所有csv和json文件均以任务为单位独立存储，便于后续分析和批量处理。
- 新飞机出现时会自动创建新的csv文件，消失后数据依然保留。
- traffic_summary.json中的first_seen_timestamp/last_seen_timestamp便于统计飞机活跃区间。
- 碰撞事件仅在检测到时记录，避免重复。
- 该结构兼容原有数据集设计，不影响ego无人机和传感器数据的采集与存储。

---
如需扩展其他传感器或自定义数据结构，请参考`data_collector_node.py`和配置文件进行修改。

如需进一步补充或有特殊格式需求，请告知！