#!/usr/bin/env python3
"""
Test script for AirSim occupancy ground truth conversion

This script creates sample data and tests the conversion functionality.
"""

import os
import sys
import numpy as np
import pandas as pd
from os import path as osp

# Add project root to Python path
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__))))

import mmcv
from tools.create_airsim_occupancy_gt import create_airsim_occupancy_gt


def create_sample_data(data_root):
    """Create sample AirSim dataset for testing."""
    print(f"Creating sample data in {data_root}...")
    
    # Create directory structure
    drone_dir = osp.join(data_root, 'Drone1')
    traj_dir = osp.join(drone_dir, '1700000000')
    mmcv.mkdir_or_exist(traj_dir)
    
    # Create sample camera directories
    camera_names = ['CAM_FRONT', 'CAM_BACK', 'CAM_LEFT', 'CAM_RIGHT', 'CAM_FRONT_LEFT', 'CAM_FRONT_RIGHT']
    for cam_name in camera_names:
        cam_dir = osp.join(traj_dir, cam_name)
        mmcv.mkdir_or_exist(cam_dir)
        
        # Create dummy image files
        for i in range(5):
            timestamp = 1700000000.0 + i * 0.1
            img_path = osp.join(cam_dir, f'{timestamp:.3f}.png')
            # Create a tiny dummy file
            with open(img_path, 'w') as f:
                f.write('dummy')
    
    # Create sample world point cloud
    np.random.seed(42)
    n_points = 10000
    
    # Generate points in a 200x200x20 meter world
    x = np.random.uniform(-100, 100, n_points)
    y = np.random.uniform(-100, 100, n_points)
    z = np.random.uniform(-10, 10, n_points)
    
    # Create sample world points (without semantic labels)
    world_points = np.column_stack([x, y, z])
    map_cloud_path = osp.join(data_root, 'map_cloud_resolution1.npy')
    np.save(map_cloud_path, world_points)
    print(f"Created sample world point cloud: {world_points.shape}")
    
    # Create sample trajectory data
    n_frames = 5
    timestamps = [1700000000.0 + i * 0.1 for i in range(n_frames)]
    
    # Sample vehicle trajectory (circular motion)
    positions_x = [10 * np.cos(i * 0.5) for i in range(n_frames)]
    positions_y = [10 * np.sin(i * 0.5) for i in range(n_frames)]
    positions_z = [5.0] * n_frames
    
    # Sample quaternions (slight rotation around z-axis)
    quats = []
    for i in range(n_frames):
        angle = i * 0.1  # rotation angle
        quat = [0, 0, np.sin(angle/2), np.cos(angle/2)]  # rotation around z-axis
        quats.append(quat)
    
    # Create DataFrame
    data = {
        'timestamp': timestamps,
        'desired_vel': [2.0] * n_frames,
        'quat_1': [q[0] for q in quats],  # x
        'quat_2': [q[1] for q in quats],  # y
        'quat_3': [q[2] for q in quats],  # z
        'quat_4': [q[3] for q in quats],  # w
        'pos_x': positions_x,
        'pos_y': positions_y,
        'pos_z': positions_z,
        'vel_x': [1.0] * n_frames,
        'vel_y': [0.5] * n_frames,
        'vel_z': [0.0] * n_frames,
        'velcmd_x': [1.0] * n_frames,
        'velcmd_y': [0.5] * n_frames,
        'velcmd_z': [0.0] * n_frames,
        'is_collide': [False] * n_frames
    }
    
    df = pd.DataFrame(data)
    data_csv_path = osp.join(traj_dir, 'data.csv')
    df.to_csv(data_csv_path, index=False)
    print(f"Created sample trajectory data: {len(df)} frames")
    
    # Create mission info
    mission_info = {
        "mission_id": "test_mission",
        "start_time": timestamps[0],
        "end_time": timestamps[-1],
        "drone_id": "Drone1"
    }
    
    import json
    mission_path = osp.join(traj_dir, 'mission_info.json')
    with open(mission_path, 'w') as f:
        json.dump(mission_info, f, indent=2)
    
    print(f"Sample dataset created successfully!")
    return data_root


def test_conversion():
    """Test the AirSim to SurroundOcc conversion."""
    # Create temporary test data
    test_data_root = '/tmp/test_airsim_data'
    
    try:
        # Create sample data
        data_root = create_sample_data(test_data_root)
        
        # Test conversion
        print("\n" + "="*50)
        print("Testing AirSim occupancy ground truth conversion...")
        print("="*50)
        
        create_airsim_occupancy_gt(
            airsim_data_root=data_root,
            point_cloud_range=[-50, -50, -5.0, 50, 50, 3.0],
            default_semantic_label=29
        )
        
        # Verify results
        print("\n" + "="*50)
        print("Verifying conversion results...")
        print("="*50)
        
        occ_gt_dir = osp.join(data_root, 'Drone1', '1700000000', 'OCCUPANCY_GT')
        if osp.exists(occ_gt_dir):
            occ_files = [f for f in os.listdir(occ_gt_dir) if f.endswith('.npy')]
            print(f"Generated {len(occ_files)} occupancy ground truth files")
            
            if occ_files:
                # Load and examine one file
                sample_file = osp.join(occ_gt_dir, occ_files[0])
                occ_data = np.load(sample_file)
                print(f"Sample file: {occ_files[0]}")
                print(f"  Shape: {occ_data.shape}")
                print(f"  X range: [{occ_data[:, 0].min():.2f}, {occ_data[:, 0].max():.2f}]")
                print(f"  Y range: [{occ_data[:, 1].min():.2f}, {occ_data[:, 1].max():.2f}]")
                print(f"  Z range: [{occ_data[:, 2].min():.2f}, {occ_data[:, 2].max():.2f}]")
                print(f"  Semantic labels: {np.unique(occ_data[:, 3])}")
                print(f"  Total points: {len(occ_data)}")
                
                # Verify data format
                assert occ_data.shape[1] == 4, f"Expected 4 columns, got {occ_data.shape[1]}"
                assert len(occ_data) > 0, "No points in occupancy ground truth"
                print("  ✓ Data format validation passed")
                
        print("\n✓ Conversion test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise
    
    finally:
        # Cleanup
        if osp.exists(test_data_root):
            import shutil
            shutil.rmtree(test_data_root)
            print(f"\nCleaned up test data: {test_data_root}")


def main():
    """Main test function."""
    print("AirSim Occupancy Ground Truth Conversion Test")
    print("=" * 50)
    
    test_conversion()


if __name__ == '__main__':
    main() 