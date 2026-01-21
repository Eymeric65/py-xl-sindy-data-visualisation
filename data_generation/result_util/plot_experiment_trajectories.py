#!/usr/bin/env python3
"""
Plot training and validation trajectories for a specific experiment using the updated dataclass structure.

Usage:
    python plot_experiment_trajectories.py <experiment_id> <trajectory_name1> <trajectory_name2> ...
"""

import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import matplotlib.gridspec as gridspec

# Import the updated dataclass
sys.path.insert(0, str(Path(__file__).parent.parent / "script"))
from ..script.dataclass import Experiment


def prettify_system_name(system_name: str) -> str:
    """Convert system folder names to pretty display names."""
    name_map = {
        "cart_pole": "Cartpole",
        "cart_pole_double": "Cartpole Double",
        "double_pendulum_pm": "Double Pendulum"
    }
    base_name = system_name.split("/")[-1]
    return name_map.get(base_name, base_name)


def prettify_method_name(paradigm: str, regression_type: str) -> str:
    """Convert paradigm/regression_type to pretty method names."""
    method_map = {
        ("mixed", "mixed"): "UNI-SINDy",
        ("xlsindy", "explicit"): "XLSINDy",
        ("sindy", "explicit"): "SINDy",
        ("sindy", "implicit"): "SINDy-PI"
    }
    return method_map.get((paradigm, regression_type), f"{paradigm}/{regression_type}")


def generate_latex_tables(experiment, first_traj, reference_traj, output_path: str, plots_dir: Path):
    """
    Generate LaTeX tables showing the library and non-null solution coefficients.
    
    Args:
        experiment: Experiment data
        first_traj: First validation trajectory (for solution mode and retrieved values)
        reference_traj: Reference trajectory (for ideal values)
        output_path: Base path for output file
        plots_dir: Directory to save the LaTeX file
    """
    
    # Get solution mode from first trajectory
    if not first_traj.solutions or len(first_traj.solutions) == 0:
        print("Warning: No solution found in first trajectory, skipping LaTeX generation")
        return
    
    solution_mode = first_traj.solutions[0].mode_solution
    
    # Find the solution with matching mode in both trajectories
    ideal_solution = None
    for sol in reference_traj.solutions:
        if sol.mode_solution == solution_mode:
            ideal_solution = sol
            break
    
    retrieved_solution = first_traj.solutions[0]
    
    if ideal_solution is None:
        print(f"Warning: No solution with mode '{solution_mode}' found in reference trajectory")
        return
    
    # Extract labels and values
    labels = ideal_solution.solution_label
    ideal_values = ideal_solution.solution_vector
    retrieved_values = retrieved_solution.solution_vector
    
    if len(labels) != len(ideal_values) or len(labels) != len(retrieved_values):
        print("Warning: Mismatched solution dimensions, skipping LaTeX generation")
        return
    
    # Generate LaTeX content as a complete standalone document
    latex_content = []
    latex_content.append("\\documentclass[11pt]{article}")
    latex_content.append("\\usepackage[margin=1in]{geometry}")
    latex_content.append("\\usepackage{amsmath}")
    latex_content.append("\\usepackage{amssymb}")
    latex_content.append("\\usepackage{longtable}")
    latex_content.append("\\begin{document}")
    latex_content.append("")
    latex_content.append("\\section*{Solution Analysis Tables}")
    latex_content.append("")
    
    # Table 1: Full library (3 columns of index-label pairs)
    latex_content.append("\\subsection*{Table 1: Complete Function Library}")
    latex_content.append("{\\scriptsize")
    latex_content.append("\\begin{longtable}{|c|l|c|l|c|l|}")
    latex_content.append("\\hline")
    latex_content.append("\\# & Function Label & \\# & Function Label & \\# & Function Label \\\\")
    latex_content.append("\\hline")
    latex_content.append("\\endfirsthead")
    latex_content.append("\\hline")
    latex_content.append("\\# & Function Label & \\# & Function Label & \\# & Function Label \\\\")
    latex_content.append("\\hline")
    latex_content.append("\\endhead")
    latex_content.append("\\hline")
    latex_content.append("\\endfoot")
    
    # Process labels in groups of 3
    for i in range(0, len(labels), 3):
        row_parts = []
        for j in range(3):
            if i + j < len(labels):
                idx = i + j
                label = labels[idx]
                # Strip any existing dollar signs and add single $ for inline math
                label_clean = label.replace('$$', '').replace('$', '').replace('\operatorname','')
                row_parts.append(f"{idx} & ${label_clean}$")
            else:
                # Fill empty cells
                row_parts.append(" & ")
        latex_content.append(" & ".join(row_parts) + " \\\\")
    
    latex_content.append("\\hline")
    latex_content.append("\\end{longtable}")
    latex_content.append("}")
    latex_content.append("")
    latex_content.append("\\clearpage")
    latex_content.append("")
    
    # Table 2: Non-null coefficients
    latex_content.append("\\subsection*{Table 2: Non-null Coefficients Comparison}")
    latex_content.append("{\\scriptsize")
    latex_content.append("\\begin{longtable}{|l|r|r|}")
    latex_content.append("\\hline")
    latex_content.append("Function Label & Ideal Value & Retrieved Value \\\\")
    latex_content.append("\\hline")
    latex_content.append("\\endfirsthead")
    latex_content.append("\\hline")
    latex_content.append("Function Label & Ideal Value & Retrieved Value \\\\")
    latex_content.append("\\hline")
    latex_content.append("\\endhead")
    latex_content.append("\\hline")
    latex_content.append("\\endfoot")
    
    # Collect non-null entries (from either ideal or retrieved)
    non_null_entries = []
    for idx, (label, ideal_val, retrieved_val) in enumerate(zip(labels, ideal_values, retrieved_values)):
        if abs(ideal_val) > 1e-10 or abs(retrieved_val) > 1e-10:
            non_null_entries.append((label, ideal_val, retrieved_val))
    
    # Sort by absolute value of ideal (for better visualization)
    non_null_entries.sort(key=lambda x: abs(x[1]), reverse=True)
    
    for label, ideal_val, retrieved_val in non_null_entries:
        # Strip any existing dollar signs and add single $ for inline math
        label_clean = label.replace('$$', '').replace('$', '').replace('\operatorname','')
        latex_content.append(f"${label_clean}$ & {ideal_val:.6f} & {retrieved_val:.6f} \\\\")
    
    latex_content.append("\\hline")
    latex_content.append("\\end{longtable}")
    latex_content.append("}")
    latex_content.append("")
    latex_content.append("\\end{document}")
    
    # Save to file (without _dark or _white suffix, just .tex extension)
    latex_file = plots_dir / f"{output_path}.tex"
    with open(latex_file, 'w') as f:
        f.write("\n".join(latex_content))
    
    print(f"✓ Saved LaTeX document to: {latex_file}")


def load_experiment(experiment_id: str) -> Experiment:
    """Load experiment data from JSON file."""
    results_dir = Path("results")
    json_path = results_dir / f"{experiment_id}.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Experiment file not found: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    return Experiment(**data)


def plot_trajectories(
    experiment: Experiment,
    trajectory_names: list[str],
    output_path: str,
    white_background: bool = True
):
    """
    Plot training and selected validation trajectories.
    
    Args:
        experiment: Experiment data
        trajectory_names: List of trajectory names to plot from validation group
        output_path: Path to save the plot
        white_background: If True, use white background style
    """
    
    if white_background:
        plt.style.use('default')
    else:
        plt.style.use('dark_background')
    
    # Extract training data - use the first trajectory (should be the training data)
    training_trajectories = experiment.data.training_group.trajectories
    if not training_trajectories:
        raise ValueError("No training trajectories found")
    
    training_traj = training_trajectories[0]  # Assume first is training data
    training_series = training_traj.series
    training_time = np.array(training_series.time.time)
    
    # Extract batch starting times
    batch_starting_times = experiment.data.training_group.batch_starting_time or []
    
    # Get validation trajectories by name
    validation_trajectories = []
    for traj_name in trajectory_names:
        traj = experiment.data.validation_group.get_trajectory_by_name(traj_name)
        if traj is None:
            print(f"Warning: Trajectory '{traj_name}' not found in validation group")
            continue
        validation_trajectories.append(traj)
    
    if not validation_trajectories:
        raise ValueError("No matching validation trajectories found")
    
    # Get reference trajectory
    reference_traj = None
    for traj in experiment.data.validation_group.trajectories:
        if traj.reference:
            reference_traj = traj
            break
    
    if reference_traj is None:
        raise ValueError("No reference trajectory found in validation group")
    
    ref_series = reference_traj.series
    ref_time = np.array(ref_series.time.time)
    
    # Determine number of coordinates
    n_coords = len(training_series.qpos.series)
    
    # Create subplots - 4 rows x n_coords columns
    width_per_coord = 6
    height_fixed = 9
    fig = plt.figure(figsize=(width_per_coord * n_coords, height_fixed))
    
    # Create grid spec with height ratios 2:1:2:1
    gs = gridspec.GridSpec(4, n_coords, figure=fig,
                          height_ratios=[2, 1, 2, 1],
                          hspace=0.4, wspace=0.1)
    
    axes = [[fig.add_subplot(gs[i, j]) for j in range(n_coords)] for i in range(4)]
    
    # Extract experiment info
    experiment_folder = prettify_system_name(experiment.generation_params.experiment_folder)
    
    # Main title
    title = f'{experiment_folder} - Training and Validation Trajectories'
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    # Define colors for trajectories
    result_colors = ['#e74c3c', '#3498db', '#9b59b6', '#f39c12', '#1abc9c', '#e67e22', '#34495e', '#16a085']
    
    # Row 0: Training positions
    for col_idx in range(n_coords):
        ax = axes[0][col_idx]
        coord_data = training_series.qpos.series[col_idx]
        qpos = np.array(coord_data.data)
        
        ax.plot(training_time, qpos, linewidth=2, color='#2ecc71')
        
        # Add vertical lines for batch starting times
        for batch_time in batch_starting_times:
            ax.axvline(x=batch_time, color='red', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.set_title(f'Coordinate {col_idx}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Position', fontsize=10, fontweight='bold')
        if col_idx == n_coords - 1:
            ax.legend(['Training Data'], loc='upper right', fontsize=9)
    
    # Row 1: Training forces
    for col_idx in range(n_coords):
        ax = axes[1][col_idx]
        coord_data = training_series.forces.series[col_idx]
        forces = np.array(coord_data.data)
        
        ax.plot(training_time, forces, linewidth=1.5, color='red', alpha=0.7)
        
        # Add vertical lines for batch starting times
        for batch_time in batch_starting_times:
            ax.axvline(x=batch_time, color='red', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Forces', fontsize=10, fontweight='bold')
    
    # Row 2: Validation positions
    for col_idx in range(n_coords):
        ax = axes[2][col_idx]
        
        # Plot reference (ground truth)
        ref_coord_data = ref_series.qpos.series[col_idx]
        ref_qpos = np.array(ref_coord_data.data)
        
        ax.plot(ref_time, ref_qpos, linewidth=2, color='#2ecc71', label='Ground Truth', alpha=0.8)
        
        # Overlay selected result trajectories
        for idx, val_traj in enumerate(validation_trajectories):
            val_series = val_traj.series
            val_time = np.array(val_series.time.time)
            val_coord_data = val_series.qpos.series[col_idx]
            val_qpos = np.array(val_coord_data.data)
            
            # Create label from trajectory name and regression info if available
            label = val_traj.name
            if val_traj.regression_result:
                rr = val_traj.regression_result.regression_parameters
                label = prettify_method_name(rr.paradigm, rr.regression_type)
                if val_traj.regression_result.RMSE_validation_position:
                    label += f" (RMSE: {val_traj.regression_result.RMSE_validation_position:.2e})"
            
            color = result_colors[idx % len(result_colors)]
            ax.plot(val_time, val_qpos, linewidth=2, color=color, label=label, alpha=0.8, linestyle='--')
        
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Position', fontsize=10, fontweight='bold')
        
        # Add legend to rightmost plot
        if col_idx == n_coords - 1:
            ax.legend(loc='upper right', fontsize=8)
    
    # Row 3: Validation forces
    for col_idx in range(n_coords):
        ax = axes[3][col_idx]
        
        # Plot reference forces
        ref_coord_data = ref_series.forces.series[col_idx]
        ref_forces = np.array(ref_coord_data.data)
        
        ax.plot(ref_time, ref_forces, linewidth=1.5, color='red', alpha=0.7)
        
        ax.set_xlabel('Time (s)', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Forces', fontsize=10, fontweight='bold')
    
    # Adjust layout
    fig.subplots_adjust(top=0.92, bottom=0.08)
    
    # Save plots
    plots_dir = Path("plots")
    plots_dir.mkdir(exist_ok=True)
    
    plt.savefig(plots_dir / f"{output_path}.png", dpi=300, bbox_inches='tight', transparent=True)
    plt.savefig(plots_dir / f"{output_path}.svg", dpi=300, bbox_inches='tight', transparent=True)
    plt.savefig(plots_dir / f"{output_path}.eps", dpi=300, bbox_inches='tight', transparent=True)
    print(f"✓ Saved plot to: plots/{output_path}.png and plots/{output_path}.svg")
    
    plt.close()


def main():
    if len(sys.argv) < 3:
        print("Usage: python plot_experiment_trajectories.py <experiment_id> <trajectory_name1> [trajectory_name2] ... [--output output_name]")
        print("\nExample:")
        print("  python plot_experiment_trajectories.py abc123def456 validation_mixed_0.0_lasso validation_sindy_0.0_lasso")
        print("  python plot_experiment_trajectories.py abc123def456 traj1 traj2 --output my_plot")
        sys.exit(1)
    
    experiment_id = sys.argv[1]
    
    # Parse arguments to separate trajectory names from output option
    args = sys.argv[2:]
    output_name = None
    trajectory_names = []
    
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_name = args[i + 1]
            i += 2
        else:
            trajectory_names.append(args[i])
            i += 1
    
    if not trajectory_names:
        print("Error: At least one trajectory name is required")
        sys.exit(1)
    
    print(f"Loading experiment: {experiment_id}")
    try:
        experiment = load_experiment(experiment_id)
    except Exception as e:
        print(f"Error loading experiment: {e}")
        sys.exit(1)
    
    print(f"Available trajectories in validation group:")
    for traj in experiment.data.validation_group.trajectories:
        ref_label = " (REFERENCE)" if traj.reference else ""
        print(f"  - {traj.name}{ref_label}")
    
    print(f"\nPlotting trajectories: {', '.join(trajectory_names)}")
    
    if output_name:
        output_base = output_name
    else:
        output_base = f"{experiment_id}_trajectories"
    
    try:
        # Generate white background version
        plot_trajectories(experiment, trajectory_names, output_base + "_white", white_background=True)
        
        # Generate dark background version
        plot_trajectories(experiment, trajectory_names, output_base + "_dark", white_background=False)
        
        # Generate LaTeX document once (not per background)
        validation_trajectories = []
        for traj_name in trajectory_names:
            traj = experiment.data.validation_group.get_trajectory_by_name(traj_name)
            if traj is not None:
                validation_trajectories.append(traj)
        
        if validation_trajectories:
            reference_traj = None
            for traj in experiment.data.validation_group.trajectories:
                if traj.reference:
                    reference_traj = traj
                    break
            
            if reference_traj:
                plots_dir = Path("plots")
                generate_latex_tables(experiment, validation_trajectories[0], reference_traj, output_base, plots_dir)
        
        print(f"\n✓ Successfully generated plots")
    except Exception as e:
        print(f"Error generating plots: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
