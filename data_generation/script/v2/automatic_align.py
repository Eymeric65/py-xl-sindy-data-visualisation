#!/usr/bin/env python3
"""
Automatic batch alignment script that launches align_data.py on multiple experiments.

This script processes all experiment JSON files and launches alignment for each configuration.
- For zero force vectors: only implicit and mixed regression types are allowed
- For non-zero force vectors: only explicit and mixed regression types are allowed
"""

import os
import json
import subprocess
import sys
from typing import List, Iterator
from pathlib import Path
import logging
from tqdm import tqdm
import tyro
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field
from data_generation.script.v2.dataclass import Experiment, RegressionParameter

tqdm.monitor_interval = 2

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ParadigmRegressionCombo(BaseModel):
    """Combination of paradigm and regression type"""
    paradigm: str
    regression_type: str


class AutomaticAlignConfig(BaseModel):
    """Configuration for automatic alignment batch processing"""
    
    results_dir: str = "results"
    """Directory containing the result JSON files"""
    
    results_data_dir: str = "results_data"
    """Directory containing the result PKL files"""
    
    combos: List[ParadigmRegressionCombo] = Field(
        default_factory=lambda: [
            ParadigmRegressionCombo(paradigm="mixed", regression_type="mixed"),
            ParadigmRegressionCombo(paradigm="sindy", regression_type="explicit"),
            ParadigmRegressionCombo(paradigm="xlsindy", regression_type="explicit"),
            ParadigmRegressionCombo(paradigm="sindy", regression_type="implicit"),
        ]
    )
    """List of paradigm/regression_type combinations to run alignment for"""
    
    noise_levels: List[float] = Field(default_factory=lambda: [0.0, 0.01, 0.05, 0.1])
    """List of noise levels to test"""
    
    optimization_function: str = "lasso_regression"
    """The optimization function to use"""
    
    random_seeds: List[int] = Field(default_factory=lambda: [0])
    """Random seeds for noise generation"""
    
    data_ratio: float = 2.0
    """Ratio of data to use (relative to catalog size)"""
    
    skip_already_done: bool = True
    """Skip experiments already processed"""
    
    dry_run: bool = False
    """Print commands without executing them"""
    
    max_workers: int = 1
    """Maximum number of parallel workers (1 = sequential)"""
    
    experiment_folders: List[str] = Field(default_factory=list)
    """Filter experiments by folder name. Empty list means all folders"""
    
    cpu_limit: int = 750
    """CPU limit percentage for cpulimit"""
    
    timeout: int = 3600
    """Timeout in seconds for each alignment"""

class AlignmentTask(BaseModel):
    """Represents a single alignment task"""
    
    experiment_id: str
    """Experiment UID"""
    
    experiment_file: str
    """Path to experiment file (without extension)"""
    
    regression_param: RegressionParameter
    """Regression parameters for this task"""
    
    def build_command(self, config: AutomaticAlignConfig) -> List[str]:
        """Build the command line for this alignment task"""
        cmd = [
            "cpulimit", "-l", str(config.cpu_limit), "--",
            sys.executable, "-m", "data_generation.script.v2.align_data",
            "--experiment-file", self.experiment_file,
            "--regression-parameters.paradigm", self.regression_param.paradigm,
            "--regression-parameters.regression-type", self.regression_param.regression_type,
            "--regression-parameters.noise-level", str(self.regression_param.noise_level),
            "--regression-parameters.optimization-function", self.regression_param.optimization_function,
            "--regression-parameters.data-ratio", str(self.regression_param.data_ratio)
        ]
        
        for seed in self.regression_param.random_seed:
            cmd.extend(["--regression-parameters.random-seed", str(seed)])
        
        if not config.skip_already_done:
            cmd.append("--no-skip-already-done")
        
        return cmd
    
    def execute(self, config: AutomaticAlignConfig) -> dict:
        """Execute this alignment task"""
        cmd = self.build_command(config)
        
        if config.dry_run:
            print(f"[DRY RUN] {' '.join(cmd)}")
            return {"success": True, "dry_run": True}
        
        process = None
        try:
            # Use Popen to have control over the process for proper termination
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait with timeout
            stdout, stderr = process.communicate(timeout=config.timeout)
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
            
        except subprocess.TimeoutExpired:
            # Kill everything matching the experiment file path
            # This will kill both cpulimit and the python align_data process
            try:
                subprocess.run(
                    ["pkill", "-9", "-f", self.experiment_file],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            
            # Signal timeout to align_data
            timeout_cmd = cmd + ["--timeout-signal"]
            try:
                subprocess.run(timeout_cmd, capture_output=True, text=True, timeout=120)
            except Exception as e:
                logger.error(f"Error signaling timeout for {self.experiment_id}: {e}")
            
            logger.error(f"Timeout for {self.experiment_id}")
            return {"success": False, "error": "timeout"}
            
        except Exception as e:
            # Clean up process on any other error
            if process:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except:
                    pass
            
            logger.error(f"Error executing {self.experiment_id}: {e}")
            return {"success": False, "error": str(e)}


def is_zero_force_vector(forces: List[float], tolerance: float = 1e-10) -> bool:
    """Check if all forces are zero"""
    return all(abs(f) < tolerance for f in forces)


def is_combo_valid_for_forces(forces: List[float], combo: ParadigmRegressionCombo) -> bool:
    """Check if a paradigm/regression_type combo is valid for the given forces"""
    is_zero = is_zero_force_vector(forces)
    regression_type = combo.regression_type
    
    if is_zero:
        # Zero forces: only implicit and mixed allowed
        return regression_type in ["implicit", "mixed"]
    else:
        # Non-zero forces: only explicit and mixed allowed
        return regression_type in ["explicit", "mixed"]


def load_experiment(json_path: str) -> Experiment:
    """Load experiment from JSON file"""
    with open(json_path, 'r') as f:
        return Experiment(**json.load(f))


def find_experiments(config: AutomaticAlignConfig) -> List[tuple[str, Experiment]]:
    """Find all valid experiments in results directory"""
    experiments = []
    json_files = Path(config.results_dir).glob("*.json")
    
    for json_path in json_files:
        experiment_id = json_path.stem
        pkl_path = Path(config.results_data_dir) / f"{experiment_id}.pkl"
        
        if not pkl_path.exists():
            logger.warning(f"PKL file not found for {experiment_id}")
            continue
        
        try:
            experiment = load_experiment(str(json_path))
            
            # Filter by experiment folder if specified
            if config.experiment_folders:
                folder_name = experiment.generation_params.experiment_folder.split('/')[-1]
                if folder_name not in config.experiment_folders:
                    logger.info(f"skipped")
                    continue
            
            experiments.append((experiment_id, experiment))
            
        except Exception as e:
            logger.error(f"Failed to load {experiment_id}: {e}")

    return experiments
    
def generate_tasks(
    experiment_id: str,
    experiment: Experiment,
    config: AutomaticAlignConfig
) -> Iterator[AlignmentTask]:
    """Generate all alignment tasks for an experiment"""
    
    forces = experiment.generation_params.forces_scale_vector
    experiment_file = str(Path(config.results_dir) / experiment_id)
    
    for combo in config.combos:
        # Check if this combo is valid for the experiment's forces
        if not is_combo_valid_for_forces(forces, combo):
            continue
        
        for noise_level in config.noise_levels:
            regression_param = RegressionParameter(
                optimization_function=config.optimization_function,
                paradigm=combo.paradigm,
                regression_type=combo.regression_type,
                noise_level=noise_level,
                random_seed=config.random_seeds,
                data_ratio=config.data_ratio
            )
            
            yield AlignmentTask(
                experiment_id=experiment_id,
                experiment_file=experiment_file,
                regression_param=regression_param
            )


def process_experiment(experiment_id: str, tasks: List[AlignmentTask], config: AutomaticAlignConfig, position: int = 1) -> List[dict]:
    """Process all tasks for a single experiment sequentially"""
    results = []
    # Create a progress bar - use dynamic_ncols for tmux compatibility
    task_pbar = tqdm(
        tasks, 
        desc=f"Exp {experiment_id[:8]}", 
        leave=False,  # Don't leave progress bars after completion to reduce clutter
        position=position, 
        mininterval=0.1, 
        maxinterval=10,
        dynamic_ncols=True,  # Adjust to terminal width dynamically
        ascii=True  # Use ASCII characters for better tmux compatibility
    )
    for task in task_pbar:
        # Update progress bar with current task details
        task_pbar.set_postfix({
            "paradigm": task.regression_param.paradigm[:5],
            "reg_type": task.regression_param.regression_type[:4],
            "noise": task.regression_param.noise_level
        })
        result = task.execute(config)
        result["experiment_id"] = task.experiment_id
        result["paradigm"] = task.regression_param.paradigm
        result["regression_type"] = task.regression_param.regression_type
        result["noise_level"] = task.regression_param.noise_level
        results.append(result)
    task_pbar.close()
    return results


def print_summary(results: List[dict], config: AutomaticAlignConfig):
    """Print execution summary"""
    if not results:
        print("No tasks executed.")
        return
    
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    failed = total - successful
    
    print(f"\n{'='*60}")
    print(f"EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total alignments: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/total*100:.1f}%")
    
    if config.dry_run:
        print("\n[Note: Dry run mode - no actual executions performed]")

def main():
    """Main execution function"""
    config = tyro.cli(AutomaticAlignConfig)
    
    # Validate directories
    if not Path(config.results_dir).exists():
        logger.error(f"Results directory not found: {config.results_dir}")
        sys.exit(1)
    
    if not Path(config.results_data_dir).exists():
        logger.error(f"Results data directory not found: {config.results_data_dir}")
        sys.exit(1)
    
    # Find experiments
    logger.info("Scanning for experiments...")
    experiments = find_experiments(config)
    
    if not experiments:
        logger.error("No experiments found!")
        sys.exit(1)
    
    logger.info(f"Found {len(experiments)} experiments")
    
    # Generate tasks grouped by experiment
    logger.info("Generating alignment tasks...")
    tasks_by_experiment = {}
    total_tasks = 0
    for experiment_id, experiment in experiments:
        tasks = list(generate_tasks(experiment_id, experiment, config))
        tasks_by_experiment[experiment_id] = tasks
        total_tasks += len(tasks)
    
    logger.info(f"Total alignment tasks: {total_tasks} across {len(tasks_by_experiment)} experiments")
    
    if config.dry_run:
        logger.info("DRY RUN MODE - Commands will be printed but not executed")
    
    # Execute tasks
    results = []
    
    if config.max_workers == 1:
        # Sequential execution - process experiments one by one
        for experiment_id, tasks in tasks_by_experiment.items():
            experiment_results = process_experiment(experiment_id, tasks, config, position=2)
            results.extend(experiment_results)
    else:
        # Parallel execution - each worker processes entire experiments
        logger.info(f"Using {config.max_workers} parallel workers")
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # Submit jobs with unique position for each worker (offset by 1 for general progress bar)
            future_to_data = {}
            for i, (experiment_id, tasks) in enumerate(tasks_by_experiment.items()):
                position = (i % config.max_workers) + 2  # Assign positions 2, 3, 4, ... (1 reserved for general)
                future = executor.submit(process_experiment, experiment_id, tasks, config, position)
                future_to_data[future] = (experiment_id, tasks)
            
            # Collect results as experiments complete with general progress bar
            completed = 0
            general_pbar = tqdm(
                total=len(tasks_by_experiment), 
                desc="Overall Progress", 
                position=0, 
                leave=True, 
                mininterval=0.1, 
                maxinterval=10,
                dynamic_ncols=True,  # Adjust to terminal width
                ascii=True  # ASCII characters for tmux compatibility
            )
            general_pbar.update(0)
            for future in as_completed(future_to_data):
                experiment_id, tasks = future_to_data[future]
                completed += 1
                general_pbar.update(1)
                try:
                    experiment_results = future.result()
                    results.extend(experiment_results)
                except Exception as e:
                    logger.error(f"Experiment {experiment_id} failed: {e}")
                    # Add failed results for all tasks in this experiment
                    for task in tasks:
                        results.append({
                            "success": False,
                            "error": str(e),
                            "experiment_id": task.experiment_id,
                            "paradigm": task.regression_param.paradigm,
                            "regression_type": task.regression_param.regression_type,
                            "noise_level": task.regression_param.noise_level
                        })
            general_pbar.close()
    
    # Print summary
    print_summary(results, config)
    
    # Save results
    if not config.dry_run:
        results_file = "automatic_align_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_file}")


if __name__ == "__main__":
    main()
