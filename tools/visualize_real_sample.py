#!/usr/bin/env python3
"""
Visualize a real sample from nuScenes dataset pickle file
"""

import pickle
import json
import numpy as np
import os
from pprint import pprint

def visualize_real_sample(pickle_path, sample_index=0, output_json=None):
    """
    Extract and visualize a real sample from nuScenes pickle file
    
    Args:
        pickle_path: Path to pickle file
        sample_index: Index of sample to visualize
        output_json: Optional JSON file to save the sample
    """
    
    print(f"Loading pickle file: {pickle_path}")
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    if sample_index >= len(data['infos']):
        print(f"Error: Sample index {sample_index} out of range (max: {len(data['infos'])-1})")
        return
    
    # Extract the real sample
    sample = data['infos'][sample_index]
    
    print(f"\n{'='*60}")
    print(f"真实nuScenes样本可视化 (索引: {sample_index})")
    print(f"{'='*60}")
    
    # 1. 基本信息
    print("\n📋 基本信息:")
    print(f"  Token: {sample['token']}")
    print(f"  Scene Token: {sample['scene_token']}")
    print(f"  Frame Index: {sample['frame_idx']}")
    print(f"  Timestamp: {sample['timestamp']}")
    print(f"  Previous Frame: {sample['prev']}")
    print(f"  Next Frame: {sample['next']}")
    
    # 2. 数据文件路径
    print("\n📁 数据文件路径:")
    print(f"  LiDAR路径: {sample['lidar_path']}")
    print(f"  占用标签路径: {sample['occ_path']}")
    print(f"  LiDAR分割路径: {sample['lidarseg']}")
    
    # 3. 相机信息
    print(f"\n📷 相机信息 (共{len(sample['cams'])}个相机):")
    for cam_name, cam_info in sample['cams'].items():
        print(f"\n  {cam_name}:")
        print(f"    图像路径: {cam_info['data_path']}")
        print(f"    相机类型: {cam_info['type']}")
        print(f"    样本数据Token: {cam_info['sample_data_token']}")
        print(f"    时间戳: {cam_info['timestamp']}")
        
        # 坐标变换
        print(f"    传感器到车体平移: {cam_info['sensor2ego_translation']}")
        print(f"    传感器到车体旋转: {cam_info['sensor2ego_rotation']}")
        print(f"    车体到全局平移: {cam_info['ego2global_translation']}")
        print(f"    车体到全局旋转: {cam_info['ego2global_rotation']}")
        
        # 相机参数
        print(f"    传感器到LiDAR旋转矩阵形状: {cam_info['sensor2lidar_rotation'].shape}")
        print(f"    传感器到LiDAR平移: {cam_info['sensor2lidar_translation']}")
        print(f"    相机内参矩阵形状: {cam_info['cam_intrinsic'].shape}")
        print(f"    相机内参矩阵:")
        print(f"      {cam_info['cam_intrinsic']}")
    
    # 4. 坐标变换信息
    print(f"\n🔄 坐标变换信息:")
    print(f"  LiDAR到车体平移: {sample['lidar2ego_translation']}")
    print(f"  LiDAR到车体旋转: {sample['lidar2ego_rotation']}")
    print(f"  车体到全局平移: {sample['ego2global_translation']}")
    print(f"  车体到全局旋转: {sample['ego2global_rotation']}")
    
    # 5. 标注信息
    print(f"\n🏷️ 标注信息:")
    print(f"  GT边界框数量: {len(sample['gt_boxes'])}")
    print(f"  GT类别: {sample['gt_names']}")
    print(f"  GT速度数量: {len(sample['gt_velocity'])}")
    print(f"  LiDAR点数: {sample['num_lidar_pts']}")
    print(f"  雷达点数: {sample['num_radar_pts']}")
    print(f"  有效标志: {sample['valid_flag']}")
    
    # 6. 其他信息
    print(f"\n📊 其他信息:")
    print(f"  CAN总线数据: {sample['can_bus']}")
    print(f"  历史帧数量: {len(sample['sweeps'])}")
    print(f"  LiDAR Token: {sample['lidar_token']}")
    
    # 7. 数据结构统计
    print(f"\n📈 数据结构统计:")
    print(f"  样本总字段数: {len(sample)}")
    print(f"  相机数量: {len(sample['cams'])}")
    print(f"  标注目标数: {len(sample['gt_boxes'])}")
    
    # 8. 保存为JSON（如果指定）
    if output_json:
        # 转换numpy数组为列表以便JSON序列化
        sample_json = {}
        for key, value in sample.items():
            if isinstance(value, np.ndarray):
                sample_json[key] = value.tolist()
            elif isinstance(value, dict):
                sample_json[key] = {}
                for k, v in value.items():
                    if isinstance(v, np.ndarray):
                        sample_json[key][k] = v.tolist()
                    else:
                        sample_json[key][k] = v
            else:
                sample_json[key] = value
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(sample_json, f, indent=2, ensure_ascii=False)
        print(f"\n💾 样本已保存到: {output_json}")
    
    return sample

def create_sample_demo(sample, output_dir="demo_sample"):
    """
    Create a demo directory with sample information
    
    Args:
        sample: The sample dictionary
        output_dir: Output directory for demo files
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建README文件
    readme_content = f"""# nuScenes 真实样本演示

## 样本信息
- Token: {sample['token']}
- Scene: {sample['scene_token']}
- Frame: {sample['frame_idx']}
- Timestamp: {sample['timestamp']}

## 数据文件
- LiDAR: {sample['lidar_path']}
- Occupancy: {sample['occ_path']}
- Cameras: {len(sample['cams'])} 个相机

## 相机配置
"""
    
    for cam_name, cam_info in sample['cams'].items():
        readme_content += f"""
### {cam_name}
- 图像: {cam_info['data_path']}
- 内参矩阵: {cam_info['cam_intrinsic'].shape}
- 传感器到LiDAR平移: {cam_info['sensor2lidar_translation']}
"""
    
    readme_content += f"""
## 标注信息
- 目标数量: {len(sample['gt_boxes'])}
- 类别: {list(sample['gt_names'])}
- 有效目标: {sum(sample['valid_flag'])}/{len(sample['valid_flag'])}

## 坐标变换
- LiDAR到车体平移: {sample['lidar2ego_translation']}
- 车体到全局平移: {sample['ego2global_translation']}
"""
    
    with open(f"{output_dir}/README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 创建相机配置文件
    camera_config = {}
    for cam_name, cam_info in sample['cams'].items():
        camera_config[cam_name] = {
            'data_path': cam_info['data_path'],
            'cam_intrinsic': cam_info['cam_intrinsic'].tolist(),
            'sensor2lidar_translation': cam_info['sensor2lidar_translation'].tolist(),
            'sensor2lidar_rotation': cam_info['sensor2lidar_rotation'].tolist()
        }
    
    with open(f"{output_dir}/camera_config.json", 'w', encoding='utf-8') as f:
        json.dump(camera_config, f, indent=2, ensure_ascii=False)
    
    # 创建标注文件
    annotations = {
        'gt_boxes': sample['gt_boxes'].tolist(),
        'gt_names': sample['gt_names'].tolist(),
        'gt_velocity': sample['gt_velocity'].tolist(),
        'num_lidar_pts': sample['num_lidar_pts'].tolist(),
        'num_radar_pts': sample['num_radar_pts'].tolist(),
        'valid_flag': sample['valid_flag'].tolist()
    }
    
    with open(f"{output_dir}/annotations.json", 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    
    # 创建变换矩阵文件
    transforms = {
        'lidar2ego_translation': sample['lidar2ego_translation'],
        'lidar2ego_rotation': sample['lidar2ego_rotation'],
        'ego2global_translation': sample['ego2global_translation'],
        'ego2global_rotation': sample['ego2global_rotation']
    }
    
    with open(f"{output_dir}/transforms.json", 'w', encoding='utf-8') as f:
        json.dump(transforms, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 演示文件已创建在: {output_dir}/")
    print(f"  - README.md: 样本信息说明")
    print(f"  - camera_config.json: 相机配置")
    print(f"  - annotations.json: 标注信息")
    print(f"  - transforms.json: 坐标变换")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize real nuScenes sample")
    parser.add_argument("--input", type=str, default="data/nuscenes_infos_val.pkl", 
                       help="Input pickle file path")
    parser.add_argument("--sample_index", type=int, default=0, 
                       help="Index of sample to visualize")
    parser.add_argument("--output_json", type=str, 
                       help="Output JSON file to save the sample")
    parser.add_argument("--create_demo", action="store_true", 
                       help="Create demo directory with sample files")
    
    args = parser.parse_args()
    
    # Visualize the sample
    sample = visualize_real_sample(args.input, args.sample_index, args.output_json)
    
    # Create demo files if requested
    if args.create_demo:
        create_sample_demo(sample) 