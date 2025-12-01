#!/usr/bin/env python3
"""
Plot training and validation data qpos (positions) for all coordinates over time.

Reads a JSON experiment file and generates a 2-row plot:
- Row 1: Training data with batch starting time markers
- Row 2: Validation data trajectories
"""

import json
import sys
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def plot_training_validation_qpos(json_data: dict, output_path: str, solution_types: list = None, noise_level: float = None, regression_types: list = None, plot_error: bool = False):
    """
    Plot training and validation qpos data for all coordinates.
    
    Args:
        json_data: Dictionary containing experiment data
        output_path: Path to save the plot
        solution_types: List of solution type keys (e.g., ['mixed', 'xlsindy', 'sindy'])
        noise_level: Noise level to add to ground truth and filter results (e.g., 0.0, 0.001, 0.01, 0.1)
        regression_types: List of regression types to filter results (e.g., ['explicit', 'implicit'])
        plot_error: If True, plot error instead of absolute trajectories
    """
    # Extract training data
    training_data = json_data["visualisation"]["training_group"]["data"]["training_data"]
    training_time = np.array(training_data["time"])
    training_series = training_data["series"]
    
    # Extract validation data - find all matching result trajectories
    validation_group_data = json_data["visualisation"]["validation_group"]["data"]
    
    # Find all matching result trajectories
    matched_results = []
    
    if solution_types is not None or noise_level is not None or regression_types is not None:
        # Generate all combinations of filters
        from itertools import product
        
        sol_types = solution_types if solution_types else [None]
        reg_types = regression_types if regression_types else [None]
        
        filter_combinations = list(product(sol_types, reg_types))
        
        for solution_type, regression_type in filter_combinations:
            # Search through all validation results
            for key, data in validation_group_data.items():
                if key == "validation_data":
                    continue  # Skip reference data

                if key == "optimizer":
                    if data != "lasso_regression":
                        continue  # Skip non-lasso_regression optimizers
                
                # Check if this entry has extra_info and solution
                if "extra_info" not in data or "solution" not in data:
                    continue
                
                extra_info = data["extra_info"]
                solution = data["solution"]
                
                # Check filters
                matches = True
                if solution_type is not None and solution_type not in solution:
                    matches = False
                if noise_level is not None and extra_info.get("noise_level") != noise_level:
                    matches = False
                if regression_type is not None and extra_info.get("regression_type") != regression_type:
                    matches = False
                
                if matches:
                    # Check if already added
                    if key not in [r["key"] for r in matched_results]:
                        matched_results.append({
                            "key": key,
                            "data": data,
                            "solution_type": solution_type,
                            "noise_level": extra_info.get("noise_level"),
                            "regression_type": extra_info.get("regression_type")
                        })
                        print(f"Found matching result: {key}")
                        print(f"  Solution type: {solution_type}")
                        print(f"  Noise level (filter): {noise_level}")
                        print(f"  Noise level (data): {extra_info.get('noise_level')}")
                        print(f"  Regression type: {extra_info.get('regression_type')}")
        
        if not matched_results:
            print(f"Warning: No results found matching filters:")
            print(f"  Solution types: {solution_types}")
            print(f"  Noise level: {noise_level}")
            print(f"  Regression types: {regression_types}")
            print("Will only show reference validation_data.")
    
    # Extract batch starting times
    batch_starting_times = json_data["visualisation"]["training_group"]["batch_starting_times"]
    
    # Get all coordinates
    coordinates = sorted([key for key in training_series.keys() if key.startswith("coor_")])
    n_coords = len(coordinates)
    
    if n_coords == 0:
        print("No coordinate data found")
        return
    
    # Create subplots - 4 rows x n_coords columns
    # Row heights: 2/3 (training positions), 1/3 (training forces), 2/3 (validation positions), 1/3 (validation forces)
    # Maintain aspect ratio: width proportional to n_coords, height fixed
    width_per_coord = 6  # Width allocated per coordinate column
    height_fixed = 9     # Fixed height for consistent aspect ratio
    fig = plt.figure(figsize=(width_per_coord * n_coords, height_fixed))
    
    # Create grid spec with height ratios 2:1:2:1
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(4, n_coords, figure=fig, 
                          height_ratios=[2, 1, 2, 1],
                          hspace=0.4, wspace=0.1)
    
    # Create axes array: 4 rows × n_coords columns
    axes = [[fig.add_subplot(gs[i, j]) for j in range(n_coords)] for i in range(4)]
    
    # Main title with noise level if applicable
    title = 'Training and Validation Trajectories - Position (qpos) over Time'
    if noise_level is not None and noise_level > 0:
        title += f' (Noise Level: {noise_level})'
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    # Row 0: Training positions (height 2/3)
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[0][col_idx]
        coord_data = training_series[coord_name]
        rng = np.random.RandomState(42)  # Fixed seed for reproducibility
        qpos = np.array(coord_data["qpos"])

        qpos += rng.normal(loc=0, scale=noise_level, size=qpos.shape)
        
        ax.plot(training_time, qpos, linewidth=2, color='#2ecc71')
        
        # Add vertical lines for batch starting times
        for batch_time in batch_starting_times:
            ax.axvline(x=batch_time, color='red', linestyle='--', linewidth=1, alpha=0.7)
        
        coord_num = coord_name.split('_')[1]
        ax.set_title(f'Coordinate {coord_num}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Position', fontsize=10, fontweight='bold')
        if col_idx == n_coords - 1:
            ax.legend(['Ground Truth'], loc='upper right', fontsize=9)
    
    # Row 1: Training forces (height 1/3)
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[1][col_idx]
        coord_data = training_series[coord_name]
        forces = np.array(coord_data["forces"])
        ax.plot(training_time, forces, linewidth=1.5, color='red', alpha=0.7)
        
        # Add vertical lines for batch starting times
        for batch_time in batch_starting_times:
            ax.axvline(x=batch_time, color='red', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Forces', fontsize=10, fontweight='bold')
    
    # Row 2: Validation positions (height 2/3)
    # Colors for different result trajectories
    result_colors = ['#e74c3c', '#3498db', '#9b59b6', '#f39c12', '#1abc9c', '#e67e22', '#34495e', '#16a085']
    
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[2][col_idx]
        
        # Get reference (ground truth)
        ref_data = validation_group_data["validation_data"]
        ref_time = np.array(ref_data["time"])
        ref_series = ref_data["series"]
        ref_qpos = np.array(ref_series[coord_name]["qpos"])
        
        # Add noise to ground truth if specified
        if noise_level is not None and noise_level > 0:

            ref_qpos = ref_qpos 
        
        if plot_error:
            # Plot absolute error: result - ground_truth
            for idx, result in enumerate(matched_results):
                result_data = result["data"]
                result_time = np.array(result_data["time"])
                result_series = result_data["series"]
                result_qpos = np.array(result_series[coord_name]["qpos"])
                
                # Calculate absolute error
                error = result_qpos - ref_qpos
                
                # Create label with solution type
                result_label = f"{result['solution_type'].upper() if result['solution_type'] else 'Result'}"
                if result['regression_type']:
                    result_label += f" [{result['regression_type']}]"
                
                color = result_colors[idx % len(result_colors)]
                ax.plot(result_time, error, linewidth=2, color=color, label=result_label, alpha=0.8)
            
            ax.set_ylabel('Error', fontsize=10, fontweight='bold') if col_idx == 0 else None
        else:
            # Plot absolute trajectories
            ax.plot(ref_time, ref_qpos, linewidth=2, color='#2ecc71', label='Ground Truth', alpha=0.8)
            
            # Overlay all matched result trajectories
            for idx, result in enumerate(matched_results):
                result_data = result["data"]
                result_time = np.array(result_data["time"])
                result_series = result_data["series"]
                result_qpos = np.array(result_series[coord_name]["qpos"])
                
                # Create label with solution type
                result_label = f"{result['solution_type'].upper() if result['solution_type'] else 'Result'}"
                if result['regression_type']:
                    result_label += f" [{result['regression_type']}]"
                
                color = result_colors[idx % len(result_colors)]
                ax.plot(result_time, result_qpos, linewidth=2, color=color, label=result_label, alpha=0.8, linestyle='--')
            
            ax.set_ylabel('Position', fontsize=10, fontweight='bold') if col_idx == 0 else None
        
        ax.grid(True, alpha=0.3)
        
        # Add legend to rightmost plot
        if col_idx == n_coords - 1:
            ax.legend(loc='upper right', fontsize=8)
    
    # Row 3: Validation forces (height 1/3)
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[3][col_idx]
        
        # Plot reference forces only (input forces don't change)
        ref_data = validation_group_data["validation_data"]
        ref_time = np.array(ref_data["time"])
        ref_series = ref_data["series"]
        ref_forces = np.array(ref_series[coord_name]["forces"])
        
        # Add noise to forces if specified
        if noise_level is not None and noise_level > 0:
            rng = np.random.RandomState(42)  # Same seed for reproducibility
            noise_scale = noise_level * np.linalg.norm(ref_forces) / len(ref_forces)
            ref_forces = ref_forces + rng.normal(loc=0, scale=noise_scale, size=ref_forces.shape)
        
        ax.plot(ref_time, ref_forces, linewidth=1.5, color='red', alpha=0.7)
        
        ax.set_xlabel('Time (s)', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Forces', fontsize=10, fontweight='bold')
    
    # Adjust layout to accommodate suptitle
    fig.subplots_adjust(top=0.92, bottom=0.08)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {output_path}")
    
    plt.close()


def main():
    """Main entry point - reads JSON from file argument."""
    
    if len(sys.argv) < 2:
        print("Usage: python plot_validation_qpos.py <input_json> [output_png] [--solution TYPE1,TYPE2,...] [--noise LEVEL] [--regression TYPE1,TYPE2,...] [--error]")
        print("Examples:")
        print("  python plot_validation_qpos.py data.json")
        print("  python plot_validation_qpos.py data.json output.png --solution mixed,xlsindy --noise 0.001 --regression explicit")
        print("  python plot_validation_qpos.py data.json --solution mixed,sindy --noise 0.0 --error")
        sys.exit(1)
    
    # Read from file
    json_path = sys.argv[1]
    
    # Parse arguments
    output_path = None
    solution_types = None
    noise_level = None
    regression_types = None
    plot_error = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--error":
            plot_error = True
            i += 1
        elif arg == "--solution" and i + 1 < len(sys.argv):
            solution_types = sys.argv[i + 1].split(',')
            i += 2
        elif arg == "--noise" and i + 1 < len(sys.argv):
            noise_level = float(sys.argv[i + 1])
            i += 2
        elif arg == "--regression" and i + 1 < len(sys.argv):
            regression_types = sys.argv[i + 1].split(',')
            i += 2
        elif not arg.startswith("--"):
            # This is the output path
            output_path = arg
            i += 1
        else:
            print(f"Unknown argument: {arg}")
            i += 1
    
    # Default output path based on input filename
    if output_path is None:
        input_path = Path(json_path)
        suffix = ""
        if solution_types:
            suffix += f"_{'_'.join(solution_types)}"
        if noise_level is not None:
            suffix += f"_noise{noise_level}"
        if regression_types:
            suffix += f"_{'_'.join(regression_types)}"
        output_path = str(input_path.parent / f"{input_path.stem}_trajectories{suffix}.png")
    
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    # Generate plot
    plot_training_validation_qpos(json_data, output_path, solution_types, noise_level, regression_types, plot_error)


if __name__ == "__main__":
    main()
