#!/usr/bin/env python3
"""
Plot training and validation data qpos (positions) for all coordinates over time.

Uses Pydantic models for type-safe data validation and Click for CLI.
"""

import click
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from plot_validation_gpos_refined import load_experiment_file, ExperimentFile
import matplotlib.gridspec as gridspec


def prettify_system_name(system_name: str) -> str:
    """Convert system folder names to pretty display names."""

    name_map = {
        "cart_pole": "Cartpole",
        "cart_pole_double": "Cartpole double",
        "double_pendulum_pm": "Double pendulum"
    }
    return name_map.get(system_name.split("/")[-1], system_name)


def plot_training_validation_qpos(
    experiment_data: ExperimentFile,
    output_path: Path,
    experiment_configs: list[tuple[str, str, float, str, str]] | None = None,
    plot_error: bool = False,
    white_background: bool = True
):
    """
    Plot training and validation qpos data for all coordinates.
    
    Args:
        experiment_data: Validated experiment data
        output_path: Path to save the plot
        experiment_configs: List of tuples (catalog_type, regression_type, noise_level, optimizer, label_pretty_name)
                           e.g., [('mixed', 'mixed', 0.0, 'lasso_regression', 'Mixed'), 
                                  ('sindy', 'explicit', 0.0, 'lasso_regression', 'SINDy')]
        plot_error: If True, plot error instead of absolute trajectories
    """

    if white_background:
        plt.style.use('default')
    else:
        plt.style.use('dark_background')

    # Extract training data
    training_data = experiment_data.visualisation.training_group.data["training_data"]
    training_time = np.array(training_data.time)
    training_series = training_data.series
    
    # Extract validation data
    validation_group_data = experiment_data.visualisation.validation_group.data
    
    # Find all matching result trajectories
    matched_results = []
    # Track the maximum noise level across all configs for ground truth noise
    max_noise_level = 0.0
    
    if experiment_configs is not None:
        for catalog_type, regression_type, noise_level, optimizer, label in experiment_configs:
            max_noise_level = max(max_noise_level, noise_level)
            
            # Search through all validation results
            for key, data in validation_group_data.items():
                if key == "validation_data":
                    continue  # Skip reference data
                
                # Check if this entry has extra_info and solution
                if data.extra_info is None or not data.solution:
                    continue
                
                extra_info = data.extra_info
                solution = data.solution
                
                # Skip invalid results
                if not extra_info.valid:
                    continue
                
                # Check if all parameters match
                if catalog_type not in solution:
                    continue
                if extra_info.regression_type != regression_type:
                    continue
                if extra_info.noise_level != noise_level:
                    continue
                if extra_info.optimization_function != optimizer:
                    continue
                
                # Check if already added
                if key not in [r["key"] for r in matched_results]:
                    matched_results.append({
                        "key": key,
                        "data": data,
                        "catalog_type": catalog_type,
                        "regression_type": regression_type,
                        "noise_level": noise_level,
                        "optimizer": optimizer,
                        "label": label
                    })
                    click.echo(f"Found matching result: {key}")
                    click.echo(f"  Catalog type: {catalog_type}")
                    click.echo(f"  Regression type: {regression_type}")
                    click.echo(f"  Noise level: {noise_level}")
                    click.echo(f"  Optimizer: {optimizer}")
                    click.echo(f"  Label: {label}")
                    break  # Only take first match for this config
        
        if not matched_results:
            click.secho("Warning: No results found matching experiment configs:", fg="yellow")
            click.echo(f"  Configs: {experiment_configs}")
            click.echo("Will only show reference validation_data.")
    
    # Extract batch starting times
    batch_starting_times = experiment_data.visualisation.training_group.batch_starting_times or []
    
    # Get all coordinates
    coordinates = sorted([key for key in training_series.keys() if key.startswith("coor_")])
    n_coords = len(coordinates)
    
    if n_coords == 0:
        click.secho("Error: No coordinate data found", fg="red")
        return
    
    # Create subplots - 4 rows x n_coords columns
    width_per_coord = 6  # Width allocated per coordinate column
    height_fixed = 9     # Fixed height for consistent aspect ratio
    fig = plt.figure(figsize=(width_per_coord * n_coords, height_fixed))
    
    # Create grid spec with height ratios 2:1:2:1
    gs = gridspec.GridSpec(4, n_coords, figure=fig, 
                          height_ratios=[2, 1, 2, 1],
                          hspace=0.4, wspace=0.1)
    
    # Create axes array: 4 rows × n_coords columns
    axes = [[fig.add_subplot(gs[i, j]) for j in range(n_coords)] for i in range(4)]
    
    # Extract experiment folder from settings if available

    experiment_folder = prettify_system_name(experiment_data.generation_settings.experiment_folder or "Unknown System")
    
    # Main title with experiment folder and noise level if applicable
    title = f'{experiment_folder} - Training and Validation Trajectories'
    if max_noise_level > 0:
        title += f' (Max Noise Level: {max_noise_level})'
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    # Row 0: Training positions (height 2/3)
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[0][col_idx]
        coord_data = training_series[coord_name]
        rng = np.random.RandomState(42)  # Fixed seed for reproducibility
        qpos = np.array(coord_data.qpos)

        if max_noise_level > 0:
            qpos += rng.normal(loc=0, scale=max_noise_level, size=qpos.shape)
        
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
        forces = np.array(coord_data.forces)
        
        # Add noise to forces if specified
        if max_noise_level > 0:
            rng = np.random.RandomState(42)
            noise_scale = max_noise_level * np.linalg.norm(forces) / len(forces)
            forces = forces + rng.normal(loc=0, scale=noise_scale, size=forces.shape)
        
        ax.plot(training_time, forces, linewidth=1.5, color='red', alpha=0.7)
        
        # Add vertical lines for batch starting times
        for batch_time in batch_starting_times:
            ax.axvline(x=batch_time, color='red', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Forces', fontsize=10, fontweight='bold')
    
    # Row 2: Validation positions (height 2/3)
    result_colors = ['#e74c3c', '#3498db', '#9b59b6', '#f39c12', '#1abc9c', '#e67e22', '#34495e', '#16a085']
    
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[2][col_idx]
        
        # Get reference (ground truth)
        ref_data = validation_group_data["validation_data"]
        ref_time = np.array(ref_data.time)
        ref_series = ref_data.series
        ref_qpos = np.array(ref_series[coord_name].qpos)
        
        if plot_error:
            # Plot absolute error: result - ground_truth
            for idx, result in enumerate(matched_results):
                result_data = result["data"]
                result_time = np.array(result_data.time)
                result_series = result_data.series
                result_qpos = np.array(result_series[coord_name].qpos)
                
                # Calculate absolute error
                error = result_qpos - ref_qpos
                
                # Use the pretty label from the config
                result_label = result['label']
                
                color = result_colors[idx % len(result_colors)]
                ax.plot(result_time, error, linewidth=2, color=color, label=result_label, alpha=0.8)
            
            if col_idx == 0:
                ax.set_ylabel('Error', fontsize=10, fontweight='bold')
        else:
            # Plot absolute trajectories
            ax.plot(ref_time, ref_qpos, linewidth=2, color='#2ecc71', label='Ground Truth', alpha=0.8)
            
            # Overlay all matched result trajectories
            for idx, result in enumerate(matched_results):
                result_data = result["data"]
                result_time = np.array(result_data.time)
                result_series = result_data.series
                result_qpos = np.array(result_series[coord_name].qpos)
                
                # Use the pretty label from the config
                result_label = result['label']
                
                color = result_colors[idx % len(result_colors)]
                ax.plot(result_time, result_qpos, linewidth=2, color=color, label=result_label, alpha=0.8, linestyle='--')
            
            if col_idx == 0:
                ax.set_ylabel('Position', fontsize=10, fontweight='bold')
        
        ax.grid(True, alpha=0.3)
        
        # Add legend to rightmost plot
        if col_idx == n_coords - 1:
            ax.legend(loc='upper right', fontsize=8)
    
    # Row 3: Validation forces (height 1/3)
    for col_idx, coord_name in enumerate(coordinates):
        ax = axes[3][col_idx]
        
        # Plot reference forces only (input forces don't change)
        ref_data = validation_group_data["validation_data"]
        ref_time = np.array(ref_data.time)
        ref_series = ref_data.series
        ref_forces = np.array(ref_series[coord_name].forces)
        
        # Add noise to forces if specified
        if max_noise_level > 0:
            rng = np.random.RandomState(42)  # Same seed for reproducibility
            noise_scale = max_noise_level * np.linalg.norm(ref_forces) / len(ref_forces)
            ref_forces = ref_forces + rng.normal(loc=0, scale=noise_scale, size=ref_forces.shape)
        
        ax.plot(ref_time, ref_forces, linewidth=1.5, color='red', alpha=0.7)
        
        ax.set_xlabel('Time (s)', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        if col_idx == 0:
            ax.set_ylabel('Forces', fontsize=10, fontweight='bold')
    
    # Adjust layout to accommodate suptitle
    fig.subplots_adjust(top=0.92, bottom=0.08)
    
    plt.savefig(Path("plots") / (output_path+".png"), dpi=300, bbox_inches='tight',transparent=True)
    plt.savefig(Path("plots") / (output_path+".svg"), dpi=300, bbox_inches='tight',transparent=True)
    click.secho(f"✓ Saved plot to: {output_path}", fg="green")
    
    plt.close()


@click.command()
@click.argument('input_json', type=click.Path(exists=True, path_type=Path))
@click.argument('output_png', type=click.Path(path_type=Path), required=False)
@click.option('--config', '-c', 'experiment_configs', multiple=True,
              help='Experiment config as "catalog_type,regression_type,noise_level,optimizer,label". Can be specified multiple times. '
                   'Example: -c "mixed,mixed,0.0,lasso_regression,Mixed" -c "sindy,explicit,0.0,lasso_regression,SINDy"')
@click.option('--error', '-e', 'plot_error', is_flag=True,
              help='Plot error instead of absolute trajectories')
def main(input_json: Path, output_png: Path | None, experiment_configs: tuple[str, ...], 
         plot_error: bool):
    """
    Plot training and validation trajectories from experiment JSON file.
    
    INPUT_JSON: Path to the experiment JSON file
    
    OUTPUT_PNG: Optional output path for the plot (default: <input>_trajectories.png)
    
    Examples:
    
      \b
      # Plot with specific experiment configs
      python plot_validation_qpos_v2.py data.json -c "mixed,mixed,0.0,lasso_regression,Mixed" -c "sindy,explicit,0.0,lasso_regression,SINDy"
      
      \b
      # With different noise levels
      python plot_validation_qpos_v2.py data.json -c "mixed,mixed,0.01,lasso_regression,Mixed" -c "sindy,explicit,0.01,lasso_regression,SINDy"
      
      \b
      # Plot errors
      python plot_validation_qpos_v2.py data.json output.png -c "mixed,mixed,0.0,lasso_regression,Mixed" --error
    """
    
    # Parse experiment configs
    config_list = None
    if experiment_configs:
        config_list = []
        for config_str in experiment_configs:
            parts = config_str.split(',')
            if len(parts) != 5:
                click.secho(f"✗ Invalid config format: {config_str}. Expected 'catalog_type,regression_type,noise_level,optimizer,label'", 
                           fg="red", err=True)
                raise click.Abort()
            try:
                noise = float(parts[2].strip())
            except ValueError:
                click.secho(f"✗ Invalid noise level: {parts[2]}. Must be a number.", 
                           fg="red", err=True)
                raise click.Abort()
            config_list.append((parts[0].strip(), parts[1].strip(), noise, parts[3].strip(), parts[4].strip()))
    
    # Default output path
    if output_png is None:
        suffix = ""
        if config_list:
            labels = [label for _, _, _, _, label in config_list]
            suffix += f"_{'_'.join(labels)}"
            # Add noise info from configs
            noise_levels = set(noise for _, _, noise, _, _ in config_list)
            if noise_levels:
                suffix += f"_noise{max(noise_levels)}"
        output_png =  f"{input_json.stem}_trajectories{suffix}"
    
    # Load and validate experiment data
    click.echo(f"Loading experiment data from: {input_json}")
    try:
        experiment_data = load_experiment_file(str(input_json))
        click.secho("✓ Data validation successful", fg="green")
    except Exception as e:
        click.secho(f"✗ Failed to load/validate experiment data: {e}", fg="red", err=True)
        raise click.Abort()
    
    # Generate plot
    click.echo(f"Generating plot...")
    try:
        plot_training_validation_qpos(
            experiment_data, 
            output_png + "_white.png", 
            config_list, 
            plot_error,
            white_background=True
        )
        plot_training_validation_qpos(
            experiment_data, 
            output_png + "_dark.png", 
            config_list, 
            plot_error,
            white_background=False
        )
    except Exception as e:
        click.secho(f"✗ Failed to generate plot: {e}", fg="red", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
