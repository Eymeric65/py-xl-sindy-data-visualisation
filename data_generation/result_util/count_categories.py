#!/usr/bin/env python3
"""
Script to count experiments by damping and force scale vector categories.
"""

import csv
import ast
from collections import defaultdict

def parse_vector(vector_str):
    """Parse a vector string like '[-1.0, -1.0]' into a list of floats."""
    try:
        return ast.literal_eval(vector_str)
    except:
        return None

def is_all_null(vector):
    """Check if all elements in vector are null (0 or 0.0)."""
    if vector is None:
        return None
    return all(v == 0 or v == 0.0 for v in vector)

def is_all_non_null(vector):
    """Check if all elements in vector are non-null (not 0)."""
    if vector is None:
        return None
    return all(v != 0 and v != 0.0 for v in vector)

def is_mixed(vector):
    """Check if vector has both null and non-null elements."""
    if vector is None:
        return None
    has_null = any(v == 0 or v == 0.0 for v in vector)
    has_non_null = any(v != 0 and v != 0.0 for v in vector)
    return has_null and has_non_null

def categorize_experiment(damping_coefficients, force_scale_vector):
    """
    Categorize an experiment based on force scale vectors only.
    
    Categories:
    - explicit: All force scale vectors are non-null
    - implicit: All force scale vectors are null
    - mixed: Force scale vectors are mixed (some null, some non-null)
    
    Also determines damping status:
    - no_damping: All damping coefficients are null
    - damping: At least one damping coefficient is non-null
    """
    damping = parse_vector(damping_coefficients)
    force = parse_vector(force_scale_vector)
    
    if damping is None or force is None:
        return "unknown", "unknown"
    
    # Determine damping status
    damping_all_null = is_all_null(damping)
    damping_status = "no_damping" if damping_all_null else "damping"
    
    # Determine force category
    force_all_null = is_all_null(force)
    force_all_non_null = is_all_non_null(force)
    force_mixed = is_mixed(force)
    
    if force_all_non_null:
        return "explicit", damping_status
    elif force_all_null:
        return "implicit", damping_status
    elif force_mixed:
        return "mixed", damping_status
    
    return "unknown", "unknown"

def main():
    csv_file = '/home/eymeric/py-xl-sindy-data-visualisation/results_database.csv'
    
    # Track unique experiment_ids and their categories
    experiment_data = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            experiment_id = row.get('experiment_id', '')
            
            # Only process if we haven't seen this experiment_id yet
            if experiment_id not in experiment_data:
                experiment_type = row.get('experiment_type', 'unknown')
                damping = row.get('damping_coefficients', '')
                force = row.get('force_scale_vector', '')
                
                category, damping_status = categorize_experiment(damping, force)
                experiment_data[experiment_id] = {
                    'category': category,
                    'damping_status': damping_status,
                    'experiment_type': experiment_type
                }
    
    # Count by category and by system
    category_counts = defaultdict(int)
    damping_category_counts = defaultdict(int)
    system_category_counts = defaultdict(lambda: defaultdict(int))
    
    for exp_data in experiment_data.values():
        category = exp_data['category']
        damping_status = exp_data['damping_status']
        experiment_type = exp_data['experiment_type']
        
        category_counts[category] += 1
        damping_category_counts[f"{category}_{damping_status}"] += 1
        system_category_counts[experiment_type][category] += 1
    
    total = len(experiment_data)
    
    # Print results in table format
    print("=" * 80)
    print("EXPERIMENT COUNTS FOR LATEX TABLE")
    print("=" * 80)
    print()
    
    # Get counts for each system
    cart_pole = system_category_counts['cart_pole']
    cart_pole_double = system_category_counts['cart_pole_double']
    double_pendulum = system_category_counts['double_pendulum_pm']
    
    # Calculate totals
    explicit_total = category_counts['explicit']
    implicit_total = category_counts['implicit']
    mixed_total = category_counts['mixed']
    
    # Print in simple table format
    print("Experiment type            | Cartpole | Cartpole double | Double pendulum | Total")
    print("-" * 80)
    print(f"No Damping explicit        |    {damping_category_counts['explicit_no_damping']//3}    |        {damping_category_counts['explicit_no_damping']//3}        |        {damping_category_counts['explicit_no_damping']//3}        |   {damping_category_counts['explicit_no_damping']}")
    print(f"Damping explicit           |   {cart_pole['explicit']}    |       {cart_pole_double['explicit']}        |       {double_pendulum['explicit']}        |  {explicit_total}")
    print(f"Damping implicit           |   {cart_pole['implicit']}    |       {cart_pole_double['implicit']}        |       {double_pendulum['implicit']}        |  {implicit_total}")
    print(f"Damping mixed              |   {cart_pole['mixed']}    |       {cart_pole_double['mixed']}        |       {double_pendulum['mixed']}        |  {mixed_total}")
    print()
    print("=" * 80)
    print()
    print("FOR LATEX TABLE:")
    print("-" * 80)
    print(f"No Damping explicit & {damping_category_counts['explicit_no_damping']//3} & {damping_category_counts['explicit_no_damping']//3} & {damping_category_counts['explicit_no_damping']//3} & {damping_category_counts['explicit_no_damping']} \\\\")
    print(f"Damping explicit & {cart_pole['explicit']} & {cart_pole_double['explicit']} & {double_pendulum['explicit']} & {explicit_total} \\\\")
    print(f"Damping implicit & {cart_pole['implicit']} & {cart_pole_double['implicit']} & {double_pendulum['implicit']} & {implicit_total} \\\\")
    print(f"Damping mixed & {cart_pole['mixed']} & {cart_pole_double['mixed']} & {double_pendulum['mixed']} & {mixed_total} \\\\")
    print("=" * 80)

if __name__ == '__main__':
    main()
