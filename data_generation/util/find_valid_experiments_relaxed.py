#!/usr/bin/env python3
"""
Find experiments with valid results for specific catalog/solution type combinations.

This script analyzes the results_database.csv to find experiment_ids where:
- valid is True (timeout can be True or False)
For ALL of the following combinations simultaneously:
- (mixed, mixed)
- (xlsindy, explicit)
- (sindy, explicit)

Groups results by noise_level showing experiments that have all three combos valid.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def find_valid_experiments(csv_path: str) -> tuple:
    """
    Find experiments where ALL target combinations are valid (relaxed - timeout allowed).
    
    Args:
        csv_path: Path to results_database.csv
        
    Returns:
        Tuple of (common_experiments, all_results, experiment_types, validation_errors, end_sim_times)
        - common_experiments: {noise_level: set of experiment_ids with all combos valid}
        - all_results: {(catalog_type, solution_type): {noise_level: [experiment_ids]}}
        - experiment_types: {experiment_id: experiment_type}
        - validation_errors: {(experiment_id, noise_level, combo): validation_error}
        - end_sim_times: {(experiment_id, noise_level, combo): end_simulation_time}
    """
    # Target combinations
    target_combos = [
        ("mixed", "mixed"),
        ("xlsindy", "explicit"),
        ("sindy", "explicit")
    ]
    
    # Store results: {(catalog_type, solution_type): {noise_level: set of experiment_ids}}
    all_results = defaultdict(lambda: defaultdict(set))
    
    # Store experiment types: {experiment_id: experiment_type}
    experiment_types = {}
    
    # Store validation errors: {(experiment_id, noise_level, combo): validation_error}
    validation_errors = {}
    
    # Store end simulation times: {(experiment_id, noise_level, combo): end_simulation_time}
    end_sim_times = {}
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            catalog_type = row['catalog_type']
            solution_type = row['solution_type']
            combo = (catalog_type, solution_type)
            
            experiment_id = row['experiment_id']
            experiment_type = row['experiment_type']
            
            # Store experiment type
            if experiment_id not in experiment_types:
                experiment_types[experiment_id] = experiment_type
            
            # Check if this is one of our target combinations
            if combo not in target_combos:
                continue
            
            # Only check if valid is True (relaxed - allow timeout)
            valid = row['valid'].strip().lower() == 'true'
            
            if valid:
                noise_level = float(row['noise_level'])
                validation_error = row.get('validation_error', '')
                end_sim_time = row.get('end_simulation_time', '')
                
                # Store validation error and end_simulation_time
                key = (experiment_id, noise_level, combo)
                validation_errors[key] = validation_error
                end_sim_times[key] = end_sim_time
                
                all_results[combo][noise_level].add(experiment_id)
    
    # Find experiments that have ALL three combinations valid for each noise level
    common_experiments = defaultdict(set)
    
    # Get all noise levels
    all_noise_levels = set()
    for combo_data in all_results.values():
        all_noise_levels.update(combo_data.keys())
    
    for noise_level in all_noise_levels:
        # Get experiment sets for each combo at this noise level
        sets = []
        for combo in target_combos:
            if noise_level in all_results[combo]:
                sets.append(all_results[combo][noise_level])
            else:
                sets.append(set())
        
        # Find intersection (experiments valid for ALL combos)
        if sets:
            common = sets[0].intersection(*sets[1:]) if len(sets) > 1 else sets[0]
            if common:
                common_experiments[noise_level] = common
    
    return common_experiments, all_results, experiment_types, validation_errors, end_sim_times


def print_results(common_experiments: dict, all_results: dict, experiment_types: dict, validation_errors: dict, end_sim_times: dict):
    """Print the results in a readable format."""
    
    # Target combinations for display
    target_combos = [
        ("mixed", "mixed"),
        ("xlsindy", "explicit"),
        ("sindy", "explicit")
    ]
    
    print("=" * 80)
    print("EXPERIMENTS WITH ALL COMBINATIONS VALID (relaxed - timeout allowed)")
    print("=" * 80)
    print()
    print("Target combinations:")
    print("  1. (mixed, mixed)")
    print("  2. (xlsindy, explicit)")
    print("  3. (sindy, explicit)")
    print()
    print("=" * 80)
    print()
    
    if not common_experiments:
        print("✗ No experiments found where ALL three combinations are valid simultaneously.")
        print()
        return
    
    # Print experiments with all combos valid, grouped by noise level
    for noise_level in sorted(common_experiments.keys()):
        experiment_ids = sorted(common_experiments[noise_level])
        print(f"Noise Level: {noise_level}")
        print(f"  Count: {len(experiment_ids)} experiments with ALL combos valid")
        print(f"  Experiment IDs:")
        for exp_id in experiment_ids:
            exp_type = experiment_types.get(exp_id, "unknown")
            print(f"    - {exp_id} (type: {exp_type})")
            
            # Print validation errors and end_simulation_time for each combo
            for combo in target_combos:
                catalog_type, solution_type = combo
                key = (exp_id, noise_level, combo)
                val_error = validation_errors.get(key, "N/A")
                end_sim = end_sim_times.get(key, "N/A")
                
                # Format validation error
                val_error_str = "N/A"
                if val_error:
                    try:
                        val_error_float = float(val_error)
                        val_error_str = f"{val_error_float:.6f}"
                    except (ValueError, TypeError):
                        val_error_str = str(val_error)
                
                # Format end_simulation_time
                end_sim_str = "N/A"
                if end_sim:
                    try:
                        end_sim_float = float(end_sim)
                        end_sim_str = f"{end_sim_float:.2f}s"
                    except (ValueError, TypeError):
                        end_sim_str = str(end_sim)
                
                print(f"        ({catalog_type:8s}, {solution_type:8s}): val_error={val_error_str:>12s}, end_sim_time={end_sim_str:>8s}")
            print()
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_experiments = sum(len(exps) for exps in common_experiments.values())
    print(f"✓ Total: {total_experiments} experiments where ALL 3 combinations are valid")
    print(f"  Across {len(common_experiments)} noise levels: {sorted(common_experiments.keys())}")
    print()
    
    # Group by experiment type
    exp_types_summary = defaultdict(set)
    for exps in common_experiments.values():
        for exp_id in exps:
            exp_type = experiment_types.get(exp_id, "unknown")
            exp_types_summary[exp_type].add(exp_id)
    
    print("Breakdown by experiment type:")
    for exp_type, exp_ids in sorted(exp_types_summary.items()):
        print(f"  - {exp_type}: {len(exp_ids)} unique experiments")
    print()
    
    # Show breakdown by combo for context
    print("Individual combination stats (for context):")
    
    for combo in target_combos:
        catalog_type, solution_type = combo
        if combo in all_results:
            total = sum(len(exp_ids) for exp_ids in all_results[combo].values())
            noise_levels = sorted(all_results[combo].keys())
            print(f"  - ({catalog_type}, {solution_type}): {total} valid experiments")
        else:
            print(f"  - ({catalog_type}, {solution_type}): 0 valid experiments")
    
    print()


def main():
    """Main entry point."""
    # Default path to CSV (relative to script location)
    default_csv = Path(__file__).parent.parent.parent / "results_database.csv"
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else str(default_csv)
    
    if not Path(csv_path).exists():
        print(f"Error: CSV file not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading database from: {csv_path}")
    print()
    
    common_experiments, all_results, experiment_types, validation_errors, end_sim_times = find_valid_experiments(csv_path)
    print_results(common_experiments, all_results, experiment_types, validation_errors, end_sim_times)


if __name__ == "__main__":
    main()
