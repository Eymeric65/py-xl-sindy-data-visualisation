#!/usr/bin/env python3
"""
Generate manifest file from JSON result files.
This script scans the results directory for .json files and creates a manifest
with metadata extracted from each file's generation_settings.

Usage:
    python3 data_generation/generate_manifest.py
    python3 data_generation/generate_manifest.py --results-dir custom_results
    python3 data_generation/generate_manifest.py --output custom_manifest.json

Output format:
{
  "files": [
    {
      "filename": "hash.json",
      "forces_scale_vector": [5.0, 0.0],
      "experiment_folder": "cart_pole",
      "damping_coefficients": [-0.3, -0.3]
    },
    ...
  ]
}
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Any
from dataclass import Experiment

def extract_experiment_folder_name(experiment_folder: str) -> str:
    """Extract the last part of the experiment folder path after the last slash."""
    return Path(experiment_folder).name

def check_all_solutions_invalid(experiment: 'Experiment') -> bool:
    """
    Check if all solutions in the experiment are invalid.
    
    Args:
        experiment: The experiment object to check
    
    Returns:
        True if all solutions are invalid, False if at least one is valid
    """
    has_solutions = False
    
    # Check both validation_group and training_group
    for group_key in ['validation_group', 'training_group']:
        group = getattr(experiment.data, group_key, None)
        if group is None:
            continue
            
        # Iterate through trajectories
        for traj in group.trajectories:
            # Skip reference trajectories (they don't have regression results)
            if traj.reference:
                continue
                
            # Check if trajectory has solutions and regression results
            if traj.solutions and traj.regression_result:
                has_solutions = True
                
                # If we find at least one valid solution, return False
                if traj.regression_result.valid:
                    return False
    
    # If we found solutions but none were valid, return True
    # If we found no solutions at all, also return True (consider it as failed)
    return has_solutions or True  # True if has_solutions is False (no solutions found)

def generate_manifest(results_dir: str = "results", output_file: str = None) -> Dict[str, Any]:
    """
    Generate manifest from JSON files in the results directory.
    
    Args:
        results_dir: Directory containing the JSON result files
        output_file: Output file path (defaults to results/files.json)
    
    Returns:
        Dictionary containing the manifest data
    """
    if output_file is None:
        output_file = os.path.join(results_dir, "files.json")
    
    # Find all JSON files in results directory (excluding files.json itself)
    json_pattern = os.path.join(results_dir, "*.json")
    json_files = [f for f in glob.glob(json_pattern) 
                  if not f.endswith("files.json")]
    
    manifest_files = []
    
    print(f"Processing {len(json_files)} JSON files...")
    
    for json_file in json_files:
        filename = os.path.basename(json_file)
        print(f"Processing: {filename}")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Parse using Experiment dataclass
            experiment = Experiment(**data)
            
            # Extract required fields from generation_params
            gen_params = experiment.generation_params
            
            # Check if all solutions are invalid
            all_invalid = check_all_solutions_invalid(experiment)
            
            # Create file entry
            file_entry = {
                "filename": filename,
                "forces_scale_vector": gen_params.forces_scale_vector,
                "experiment_folder": extract_experiment_folder_name(gen_params.experiment_folder),
                "damping_coefficients": gen_params.damping_coefficients,
                "all_solutions_invalid": all_invalid
            }
            
            manifest_files.append(file_entry)
            status_icon = "❌" if all_invalid else "✓"
            print(f"  {status_icon} Extracted: experiment={file_entry['experiment_folder']}, "
                  f"forces={gen_params.forces_scale_vector}, damping={gen_params.damping_coefficients}, "
                  f"all_invalid={all_invalid}")
            
        except Exception as e:
            print(f"  ✗ Error processing {filename}: {e}")
            continue
    
    # Create manifest structure
    manifest = {
        "files": manifest_files
    }
    
    # Write manifest file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✓ Manifest generated: {output_file}")
    print(f"  Total files processed: {len(manifest_files)}")
    
    return manifest

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate manifest from JSON result files")
    parser.add_argument("--results-dir", default="results", 
                       help="Directory containing JSON result files (default: results)")
    parser.add_argument("--output", 
                       help="Output manifest file (default: results/files.json)")
    
    args = parser.parse_args()
    
    # Generate manifest
    manifest = generate_manifest(args.results_dir, args.output)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Files processed: {len(manifest['files'])}")
    
    # Group by experiment folder
    experiments = {}
    for file_info in manifest['files']:
        exp = file_info['experiment_folder']
        if exp not in experiments:
            experiments[exp] = 0
        experiments[exp] += 1
    
    print("By experiment:")
    for exp, count in experiments.items():
        print(f"  {exp}: {count} files")

if __name__ == "__main__":
    main()