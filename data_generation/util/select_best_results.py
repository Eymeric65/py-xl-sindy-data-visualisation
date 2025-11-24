#!/usr/bin/env python3
"""
Analyze results_database.csv to help select good examples for visualization.

For each combination of experiment_id and noise_level, prints a sorted list
of solution_type × experiment_type with their validation errors (only valid results).
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def analyze_results(csv_path: str, find_ranking: bool = False):
    """
    Analyze the results database and print sorted results by experiment and noise level.
    
    Args:
        csv_path: Path to the results_database.csv file
        find_ranking: If True, only show experiments with ranking: mixed < sindy < xlsindy
    """
    # Structure: {(experiment_id, noise_level): [(catalog_type, solution_type, validation_error), ...]}
    results_by_combo = defaultdict(list)
    
    # Allowed combinations: (catalog_type, solution_type)
    allowed_combos = {
        ('mixed', 'mixed'),
        ('sindy', 'explicit'),
        ('xlsindy', 'explicit')
    }
    
    # Read the CSV file
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            experiment_id = row['experiment_id']
            noise_level = float(row['noise_level'])
            catalog_type = row['catalog_type']
            solution_type = row['solution_type']
            valid = row['valid'].lower() == 'true'
            
            # Only include valid results
            if not valid:
                continue
            
            # Only include allowed combinations
            if (catalog_type, solution_type) not in allowed_combos:
                continue
            
            try:
                validation_error = float(row['validation_error'])
                end_simulation_time = float(row['end_simulation_time'])
            except (ValueError, KeyError):
                continue
            
            # Store the result
            key = (experiment_id, noise_level)
            results_by_combo[key].append((catalog_type, solution_type, validation_error, end_simulation_time))
    
    # Sort combinations by experiment_id then noise_level
    sorted_combos = sorted(results_by_combo.keys(), key=lambda x: (x[0], x[1]))
    
    # Print results
    if find_ranking:
        print("=" * 120)
        print("EXPERIMENTS WITH RANKING: mixed < sindy")
        print("=" * 120)
        print()
    else:
        print("=" * 120)
        print("VALIDATION RESULTS BY EXPERIMENT AND NOISE LEVEL")
        print("=" * 120)
        print()
    
    found_count = 0
    
    for experiment_id, noise_level in sorted_combos:
        results = results_by_combo[(experiment_id, noise_level)]
        
        # Sort by validation error (ascending)
        results.sort(key=lambda x: x[2])
        
        # If find_ranking is enabled, check if we have both mixed and sindy with correct ranking
        if find_ranking:
            # Create a dict for easy lookup
            error_by_method = {}
            for catalog_type, solution_type, validation_error, end_simulation_time in results:
                error_by_method[catalog_type] = validation_error
            
            # Check if we have at least mixed and sindy
            if 'mixed' not in error_by_method or 'sindy' not in error_by_method:
                continue
            
            # Check if ranking is correct: mixed < sindy
            if not (error_by_method['mixed'] < error_by_method['sindy']):
                continue
            
            # This experiment matches!
            found_count += 1
        
        print(f"Experiment: {experiment_id}")
        print(f"Noise Level: {noise_level}")
        print("-" * 120)
        print(f"{'Catalog Type':<20} {'Solution Type':<20} {'Validation Error':>20} {'End Sim Time':>20}")
        print("-" * 120)
        
        for catalog_type, solution_type, validation_error, end_simulation_time in results:
            print(f"{catalog_type:<20} {solution_type:<20} {validation_error:>20.6f} {end_simulation_time:>20.2f}")
        
        print()
        print()
    
    if find_ranking:
        print(f"Found {found_count} experiments with ranking: mixed < sindy")


def main():
    """Main entry point."""
    
    if len(sys.argv) < 2:
        print("Usage: python select_best_results.py <results_database.csv> [--find-ranking]")
        print("Example: python select_best_results.py results_database.csv")
        print("         python select_best_results.py results_database.csv --find-ranking")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    find_ranking = '--find-ranking' in sys.argv
    
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    analyze_results(csv_path, find_ranking)


if __name__ == "__main__":
    main()
