#!/usr/bin/env python3
"""
Create a mini dataset for testing with only a few samples
"""

import pickle
import os
import argparse

def create_mini_dataset(input_pkl, output_pkl, num_samples=1):
    """
    Create a mini dataset with only num_samples samples
    
    Args:
        input_pkl: Path to original pickle file
        output_pkl: Path to output mini pickle file  
        num_samples: Number of samples to include (default: 1)
    """
    
    # Load original dataset
    with open(input_pkl, 'rb') as f:
        data_infos = pickle.load(f)
    
    print(f"Original dataset structure:")
    print(f"  - Root keys: {list(data_infos.keys())}")
    print(f"  - Number of samples: {len(data_infos['infos'])}")
    
    # Create mini dataset by copying the structure and taking only first num_samples
    mini_data_infos = {
        'infos': data_infos['infos'][:num_samples],
        'metadata': data_infos['metadata']
    }
    
    print(f"Creating mini dataset with {len(mini_data_infos['infos'])} samples")
    
    # Save mini dataset
    with open(output_pkl, 'wb') as f:
        pickle.dump(mini_data_infos, f)
    
    print(f"Mini dataset saved to {output_pkl}")
    
    # Print sample info
    for i, info in enumerate(mini_data_infos['infos']):
        print(f"Sample {i}:")
        print(f"  - Token: {info.get('token', 'N/A')}")
        print(f"  - LiDAR: {info.get('lidar_path', 'N/A')}")
        print(f"  - Occupancy: {info.get('occ_path', 'N/A')}")
        print(f"  - Cameras: {list(info.get('cams', {}).keys())}")
        print(f"  - GT boxes: {len(info.get('gt_boxes', []))} objects")

def analyze_sample_structure(pickle_path, sample_index=0):
    """
    Analyze a specific sample in detail
    
    Args:
        pickle_path: Path to pickle file
        sample_index: Index of sample to analyze
    """
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    if sample_index < len(data['infos']):
        sample = data['infos'][sample_index]
        print(f"\nDetailed analysis of sample {sample_index}:")
        print(f"Token: {sample['token']}")
        print(f"Scene: {sample['scene_token']}")
        print(f"Frame: {sample['frame_idx']}")
        print(f"Timestamp: {sample['timestamp']}")
        print(f"LiDAR path: {sample['lidar_path']}")
        print(f"Occupancy path: {sample['occ_path']}")
        print(f"Cameras: {list(sample['cams'].keys())}")
        print(f"GT objects: {len(sample['gt_boxes'])}")
        print(f"GT names: {sample['gt_names']}")
        
        # Analyze camera info
        for cam_name, cam_info in sample['cams'].items():
            print(f"\nCamera {cam_name}:")
            print(f"  - Image: {cam_info['data_path']}")
            print(f"  - Intrinsic shape: {cam_info['cam_intrinsic'].shape}")
            print(f"  - Sensor2LiDAR translation: {cam_info['sensor2lidar_translation']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create mini dataset for testing")
    parser.add_argument("--input", type=str, required=True, help="Input pickle file path")
    parser.add_argument("--output", type=str, help="Output mini pickle file path")
    parser.add_argument("--num_samples", type=int, default=1, help="Number of samples to include")
    parser.add_argument("--analyze", type=int, help="Analyze specific sample index")
    
    args = parser.parse_args()
    
    if args.analyze is not None:
        analyze_sample_structure(args.input, args.analyze)
    elif args.output:
        create_mini_dataset(args.input, args.output, args.num_samples)
    else:
        print("Please specify either --output to create mini dataset or --analyze to analyze a sample") 