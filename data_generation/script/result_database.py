#!/usr/bin/env python3
"""
Result Database Compiler

This script compiles all JSON result files into a unified pandas DataFrame where each row
represents a trajectory with all metadata columns extracted from the v2 dataclasses.
For valid solutions, it computes the validation error as the relative difference between 
solution and validation reference series.
"""

import json
import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from tqdm import tqdm
import tyro

from data_generation.script.dataclass import Experiment, TrajectoryData, Series


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_experiment(file_path: str) -> Optional[Experiment]:
    """Load and parse an experiment JSON file safely."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return Experiment(**data)
    except (json.JSONDecodeError, IOError, Exception) as e:
        logging.error(f"Failed to load {file_path}: {e}")
        return None


def extract_experiment_folder_name(experiment_folder: str) -> str:
    """Extract the folder name from the experiment_folder path."""
    return Path(experiment_folder).name


def compute_end_simulation_time(trajectory: TrajectoryData) -> Optional[float]:
    """
    Compute the end simulation time by finding the last non-zero time in the time array.
    
    Args:
        trajectory: TrajectoryData containing the series with time data
        
    Returns:
        The last non-zero time value, or None if no time data found
    """
    try:
        if not trajectory.series or not trajectory.series.time:
            return None
            
        time_array = np.array(trajectory.series.time.time)
        
        if len(time_array) == 0:
            return None
        
        # Find the last non-zero time (or use the last time if all are valid)
        non_zero_times = time_array[time_array > 0]
        if len(non_zero_times) > 0:
            return float(np.max(non_zero_times))
        else:
            # If no positive times, use the last time value
            return float(time_array[-1]) if len(time_array) > 0 else None
        
    except Exception as e:
        logging.warning(f"Error computing end simulation time: {e}")
        return None


def compute_validation_error(trajectory: TrajectoryData) -> Optional[float]:
    """
    Extract the validation error from the trajectory's regression result.
    
    Returns the RMSE_validation_position if available, otherwise None.
    """
    if trajectory.regression_result and trajectory.regression_result.RMSE_validation_position is not None:
        return trajectory.regression_result.RMSE_validation_position
    return None


def extract_trajectory_data(experiment: Experiment, 
                           trajectory: TrajectoryData,
                           validation_reference: Optional[TrajectoryData]) -> Dict[str, Any]:
    """Extract all relevant data from a trajectory into a flat dictionary."""
    
    # Base trajectory info
    experiment_id = experiment.generation_params.UID
    row_data = {
        'experiment_id': experiment_id,
        'trajectory_name': trajectory.name,
        'is_reference': trajectory.reference,
    }
    
    # Extract experiment type from generation params
    row_data['experiment_type'] = extract_experiment_folder_name(
        experiment.generation_params.experiment_folder
    )
    
    # Add generation parameters
    row_data.update({
        'max_time': experiment.generation_params.max_time,
        'sample_number': experiment.generation_params.sample_number,
        'generation_type': experiment.generation_params.generation_type,
        'batch_number': experiment.generation_params.batch_number,
        'damping_coefficients': experiment.generation_params.damping_coefficients,
        'force_scale_vector': experiment.generation_params.forces_scale_vector,
    })
    
    # Extract regression result fields if available
    if trajectory.regression_result:
        rr = trajectory.regression_result
        params = rr.regression_parameters
        
        row_data.update({
            'paradigm': params.paradigm,
            'regression_type': params.regression_type,
            'optimizer': params.optimization_function,
            'noise_level': params.noise_level,
            'data_ratio': params.data_ratio,
            'valid': rr.valid,
            'timeout': rr.timeout,
            'regression_time': rr.regression_time,
            'RMSE_acceleration': rr.RMSE_acceleration,
            'RMSE_validation_position': rr.RMSE_validation_position,
        })
    else:
        # Set defaults if no regression result
        row_data.update({
            'paradigm': None,
            'regression_type': None,
            'optimizer': None,
            'noise_level': None,
            'data_ratio': None,
            'valid': None,
            'timeout': None,
            'regression_time': None,
            'RMSE_acceleration': None,
            'RMSE_validation_position': None,
        })
    
    # Extract validation error from regression result
    validation_error = compute_validation_error(trajectory) if row_data['valid'] else None
    row_data['validation_error'] = validation_error
    
    # Compute end simulation time from the trajectory data
    end_simulation_time = compute_end_simulation_time(trajectory)
    row_data['end_simulation_time'] = end_simulation_time
    
    # Extract solution information if available
    if trajectory.solutions:
        # For now, use the first solution
        solution = trajectory.solutions[0]
        row_data.update({
            'solution_mode': solution.mode_solution,
            'solution_size': len(solution.solution_vector),
        })
    else:
        row_data.update({
            'solution_mode': None,
            'solution_size': None,
        })
    
    return row_data


def process_experiment_file(file_path: str) -> List[Dict[str, Any]]:
    """Process a single experiment JSON file and extract all trajectory data."""
    
    experiment = load_experiment(file_path)
    if not experiment:
        return []
    
    rows = []
    
    try:
        # Get validation reference data
        validation_reference = None
        for traj in experiment.data.validation_group.trajectories:
            if traj.name == "validation_data" or traj.reference:
                validation_reference = traj
                break
        
        # Process each trajectory in validation_group
        for trajectory in experiment.data.validation_group.trajectories:
            # Skip the validation reference itself
            if trajectory.name == "validation_data" or trajectory.reference:
                continue
            
            try:
                row_data = extract_trajectory_data(
                    experiment, 
                    trajectory, 
                    validation_reference
                )
                rows.append(row_data)
                
            except Exception as e:
                logging.warning(f"Error processing trajectory {trajectory.name} in {experiment.generation_params.UID}: {e}")
                continue
                
    except Exception as e:
        logging.error(f"Error processing experiment file {file_path}: {e}")
        return []
    
    return rows


def compile_results_database(results_dir: str, 
                           output_file: str,
                           pattern: str = "*.json",
                           max_files: Optional[int] = None) -> pd.DataFrame:
    """
    Compile all result files into a unified DataFrame.
    
    Args:
        results_dir: Directory containing result JSON files
        output_file: Path to save the compiled DataFrame (CSV format)
        pattern: File pattern to match (default: "*.json")
        max_files: Maximum number of files to process (for testing)
    
    Returns:
        pandas DataFrame with all trajectory data
    """
    
    # Find all result files
    result_files = glob.glob(os.path.join(results_dir, pattern))
    
    # Filter out files.json if present
    result_files = [f for f in result_files if not f.endswith('files.json')]
    
    if max_files:
        result_files = result_files[:max_files]
    
    logging.info(f"Found {len(result_files)} result files to process")
    
    all_rows = []
    
    # Process each file
    for file_path in tqdm(result_files, desc="Processing result files"):
        rows = process_experiment_file(file_path)
        all_rows.extend(rows)
        
        if len(all_rows) % 1000 == 0 and len(all_rows) > 0:
            logging.info(f"Processed {len(all_rows)} trajectories so far...")
    
    # Create DataFrame
    if not all_rows:
        logging.warning("No trajectory data found!")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows)
    
    # Sort by experiment_id and trajectory_name for consistent output
    if 'trajectory_name' in df.columns:
        df = df.sort_values(['experiment_id', 'trajectory_name']).reset_index(drop=True)
    else:
        df = df.sort_values(['experiment_id']).reset_index(drop=True)
    
    # Save to file
    df.to_csv(output_file, index=False)
    logging.info(f"Saved {len(df)} trajectories to {output_file}")
    
    # Print summary statistics
    logging.info(f"\nDatabase Summary:")
    logging.info(f"Total trajectories: {len(df)}")
    logging.info(f"Total experiments: {df['experiment_id'].nunique()}")
    
    if 'valid' in df.columns:
        valid_count = df['valid'].sum()
        logging.info(f"Valid trajectories: {valid_count}")
    
    if 'experiment_type' in df.columns:
        logging.info(f"Unique experiment types: {df['experiment_type'].nunique()}")
        type_counts = df['experiment_type'].value_counts()
        for exp_type, count in type_counts.items():
            logging.info(f"  {exp_type}: {count} trajectories")
    
    if 'paradigm' in df.columns:
        paradigm_counts = df['paradigm'].value_counts()
        logging.info(f"\nTrajectories by paradigm:")
        for paradigm, count in paradigm_counts.items():
            logging.info(f"  {paradigm}: {count}")
    
    if 'validation_error' in df.columns:
        valid_errors = df[df['valid'] == True]['validation_error'].dropna()
        if len(valid_errors) > 0:
            logging.info(f"\nValidation errors computed for {len(valid_errors)} valid trajectories")
            logging.info(f"Mean validation error: {valid_errors.mean():.6f}")
            logging.info(f"Median validation error: {valid_errors.median():.6f}")
    
    return df


def main():
    """Main entry point for the script."""
    @dataclass
    class Args:
        results_dir: str = "results"
        """Directory containing result JSON files"""
        output: str = "results_database.csv"
        """Output CSV file path"""
        pattern: str = "*.json"
        """File pattern to match in results directory"""
        max_files: Optional[int] = None
        """Maximum number of files to process (for testing)"""
        verbose: bool = False
        """Enable verbose logging"""
    
    args = tyro.cli(Args)
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate inputs
    if not os.path.exists(args.results_dir):
        logging.error(f"Results directory not found: {args.results_dir}")
        return 1
    
    # Compile database
    try:
        df = compile_results_database(
            args.results_dir,
            args.output,
            args.pattern,
            args.max_files
        )
        
        if len(df) == 0:
            logging.warning("No data compiled!")
            return 1
        
        logging.info(f"Successfully compiled database with {len(df)} trajectories")
        return 0
        
    except Exception as e:
        logging.error(f"Failed to compile database: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
