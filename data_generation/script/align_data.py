"""
This script is the second part of mujoco_gernerate_data and append the info file with regression data.
User can choose :
- the type of algorithm : Sindy, XLSindy, Mixed
- the regression algorithm : coordinate descent (scipy lasso), hard treshold
- level of noise added to imported data

Actually align_data.py is in developpement, Implicit explicit regression is under test

"""

# tyro cly dependencies

from pydantic import BaseModel

from typing import List
import tyro

import xlsindy

import time

import numpy as np
import json

import hashlib

import sys
import os
import importlib

from jax import jit
from jax import vmap

import pickle

import pandas as pd

from tqdm import tqdm

from xlsindy.logger import setup_logger

from data_generation.script.generate_trajectory import generate_theoretical_trajectory

from data_generation.script.dataclass import DataGenerationParams,Experiment,TrajectoryData,RegressionParameter
from data_generation.script.dataclass import RegressionResult,Solution

logger = setup_logger(__name__)

class Args(BaseModel):
    experiment_file: str = "None"
    """the experiment file (without extension)"""
    regression_parameters: RegressionParameter
    """the regression parameters for the experiment"""
    skip_already_done: bool = True
    """if true, skip the experiment if already present in the result file"""
    timeout_signal: bool = False
    """if true, skip everything and return the experiment with a timeout"""


if __name__ == "__main__":

    args = tyro.cli(Args)

    ## CLI validation
    if args.experiment_file == "None":
        raise ValueError(
            "experiment_file should be provided, don't hesitate to invoke --help"
        )

    with open(args.experiment_file + ".json", "r") as json_file:
        experiment_data = Experiment(**json.load(json_file))

    sys.path.append(experiment_data.generation_params.experiment_folder)

    # import the xlsindy_gen.py script
    xlsindy_gen = importlib.import_module("xlsindy_gen")

    try:
        xlsindy_component = eval(f"xlsindy_gen.xlsindy_component")
    except AttributeError:
        raise AttributeError(
            f"xlsindy_gen.py should contain a function named {args.regression_parameters.paradigm}_component in order to work with algorithm {args.regression_parameters.paradigm}"
        )

    try:
        forces_wrapper = xlsindy_gen.forces_wrapper
    except AttributeError:
        forces_wrapper = None

    random_seed = experiment_data.generation_params.random_seed + args.regression_parameters.random_seed
    print("random seed is :", random_seed)
    num_coordinates, time_sym, symbols_matrix, full_catalog, xml_content, extra_info = (
        xlsindy_component(mode=args.regression_parameters.paradigm, random_seed=random_seed)
    )

    full_catalog: xlsindy.catalog.CatalogRepartition = full_catalog

    regression_function = eval(f"xlsindy.optimization.{args.regression_parameters.optimization_function}")

    # Add the other ideal vector if another mode is present.

    if args.regression_parameters.paradigm not in experiment_data.data.training_group.get_trajectory_by_name("training_data").get_solution_mode() :

        experiment_data.data.training_group.get_trajectory_by_name("training_data").solutions.append(
            Solution(
                mode_solution=args.regression_parameters.paradigm,
                solution_vector=extra_info["ideal_solution_vector"],
                solution_label=full_catalog.label()
            )
        )


    if args.regression_parameters.paradigm not in experiment_data.data.validation_group.get_trajectory_by_name("validation_data").get_solution_mode() :

        experiment_data.data.validation_group.get_trajectory_by_name("validation_data").solutions.append(
            Solution(
                mode_solution=args.regression_parameters.paradigm,
                solution_vector=extra_info["ideal_solution_vector"],
                solution_label=full_catalog.label()
            )
        )

    ## Mark the experiment as timeout if needed
    if args.timeout_signal:

        experiment_data.data.validation_group.del_trajectory_by_name(args.regression_parameters.UID)
        experiment_data.data.validation_group.trajectories.append(
            TrajectoryData(
                name=args.regression_parameters.UID,
                regression_result=RegressionResult(
                    regression_parameters=args.regression_parameters
                )
            )
        )
        
        print("print model ...")
        with open(args.experiment_file + ".json", "w") as file:
            file.write(experiment_data.model_dump_json(indent=4))

        exit()

    if args.skip_already_done:
        if args.regression_parameters.UID in experiment_data.data.validation_group.get_trajectory_name():
            print("already aligned")
            exit()


    try:
        with open(experiment_data.data_path, 'rb') as f:
            sim_data = pickle.load(f)

        rng = np.random.default_rng(random_seed)
        # load
        imported_time = sim_data["simulation_time_training"]
        imported_qpos = sim_data["simulation_qpos_training"]
        imported_qvel = sim_data["simulation_qvel_training"]
        imported_qacc = sim_data["simulation_qacc_training"]
        imported_force = sim_data["force_vector_training"]


        # add noise
        imported_qpos += rng.normal(loc=0, scale=args.regression_parameters.noise_level, size=imported_qpos.shape)#*np.linalg.norm(imported_qpos)/imported_qpos.shape[0]
        imported_qvel += rng.normal(loc=0, scale=args.regression_parameters.noise_level, size=imported_qvel.shape)#*np.linalg.norm(imported_qvel)/imported_qvel.shape[0]
        imported_qacc += rng.normal(loc=0, scale=args.regression_parameters.noise_level, size=imported_qacc.shape)#*np.linalg.norm(imported_qacc)/imported_qacc.shape[0]
        imported_force += rng.normal(loc=0, scale=args.regression_parameters.noise_level, size=imported_force.shape)#*np.linalg.norm(imported_force)/imported_force.shape[0]

        # Use a fixed ratio of the data in respect with catalog size
        catalog_size = full_catalog.catalog_length
        data_ratio = args.regression_parameters.data_ratio
        
        # Sample uniformly n samples from the imported arrays
        n_samples = int(catalog_size * data_ratio)
        total_samples = imported_qpos.shape[0]
        
        if n_samples < total_samples:

            # Evenly spaced sampling (deterministic, uniform distribution)
            sample_indices = np.linspace(0, total_samples - 1, n_samples, dtype=int)
            
            # Apply sampling to all arrays
            imported_qpos = imported_qpos[sample_indices]
            imported_qvel = imported_qvel[sample_indices]
            imported_qacc = imported_qacc[sample_indices]
            imported_force = imported_force[sample_indices]
            
            logger.info(f"Sampled {n_samples} points uniformly from {total_samples} total samples")
        else:
            logger.info(f"Using all {total_samples} samples (requested {n_samples})")

        ## XLSINDY dependent

        start_time = time.perf_counter()

        pre_knowledge_indices = np.nonzero(experiment_data.generation_params.forces_scale_vector)[0] + full_catalog.starting_index_by_type("ExternalForces")


        pre_knowledge_mask = np.zeros((full_catalog.catalog_length,))
        pre_knowledge_mask[pre_knowledge_indices] = 1.0

        if args.regression_parameters.regression_type == "implicit":

            logger.info("Starting implicit regression")

            solution, exp_matrix = xlsindy.simulation.regression_implicite(
                theta_values=imported_qpos,
                velocity_values=imported_qvel,
                acceleration_values=imported_qacc,
                time_symbol=time_sym,
                symbol_matrix=symbols_matrix,
                catalog_repartition=full_catalog,
                regression_function=regression_function,
            )

        elif args.regression_parameters.regression_type == "explicit":
            
            logger.info("Starting explicit regression")

            solution, exp_matrix = xlsindy.simulation.regression_explicite(
                theta_values=imported_qpos,
                velocity_values=imported_qvel,
                acceleration_values=imported_qacc,
                time_symbol=time_sym,
                symbol_matrix=symbols_matrix,
                catalog_repartition=full_catalog,
                external_force=imported_force,
                regression_function=regression_function,
                pre_knowledge_mask=pre_knowledge_mask
            )

        elif args.regression_parameters.regression_type == "mixed":

            logger.info("Starting mixed regression")

            solution, exp_matrix = xlsindy.simulation.regression_mixed(
                theta_values=imported_qpos,
                velocity_values=imported_qvel,
                acceleration_values=imported_qacc,
                time_symbol=time_sym,
                symbol_matrix=symbols_matrix,
                catalog_repartition=full_catalog,
                external_force=imported_force,
                regression_function=regression_function,
                pre_knowledge_mask=pre_knowledge_mask
            )

        end_time = time.perf_counter()

        regression_time = end_time - start_time

        logger.info(f"Regression completed in {end_time - start_time:.2f} seconds")

        # DEBUG
        # solution = extra_info["ideal_solution_vector"]
        # Apply hard thresholding to the solution
        threshold = 1e-2  # Adjust threshold value as needed
        solution = np.where(np.abs(solution)/np.linalg.norm(solution) < threshold, 0, solution)

        ##--------------------------------

        model_acceleration_func, valid_model = (
            xlsindy.dynamics_modeling.generate_acceleration_function(
                solution, 
                full_catalog,
                symbols_matrix,
                time_sym,
                lambdify_module="jax",
            )
        )
        model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function_RK4_env(
            model_acceleration_func
        )

        ## Analysis of result

        regression_result = RegressionResult(
            regression_parameters=args.regression_parameters,
            valid=valid_model,
            timeout=False,
            regression_time=regression_time
        )


        if valid_model:

            # Acceleration comparison result

            model_dynamics_system = vmap(model_dynamics_system, in_axes=(1, 1), out_axes=1)
            
            model_coordinate = xlsindy.dynamics_modeling.vectorised_acceleration_generation(
                model_dynamics_system, imported_qpos, imported_qvel, imported_force
            )
            # Finally, select the columns of interest (e.g., every second column starting at index 1)
            model_acc = model_coordinate[:, 1::2]

            # Estimate of the variance between model and mujoco
            RMSE_acceleration = xlsindy.result_formatting.relative_mse(
                model_acc[3:-3], imported_qacc[3:-3]
            )

            regression_result.RMSE_acceleration = RMSE_acceleration
            print("estimate variance between mujoco and model is : ", RMSE_acceleration)

            # Trajectory comparison result

            model_acceleration_func_np, _ = (
                xlsindy.dynamics_modeling.generate_acceleration_function(
                    solution, 
                    full_catalog,
                    symbols_matrix,
                    time_sym,
                    lambdify_module="numpy",
                )
            )


            (simulation_time_g, 
            simulation_qpos_g, 
            simulation_qvel_g, 
            simulation_qacc_g, 
            force_vector_g,
            _) = generate_theoretical_trajectory(
                num_coordinates,
                experiment_data.generation_params.initial_position,
                experiment_data.generation_params.initial_condition_randomness,
                [experiment_data.generation_params.random_seed,0], # Ensure same seed as for data generation
                1,
                experiment_data.generation_params.validation_time,
                solution,
                full_catalog,
                time_sym,
                symbols_matrix,
                experiment_data.generation_params.forces_scale_vector,
            )

            new_trajectory = TrajectoryData.from_numpy(
                            name=args.regression_parameters.UID,
                            time=simulation_time_g,
                            qpos=simulation_qpos_g,
                            qvel=simulation_qvel_g,
                            qacc=simulation_qacc_g,
                            forces=force_vector_g,
                            reference_time=experiment_data.data.validation_group.get_trajectory_by_name("validation_data").series.time.time,
                            mode_solution=args.regression_parameters.paradigm,
                            solution_vector=solution,
                            solution_label=full_catalog.label(),
                            reference=False,
                            regression_result=regression_result
                        )

            # Compute the position RMSE on the validation trajectory

            validation_pos = experiment_data.data.validation_group.get_trajectory_by_name("validation_data").series.qpos.get_numpy_series()
            regression_pos = new_trajectory.series.qpos.get_numpy_series()

            error = xlsindy.result_formatting.relative_mse(
                regression_pos, validation_pos
            )

            new_trajectory.regression_result.RMSE_validation_position = error

            logger.info(f"Position RMSE on validation trajectory: {error}")


            experiment_data.data.validation_group.del_trajectory_by_name(args.regression_parameters.UID)
            experiment_data.data.validation_group.trajectories.append(new_trajectory)
            
        else: 
            experiment_data.data.validation_group.del_trajectory_by_name(args.regression_parameters.UID)
            experiment_data.data.validation_group.trajectories.append(
                TrajectoryData(
                    name=args.regression_parameters.UID,
                    regression_result=regression_result,
                    solutions=[
                        Solution(
                            mode_solution=args.regression_parameters.paradigm,
                            solution_vector=solution,
                            solution_label=full_catalog.label()
                        )
                    ],
                )
            )

            # Generate the batch as a theory one

        if not valid_model:
            print("Skipped model verification, retrieval failed")
        
        print("print model ...")
        with open(args.experiment_file + ".json", "w") as file:
            file.write(experiment_data.model_dump_json(indent=4))

    except Exception as e:
        
        print("Alignment failed with error :", e)

        experiment_data.data.validation_group.del_trajectory_by_name(args.regression_parameters.UID)
        experiment_data.data.validation_group.trajectories.append(
            TrajectoryData(
                name=args.regression_parameters.UID,
                regression_result=RegressionResult(
                    regression_parameters=args.regression_parameters,
                    timeout=False
                )
            )
        )
        
        print("print model ...")
        with open(args.experiment_file + ".json", "w") as file:
            file.write(experiment_data.model_dump_json(indent=4))

