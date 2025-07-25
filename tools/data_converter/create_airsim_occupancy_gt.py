#!/usr/bin/env python3
"""
AirSim Occupancy Ground Truth Generator

This script converts AirSim multi-camera drone dataset to SurroundOcc format occupancy ground truth.
Now supports traffic information (other aircraft) in the occupancy map.

Usage:
    python tools/create_airsim_occupancy_gt.py --airsim-data-root /path/to/airsim_data_sample

Requirements:
    - AirSim dataset with structure as described in data_intro.md
    - map_cloud_resolution1.npy file containing world coordinate point cloud
    - data.csv files with vehicle pose information
    - traffic/ directory with traffic information (optional)
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import glob
import json
from os import path as osp
from scipy.spatial.transform import Rotation as R
import time

# Add project root to Python path
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__))))


def create_airsim_occupancy_gt(airsim_data_root, 
                              map_cloud_path=None,
                              point_cloud_range=[-50, -50, -5.0, 50, 50, 3.0],
                              default_semantic_label=29,
                              resolution=0.5,
                              uav_semantic_label=30,
                              evtol_semantic_label=31):
    """Generate occupancy ground truth for AirSim dataset with traffic support.
    
    Args:
        airsim_data_root (str): Root path of AirSim dataset
        map_cloud_path (str): Path to map_cloud_resolution1.npy file. 
                             If None, will look for it in airsim_data_root
        point_cloud_range (list): [x_min, y_min, z_min, x_max, y_max, z_max]
        default_semantic_label (int): Default semantic label for map points
        resolution (float): Point cloud resolution for traffic aircraft
        uav_semantic_label (int): Semantic label for UAV aircraft
        evtol_semantic_label (int): Semantic label for eVTOL aircraft
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
            
            # Load traffic information
            traffic_info = load_traffic_info(traj_dir, resolution, 
                                           uav_semantic_label, evtol_semantic_label)
            
            # Create OCCUPANCY_GT directory
            occ_gt_dir = osp.join(traj_dir, 'OCCUPANCY_GT')
            os.makedirs(occ_gt_dir, exist_ok=True)
            
            # Process each frame
            for idx, row in df.iterrows():
                timestamp = row['timestamp']
                
                t0 = time.time()
                vehicle_pos = np.array([row['pos_x'], row['pos_y'], row['pos_z']])
                vehicle_quat = np.array([row['quat_1'], row['quat_2'], 
                                       row['quat_3'], row['quat_4']])  # x,y,z,w
                t1 = time.time()
                vehicle_points = transform_points_to_vehicle_frame(
                    world_points, vehicle_pos, vehicle_quat, point_cloud_range)
                t2 = time.time()
                filtered_map_points = filter_points_by_range(vehicle_points, point_cloud_range)
                t3 = time.time()
                traffic_points = get_traffic_points_at_timestamp(
                    traffic_info, timestamp, vehicle_pos, vehicle_quat, point_cloud_range)
                t4 = time.time()

                # Combine map and traffic points
                if len(traffic_points) > 0:
                    combined_points = np.concatenate([filtered_map_points, traffic_points], axis=0)
                    total_traffic_points = len(traffic_points)
                else:
                    combined_points = filtered_map_points
                    total_traffic_points = 0
                t5 = time.time()

                # Save occupancy ground truth
                output_filename = f'{timestamp:.3f}.npy'
                output_path = osp.join(occ_gt_dir, output_filename)
                np.save(output_path, combined_points)
                t6 = time.time()

                print(
                    f'Processed frame {idx+1}/{len(df)}, '
                    f'map points: {len(filtered_map_points)}/{len(world_points)}, '
                    f'traffic points: {total_traffic_points}'
                )
                print(
                    f'    Timing (s): '
                    f'vehicle_pose: {t1-t0:.3f}, '
                    f'transform: {t2-t1:.3f}, '
                    f'filter: {t3-t2:.3f}, '
                    f'get_traffic: {t4-t3:.3f}, '
                    f'combine: {t5-t4:.3f}, '
                    f'save: {t6-t5:.3f}, '
                    f'total: {t6-t0:.3f}'
                )
            
            total_frames_processed += len(df)
            print(f'    Completed trajectory {traj_name}, saved {len(df)} occupancy files')
            if traffic_info['aircraft']:
                print(f'    Traffic aircraft processed: {list(traffic_info["aircraft"].keys())}')
    
    print(f'\n=== Summary ===')
    print(f'Total frames processed: {total_frames_processed}')
    print(f'Point cloud range: {point_cloud_range}')
    print(f'Map semantic label: {default_semantic_label}')
    print(f'UAV semantic label: {uav_semantic_label}')
    print(f'eVTOL semantic label: {evtol_semantic_label}')
    print(f'Traffic resolution: {resolution}')
    print(f'AirSim occupancy ground truth creation completed!')


def load_traffic_info(traj_dir, resolution, uav_semantic_label, evtol_semantic_label):
    """Load traffic information for a trajectory.
    
    Args:
        traj_dir (str): Trajectory directory path
        resolution (float): Point cloud resolution
        uav_semantic_label (int): Semantic label for UAV
        evtol_semantic_label (int): Semantic label for eVTOL
    
    Returns:
        dict: Traffic information with aircraft data and point clouds
    """
    traffic_dir = osp.join(traj_dir, 'traffic')
    traffic_info = {'aircraft': {}, 'resolution': resolution}
    
    if not osp.exists(traffic_dir):
        print(f'    No traffic directory found in {traj_dir}')
        return traffic_info
    
    # Load traffic summary
    summary_path = osp.join(traffic_dir, 'traffic_summary.json')
    if not osp.exists(summary_path):
        print(f'    Warning: traffic_summary.json not found in {traffic_dir}')
        return traffic_info
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    aircraft_registry = summary.get('aircraft_registry', {})
    print(f'    Found {len(aircraft_registry)} aircraft in traffic summary')
    
    # Process each aircraft
    for aircraft_name, aircraft_data in aircraft_registry.items():
        aircraft_type = aircraft_data.get('aircraft_type', 'unknown')
        
        # Determine semantic label
        if aircraft_type == 'uav':
            semantic_label = uav_semantic_label
        elif aircraft_type == 'evtol':
            semantic_label = evtol_semantic_label
        else:
            semantic_label = uav_semantic_label  # Default to UAV
        
        # Get bbox parameters
        bbox_width = aircraft_data.get('bbox_width', 2.0)
        bbox_length = aircraft_data.get('bbox_length', 2.0)
        bbox_height = aircraft_data.get('bbox_height', 1.0)
        
        # Generate aircraft point cloud
        aircraft_points = generate_aircraft_point_cloud(
            bbox_width, bbox_length, bbox_height, resolution, semantic_label)
        
        # Load trajectory data
        data_file = aircraft_data.get('data_file', f'{aircraft_name}.csv')
        trajectory_path = osp.join(traffic_dir, data_file)
        
        if osp.exists(trajectory_path):
            trajectory_df = pd.read_csv(trajectory_path)
            print(f'      Loaded {aircraft_name} ({aircraft_type}) with {len(trajectory_df)} trajectory points')
        else:
            print(f'      Warning: trajectory file not found for {aircraft_name}: {trajectory_path}')
            trajectory_df = pd.DataFrame()
        
        traffic_info['aircraft'][aircraft_name] = {
            'type': aircraft_type,
            'semantic_label': semantic_label,
            'bbox': {'width': bbox_width, 'length': bbox_length, 'height': bbox_height},
            'point_cloud': aircraft_points,
            'trajectory': trajectory_df
        }
    
    return traffic_info


def generate_aircraft_point_cloud(bbox_width, bbox_length, bbox_height, resolution, semantic_label):
    """Generate point cloud for an aircraft based on its bounding box.
    
    Args:
        bbox_width (float): Aircraft width (Y-axis)
        bbox_length (float): Aircraft length (X-axis)
        bbox_height (float): Aircraft height (Z-axis)
        resolution (float): Point cloud resolution
        semantic_label (int): Semantic label for this aircraft
    
    Returns:
        np.ndarray: Aircraft point cloud in its own coordinate system (N, 4) [x,y,z,semantic]
    """
    # Generate grid points within the bounding box
    x_range = np.arange(-bbox_length/2, bbox_length/2 + resolution/2, resolution)
    y_range = np.arange(-bbox_width/2, bbox_width/2 + resolution/2, resolution)
    z_range = np.arange(-bbox_height/2, bbox_height/2 + resolution/2, resolution)
    
    # Create meshgrid
    xx, yy, zz = np.meshgrid(x_range, y_range, z_range, indexing='ij')
    
    # Flatten and create point cloud
    points = np.stack([xx.flatten(), yy.flatten(), zz.flatten()], axis=1)
    
    # Add semantic labels
    semantic_labels = np.full((points.shape[0], 1), semantic_label, dtype=np.float32)
    aircraft_points = np.concatenate([points, semantic_labels], axis=1)
    
    return aircraft_points


def get_traffic_points_at_timestamp(traffic_info, timestamp, ego_pos, ego_quat, point_cloud_range):
    """Get traffic points for a specific timestamp in ego coordinate system.
    
    Args:
        traffic_info (dict): Traffic information
        timestamp (float): Current timestamp
        ego_pos (np.ndarray): Ego vehicle position
        ego_quat (np.ndarray): Ego vehicle quaternion
        point_cloud_range (list): Point cloud range for filtering
    
    Returns:
        np.ndarray: Traffic points in ego coordinate system
    """
    all_traffic_points = []
    
    for aircraft_name, aircraft_data in traffic_info['aircraft'].items():
        trajectory_df = aircraft_data['trajectory']
        
        if len(trajectory_df) == 0:
            continue
        
        # Find the closest timestamp
        time_diffs = np.abs(trajectory_df['timestamp'].values - timestamp)
        closest_idx = np.argmin(time_diffs)
        closest_row = trajectory_df.iloc[closest_idx]
        
        # Skip if time difference is too large (e.g., > 0.1 seconds)
        if time_diffs[closest_idx] > 0.1:
            continue
        
        # Get aircraft pose
        aircraft_pos = np.array([closest_row['pos_x'], closest_row['pos_y'], closest_row['pos_z']])
        aircraft_quat = np.array([closest_row['quat_x'], closest_row['quat_y'], 
                                closest_row['quat_z'], closest_row['quat_w']])  # x,y,z,w
        
        # Get aircraft point cloud in its own coordinate system
        aircraft_points = aircraft_data['point_cloud']
        
        # Transform aircraft points to world coordinate system
        world_aircraft_points = transform_aircraft_to_world(
            aircraft_points, aircraft_pos, aircraft_quat)
        
        # Transform world aircraft points to ego coordinate system
        ego_aircraft_points = transform_points_to_vehicle_frame(
            world_aircraft_points, ego_pos, ego_quat, point_cloud_range)
        
        # Filter points within range
        filtered_aircraft_points = filter_points_by_range(ego_aircraft_points, point_cloud_range)
        
        if len(filtered_aircraft_points) > 0:
            all_traffic_points.append(filtered_aircraft_points)
    
    # Combine all traffic points
    if all_traffic_points:
        combined_traffic_points = np.concatenate(all_traffic_points, axis=0)
    else:
        combined_traffic_points = np.empty((0, 4), dtype=np.float32)
    
    return combined_traffic_points


def transform_aircraft_to_world(aircraft_points, aircraft_pos, aircraft_quat):
    """Transform aircraft points from aircraft coordinate to world coordinate system.
    
    Args:
        aircraft_points (np.ndarray): Points in aircraft coordinate system (N, 4)
        aircraft_pos (np.ndarray): Aircraft position in world coordinates (3,)
        aircraft_quat (np.ndarray): Aircraft quaternion (4,) [x,y,z,w]
    
    Returns:
        np.ndarray: Points in world coordinate system (N, 4)
    """
    # Extract xyz coordinates and semantic labels
    xyz = aircraft_points[:, :3].copy()
    semantic = aircraft_points[:, 3:4].copy()
    
    # Apply rotation (aircraft frame to world frame)
    rotation = R.from_quat(aircraft_quat)  # [x,y,z,w] format
    xyz_rotated = rotation.apply(xyz)
    
    # Apply translation
    xyz_world = xyz_rotated + aircraft_pos[np.newaxis, :]
    
    # Combine back with semantic labels
    world_points = np.concatenate([xyz_world, semantic], axis=1)
    
    return world_points


def transform_points_to_vehicle_frame(world_points, vehicle_pos, vehicle_quat, point_cloud_range):
    """Transform points from world coordinate to vehicle coordinate system.
    
    Args:
        world_points (np.ndarray): World coordinate points (N, 4) [x,y,z,semantic]
        vehicle_pos (np.ndarray): Vehicle position (3,) [x,y,z]
        vehicle_quat (np.ndarray): Vehicle quaternion (4,) [x,y,z,w]
    
    Returns:
        np.ndarray: Points in vehicle coordinate system (N, 4) [x,y,z,semantic]
    """
    # Extract xyz coordinates and semantic labels
    # filter points, speed up the computation when the point cloud is large
    x_min, y_min, z_min, x_max, y_max, z_max = point_cloud_range
    x_range = (x_max - x_min) * 1.5
    y_range = (y_max - y_min) * 1.5

    # 以 vehicle_pos 为中心，筛选 x/y 在范围内的点
    x_center, y_center = vehicle_pos[0], vehicle_pos[1]
    x_lower, x_upper = x_center - x_range / 2, x_center + x_range / 2
    y_lower, y_upper = y_center - y_range / 2, y_center + y_range / 2

    # mask: 只保留在水平范围内的点
    mask = (
        (world_points[:, 0] >= x_lower) & (world_points[:, 0] <= x_upper) &
        (world_points[:, 1] >= y_lower) & (world_points[:, 1] <= y_upper)
    )
    filtered_world_points = world_points[mask]
    xyz = filtered_world_points[:, :3]  #
    semantic = filtered_world_points[:, 3:4]  #
    
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
    xyz_converted = xyz_rotated.copy()
    xyz_converted[:, 0] = xyz_rotated[:, 0]  # x: forward
    xyz_converted[:, 1] = -xyz_rotated[:, 1]  # y: left (flip if needed)
    xyz_converted[:, 2] = -xyz_rotated[:, 2]   # z: up
    
    # Combine back with semantic labels
    vehicle_points = np.concatenate([xyz_converted, semantic], axis=1)
    
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
        description='Create occupancy ground truth for AirSim dataset with traffic support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python tools/create_airsim_occupancy_gt.py --airsim-data-root /path/to/airsim_data_sample
    
    # Specify custom map cloud path
    python tools/create_airsim_occupancy_gt.py \\
        --airsim-data-root /path/to/airsim_data_sample \\
        --map-cloud-path /path/to/map_cloud_resolution1.npy
    
    # Custom parameters including traffic labels
    python tools/create_airsim_occupancy_gt.py \\
        --airsim-data-root data/airsim_dataset \\
        --map-cloud-path data/airsim_dataset/map_cloud_1600x1600x600_0_50m.npy \\
        --point-cloud-range -200 -200 -100 200 200 100 \\
        --default-semantic-label 0 \\
        --uav-semantic-label 30 \\
        --evtol-semantic-label 31 \\
        --resolution 0.5
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
                       help='Default semantic label for map points without labels. '
                            'Default: 29 (nuScenes static.other)')
    parser.add_argument('--resolution', type=float, default=0.5,
                       help='Point cloud resolution for traffic aircraft. Default: 0.5')
    parser.add_argument('--uav-semantic-label', type=int, default=30,
                       help='Semantic label for UAV aircraft. Default: 30')
    parser.add_argument('--evtol-semantic-label', type=int, default=31,
                       help='Semantic label for eVTOL aircraft. Default: 31')
    
    args = parser.parse_args()
    
    # Validate input paths
    if not osp.exists(args.airsim_data_root):
        raise FileNotFoundError(f"AirSim data root not found: {args.airsim_data_root}")
    
    if args.map_cloud_path and not osp.exists(args.map_cloud_path):
        raise FileNotFoundError(f"Map cloud file not found: {args.map_cloud_path}")
    
    # Print configuration
    print("=== AirSim Occupancy Ground Truth Generator (with Traffic Support) ===")
    print(f"AirSim data root: {args.airsim_data_root}")
    print(f"Map cloud path: {args.map_cloud_path or 'Auto-detect'}")
    print(f"Point cloud range: {args.point_cloud_range}")
    print(f"Map semantic label: {args.default_semantic_label}")
    print(f"UAV semantic label: {args.uav_semantic_label}")
    print(f"eVTOL semantic label: {args.evtol_semantic_label}")
    print(f"Traffic resolution: {args.resolution}")
    print()
    
    # Run the conversion
    create_airsim_occupancy_gt(
        airsim_data_root=args.airsim_data_root,
        map_cloud_path=args.map_cloud_path,
        point_cloud_range=args.point_cloud_range,
        default_semantic_label=args.default_semantic_label,
        resolution=args.resolution,
        uav_semantic_label=args.uav_semantic_label,
        evtol_semantic_label=args.evtol_semantic_label
    )


if __name__ == '__main__':
    main() 