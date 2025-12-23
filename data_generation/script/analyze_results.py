#!/usr/bin/env python3
"""Quick analysis of experiment results grouped by paradigm and regression type."""

import os
import json
from pathlib import Path
from collections import defaultdict
import statistics
import tyro
from tqdm import tqdm

from data_generation.script.dataclass import Experiment


def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def analyze_results(results_dir: str = "results", only_valid_experiments: bool = True):
    """Analyze all experiments and show statistics by paradigm/regression_type.
    
    Args:
        results_dir: Directory containing result JSON files
        only_valid_experiments: If True, only count failures when at least one solution was valid in the experiment
    """
    
    # Group results by (system, paradigm, regression_type)
    stats = defaultdict(lambda: {"valid": 0, "failed": 0, "timeout": 0, "rmse_values": []})
    overall_stats = defaultdict(lambda: {"valid": 0, "failed": 0, "timeout": 0, "rmse_values": []})
    no_friction_stats = defaultdict(lambda: {"valid": 0, "failed": 0, "timeout": 0, "rmse_values": []})
    implicit_stats = defaultdict(lambda: {"valid": 0, "failed": 0, "timeout": 0, "rmse_values": []})
    
    # Load all experiments
    json_files = list(Path(results_dir).glob("*.json"))
    for json_path in tqdm(json_files, desc="Analyzing experiments"):
        try:
            with open(json_path, 'r') as f:
                experiment = Experiment(**json.load(f))
            
            # Extract system name from experiment folder
            system_name = experiment.generation_params.experiment_folder.split('/')[-1]
            
            # Check if system has no friction (empty damping coefficients)
            has_no_friction = sum(experiment.generation_params.damping_coefficients) == 0
            is_implicit = sum(experiment.generation_params.forces_scale_vector) == 0
            
            # First pass: check if any trajectory is valid in this experiment
            has_any_valid = False
            for traj in experiment.data.validation_group.trajectories:
                if traj.regression_result and traj.name != "validation_data":
                    if traj.regression_result.valid:
                        has_any_valid = True
                        break
            
            # Second pass: collect statistics (only count failures if at least one solution was valid)
            for traj in experiment.data.validation_group.trajectories:


                if traj.regression_result and traj.name != "validation_data":
                    params = traj.regression_result.regression_parameters
                    key = (system_name, params.paradigm, params.regression_type)
                    overall_key = (params.paradigm, params.regression_type)
                    
                    if traj.regression_result.valid:
                        stats[key]["valid"] += 1
                        overall_stats[overall_key]["valid"] += 1
                        if has_no_friction:
                            no_friction_stats[overall_key]["valid"] += 1
                        if is_implicit:
                            implicit_stats[overall_key]["valid"] += 1
                        if traj.regression_result.RMSE_validation_position is not None:
                            stats[key]["rmse_values"].append(traj.regression_result.RMSE_validation_position)
                            overall_stats[overall_key]["rmse_values"].append(traj.regression_result.RMSE_validation_position)
                            if has_no_friction:
                                no_friction_stats[overall_key]["rmse_values"].append(traj.regression_result.RMSE_validation_position)
                            if is_implicit:
                                implicit_stats[overall_key]["rmse_values"].append(traj.regression_result.RMSE_validation_position)
                    else:
                        # Count timeouts
                        if traj.regression_result.timeout:
                            stats[key]["timeout"] += 1
                            overall_stats[overall_key]["timeout"] += 1
                            if has_no_friction:
                                no_friction_stats[overall_key]["timeout"] += 1
                            if is_implicit:
                                implicit_stats[overall_key]["timeout"] += 1
                        # Only count failures if at least one other solution was valid (when flag is enabled)
                        if not only_valid_experiments or has_any_valid:
                            stats[key]["failed"] += 1
                            overall_stats[overall_key]["failed"] += 1
                            if has_no_friction:
                                no_friction_stats[overall_key]["failed"] += 1
                            if is_implicit:
                                implicit_stats[overall_key]["failed"] += 1
        except Exception as e:
            print("Error processing file:", json_path,e)
            continue
    
    # Display results
    clear_screen()
    print(f"\n{'='*90}")
    print(f"EXPERIMENT RESULTS ANALYSIS - BY SYSTEM")
    print(f"{'='*90}\n")
    
    current_system = None
    for (system, paradigm, reg_type), data in sorted(stats.items()):
        if system != current_system:
            if current_system is not None:
                print()
            print(f">>> {system.upper()}")
            current_system = system
        
        valid = data["valid"]
        failed = data["failed"]
        timeout = data["timeout"]
        total = valid + failed
        median_rmse = statistics.median(data["rmse_values"]) if data["rmse_values"] else float('nan')
        
        print(f"  {paradigm:10s} / {reg_type:10s} | Valid: {valid:4d} | Failed: {failed:4d} | Timeout: {timeout:4d} | Total: {total:4d} | Median RMSE: {median_rmse:.6f}")
    
    print(f"\n{'='*90}")
    print(f"OVERALL STATISTICS")
    print(f"{'='*90}\n")
    
    for (paradigm, reg_type), data in sorted(overall_stats.items()):
        valid = data["valid"]
        failed = data["failed"]
        timeout = data["timeout"]
        total = valid + failed
        median_rmse = statistics.median(data["rmse_values"]) if data["rmse_values"] else float('nan')
        
        print(f"{paradigm:10s} / {reg_type:10s} | Valid: {valid:4d} | Failed: {failed:4d} | Timeout: {timeout:4d} | Total: {total:4d} | Median RMSE: {median_rmse:.6f}")
    
    print(f"\n{'='*90}")
    print(f"OVERALL STATISTICS (NO FRICTION SYSTEMS ONLY)")
    print(f"{'='*90}\n")
    
    for (paradigm, reg_type), data in sorted(no_friction_stats.items()):
        valid = data["valid"]
        failed = data["failed"]
        timeout = data["timeout"]
        total = valid + failed
        median_rmse = statistics.median(data["rmse_values"]) if data["rmse_values"] else float('nan')
        
        print(f"{paradigm:10s} / {reg_type:10s} | Valid: {valid:4d} | Failed: {failed:4d} | Timeout: {timeout:4d} | Total: {total:4d} | Median RMSE: {median_rmse:.6f}")
    
    print(f"\n{'='*90}\n")

    print(f"\n{'='*90}")
    print(f"OVERALL STATISTICS (IMPLICIT SYSTEMS ONLY)")
    print(f"{'='*90}\n")
    
    for (paradigm, reg_type), data in sorted(implicit_stats.items()):
        valid = data["valid"]
        failed = data["failed"]
        timeout = data["timeout"]
        total = valid + failed
        median_rmse = statistics.median(data["rmse_values"]) if data["rmse_values"] else float('nan')
        
        print(f"{paradigm:10s} / {reg_type:10s} | Valid: {valid:4d} | Failed: {failed:4d} | Timeout: {timeout:4d} | Total: {total:4d} | Median RMSE: {median_rmse:.6f}")
    
    print(f"\n{'='*90}\n")


if __name__ == "__main__":
    tyro.cli(analyze_results)
