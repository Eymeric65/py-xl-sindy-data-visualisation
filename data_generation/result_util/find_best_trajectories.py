"""
Script to find the best trajectories (lowest validation error) for different damping/force configurations.
"""

import pandas as pd
import ast
from pathlib import Path
import subprocess
import sys

def parse_vector(vec_str):
    """Parse a vector string to list of floats."""
    return ast.literal_eval(vec_str)

def all_zero(vec):
    """Check if all elements are 0."""
    return all(x == 0.0 for x in vec)

def all_non_zero(vec):
    """Check if all elements are non-zero."""
    return all(x != 0.0 for x in vec)

def mixed_values(vec):
    """Check if vector has mixed zero and non-zero values."""
    has_zero = any(x == 0.0 for x in vec)
    has_non_zero = any(x != 0.0 for x in vec)
    return has_zero and has_non_zero

def categorize_trajectory(row):
    """Categorize trajectory based on damping and force scale vector."""
    damping = parse_vector(row['damping_coefficients'])
    force = parse_vector(row['force_scale_vector'])
    
    damping_all_zero = all_zero(damping)
    damping_non_zero = not all_zero(damping)
    
    force_all_non_zero = all_non_zero(force)
    force_all_zero = all_zero(force)
    force_mixed = mixed_values(force)
    
    if damping_all_zero and force_all_non_zero:
        return "damping_zero_force_nonzero"
    elif damping_non_zero and force_all_non_zero:
        return "damping_nonzero_force_nonzero"
    elif damping_non_zero and force_all_zero:
        return "damping_nonzero_force_zero"
    elif damping_non_zero and force_mixed:
        return "damping_nonzero_force_mixed"
    else:
        return "other"

def main():
    # Check for --plot flag
    plot_results = "--plot" in sys.argv
    
    # Load data
    data_path = "results_database.csv"
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    
    # Filter for mixed paradigm, mixed regression type, noise level 0
    filtered = df[
        (df['paradigm'] == 'mixed') & 
        (df['regression_type'] == 'mixed') & 
        (df['noise_level'] == 0.0) &
        (df['valid'] == True) &
        (df['timeout'] == False)
    ].copy()
    
    print(f"\nFound {len(filtered)} trajectories matching criteria")
    print(f"(paradigm=mixed, regression_type=mixed, noise_level=0, valid=True, timeout=False)")
    
    if plot_results:
        print(f"\n[PLOT MODE ENABLED] Will generate plots for each best trajectory with friends")
    
    # Add category column
    filtered['category'] = filtered.apply(categorize_trajectory, axis=1)
    
    # Get unique experiment types
    experiment_types = filtered['experiment_type'].unique()
    
    # Categories to report
    categories = [
        ("damping_zero_force_nonzero", "Damping all 0, Force all non-null"),
        ("damping_nonzero_force_nonzero", "Damping non-null, Force all non-null"),
        ("damping_nonzero_force_zero", "Damping non-null, Force all null"),
        ("damping_nonzero_force_mixed", "Damping non-null, Force mixed"),
    ]
    
    print("\n" + "="*100)
    print("BEST TRAJECTORIES (LOWEST VALIDATION ERROR) BY CATEGORY AND EXPERIMENT TYPE")
    print("="*100)
    
    for exp_type in sorted(experiment_types):
        print(f"\n{'='*100}")
        print(f"EXPERIMENT TYPE: {exp_type}")
        print(f"{'='*100}")
        
        exp_data = filtered[filtered['experiment_type'] == exp_type]
        
        for cat_key, cat_name in categories:
            cat_data = exp_data[exp_data['category'] == cat_key]
            
            print(f"\n  Category: {cat_name}")
            print(f"  {'-'*90}")
            
            if len(cat_data) == 0:
                print(f"    No trajectories found in this category")
                continue
            
            # Find the row with minimum validation_error
            best_idx = cat_data['validation_error'].idxmin()
            best = cat_data.loc[best_idx]
            
            print(f"    Experiment ID:     {best['experiment_id']}")
            print(f"    Trajectory Name:   {best['trajectory_name']}")
            print(f"    Validation Error:  {best['validation_error']:.6e}")
            print(f"    End Sim Time:      {best['end_simulation_time']:.2f}")
            print(f"    Damping Coeffs:    {best['damping_coefficients']}")
            print(f"    Force Scale Vec:   {best['force_scale_vector']}")
            print(f"    Total in category: {len(cat_data)}")
            
            # Find friend trajectories (same experiment_id, same noise_level, different paradigm/regression_type)
            friends = df[
                (df['experiment_id'] == best['experiment_id']) &
                (df['noise_level'] == best['noise_level']) &
                (df['valid'] == True) &
                (df['timeout'] == False) &
                ((df['paradigm'] != best['paradigm']) | (df['regression_type'] != best['regression_type']))
            ].sort_values('validation_error')
            
            if len(friends) > 0:
                print(f"\n    Friend trajectories (same experiment_id, same noise, other paradigm/regression):")
                for _, friend in friends.iterrows():
                    print(f"      {friend['validation_error']:.6e}, {friend['paradigm']:15s}, {friend['regression_type']:10s}, {friend['trajectory_name']}")
            else:
                print(f"\n    No friend trajectories found")
            
            # Plot if --plot flag is set
            if plot_results:
                # Collect all friend trajectory names
                friend_traj_names = [best['trajectory_name']]
                if len(friends) > 0:
                    friend_traj_names.extend(friends['trajectory_name'].tolist())
                
                # Create output name: category_experimenttype
                output_name = f"{cat_key}_{exp_type}"
                
                # Call plot_experiment_trajectories
                try:
                    cmd = [
                        sys.executable, "-m", 
                        "data_generation.result_util.plot_experiment_trajectories",
                        best['experiment_id']
                    ] + friend_traj_names + ["--output", output_name]
                    
                    print(f"\n    Generating plot: {output_name}...")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"    ✓ Plot generated successfully")
                    else:
                        print(f"    ✗ Plot generation failed: {result.stderr}")
                except Exception as e:
                    print(f"    ✗ Error generating plot: {e}")
    
    print(f"\n{'='*100}\n")

if __name__ == "__main__":
    main()
