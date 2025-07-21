#!/usr/bin/env python3
"""
Save a real nuScenes sample to JSON file for future reference
"""

import pickle
import json
import numpy as np
import os
from datetime import datetime

def convert_numpy_to_list(obj):
    """
    Recursively convert numpy arrays to lists for JSON serialization
    
    Args:
        obj: Object to convert
        
    Returns:
        Converted object
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return obj

def save_sample_to_json(pickle_path, sample_index=0, output_json=None):
    """
    Extract a real sample from nuScenes pickle and save to JSON
    
    Args:
        pickle_path: Path to pickle file
        sample_index: Index of sample to extract
        output_json: Output JSON file path
    """
    
    print(f"Loading pickle file: {pickle_path}")
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    if sample_index >= len(data['infos']):
        print(f"Error: Sample index {sample_index} out of range (max: {len(data['infos'])-1})")
        return
    
    # Extract the real sample
    sample = data['infos'][sample_index]
    
    # Convert all numpy arrays to lists for JSON serialization
    sample_json = convert_numpy_to_list(sample)
    
    # Add metadata about the extraction
    sample_json['_metadata'] = {
        'extraction_time': datetime.now().isoformat(),
        'source_file': pickle_path,
        'sample_index': sample_index,
        'total_samples_in_file': len(data['infos']),
        'file_metadata': convert_numpy_to_list(data['metadata'])
    }
    
    # Generate output filename if not provided
    if output_json is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_json = f"nuscenes_sample_{sample_index}_{timestamp}.json"
    
    # Save to JSON file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(sample_json, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 样本已保存到: {output_json}")
    print(f"📊 文件大小: {os.path.getsize(output_json)} bytes")
    print(f"📋 样本信息:")
    print(f"  - Token: {sample['token']}")
    print(f"  - Scene: {sample['scene_token']}")
    print(f"  - Frame: {sample['frame_idx']}")
    print(f"  - 相机数量: {len(sample['cams'])}")
    print(f"  - 标注目标数: {len(sample['gt_boxes'])}")
    print(f"  - 字段总数: {len(sample)}")
    
    return output_json

def create_reference_documentation(sample_json, output_md=None):
    """
    Create documentation for the sample structure
    
    Args:
        sample_json: The sample JSON data
        output_md: Output markdown file path
    """
    
    if output_md is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_md = f"nuscenes_sample_documentation_{timestamp}.md"
    
    # Create documentation
    doc_content = f"""# nuScenes 样本结构文档

## 样本基本信息
- **Token**: {sample_json['token']}
- **Scene Token**: {sample_json['scene_token']}
- **Frame Index**: {sample_json['frame_idx']}
- **Timestamp**: {sample_json['timestamp']}
- **Previous Frame**: {sample_json['prev']}
- **Next Frame**: {sample_json['next']}

## 数据文件路径
- **LiDAR路径**: {sample_json['lidar_path']}
- **占用标签路径**: {sample_json['occ_path']}
- **LiDAR分割路径**: {sample_json['lidarseg']}

## 相机配置 (共{len(sample_json['cams'])}个相机)

"""
    
    for cam_name, cam_info in sample_json['cams'].items():
        doc_content += f"""### {cam_name}
- **图像路径**: {cam_info['data_path']}
- **相机类型**: {cam_info['type']}
- **样本数据Token**: {cam_info['sample_data_token']}
- **时间戳**: {cam_info['timestamp']}
- **传感器到车体平移**: {cam_info['sensor2ego_translation']}
- **传感器到车体旋转**: {cam_info['sensor2ego_rotation']}
- **车体到全局平移**: {cam_info['ego2global_translation']}
- **车体到全局旋转**: {cam_info['ego2global_rotation']}
- **传感器到LiDAR平移**: {cam_info['sensor2lidar_translation']}
- **相机内参矩阵**: {cam_info['cam_intrinsic']}

"""
    
    doc_content += f"""## 坐标变换信息
- **LiDAR到车体平移**: {sample_json['lidar2ego_translation']}
- **LiDAR到车体旋转**: {sample_json['lidar2ego_rotation']}
- **车体到全局平移**: {sample_json['ego2global_translation']}
- **车体到全局旋转**: {sample_json['ego2global_rotation']}

## 标注信息
- **GT边界框数量**: {len(sample_json['gt_boxes'])}
- **GT类别**: {sample_json['gt_names']}
- **GT速度数量**: {len(sample_json['gt_velocity'])}
- **LiDAR点数**: {sample_json['num_lidar_pts']}
- **雷达点数**: {sample_json['num_radar_pts']}
- **有效标志**: {sample_json['valid_flag']}

## 其他信息
- **CAN总线数据**: {sample_json['can_bus']}
- **历史帧数量**: {len(sample_json['sweeps'])}
- **LiDAR Token**: {sample_json['lidar_token']}

## 数据结构说明

### 字段类型
- `str`: 字符串类型 (Token, 路径等)
- `int`: 整数类型 (时间戳, 帧索引等)
- `list`: 列表类型 (平移向量, 旋转四元数等)
- `list[list]`: 二维列表 (相机内参矩阵等)
- `list[int]`: 整数列表 (LiDAR点数等)
- `list[str]`: 字符串列表 (类别名称等)
- `list[bool]`: 布尔列表 (有效标志等)
- `list[list[float]]`: 二维浮点列表 (3D边界框等)

### 关键字段说明
1. **cams**: 包含6个相机的完整配置信息
2. **gt_boxes**: 3D边界框，格式为 [x, y, z, l, w, h, yaw]
3. **gt_names**: 目标类别名称
4. **occ_path**: 占用标签文件路径 (SurroundOcc需要)
5. **lidar_path**: LiDAR点云文件路径

### 坐标系说明
- **LiDAR坐标系**: 传感器坐标系
- **车体坐标系**: 车辆中心坐标系
- **全局坐标系**: 世界坐标系

## 提取信息
- **提取时间**: {sample_json['_metadata']['extraction_time']}
- **源文件**: {sample_json['_metadata']['source_file']}
- **样本索引**: {sample_json['_metadata']['sample_index']}
- **文件总样本数**: {sample_json['_metadata']['total_samples_in_file']}
"""
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print(f"📚 文档已保存到: {output_md}")
    return output_md

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Save nuScenes sample to JSON")
    parser.add_argument("--input", type=str, default="data/nuscenes_infos_val.pkl", 
                       help="Input pickle file path")
    parser.add_argument("--sample_index", type=int, default=0, 
                       help="Index of sample to extract")
    parser.add_argument("--output_json", type=str, 
                       help="Output JSON file path")
    parser.add_argument("--output_md", type=str, 
                       help="Output documentation markdown file path")
    parser.add_argument("--create_doc", action="store_true", 
                       help="Create documentation file")
    
    args = parser.parse_args()
    
    # Save sample to JSON
    json_file = save_sample_to_json(args.input, args.sample_index, args.output_json)
    
    # Create documentation if requested
    if args.create_doc:
        with open(json_file, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        create_reference_documentation(sample_data, args.output_md) 