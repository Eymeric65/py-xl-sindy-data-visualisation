#!/usr/bin/env python3
"""
Generate align commands for failed experiments.

This script analyzes the result JSON files to identify missing algorithm/regression/noise combinations
and generates the necessary align_data.py commands to rerun only the failed experiments.
"""

import json
import os
import glob
import sys
from typing import List, Dict, Set, Tuple

def check_force_vector_type(forces_scale_vector: List[float]) -> str:
    """
    Determine if force vector has all zeros or at least one non-zero value.
    
    Returns:
        "zero" if all forces are zero (within tolerance)
        "non_zero" if at least one force is non-zero
    """
    tolerance = 1e-10
    has_non_zero = any(abs(f) > tolerance for f in forces_scale_vector)
    return "non_zero" if has_non_zero else "zero"

def get_allowable_regression_types(force_type: str) -> List[str]:
    """
    Get allowable regression types based on force vector type.
    
    Args:
        force_type: "zero" or "non_zero"
        
    Returns:
        List of allowable regression types
    """
    if force_type == "zero":
        return ["implicit", "mixed"]
    else:  # non_zero
        return ["explicit", "mixed"]

def analyze_experiment_file(json_file: str) -> Dict:
    """
    Analyze a single experiment file to find missing combinations.
    
    Returns:
        Dict with experiment info and missing combinations
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    experiment_id = os.path.basename(json_file)[:-5]  # remove .json
    
    try:
        generation_settings = data['generation_settings']
        experiment_folder = generation_settings['experiment_folder']
        forces_scale_vector = generation_settings['forces_scale_vector']
        
        # Check force type and get allowable regression types
        force_type = check_force_vector_type(forces_scale_vector)
        allowable_regression_types = get_allowable_regression_types(force_type)
        
        # Count present solutions
        validation_group = data['visualisation']['validation_group']['data']
        present_count = sum(1 for k, v in validation_group.items() 
                          if k != 'validation_data' and isinstance(v, dict) and 'extra_info' in v)
        
        # Generate all expected combinations
        algorithms = ["mixed", "xlsindy", "sindy"]
        noise_levels = [0.0, 0.01, 0.1, 0.001]
        
        expected_combinations = []
        for alg in algorithms:
            for reg_type in allowable_regression_types:
                for noise in noise_levels:
                    expected_combinations.append((alg, reg_type, noise))
        
        expected_count = len(expected_combinations)
        missing_count = expected_count - present_count
        
        # If we have missing solutions, assume they are the missing algorithm runs
        # Since we can see that the basic regression_type/noise combinations exist,
        # but we're missing algorithm variants
        missing_combinations = []
        
        if missing_count > 0:
            # We know which regression_type/noise combinations should exist
            expected_basic_combinations = set()
            for reg_type in allowable_regression_types:
                for noise in noise_levels:
                    expected_basic_combinations.add((reg_type, noise))
            
            # Get present combinations
            present_combinations = set()
            for key, value in validation_group.items():
                if key != 'validation_data' and isinstance(value, dict) and 'extra_info' in value:
                    extra_info = value['extra_info']
                    combo = (
                        extra_info.get('regression_type'),
                        extra_info.get('noise_level')
                    )
                    if combo[0] is not None and combo[1] is not None:
                        present_combinations.add(combo)
            
            # Calculate how many algorithm runs we're missing per combination
            algorithms_per_combo = present_count // len(present_combinations) if present_combinations else 1
            missing_algorithms_per_combo = len(algorithms) - algorithms_per_combo
            
            # Generate missing combinations
            # Assume we're missing the more complex algorithms (mixed, xlsindy) more often
            for reg_type, noise in expected_basic_combinations:
                for i, alg in enumerate(algorithms):
                    if i >= algorithms_per_combo:  # Missing algorithms
                        missing_combinations.append((alg, reg_type, noise))
        
        return {
            'experiment_id': experiment_id,
            'experiment_folder': experiment_folder,
            'force_type': force_type,
            'allowable_regression_types': allowable_regression_types,
            'present_count': present_count,
            'expected_count': expected_count,
            'missing_combinations': missing_combinations,
            'has_failures': len(missing_combinations) > 0
        }
        
    except Exception as e:
        print(f"Error processing {experiment_id}: {e}")
        return {
            'experiment_id': experiment_id,
            'error': str(e),
            'has_failures': False,
            'missing_combinations': []
        }

def generate_align_command(experiment_id: str, algorithm: str, regression_type: str, noise_level: float) -> str:
    """
    Generate the align_data.py command for a specific combination.
    
    Returns:
        Command string
    """
    cmd_parts = [
        "python -m data_generation.script.align_data",
        f"--experiment-file results/{experiment_id}",
        f"--algorithm {algorithm}",
        f"--regression-type {regression_type}",
        f"--noise-level {noise_level}",
        "--optimization-function lasso_regression",
        "--data-ratio 2",
        "--random-seed 1"
    ]
    
    return " ".join(cmd_parts)

def main():
    """Main function to analyze all experiments and generate commands."""
    
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        print(f"Error: Results directory '{results_dir}' not found!")
        sys.exit(1)
    
    # Find all JSON files
    json_files = glob.glob(os.path.join(results_dir, "*.json"))
    json_files = [f for f in json_files if not f.endswith('files.json')]
    
    print(f"Analyzing {len(json_files)} experiment files...")
    
    failed_experiments = []
    total_missing = 0
    
    # Analyze each experiment
    for json_file in json_files:
        result = analyze_experiment_file(json_file)
        
        if result['has_failures']:
            failed_experiments.append(result)
            total_missing += len(result['missing_combinations'])
            
            print(f"FAILED: {result['experiment_id'][:8]}... - {len(result['missing_combinations'])}/{result['expected_count']} missing combinations")
    
    print(f"\nSUMMARY:")
    print(f"Total experiments analyzed: {len(json_files)}")
    print(f"Experiments with failures: {len(failed_experiments)}")
    print(f"Total missing combinations: {total_missing}")
    
    # Generate commands file
    output_file = "failed_experiments_commands.txt"
    
    with open(output_file, 'w') as f:
        f.write("# Failed Experiments - Align Commands to Rerun\n")
        f.write("# Generated automatically from missing experiment combinations\n")
        f.write(f"# Total experiments with failures: {len(failed_experiments)}\n")
        f.write(f"# Total missing combinations: {total_missing}\n")
        f.write("# \n")
        f.write("# Usage: Copy and paste these commands to rerun failed experiments\n")
        f.write("# Or use: bash failed_experiments_commands.txt\n")
        f.write("\n")
        
        for exp_info in failed_experiments:
            exp_id = exp_info['experiment_id']
            folder = exp_info['experiment_folder'].split('/')[-1] if 'experiment_folder' in exp_info else 'unknown'
            force_type = exp_info.get('force_type', 'unknown')
            
            f.write(f"\n# Experiment: {exp_id}\n")
            f.write(f"# Folder: {folder}, Force type: {force_type}\n")
            f.write(f"# Missing {len(exp_info['missing_combinations'])} combinations:\n")
            
            for alg, reg_type, noise in exp_info['missing_combinations']:
                cmd = generate_align_command(exp_id, alg, reg_type, noise)
                f.write(f"{cmd}\n")
    
    print(f"\nGenerated commands file: {output_file}")
    print(f"You can run the failed experiments with:")
    print(f"  bash {output_file}")
    print(f"\nOr run individual commands from the file.")

if __name__ == "__main__":
    main()