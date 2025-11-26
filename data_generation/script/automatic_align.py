#!/usr/bin/env python3
"""
Automatic batch alignment script that launches align_data.py on multiple experiments.

This script processes all result JSON and PKL files, launching alignment for each algorithm
(mixed, xlsindy, sindy) and each allowable regression type based on the force scale vector:
- For zero force vectors: only implicit and mixed regression
- For non-zero force vectors: only explicit and mixed regression

Users can constrain the batch with CLI arguments to run only specific algorithms,
regression types, and noise levels.
"""

import os
import json
import glob
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Set
import tyro
from pathlib import Path
import logging
from tqdm import tqdm
import concurrent.futures
import time


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Args:
    results_dir: str = "results"
    """Directory containing the result JSON files"""
    
    results_data_dir: str = "results_data"
    """Directory containing the result PKL files"""
    
    algorithms: List[str] = field(default_factory=lambda: ["mixed", "xlsindy", "sindy"])
    """List of algorithms to run alignment for (default: all)"""
    
    regression_types: List[str] = field(default_factory=lambda: ["implicit", "explicit", "mixed"])
    """List of regression types to run alignment for (default: all allowable based on force vector)"""
    
    noise_levels: List[float] = field(default_factory=lambda: [0.0, 0.01, 0.05, 0.1])
    """List of noise levels to test"""
    
    optimization_function: str = "lasso_regression"
    """The regression function to use"""
    
    random_seed: List[int] = field(default_factory=lambda: [0])
    """Random seed for noise generation"""
    
    data_ratio: float = 2.0
    """Ratio of data to use (relative to catalog size)"""
    
    skip_already_done: bool = True
    """Skip experiments already present in result files"""
    
    max_workers: int = 1
    """Maximum number of parallel workers"""
    
    dry_run: bool = False
    """Print commands without executing them"""
    
    verbose: bool = False
    """Enable verbose output"""
    
    experiment_folders: List[str] = field(default_factory=lambda: ["cart_pole", "double_pendulum_pm", "cart_pole_double"])
    """Filter experiments by folder name (last component after slash). Default: all supported folders"""

def extract_experiment_folder_name(experiment_folder: str) -> str:
    """
    Extract the last component of experiment folder path.
    
    Args:
        experiment_folder: Full path like "data_generation/mujoco_align_data/cart_pole"
        
    Returns:
        Last component like "cart_pole"
    """
    return experiment_folder.split('/')[-1]

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

def get_allowable_regression_types(force_type: str, requested_types: List[str]) -> List[str]:
    """
    Get allowable regression types based on force vector type and user constraints.
    
    Args:
        force_type: "zero" or "non_zero"
        requested_types: User-requested regression types
        
    Returns:
        List of allowable regression types
    """
    if force_type == "zero":
        allowable = ["implicit", "mixed"]
    else:  # non_zero
        allowable = ["explicit", "mixed"]
    
    # Return intersection of allowable and requested types
    return [t for t in requested_types if t in allowable]

def find_result_files(results_dir: str, results_data_dir: str) -> List[dict]:
    """
    Find all result JSON files and match them with corresponding PKL files.
    
    Returns:
        List of dicts with 'json_path', 'pkl_path', and 'experiment_id'
    """
    json_pattern = os.path.join(results_dir, "*.json")
    json_files = glob.glob(json_pattern)
    
    result_files = []
    
    for json_path in json_files:
        # Extract experiment ID from filename (without extension)
        experiment_id = os.path.splitext(os.path.basename(json_path))[0]
        pkl_path = os.path.join(results_data_dir, f"{experiment_id}.pkl")
        
        # Check if corresponding PKL file exists
        if os.path.exists(pkl_path):
            result_files.append({
                'json_path': json_path,
                'pkl_path': pkl_path,
                'experiment_id': experiment_id
            })
        else:
            logger.warning(f"PKL file not found for {experiment_id}")
    
    return result_files

def load_experiment_metadata(json_path: str) -> dict:
    """Load experiment metadata from JSON file."""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading {json_path}: {e}")
        return {}

def build_align_command(
    experiment_file: str, 
    algorithm: str, 
    regression_type: str, 
    noise_level: float,
    args: Args
) -> List[str]:
    """
    Build the command line for align_data.py
    
    Args:
        experiment_file: Path to experiment file (without extension)
        algorithm: Algorithm name (mixed, xlsindy, sindy)
        regression_type: Regression type (implicit, explicit, mixed)
        noise_level: Noise level to add
        args: CLI arguments
        
    Returns:
        Command as list of strings
    """
    cmd = [
        "cpulimit", "-l", "1000", "--",  # Limit CPU usage to 2000%
        sys.executable, "-m", "data_generation.script.align_data",
        "--experiment-file", experiment_file,
        "--algorithm", algorithm,
        "--regression-type", regression_type,
        "--noise-level", str(noise_level),
        "--optimization-function", args.optimization_function,
        "--data-ratio", str(args.data_ratio)
    ]
    
    # Add random seed
    for seed in args.random_seed:
        cmd.extend(["--random-seed", str(seed)])
    
    if args.skip_already_done:
        cmd.append("--skip-already-done")
    
    return cmd

def run_single_alignment(cmd: List[str], args: Args) -> dict:
    """
    Run a single alignment command.
    
    Returns:
        Dict with execution results
    """
    if args.dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return {"success": True, "dry_run": True}
    
    try:
        if args.verbose:
            logger.info(f"Executing: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=3600  # 60 minute timeout per alignment
        )
        end_time = time.time()
        
        success = result.returncode == 0
        
        if not success and args.verbose:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"STDERR: {result.stderr}")
        
        return {
            "success": success,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": end_time - start_time,
            "command": " ".join(cmd)
        }
        
    except subprocess.TimeoutExpired:

        #Register the timeout
        cmd += ["--timeout-signal"]
        subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120
        )

        logger.error(f"Command timed out: {' '.join(cmd)}")
        return {"success": False, "error": "timeout", "command": " ".join(cmd)}
    except Exception as e:
        logger.error(f"Unexpected error running command: {e}")
        return {"success": False, "error": str(e), "command": " ".join(cmd)}

def process_experiment(experiment_info: dict, args: Args) -> List[dict]:
    """
    Process a single experiment file, generating all required alignment commands.
    
    Args:
        experiment_info: Dict with experiment file paths and metadata
        args: CLI arguments
        
    Returns:
        List of execution results
    """
    json_path = experiment_info['json_path']
    experiment_id = experiment_info['experiment_id']
    
    # Load experiment metadata
    metadata = load_experiment_metadata(json_path)
    if not metadata:
        logger.error(f"Failed to load metadata for {experiment_id}")
        return []
    
    # Check if experiment folder matches filter
    try:
        experiment_folder = metadata['generation_settings']['experiment_folder']
        folder_name = extract_experiment_folder_name(experiment_folder)
        
        if folder_name not in args.experiment_folders:
            if args.verbose:
                logger.info(f"Skipping {experiment_id}: folder '{folder_name}' not in filter {args.experiment_folders}")
            return []
            
    except KeyError:
        logger.error(f"No experiment_folder found in {experiment_id}")
        return []
    
    # Get force scale vector from generation settings
    try:
        forces_scale_vector = metadata['generation_settings']['forces_scale_vector']
    except KeyError:
        logger.error(f"No forces_scale_vector found in {experiment_id}")
        return []
    
    # Determine force type and allowable regression types
    force_type = check_force_vector_type(forces_scale_vector)
    allowable_regression_types = get_allowable_regression_types(force_type, args.regression_types)
    
    if args.verbose:
        logger.info(f"Processing {experiment_id} [{folder_name}]: force_type={force_type}, "
                   f"allowable_regression_types={allowable_regression_types}")
    
    # Generate all combinations of parameters
    results = []
    experiment_file = os.path.join(args.results_dir, experiment_id)  # Without extension
    
    for algorithm in args.algorithms:
        for regression_type in allowable_regression_types:
            for noise_level in args.noise_levels:
                cmd = build_align_command(
                    experiment_file, algorithm, regression_type, noise_level, args
                )
                result = run_single_alignment(cmd, args)
                result.update({
                    "experiment_id": experiment_id,
                    "algorithm": algorithm,
                    "regression_type": regression_type,
                    "noise_level": noise_level,
                    "force_type": force_type
                })
                results.append(result)
    
    return results

def print_summary(all_results: List[dict]):
    """Print execution summary statistics."""
    if not all_results:
        print("No results to summarize.")
        return
    
    total = len(all_results)
    successful = sum(1 for r in all_results if r.get("success", False))
    failed = total - successful
    
    print(f"\n{'='*60}")
    print(f"EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total alignments: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/total*100:.1f}%")
    
    if failed > 0:
        print(f"\nFAILED ALIGNMENTS:")
        for result in all_results:
            if not result.get("success", False):
                exp_id = result.get("experiment_id", "unknown")
                alg = result.get("algorithm", "unknown")
                reg = result.get("regression_type", "unknown")
                noise = result.get("noise_level", "unknown")
                error = result.get("error", "unknown error")
                print(f"  - {exp_id} [{alg}/{reg}/noise={noise}]: {error}")
    
    # Execution time statistics
    exec_times = [r.get("execution_time", 0) for r in all_results if "execution_time" in r]
    if exec_times:
        avg_time = sum(exec_times) / len(exec_times)
        total_time = sum(exec_times)
        print(f"\nTIMING:")
        print(f"Average alignment time: {avg_time:.2f} seconds")
        print(f"Total execution time: {total_time:.2f} seconds")

def main():
    """Main execution function."""
    args = tyro.cli(Args)
    
    # Validate directories
    if not os.path.exists(args.results_dir):
        logger.error(f"Results directory not found: {args.results_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.results_data_dir):
        logger.error(f"Results data directory not found: {args.results_data_dir}")
        sys.exit(1)
    
    # Find all experiment files
    logger.info("Scanning for experiment files...")
    experiment_files = find_result_files(args.results_dir, args.results_data_dir)
    
    if not experiment_files:
        logger.error("No experiment files found!")
        sys.exit(1)
    
    logger.info(f"Found {len(experiment_files)} experiment files")
    
    # Estimate total number of alignments
    total_alignments = 0
    for exp_info in experiment_files:
        metadata = load_experiment_metadata(exp_info['json_path'])
        if metadata and 'generation_settings' in metadata:
            forces = metadata['generation_settings'].get('forces_scale_vector', [])
            force_type = check_force_vector_type(forces)
            allowable_types = get_allowable_regression_types(force_type, args.regression_types)
            total_alignments += len(args.algorithms) * len(allowable_types) * len(args.noise_levels)
    
    logger.info(f"Total alignments to run: {total_alignments}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual alignments will be executed")
    
    # Process experiments
    all_results = []
    
    if args.max_workers == 1:
        # Sequential processing
        for exp_info in tqdm(experiment_files, desc="Processing experiments"):
            results = process_experiment(exp_info, args)
            all_results.extend(results)
    else:
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = []
            for exp_info in experiment_files:
                future = executor.submit(process_experiment, exp_info, args)
                futures.append(future)
            
            # Collect results with progress bar
            for future in tqdm(concurrent.futures.as_completed(futures), 
                             total=len(futures), desc="Processing experiments"):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error processing experiment: {e}")
    
    # Print summary
    print_summary(all_results)
    
    # Save detailed results if requested
    if args.verbose and not args.dry_run:
        results_file = "automatic_align_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"Detailed results saved to {results_file}")

if __name__ == "__main__":
    main()
