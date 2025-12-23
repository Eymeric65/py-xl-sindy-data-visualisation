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
from pydantic import BaseModel

from tqdm import tqdm

from data_generation.script.generate_trajectory import generate_theoretical_trajectory,generate_mujoco_trajectory

from data_generation.script.dataclass import DataGenerationParams,Experiment,TrajectoryData

logger = setup_logger(__name__)

@dataclass
class Args:
    params: DataGenerationParams
    skip_already_done: bool = True
    """if true, skip the generation if the data already exists (default true)"""

if __name__ == "__main__":

    args = tyro.cli(Args)

    # Check if data already exists and skip if requested
    if args.skip_already_done:
        json_filename = f"results/{args.params.UID}.json"
        if os.path.exists(json_filename):
            logger.info(f"Data already exists for UID {args.params.UID}, skipping generation")
            sys.exit(0)
    
    # Use args.params for the actual parameters
    args = args.params

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
             mujoco_transform,
             inverse_mujoco_transform
         )

    elif args.generation_type == "theorical": # Theorical generation

        (simulation_time_t, 
         simulation_qpos_t, 
         simulation_qvel_t, 
         simulation_qacc_t, 
         force_vector_t,
         batch_starting_times) = generate_theoretical_trajectory(
             num_coordinates,
             args.initial_position,
             args.initial_condition_randomness,
             args.random_seed,
             args.batch_number,
             args.max_time,
             ideal_solution_vector,
             full_catalog,
             time_sym,
             symbols_matrix,
             args.forces_scale_vector,
         )
        
        (simulation_time_v, 
         simulation_qpos_v, 
         simulation_qvel_v, 
         simulation_qacc_v, 
         force_vector_v,
         _) = generate_theoretical_trajectory(
             num_coordinates,
             args.initial_position,
             args.initial_condition_randomness,
             [args.random_seed,0],# Important to keep in mind the change of seed for validation
             1,
             args.validation_time,
             ideal_solution_vector,
             full_catalog,
             time_sym,
             symbols_matrix,
             args.forces_scale_vector,
         )

    logger.info( f"Raw simulation len {len(simulation_time_t)}")

    # Reduce the data to the desired lenght

    subsample_t = len(simulation_time_t) // args.sample_number

    subsample_v = len(simulation_time_v) // args.max_validation_sample

    if subsample_t == 0 :
        subsample_t =1

    if subsample_v == 0 :
        subsample_v = 1

    truncation = 5

    logger.info(f"time shape : {simulation_time_t.shape} {simulation_time_v.shape}")

    logger.info( f"Subsample training factor {subsample_t} and validation factor {subsample_v}")

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

    filename = f"results_data/{args.UID}.pkl"
    with open(filename,'wb') as f : 
        pickle.dump(data, f)
    logger.info(f"Data saved with uid {args.UID}")

    ## ----------------------- Part 2, generate the json file for visualisation ----------------------
    
    experiment_data= Experiment(
        generation_params=args,
        data_path=filename,
        data=Experiment.ExperimentData(
            training_group=Experiment.ExperimentData.TrajectoryGroup(
                batch_starting_time=batch_starting_times,
                trajectories=[TrajectoryData.from_numpy(
                    name="training_data",
                    time=simulation_time_data_training,
                    qpos=simulation_qpos_data_training,
                    qvel=simulation_qvel_data_training,
                    qacc=simulation_qacc_data_training,
                    forces=force_vector_data_training,
                    sample_number=args.sample_number,
                    mode_solution="mixed",
                    solution_vector=ideal_solution_vector,
                    solution_label=full_catalog.label(),
                    reference=True
                )],
            ),
            validation_group=Experiment.ExperimentData.TrajectoryGroup(
                batch_starting_time=[],
                trajectories=[TrajectoryData.from_numpy(
                    name="validation_data",
                    time=simulation_time_data_validation,
                    qpos=simulation_qpos_data_validation,
                    qvel=simulation_qvel_data_validation,
                    qacc=simulation_qacc_data_validation,
                    forces=force_vector_data_validation,
                    sample_number=args.sample_number,
                    mode_solution="mixed",
                    solution_vector=ideal_solution_vector,
                    solution_label=full_catalog.label(),
                    reference=True
                )],
            ),
        )
    )

    # Save json file
    json_filename = f"results/{args.UID}.json"

    with open(json_filename,'w') as f :
        f.write(experiment_data.model_dump_json(indent=4))

    logger.info(f"Settings saved with uid {args.UID}")



