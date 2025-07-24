#!/usr/bin/env python3
import os
import json
import pickle
import uuid
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from typing import Dict, List, Optional, Tuple
import argparse
from pathlib import Path

def generate_uuid_token():
    """生成UUID token"""
    return str(uuid.uuid4()).replace('-', '')

def quaternion_to_matrix(quat):
    """将四元数转换为旋转矩阵
    Args:
        quat: [x, y, z, w] 格式的四元数
    Returns:
        3x3 旋转矩阵
    """
    return R.from_quat(quat).as_matrix()

def load_airsim_camera_config():
    """AirSim默认相机配置
    这里提供了AirSim的默认6相机配置，用户可以根据实际情况修改
    """
    # AirSim默认相机内参 (可以根据实际相机配置修改)
    default_intrinsic = [
        [1266.417203046554, 0.0, 640.0],  # fx, 0, cx
        [0.0, 1266.417203046554, 360.0],  # 0, fy, cy  
        [0.0, 0.0, 1.0]
    ]
    
    # AirSim 6相机配置 (相对于vehicle的位置和姿态)
    # 这里使用类似nuScenes的布局，用户需要根据实际AirSim配置修改
    camera_configs = {
        'CAM_FRONT': {
            'sensor2ego_translation': [0.7, 0.0, 0.0],  # 前向，车体坐标系
            'sensor2ego_rotation': [0.5, -0.5, 0.5, -0.5],  # [x,y,z,w] 四元数
            'cam_intrinsic': np.array([[1142.5184, 0.0,  800.0], 
                              [0.0, 1142.5184, 450.0], 
                              [0.0, 0.0, 1.0]])
        },
        'CAM_FRONT_LEFT': {
            'sensor2ego_translation': [0.5, 0.5, 0.0],
            'sensor2ego_rotation': [0.6743797, -0.6743797, 0.2126311, -0.2126311],  
            'cam_intrinsic': np.array([[1142.5184, 0.0,  800.0], 
                              [0.0, 1142.5184, 450.0], 
                              [0.0, 0.0, 1.0]])
        },
        'CAM_FRONT_RIGHT': {
            'sensor2ego_translation': [0.5, -0.5, 0.0],
            'sensor2ego_rotation': [0.2126311, -0.2126311, 0.6743797, -0.6743797],  
            'cam_intrinsic': np.array([[1142.5184, 0.0,  800.0], 
                              [0.0, 1142.5184, 450.0], 
                              [0.0, 0.0, 1.0]])
        },
        'CAM_BACK': {
            'sensor2ego_translation': [-0.4, 0.0, 0.0],
            'sensor2ego_rotation': [0.5, -0.5, -0.5, 0.5],  # 向后
            'cam_intrinsic': np.array([[560.166029, 0.0,  800.0], 
                              [0.0, 560.166029, 450.0], 
                              [0.0, 0.0, 1.0]])
        },
        'CAM_BACK_LEFT': {
            'sensor2ego_translation': [0.0, 0.5, 0.0],
            'sensor2ego_rotation': [0.6963642, -0.6963642, -0.1227878, 0.1227878],  
            'cam_intrinsic': np.array([[1142.5184, 0.0,  800.0], 
                              [0.0, 1142.5184, 450.0], 
                              [0.0, 0.0, 1.0]])
        },
        'CAM_BACK_RIGHT': {
            'sensor2ego_translation': [0.0, -0.5, 0.0],
            'sensor2ego_rotation': [-0.1227878, 0.1227878, 0.6963642, -0.6963642],  
            'cam_intrinsic': np.array([[1142.5184, 0.0,  800.0], 
                              [0.0, 1142.5184, 450.0], 
                              [0.0, 0.0, 1.0]])
        }
    }
    
    return camera_configs

def compute_sensor2lidar_transform(sensor2ego_translation, sensor2ego_rotation, 
                                 lidar2ego_translation, lidar2ego_rotation):
    """计算sensor到lidar的变换矩阵"""
    # 假设lidar和ego重合或者有已知变换
    # 这里我们假设lidar就是ego坐标系的原点
    # 所以 sensor2lidar = sensor2ego
    
    # 创建4x4变换矩阵
    sensor2ego_matrix = np.eye(4)
    sensor2ego_matrix[:3, :3] = quaternion_to_matrix(sensor2ego_rotation)
    sensor2ego_matrix[:3, 3] = sensor2ego_translation
    
    # 如果lidar和ego不重合，需要计算相对变换
    # 这里简化处理，假设lidar就在ego坐标系原点
    lidar2ego_matrix = np.eye(4)
    if lidar2ego_translation is not None and lidar2ego_rotation is not None:
        lidar2ego_matrix[:3, :3] = quaternion_to_matrix(lidar2ego_rotation)
        lidar2ego_matrix[:3, 3] = lidar2ego_translation
    
    # sensor2lidar = inv(lidar2ego) @ sensor2ego
    ego2lidar_matrix = np.linalg.inv(lidar2ego_matrix)
    sensor2lidar_matrix = ego2lidar_matrix @ sensor2ego_matrix
    
    return sensor2lidar_matrix[:3, :3], sensor2lidar_matrix[:3, 3]

def check_data_completeness(trajectory_dir: str, timestamp: str) -> bool:
    """检查指定时间戳下的数据完整性"""
    trajectory_path = Path(trajectory_dir)
    
    # 检查6个相机图像
    camera_names = ['CAM_FRONT', 'CAM_FRONT_LEFT', 'CAM_FRONT_RIGHT', 
                   'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT']
    
    for cam_name in camera_names:
        cam_dir = trajectory_path / cam_name
        img_file = cam_dir / f"{timestamp}.png"
        if not img_file.exists():
            print(f"Missing camera image: {img_file}")
            return False
    
    # 检查occupancy ground truth
    occ_dir = trajectory_path / "OCCUPANCY_GT"
    occ_file = occ_dir / f"{timestamp}.npy"
    if not occ_file.exists():
        print(f"Missing occupancy file: {occ_file}")
        return False
    
    return True

def create_sample_info(trajectory_dir: str, row: pd.Series, camera_configs: Dict, 
                      dataset_root: str, frame_idx: int, prev_token: str = "", 
                      next_token: str = "") -> Dict:
    """为单个样本创建info字典"""
    
    # 时间戳处理：保留小数点后三位，文件名和索引统一
    timestamp = f"{row['timestamp']:.3f}"
    token = generate_uuid_token()
    scene_token = Path(trajectory_dir).name  # 使用trajectory名称作为scene_token
    
    # 基础信息
    sample_info = {
        'token': token,
        'scene_token': scene_token,
        'timestamp': row['timestamp'],  # 保留原始浮点型
        'frame_idx': frame_idx,
        'prev': prev_token,
        'next': next_token,
    }
    
    # LiDAR信息 (AirSim中我们没有真实LiDAR，用占位符)
    sample_info.update({
        'lidar_path': "",  # 空路径
        'lidar_token': generate_uuid_token(),
        'lidarseg': "",
        'sweeps': [],
    })
    
    # Occupancy路径
    # occ_path = os.path.join(dataset_root, os.path.relpath(
    #     os.path.join(trajectory_dir, "OCCUPANCY_GT", f"{timestamp}.npy"),
    #     dataset_root
    # ))
    occ_path = os.path.join(trajectory_dir, "OCCUPANCY_GT", f"{timestamp}.npy")
    sample_info['occ_path'] = occ_path
    
    # 车辆状态信息
    position = [row['pos_x'], row['pos_y'], row['pos_z']]
    orientation = [row['quat_4'], row['quat_1'], row['quat_2'], row['quat_3']]  # [w,x,y,z]
    
    # LiDAR到ego的变换 (这里假设LiDAR和ego重合)
    # 目前确实是重合的
    sample_info.update({
        'lidar2ego_translation': [0.0, 0.0, 0.0],
        'lidar2ego_rotation': [0.0, 0.0, 0.0, 1.0],  # 单位四元数
        'ego2global_translation': position,
        'ego2global_rotation': orientation,
    })
    
    # CAN总线数据 (模拟nuScenes格式)
    can_bus = [0.0] * 18
    can_bus[:3] = position  # 位置
    can_bus[3:7] = orientation  # 四元数
    sample_info['can_bus'] = can_bus
    
    # 相机信息
    cams = {}
    for cam_name in camera_configs.keys():
        cam_config = camera_configs[cam_name]
        
        # 图像路径
        # img_path = os.path.join(dataset_root, os.path.relpath(
        #     os.path.join(trajectory_dir, cam_name, f"{timestamp}.png"),
        #     dataset_root
        # ))
        img_path = os.path.join(trajectory_dir, cam_name, f"{timestamp}.png")
        # 计算sensor2lidar变换
        sensor2lidar_rotation, sensor2lidar_translation = compute_sensor2lidar_transform(
            cam_config['sensor2ego_translation'],
            cam_config['sensor2ego_rotation'],
            sample_info['lidar2ego_translation'],
            sample_info['lidar2ego_rotation']
        )
        # sensor2lidar_rotation, sensor2lidar_translation,cam_intrinsic are numpy array
        cam_info = {
            'data_path': img_path,
            'type': cam_name,
            'sample_data_token': generate_uuid_token(),
            'sensor2ego_translation': cam_config['sensor2ego_translation'],
            'sensor2ego_rotation': cam_config['sensor2ego_rotation'],
            'ego2global_translation': position,
            'ego2global_rotation': orientation,
            'timestamp': row['timestamp'],
            'sensor2lidar_rotation': sensor2lidar_rotation,
            'sensor2lidar_translation': sensor2lidar_translation,
            'cam_intrinsic': cam_config['cam_intrinsic']
        }
        
        cams[cam_name] = cam_info
    
    sample_info['cams'] = cams
    
    # 标注信息 (AirSim中我们没有3D检测标注，用空列表)
    sample_info.update({
        'gt_boxes': [],
        'gt_names': [],
        'gt_velocity': [],
        'num_lidar_pts': [],
        'num_radar_pts': [],
        'valid_flag': [],
    })
    
    return sample_info

def process_trajectory(trajectory_dir: str, camera_configs: Dict, dataset_root: str) -> List[Dict]:
    """处理单个trajectory的所有数据"""
    print(f"Processing trajectory: {trajectory_dir}")
    
    # 读取data.csv
    data_csv = os.path.join(trajectory_dir, "data.csv")
    if not os.path.exists(data_csv):
        print(f"data.csv not found in {trajectory_dir}")
        return []
    
    df = pd.read_csv(data_csv)
    print(f"Found {len(df)} samples in data.csv")
    
    # 检查数据完整性并创建样本信息
    valid_samples = []
    sample_infos = []
    
    for idx, row in df.iterrows():
        # 时间戳处理：保留小数点后三位
        timestamp = f"{row['timestamp']:.3f}"
        
        if check_data_completeness(trajectory_dir, timestamp):
            valid_samples.append((idx, row))
        else:
            print(f"Skipping incomplete sample at timestamp {timestamp}")
    
    print(f"Found {len(valid_samples)} complete samples")
    
    # 创建样本信息
    for i, (idx, row) in enumerate(valid_samples):
        prev_token = sample_infos[i-1]['token'] if i > 0 else ""
        next_token = ""  # 会在后面填充
        
        sample_info = create_sample_info(
            trajectory_dir, row, camera_configs, dataset_root, 
            frame_idx=i, prev_token=prev_token, next_token=next_token
        )
        sample_infos.append(sample_info)
        
        # 填充前一个样本的next_token
        if i > 0:
            sample_infos[i-1]['next'] = sample_info['token']
    
    return sample_infos

def create_airsim_infos_pkl(dataset_root: str, output_pkl: str, camera_config_file: str = None):
    """创建AirSim数据集的pkl文件"""
    
    print(f"Creating pkl file for dataset: {dataset_root}")
    
    # 加载相机配置
    if camera_config_file and os.path.exists(camera_config_file):
        with open(camera_config_file, 'r') as f:
            camera_configs = json.load(f)
        print(f"Loaded camera config from: {camera_config_file}")
    else:
        camera_configs = load_airsim_camera_config()
        print("Using default camera configuration")
    
    # 查找所有trajectory目录
    dataset_path = Path(dataset_root)
    all_infos = []
    
    # 假设结构是 airsim_data_sample/Drone1/1700000000/
    for drone_dir in dataset_path.glob("Drone*"):
        if not drone_dir.is_dir():
            continue
            
        print(f"Processing drone: {drone_dir.name}")
        
        for trajectory_dir in drone_dir.iterdir():
            if not trajectory_dir.is_dir():
                continue
            # 只处理包含data.csv的子文件夹
            if not (trajectory_dir / "data.csv").exists():
                continue
            trajectory_infos = process_trajectory(
                str(trajectory_dir), camera_configs, dataset_root
            )
            all_infos.extend(trajectory_infos)
    
    # 创建最终的数据结构
    data_infos = {
        'infos': all_infos,
        'metadata': {
            'version': 'airsim_v1.0',
            'dataset_root': dataset_root,
            'total_samples': len(all_infos),
            'camera_configs': camera_configs
        }
    }
    
    # 保存pkl文件
    print(f"Saving {len(all_infos)} samples to {output_pkl}")
    with open(output_pkl, 'wb') as f:
        pickle.dump(data_infos, f)
    
    print(f"Successfully created pkl file: {output_pkl}")
    
    # 打印一些统计信息
    print("\n=== Dataset Statistics ===")
    print(f"Total samples: {len(all_infos)}")
    if all_infos:
        print(f"Sample trajectory distribution:")
        trajectory_counts = {}
        for info in all_infos:
            scene = info['scene_token']
            trajectory_counts[scene] = trajectory_counts.get(scene, 0) + 1
        
        for traj, count in trajectory_counts.items():
            print(f"  {traj}: {count} samples")

def save_camera_config_template(output_file: str):
    """保存相机配置模板文件"""
    configs = load_airsim_camera_config()
    with open(output_file, 'w') as f:
        json.dump(configs, f, indent=2)
    print(f"Camera configuration template saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Create AirSim dataset pkl file for SurroundOcc')
    parser.add_argument('--dataset_root', type=str, required=True,
                       help='Root directory of AirSim dataset (e.g., airsim_data_sample)')
    parser.add_argument('--output_pkl', type=str, required=True,
                       help='Output pkl file path (e.g., airsim_infos_val.pkl)')
    parser.add_argument('--camera_config', type=str, default=None,
                       help='Camera configuration JSON file (optional)')
    parser.add_argument('--save_config_template', type=str, default=None,
                       help='Save camera configuration template to specified file')
    
    args = parser.parse_args()
    
    # 如果用户想要保存配置模板
    if args.save_config_template:
        save_camera_config_template(args.save_config_template)
        return
    
    # 创建pkl文件
    create_airsim_infos_pkl(args.dataset_root, args.output_pkl, args.camera_config)

if __name__ == "__main__":
    main() 