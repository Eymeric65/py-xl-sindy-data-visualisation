"""
This script is used to generate data for experiments. save everything in a folder. It is using the V2 of the formalism of batch generation for xlsindy. It is aimed for the journal paper.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro

import sys
import os 
import importlib

import mujoco

import numpy as np
import xlsindy

import pickle

import json
import hashlib

from xlsindy.logger import setup_logger

from tqdm import tqdm

from data_generation.script.util import generate_theorical_trajectory,generate_mujoco_trajectory,json_format_time_series,convert_to_lists

logger = setup_logger(__name__)

@dataclass
class Args:
    ## System definition 
    experiment_folder: str = "None"
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    damping_coefficients: List[float] = field(default_factory=lambda: [])
    """the damping coefficients for the system, this is used to replace the DAMPING value in the environment.xml file"""
    ## Randomness
    random_seed: List[int] = field(default_factory=lambda: [0])
    """the random seed of the experiment (only used for force function)"""
    ## Data generation
    batch_number: int = 1
    """the number of batch to generate, this is used to generate more data mainly in implicit case (default 1)"""
    generation_type:str = "theorical"
    """if true generate the data using mujoco otherwise use the theoritical generator (default true)"""
    max_time: float = 10.0
    """the maximum time for the simulation"""
    initial_condition_randomness: List[float] = field(default_factory=lambda: [0.0])
    """the randomness of the initial condition, this is used to generate a random initial condition around the initial position for each batch can be a scalar or a list of lenght coordinate times two."""
    initial_position: List[float] = field(default_factory=lambda: [])
    """the initial position of the system"""
    forces_scale_vector: List[float] = field(default_factory=lambda: [])
    """the different scale for the forces vector to be applied, this can mimic an action mask over the system if some entry are 0"""
    forces_period: float = 3.0
    """the period for the forces function"""
    forces_period_shift: float = 0.5
    """the shift for the period of the forces function"""
    sample_number: int = 1000
    """the number of sample for the experiment (ten times the lenght of the catalog works well)"""
    visualisation_sample: int = 1000
    """the number of sample for the visualisation of the trajectory (should be high enough to be smooth)"""
    validation_time: float = 20.0
    """the time for the validation trajectory"""
    max_validation_sample: int = 4000
    """the maximum number of sample for the validation trajectory, if the validation time is too high compared to the max time and the sample number, this will limit the number of sample to avoid memory issues"""


    def get_json(self) -> str: 
        """Generate a JSON string from parameters."""
        d = vars(self).copy()
        d.pop("visualisation_sample", None)
        d.pop("validation_time", None)
        d.pop("max_validation_sample", None)
        return json.dumps(d, sort_keys=True)

    def get_uid(self) -> str:
        """Generate a hash-based UID from parameters."""
        return hashlib.md5(self.get_json().encode()).hexdigest()
if __name__ == "__main__":

    args = tyro.cli(Args)

    # CLI validation
    if args.forces_scale_vector == []:
        raise ValueError(
            "forces_scale_vector should be provided, don't hesitate to invoke --help"
        )
    if args.experiment_folder == "None":
        raise ValueError(
            "experiment_folder should be provided, don't hesitate to invoke --help"
        )
    else:  # import the xlsindy_back_script
        folder_path = os.path.join(os.getcwd(), args.experiment_folder)
        logger.info(f"INFO : Using experiment folder {folder_path}")
        sys.path.append(folder_path)

        # import the xlsindy_gen.py script
        xlsindy_gen = importlib.import_module("xlsindy_gen")

        try:
            xlsindy_component = xlsindy_gen.xlsindy_component
        except AttributeError:
            raise AttributeError(
                "xlsindy_gen.py should contain a function named xlsindy_component"
            )

        try:
            mujoco_transform = xlsindy_gen.mujoco_transform
        except AttributeError:
            mujoco_transform = None

        try:
            inverse_mujoco_transform = xlsindy_gen.inverse_mujoco_transform
        except AttributeError:
            inverse_mujoco_transform = None


        num_coordinates, time_sym, symbols_matrix, full_catalog, xml_content, extra_info = (
            xlsindy_component( random_seed=args.random_seed, damping_coefficients=args.damping_coefficients)  # type: ignore
        )

        

        ideal_solution_vector = extra_info.get("ideal_solution_vector", None)
        if ideal_solution_vector is None:
            raise ValueError(
                "xlsindy_gen.py should return an ideal_solution_vector in the extra_info dictionary"
            )
        

    logger.info("INFO : Cli validated")
    ## TODO add a check for the number of forces scale vector in the input

### ----------------------- Part 1, generate the data using Mujoco or theorical ----------------------
    
    # Batch generation
    if args.generation_type == "mujoco" : # Mujoco Generation
        
        if mujoco_transform is None or inverse_mujoco_transform is None:
            raise ValueError(
                "mujoco_transform and inverse_mujoco_transform functions must be defined in xlsindy_gen.py for MuJoCo generation"
            )
        
        (simulation_time_t, 
         simulation_qpos_t, 
         simulation_qvel_t, 
         simulation_qacc_t, 
         force_vector_t,
         batch_starting_times) = generate_mujoco_trajectory(
             num_coordinates,
             args.initial_position,
             args.initial_condition_randomness,
             args.random_seed,
             args.batch_number,
             args.max_time,
             xml_content,
             args.forces_scale_vector,
             args.forces_period,
             args.forces_period_shift,
             extra_info,
             mujoco_transform,
             inverse_mujoco_transform
         )
        
        (simulation_time_v, 
         simulation_qpos_v, 
         simulation_qvel_v, 
         simulation_qacc_v, 
         force_vector_v,
         _) = generate_mujoco_trajectory(
             num_coordinates,
             args.initial_position,
             args.initial_condition_randomness,
             [args.random_seed,0], # Important to keep in mind the change of seed for validation
             1,
             args.validation_time,
             xml_content,
             args.forces_scale_vector,
             args.forces_period,
             args.forces_period_shift,
             extra_info,
             mujoco_transform,
             inverse_mujoco_transform
         )

    elif args.generation_type == "theorical": # Theorical generation

        (simulation_time_t, 
         simulation_qpos_t, 
         simulation_qvel_t, 
         simulation_qacc_t, 
         force_vector_t,
         batch_starting_times) = generate_theorical_trajectory(
             num_coordinates,
             args.initial_position,
             args.initial_condition_randomness,
             args.random_seed,
             args.batch_number,
             args.max_time,
             ideal_solution_vector,
             full_catalog,
             extra_info,
             time_sym,
             symbols_matrix,
             args.forces_scale_vector,
             args.forces_period,
             args.forces_period_shift
         )
        
        (simulation_time_v, 
         simulation_qpos_v, 
         simulation_qvel_v, 
         simulation_qacc_v, 
         force_vector_v,
         _) = generate_theorical_trajectory(
             num_coordinates,
             args.initial_position,
             args.initial_condition_randomness,
             [args.random_seed,0],# Important to keep in mind the change of seed for validation
             1,
             args.validation_time,
             ideal_solution_vector,
             full_catalog,
             extra_info,
             time_sym,
             symbols_matrix,
             args.forces_scale_vector,
             args.forces_period,
             args.forces_period_shift
         )

    logger.info( f"Raw simulation len {len(simulation_time_t)}")

    # Reduce the data to the desired lenght

    subsample_t = len(simulation_time_t) // args.sample_number

    subsample_v = len(simulation_time_v) // args.max_validation_sample

    if subsample_t == 0 :
        subsample_t =1

    if subsample_v == 0 :
        subsample_v = 1

    truncation = 20

    simulation_time_data_training = simulation_time_t[truncation:-truncation:subsample_t]
    simulation_qpos_data_training = simulation_qpos_t[truncation:-truncation:subsample_t]
    simulation_qvel_data_training = simulation_qvel_t[truncation:-truncation:subsample_t]
    simulation_qacc_data_training = simulation_qacc_t[truncation:-truncation:subsample_t]
    force_vector_data_training = force_vector_t[truncation:-truncation:subsample_t]

    simulation_time_data_validation = simulation_time_v[truncation:-truncation:subsample_v]
    simulation_qpos_data_validation = simulation_qpos_v[truncation:-truncation:subsample_v]
    simulation_qvel_data_validation = simulation_qvel_v[truncation:-truncation:subsample_v]
    simulation_qacc_data_validation = simulation_qacc_v[truncation:-truncation:subsample_v]
    force_vector_data_validation = force_vector_v[truncation:-truncation:subsample_v]

    data = {
        "simulation_time_training": simulation_time_data_training,
        "simulation_qpos_training": simulation_qpos_data_training,
        "simulation_qvel_training": simulation_qvel_data_training,
        "simulation_qacc_training": simulation_qacc_data_training,
        "force_vector_training": force_vector_data_training,
        "simulation_time_validation": simulation_time_data_validation,
        "simulation_qpos_validation": simulation_qpos_data_validation,
        "simulation_qvel_validation": simulation_qvel_data_validation,
        "simulation_qacc_validation": simulation_qacc_data_validation,
        "force_vector_validation": force_vector_data_validation,
    }

    # Save pickle file

    filename = f"results_data/{args.get_uid()}.pkl"
    with open(filename,'wb') as f : 
        pickle.dump(data, f)
    logger.info(f"Data saved with uid {args.get_uid()}")

    settings_dict = json.loads(args.get_json())

    data_json = {
        "generation_settings" : settings_dict,
        "data_path" : filename,
        "visualisation" : {
            "training_group": {
                "data": {
                    **json_format_time_series(
                        name="training_data",
                        time= simulation_time_data_training,
                        series = {
                            "qpos": simulation_qpos_data_training,
                            "qvel": simulation_qvel_data_training,
                            "qacc": simulation_qacc_data_training,
                            "forces": force_vector_data_training
                        },
                        sample= args.visualisation_sample,
                        mode_solution="mixed",
                        ideal_solution_vector=ideal_solution_vector,
                        solution_label=full_catalog.label(),
                        reference=True
                    )
                },
                "batch_starting_times": batch_starting_times,
            },
            "validation_group":{
                "data": {
                    **json_format_time_series(
                        name="validation_data",
                        time= simulation_time_data_validation,
                        series = {
                            "qpos": simulation_qpos_data_validation,
                            "qvel": simulation_qvel_data_validation,
                            "qacc": simulation_qacc_data_validation,
                            "forces": force_vector_data_validation
                        },
                        sample= args.visualisation_sample,
                        mode_solution="mixed",
                        ideal_solution_vector=ideal_solution_vector,
                        solution_label=full_catalog.label(),
                        reference=True
                    )
                },
            },
        }
    }
    
    data_json = convert_to_lists(data_json)

    # Save json file
    json_filename = f"results/{args.get_uid()}.json"

    with open(json_filename,'w') as f :
        json.dump(data_json, f, indent=None)

    logger.info(f"Settings saved with uid {args.get_uid()}")



