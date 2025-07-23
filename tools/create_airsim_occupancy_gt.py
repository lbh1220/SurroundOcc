#!/usr/bin/env python3
"""
AirSim Occupancy Ground Truth Generator

This script converts AirSim multi-camera drone dataset to SurroundOcc format occupancy ground truth.

Usage:
    python tools/create_airsim_occupancy_gt.py --airsim-data-root /path/to/airsim_data_sample

Requirements:
    - AirSim dataset with structure as described in data_intro.md
    - map_cloud_resolution1.npy file containing world coordinate point cloud
    - data.csv files with vehicle pose information
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import glob
from os import path as osp
from scipy.spatial.transform import Rotation as R

# Add project root to Python path
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__))))

import mmcv


def create_airsim_occupancy_gt(airsim_data_root, 
                              map_cloud_path=None,
                              point_cloud_range=[-50, -50, -5.0, 50, 50, 3.0],
                              default_semantic_label=29):
    """Generate occupancy ground truth for AirSim dataset.
    
    Args:
        airsim_data_root (str): Root path of AirSim dataset
        map_cloud_path (str): Path to map_cloud_resolution1.npy file. 
                             If None, will look for it in airsim_data_root
        point_cloud_range (list): [x_min, y_min, z_min, x_max, y_max, z_max]
        default_semantic_label (int): Default semantic label for points without labels
    """
    print(f'Creating occupancy ground truth for AirSim dataset at {airsim_data_root}')
    
    # Load world coordinate point cloud
    if map_cloud_path is None:
        map_cloud_path = osp.join(airsim_data_root, 'map_cloud_resolution1.npy')
    
    if not osp.exists(map_cloud_path):
        raise FileNotFoundError(f"Map cloud file not found: {map_cloud_path}")
    
    world_points = np.load(map_cloud_path)
    print(f'Loaded world point cloud with shape: {world_points.shape}')
    
    # Check if semantic labels exist, if not add default label
    if world_points.shape[1] == 3:
        print(f'No semantic labels found, adding default label {default_semantic_label}')
        semantic_labels = np.full((world_points.shape[0], 1), default_semantic_label, dtype=np.float32)
        world_points = np.concatenate([world_points, semantic_labels], axis=1)
    elif world_points.shape[1] == 4:
        print('Semantic labels found in point cloud')
    else:
        raise ValueError(f"Unexpected point cloud shape: {world_points.shape}")
    
    # Find all drone directories
    drone_dirs = glob.glob(osp.join(airsim_data_root, 'Drone*'))
    
    if not drone_dirs:
        raise ValueError(f"No drone directories found in {airsim_data_root}")
    
    total_frames_processed = 0
    
    for drone_dir in drone_dirs:
        drone_name = osp.basename(drone_dir)
        print(f'\nProcessing {drone_name}...')
        
        # Find all trajectory directories (timestamp directories)
        trajectory_dirs = glob.glob(osp.join(drone_dir, '[0-9]*'))
        
        if not trajectory_dirs:
            print(f'  No trajectory directories found in {drone_dir}')
            continue
        
        for traj_dir in trajectory_dirs:
            traj_name = osp.basename(traj_dir)
            print(f'  Processing trajectory {traj_name}...')
            
            # Read trajectory data
            data_csv_path = osp.join(traj_dir, 'data.csv')
            if not osp.exists(data_csv_path):
                print(f'    Warning: data.csv not found in {traj_dir}, skipping...')
                continue
            
            df = pd.read_csv(data_csv_path)
            print(f'    Found {len(df)} frames in trajectory')
            
            # Validate required columns
            required_columns = ['timestamp', 'pos_x', 'pos_y', 'pos_z', 
                              'quat_1', 'quat_2', 'quat_3', 'quat_4']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f'    Warning: Missing columns {missing_columns} in {data_csv_path}, skipping...')
                continue
            
            # Create OCCUPANCY_GT directory
            occ_gt_dir = osp.join(traj_dir, 'OCCUPANCY_GT')
            mmcv.mkdir_or_exist(occ_gt_dir)
            
            # Process each frame
            for idx, row in df.iterrows():
                timestamp = row['timestamp']
                
                # Get vehicle pose
                vehicle_pos = np.array([row['pos_x'], row['pos_y'], row['pos_z']])
                vehicle_quat = np.array([row['quat_1'], row['quat_2'], 
                                       row['quat_3'], row['quat_4']])  # x,y,z,w
                
                # Transform world points to vehicle coordinate system
                vehicle_points = transform_points_to_vehicle_frame(
                    world_points, vehicle_pos, vehicle_quat)
                
                # Filter points within point cloud range
                filtered_points = filter_points_by_range(vehicle_points, point_cloud_range)
                
                # Save occupancy ground truth
                output_filename = f'{timestamp:.3f}.npy'
                output_path = osp.join(occ_gt_dir, output_filename)
                np.save(output_path, filtered_points)
                
                if idx % 100 == 0:
                    print(f'    Processed frame {idx+1}/{len(df)}, '
                          f'filtered points: {len(filtered_points)}/{len(world_points)}')
            
            total_frames_processed += len(df)
            print(f'    Completed trajectory {traj_name}, saved {len(df)} occupancy files')
    
    print(f'\n=== Summary ===')
    print(f'Total frames processed: {total_frames_processed}')
    print(f'Point cloud range: {point_cloud_range}')
    print(f'Default semantic label: {default_semantic_label}')
    print(f'AirSim occupancy ground truth creation completed!')


def transform_points_to_vehicle_frame(world_points, vehicle_pos, vehicle_quat):
    """Transform points from world coordinate to vehicle coordinate system.
    
    Args:
        world_points (np.ndarray): World coordinate points (N, 4) [x,y,z,semantic]
        vehicle_pos (np.ndarray): Vehicle position (3,) [x,y,z]
        vehicle_quat (np.ndarray): Vehicle quaternion (4,) [x,y,z,w]
    
    Returns:
        np.ndarray: Points in vehicle coordinate system (N, 4) [x,y,z,semantic]
    """
    # Extract xyz coordinates and semantic labels
    xyz = world_points[:, :3].copy()
    semantic = world_points[:, 3:4].copy()
    
    # Translate: move to vehicle-centered coordinates
    xyz_translated = xyz - vehicle_pos[np.newaxis, :]
    
    # Rotate: apply inverse rotation to align with vehicle frame
    # Note: We use inverse rotation because we want world->vehicle transformation
    rotation = R.from_quat(vehicle_quat)  # [x,y,z,w] format
    xyz_rotated = rotation.inv().apply(xyz_translated)
    
    # Handle coordinate system conversion if needed
    # AirSim typically uses NED (North-East-Down) or FLU (Forward-Left-Up)
    # SurroundOcc expects vehicle coordinate system (usually Forward-Left-Up)
    # You may need to adjust axis mapping based on your specific setup
    
    # For now, assuming the coordinate systems are aligned
    # If you need axis conversion, uncomment and modify these lines:
    # xyz_converted = xyz_rotated.copy()
    # xyz_converted[:, 0] = xyz_rotated[:, 0]  # x: forward
    # xyz_converted[:, 1] = -xyz_rotated[:, 1]  # y: left (flip if needed)
    # xyz_converted[:, 2] = xyz_rotated[:, 2]   # z: up
    
    # Combine back with semantic labels
    vehicle_points = np.concatenate([xyz_rotated, semantic], axis=1)
    
    return vehicle_points


def filter_points_by_range(points, point_cloud_range):
    """Filter points within the specified range.
    
    Args:
        points (np.ndarray): Points (N, 4) [x,y,z,semantic]
        point_cloud_range (list): [x_min, y_min, z_min, x_max, y_max, z_max]
    
    Returns:
        np.ndarray: Filtered points within range
    """
    x_min, y_min, z_min, x_max, y_max, z_max = point_cloud_range
    
    # Filter points within range
    mask = ((points[:, 0] >= x_min) & (points[:, 0] <= x_max) &
            (points[:, 1] >= y_min) & (points[:, 1] <= y_max) &
            (points[:, 2] >= z_min) & (points[:, 2] <= z_max))
    
    filtered_points = points[mask]
    
    return filtered_points


def main():
    """Main function for command line interface."""
    parser = argparse.ArgumentParser(
        description='Create occupancy ground truth for AirSim dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python tools/create_airsim_occupancy_gt.py --airsim-data-root /path/to/airsim_data_sample
    
    # Specify custom map cloud path
    python tools/create_airsim_occupancy_gt.py \\
        --airsim-data-root /path/to/airsim_data_sample \\
        --map-cloud-path /path/to/map_cloud_resolution1.npy
    
    # Custom point cloud range and semantic label
    python tools/create_airsim_occupancy_gt.py \\
        --airsim-data-root /path/to/airsim_data_sample \\
        --point-cloud-range -100 -100 -10 100 100 10 \\
        --default-semantic-label 0
        """)
    
    parser.add_argument('--airsim-data-root', type=str, required=True,
                       help='Root directory of AirSim dataset (containing Drone1/, Drone2/, etc.)')
    parser.add_argument('--map-cloud-path', type=str, default=None,
                       help='Path to map_cloud_resolution1.npy file. '
                            'If not specified, will look for it in airsim_data_root')
    parser.add_argument('--point-cloud-range', type=float, nargs=6,
                       default=[-50, -50, -5.0, 50, 50, 3.0],
                       help='Point cloud range [x_min, y_min, z_min, x_max, y_max, z_max]. '
                            'Default: [-50, -50, -5.0, 50, 50, 3.0] (SurroundOcc default)')
    parser.add_argument('--default-semantic-label', type=int, default=29,
                       help='Default semantic label for points without labels. '
                            'Default: 29 (nuScenes static.other)')
    
    args = parser.parse_args()
    
    # Validate input paths
    if not osp.exists(args.airsim_data_root):
        raise FileNotFoundError(f"AirSim data root not found: {args.airsim_data_root}")
    
    if args.map_cloud_path and not osp.exists(args.map_cloud_path):
        raise FileNotFoundError(f"Map cloud file not found: {args.map_cloud_path}")
    
    # Print configuration
    print("=== AirSim Occupancy Ground Truth Generator ===")
    print(f"AirSim data root: {args.airsim_data_root}")
    print(f"Map cloud path: {args.map_cloud_path or 'Auto-detect'}")
    print(f"Point cloud range: {args.point_cloud_range}")
    print(f"Default semantic label: {args.default_semantic_label}")
    print()
    
    # Run the conversion
    create_airsim_occupancy_gt(
        airsim_data_root=args.airsim_data_root,
        map_cloud_path=args.map_cloud_path,
        point_cloud_range=args.point_cloud_range,
        default_semantic_label=args.default_semantic_label
    )


if __name__ == '__main__':
    main() 