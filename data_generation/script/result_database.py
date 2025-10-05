#!/usr/bin/env python3
"""
Result Database Compiler

This script compiles all JSON result files into a unified pandas DataFrame where each row
represents a solution with all metadata columns extracted from extra_info and generation_settings.
For valid solutions, it computes the validation error as the relative difference between 
solution and validation reference series.
"""

import json
import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import logging
from tqdm import tqdm


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file safely."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to load {file_path}: {e}")
        return None


def extract_experiment_folder_name(experiment_folder: str) -> str:
    """Extract the folder name from the experiment_folder path."""
    return Path(experiment_folder).name


def compute_validation_error(solution_series: Dict[str, Any], 
                           validation_reference: Dict[str, Any]) -> Optional[float]:
    """
    Compute the relative validation error between solution and validation reference.
    
    Returns the mean relative error: mean(|solution - validation| / |validation|)
    for all coordinate components (qpos, qvel, qacc, forces).
    """
    try:
        total_errors = []
        
        # Process each coordinate (coor_0, coor_1, coor_2, etc.)
        for coord_key in solution_series.keys():
            if coord_key not in validation_reference:
                continue
                
            sol_coord = solution_series[coord_key]
            val_coord = validation_reference[coord_key]
            
            # Process each component (qpos, qvel, qacc, forces)
            for component in ['qpos', 'qvel', 'qacc', 'forces']:
                if component not in sol_coord or component not in val_coord:
                    continue
                    
                sol_data = np.array(sol_coord[component])
                val_data = np.array(val_coord[component])
                
                # Ensure arrays have the same shape
                min_len = min(len(sol_data), len(val_data))
                if min_len == 0:
                    continue
                    
                sol_data = sol_data[:min_len]
                val_data = val_data[:min_len]
                
                # Avoid division by zero
                mask = np.abs(val_data) > 1e-12
                if np.any(mask):
                    rel_error = np.abs(sol_data[mask] - val_data[mask]) / np.abs(val_data[mask])
                    total_errors.extend(rel_error.flatten())
        
        return np.mean(total_errors) if total_errors else None
        
    except Exception as e:
        logging.warning(f"Error computing validation error: {e}")
        return None


def extract_solution_data(experiment_id: str, 
                         solution_id: str, 
                         solution_data: Dict[str, Any],
                         validation_reference: Optional[Dict[str, Any]],
                         generation_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract all relevant data from a solution into a flat dictionary."""
    
    # Extract catalog_type from solution structure
    catalog_type = None
    solution_info = solution_data.get('solution', {})
    if solution_info:
        # The catalog_type is the key in the solution dict (mixed, xlsindy, sindy, etc.)
        catalog_type = list(solution_info.keys())[0] if solution_info else None
    
    # Base solution info
    row_data = {
        'experiment_id': experiment_id,
        'solution_id': solution_id,
        'catalog_type': catalog_type,
    }
    
    # Extract essential extra_info fields
    extra_info = solution_data.get('extra_info', {})
    row_data.update({
        'solution_type': extra_info.get('regression_type'),  # solution type (explicit, implicit, mixed)
        'optimizer': extra_info.get('optimization_function'),  # optimizer (lasso_regression, etc.)
        'noise_level': extra_info.get('noise_level'),
        'valid': extra_info.get('valid'),
        'timeout': extra_info.get('timeout'),
    })
    
    # Extract essential generation settings
    row_data.update({
        'experiment_type': extract_experiment_folder_name(generation_settings.get('experiment_folder', '')),
    })
    
    # Compute validation error if valid and validation reference available
    validation_error = None
    if (row_data['valid'] and 
        validation_reference and 
        'series' in solution_data and 
        'series' in validation_reference):
        
        validation_error = compute_validation_error(
            solution_data['series'], 
            validation_reference['series']
        )
    
    row_data['validation_error'] = validation_error
    
    return row_data


def process_experiment_file(file_path: str) -> List[Dict[str, Any]]:
    """Process a single experiment JSON file and extract all solution data."""
    
    data = load_json_file(file_path)
    if not data:
        return []
    
    experiment_id = Path(file_path).stem
    rows = []
    
    try:
        generation_settings = data.get('generation_settings', {})
        validation_group = data.get('visualisation', {}).get('validation_group', {}).get('data', {})
        
        # Get validation reference data
        validation_reference = validation_group.get('validation_data')
        
        # Process each solution in validation_group
        for key, solution_data in validation_group.items():
            # Skip validation_data key and any non-solution entries
            if key == 'validation_data' or not isinstance(solution_data, dict):
                continue
            
            # Check if this looks like a solution (has extra_info)
            if 'extra_info' not in solution_data:
                continue
            
            solution_id = key
            
            try:
                row_data = extract_solution_data(
                    experiment_id, 
                    solution_id, 
                    solution_data, 
                    validation_reference, 
                    generation_settings
                )
                rows.append(row_data)
                
            except Exception as e:
                logging.warning(f"Error processing solution {solution_id} in {experiment_id}: {e}")
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
        pandas DataFrame with all solution data
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
            logging.info(f"Processed {len(all_rows)} solutions so far...")
    
    # Create DataFrame
    if not all_rows:
        logging.warning("No solution data found!")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows)
    
    # Sort by experiment_id and solution_id for consistent output
    df = df.sort_values(['experiment_id', 'solution_id']).reset_index(drop=True)
    
    # Save to file
    df.to_csv(output_file, index=False)
    logging.info(f"Saved {len(df)} solutions to {output_file}")
    
    # Print summary statistics
    logging.info(f"\nDatabase Summary:")
    logging.info(f"Total solutions: {len(df)}")
    logging.info(f"Total experiments: {df['experiment_id'].nunique()}")
    logging.info(f"Valid solutions: {df['valid'].sum() if 'valid' in df.columns else 'N/A'}")
    logging.info(f"Unique experiment types: {df['experiment_type'].nunique() if 'experiment_type' in df.columns else 'N/A'}")
    
    if 'experiment_type' in df.columns:
        type_counts = df['experiment_type'].value_counts()
        for exp_type, count in type_counts.items():
            logging.info(f"  {exp_type}: {count} solutions")
    
    if 'validation_error' in df.columns:
        valid_errors = df[df['valid'] == True]['validation_error'].dropna()
        if len(valid_errors) > 0:
            logging.info(f"Validation errors computed for {len(valid_errors)} valid solutions")
            logging.info(f"Mean validation error: {valid_errors.mean():.6f}")
            logging.info(f"Median validation error: {valid_errors.median():.6f}")
    
    return df


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Compile result JSON files into a unified pandas DataFrame",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Directory containing result JSON files'
    )
    
    parser.add_argument(
        '--output',
        default='results_database.csv',
        help='Output CSV file path'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.json',
        help='File pattern to match in results directory'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to process (for testing)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
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
        
        logging.info(f"Successfully compiled database with {len(df)} solutions")
        return 0
        
    except Exception as e:
        logging.error(f"Failed to compile database: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
