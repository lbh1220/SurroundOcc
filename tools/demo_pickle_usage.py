#!/usr/bin/env python3
"""
Demonstrate pickle usage in datasets
"""

import pickle
import numpy as np
import json
import os

def demo_pickle_vs_json():
    """Compare pickle vs JSON for dataset storage"""
    
    # 模拟数据集样本
    sample_data = {
        'image_path': './data/images/sample_001.jpg',
        'label': 'car',
        'bbox': np.array([[100, 200, 300, 400]]),  # numpy数组
        'keypoints': np.array([[50, 60], [70, 80], [90, 100]]),  # 关键点
        'metadata': {
            'camera_intrinsic': np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]]),
            'timestamp': 1234567890,
            'weather': 'sunny'
        }
    }
    
    print("=== Pickle vs JSON 对比 ===")
    print(f"原始数据: {sample_data}")
    print()
    
    # 保存为pickle
    with open('demo_data.pkl', 'wb') as f:
        pickle.dump(sample_data, f)
    
    # 尝试保存为JSON（会失败）
    try:
        with open('demo_data.json', 'w') as f:
            json.dump(sample_data, f)
    except Exception as e:
        print(f"JSON保存失败: {e}")
    
    # 读取pickle
    with open('demo_data.pkl', 'rb') as f:
        loaded_pickle = pickle.load(f)
    
    print("Pickle读取结果:")
    print(f"  - 数据类型保持: {type(loaded_pickle['bbox'])}")
    print(f"  - numpy数组形状: {loaded_pickle['bbox'].shape}")
    print(f"  - 嵌套字典保持: {type(loaded_pickle['metadata'])}")
    print()
    
    # 文件大小对比
    pickle_size = os.path.getsize('demo_data.pkl')
    print(f"Pickle文件大小: {pickle_size} bytes")
    
    # 清理
    os.remove('demo_data.pkl')
    if os.path.exists('demo_data.json'):
        os.remove('demo_data.json')

def demo_dataset_structure():
    """演示典型数据集pickle结构"""
    
    # 模拟nuScenes风格的pickle结构
    dataset_info = {
        'infos': [
            {
                'token': 'sample_001',
                'image_paths': [
                    './data/cam_front.jpg',
                    './data/cam_left.jpg',
                    './data/cam_right.jpg'
                ],
                'lidar_path': './data/lidar.bin',
                'gt_boxes': np.array([[10, 20, 30, 4, 2, 1.5, 0.5]]),
                'gt_labels': np.array(['car']),
                'camera_intrinsics': [
                    np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]]),
                    np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]]),
                    np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]])
                ],
                'transforms': {
                    'lidar_to_camera': np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
                    'camera_to_global': np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
                }
            },
            {
                'token': 'sample_002',
                'image_paths': [
                    './data/cam_front_2.jpg',
                    './data/cam_left_2.jpg',
                    './data/cam_right_2.jpg'
                ],
                'lidar_path': './data/lidar_2.bin',
                'gt_boxes': np.array([[15, 25, 35, 3, 1.8, 1.2, 0.3]]),
                'gt_labels': np.array(['pedestrian']),
                'camera_intrinsics': [
                    np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]]),
                    np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]]),
                    np.array([[1000, 0, 500], [0, 1000, 300], [0, 0, 1]])
                ],
                'transforms': {
                    'lidar_to_camera': np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
                    'camera_to_global': np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
                }
            }
        ],
        'metadata': {
            'version': 'v1.0',
            'dataset_name': 'demo_dataset',
            'num_samples': 2,
            'class_names': ['car', 'pedestrian', 'bicycle'],
            'sensor_config': {
                'num_cameras': 3,
                'camera_names': ['front', 'left', 'right'],
                'has_lidar': True
            }
        }
    }
    
    # 保存数据集
    with open('demo_dataset.pkl', 'wb') as f:
        pickle.dump(dataset_info, f)
    
    print("=== 数据集Pickle结构演示 ===")
    print(f"数据集包含 {len(dataset_info['infos'])} 个样本")
    print(f"元数据: {dataset_info['metadata']}")
    print()
    
    # 读取并验证
    with open('demo_dataset.pkl', 'rb') as f:
        loaded_dataset = pickle.load(f)
    
    print("读取验证:")
    print(f"  - 样本数量: {len(loaded_dataset['infos'])}")
    print(f"  - 第一个样本token: {loaded_dataset['infos'][0]['token']}")
    print(f"  - GT boxes类型: {type(loaded_dataset['infos'][0]['gt_boxes'])}")
    print(f"  - GT boxes形状: {loaded_dataset['infos'][0]['gt_boxes'].shape}")
    print(f"  - 相机内参类型: {type(loaded_dataset['infos'][0]['camera_intrinsics'][0])}")
    
    # 清理
    os.remove('demo_dataset.pkl')

def demo_common_datasets():
    """展示常见数据集如何使用pickle"""
    
    print("=== 常见数据集Pickle使用 ===")
    
    datasets = {
        'nuScenes': {
            'structure': 'dict with infos list and metadata',
            'content': 'camera images, lidar, annotations, transforms',
            'size': '~90MB for val set'
        },
        'COCO': {
            'structure': 'dict with images, annotations, categories',
            'content': 'image paths, bounding boxes, segmentation masks',
            'size': '~200MB for train set'
        },
        'ImageNet': {
            'structure': 'list of image paths and labels',
            'content': 'image paths, class labels, metadata',
            'size': '~1GB for train set'
        },
        'KITTI': {
            'structure': 'list of frame information',
            'content': 'image paths, lidar, calibration, annotations',
            'size': '~50MB for val set'
        }
    }
    
    for dataset, info in datasets.items():
        print(f"\n{dataset}:")
        print(f"  - 结构: {info['structure']}")
        print(f"  - 内容: {info['content']}")
        print(f"  - 大小: {info['size']}")

if __name__ == "__main__":
    demo_pickle_vs_json()
    print("\n" + "="*50 + "\n")
    demo_dataset_structure()
    print("\n" + "="*50 + "\n")
    demo_common_datasets() 