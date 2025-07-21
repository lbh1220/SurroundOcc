#!/usr/bin/env python3
"""
Analyze the structure of pickle files to understand the data format
"""

import pickle
import os
import argparse
from collections import defaultdict

def analyze_dict_structure(data, prefix="", max_depth=3, current_depth=0):
    """
    Recursively analyze dictionary structure
    
    Args:
        data: Data to analyze
        prefix: Current path prefix
        max_depth: Maximum depth to analyze
        current_depth: Current depth level
    """
    if current_depth >= max_depth:
        print(f"{prefix}... (max depth reached)")
        return
    
    if isinstance(data, dict):
        print(f"{prefix}Dict with {len(data)} keys:")
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                print(f"{prefix}  {key}: {type(value).__name__} with {len(value)} items")
                analyze_dict_structure(value, prefix + "    ", max_depth, current_depth + 1)
            else:
                print(f"{prefix}  {key}: {type(value).__name__} = {str(value)[:100]}")
    elif isinstance(data, list):
        print(f"{prefix}List with {len(data)} items:")
        if len(data) > 0:
            print(f"{prefix}  First item type: {type(data[0]).__name__}")
            if isinstance(data[0], dict):
                analyze_dict_structure(data[0], prefix + "    ", max_depth, current_depth + 1)
            else:
                print(f"{prefix}  First item: {str(data[0])[:100]}")
    else:
        print(f"{prefix}{type(data).__name__}: {str(data)[:100]}")

def analyze_pickle_structure(pickle_path, sample_index=0):
    """
    Analyze pickle file structure in detail
    
    Args:
        pickle_path: Path to pickle file
        sample_index: Index of sample to analyze in detail
    """
    print(f"Analyzing pickle file: {pickle_path}")
    print("=" * 50)
    
    # Load pickle file
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    print(f"Root data type: {type(data)}")
    print(f"Root data length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
    print()
    
    # Analyze root structure
    print("ROOT STRUCTURE:")
    analyze_dict_structure(data, max_depth=2)
    print()
    
    # If it's a dict, analyze each key
    if isinstance(data, dict):
        print("DETAILED KEY ANALYSIS:")
        for key, value in data.items():
            print(f"\nKey: '{key}'")
            print(f"Type: {type(value)}")
            if isinstance(value, (list, dict)):
                print(f"Length: {len(value)}")
                if len(value) > 0:
                    print("First item structure:")
                    analyze_dict_structure(value[:1] if isinstance(value, list) else {list(value.keys())[0]: value[list(value.keys())[0]]}, "  ", max_depth=2)
            else:
                print(f"Value: {str(value)[:200]}")
    
    # If it's a list, analyze first few items
    elif isinstance(data, list):
        print("LIST ANALYSIS:")
        print(f"Total items: {len(data)}")
        if len(data) > 0:
            print(f"First {min(3, len(data))} items:")
            for i in range(min(3, len(data))):
                print(f"\nItem {i}:")
                analyze_dict_structure(data[i], "  ", max_depth=2)
    
    # Analyze specific sample if requested
    if isinstance(data, dict) and 'infos' in data and isinstance(data['infos'], list):
        if sample_index < len(data['infos']):
            print(f"\nDETAILED SAMPLE ANALYSIS (index {sample_index}):")
            sample = data['infos'][sample_index]
            analyze_dict_structure(sample, "", max_depth=5)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"File size: {os.path.getsize(pickle_path)} bytes")
    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
        if 'infos' in data and isinstance(data['infos'], list):
            print(f"Number of samples: {len(data['infos'])}")
            if len(data['infos']) > 0:
                print(f"Sample keys: {list(data['infos'][0].keys())}")

def create_mini_dataset_corrected(input_pkl, output_pkl, num_samples=1):
    """
    Create mini dataset with correct structure handling
    
    Args:
        input_pkl: Path to original pickle file
        output_pkl: Path to output mini pickle file  
        num_samples: Number of samples to include (default: 1)
    """
    
    # Load original dataset
    with open(input_pkl, 'rb') as f:
        data_infos = pickle.load(f)
    
    print(f"Original dataset structure:")
    if isinstance(data_infos, dict) and 'infos' in data_infos:
        print(f"  - Root keys: {list(data_infos.keys())}")
        print(f"  - Number of samples: {len(data_infos['infos'])}")
        
        # Take only first num_samples from infos
        mini_data_infos = data_infos.copy()
        mini_data_infos['infos'] = data_infos['infos'][:num_samples]
        
        print(f"Creating mini dataset with {len(mini_data_infos['infos'])} samples")
        
        # Save mini dataset
        with open(output_pkl, 'wb') as f:
            pickle.dump(mini_data_infos, f)
        
        print(f"Mini dataset saved to {output_pkl}")
        
        # Print sample info
        for i, info in enumerate(mini_data_infos['infos']):
            print(f"Sample {i}: {info.get('token', 'N/A')}")
    else:
        print("Error: Unexpected data structure")
        analyze_pickle_structure(input_pkl)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze pickle file structure")
    parser.add_argument("--input", type=str, required=True, help="Input pickle file path")
    parser.add_argument("--output", type=str, help="Output mini pickle file path (optional)")
    parser.add_argument("--num_samples", type=int, default=1, help="Number of samples for mini dataset")
    parser.add_argument("--sample_index", type=int, default=0, help="Index of sample to analyze in detail")
    
    args = parser.parse_args()
    
    # Analyze structure
    analyze_pickle_structure(args.input, args.sample_index)
    
    # Create mini dataset if output specified
    if args.output:
        print("\n" + "=" * 50)
        print("CREATING MINI DATASET:")
        create_mini_dataset_corrected(args.input, args.output, args.num_samples) 