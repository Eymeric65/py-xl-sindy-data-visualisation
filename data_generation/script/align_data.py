"""
This script is the second part of mujoco_gernerate_data and append the info file with regression data.
User can choose :
- the type of algorithm : Sindy, XLSindy, Mixed
- the regression algorithm : coordinate descent (scipy lasso), hard treshold
- level of noise added to imported data

Actually align_data.py is in developpement, Implicit explicit regression is under test

"""

# tyro cly dependencies
from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro

import xlsindy

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

from data_generation.script.util import generate_theorical_trajectory,convert_to_lists,json_format_time_series

logger = setup_logger(__name__)

@dataclass
class Args:
    experiment_file: str = "None"
    """the experiment file (without extension)"""
    optimization_function: str = "lasso_regression"
    """the regression function used in the regression"""
    algorithm: str = "mixed"
    """the name of the algorithm used (for the moment "xlsindy", "sindy" and "mixed" are the only possible)"""
    regression_type: str = "explicit"
    """the type of regression to use (explicit, implicit, mixed)"""
    noise_level: float = 0.0
    """the level of noise introduce in the experiment"""
    random_seed: List[int] = field(default_factory=lambda: [0])
    """the random seed for the noise"""
    skip_already_done: bool = True
    """if true, skip the experiment if already present in the result file"""

    def get_uid(self):
        hash_input = (
            self.optimization_function
            + self.algorithm
            + str(self.noise_level)
            + self.regression_type
            + str(self.random_seed)
        )
        return hashlib.md5(hash_input.encode()).hexdigest()

if __name__ == "__main__":

    args = tyro.cli(Args)

    ## CLI validation
    if args.experiment_file == "None":
        raise ValueError(
            "experiment_file should be provided, don't hesitate to invoke --help"
        )

    with open(args.experiment_file + ".json", "r") as json_file:
        simulation_dict = json.load(json_file)

    if args.skip_already_done:
        if args.get_uid() in simulation_dict["visualisation"]["validation_group"]["data"]:
            print("already aligned")
            exit()

    folder_path = simulation_dict["generation_settings"]["experiment_folder"]

    sys.path.append(folder_path)

    # import the xlsindy_gen.py script
    xlsindy_gen = importlib.import_module("xlsindy_gen")

    try:
        xlsindy_component = eval(f"xlsindy_gen.xlsindy_component")
    except AttributeError:
        raise AttributeError(
            f"xlsindy_gen.py should contain a function named {args.algorithm}_component in order to work with algorithm {args.algorithm}"
        )

    try:
        forces_wrapper = xlsindy_gen.forces_wrapper
    except AttributeError:
        forces_wrapper = None

    random_seed = simulation_dict["generation_settings"]["random_seed"] + args.random_seed
    print("random seed is :", random_seed)
    num_coordinates, time_sym, symbols_matrix, full_catalog, xml_content, extra_info = (
        xlsindy_component(mode=args.algorithm, random_seed=random_seed)
    )

    regression_function = eval(f"xlsindy.optimization.{args.optimization_function}")

    with open(simulation_dict["data_path"], 'rb') as f:
        sim_data = pickle.load(f)

    rng = np.random.default_rng(random_seed)

    # load
    imported_time = sim_data["simulation_time_training"]
    imported_qpos = sim_data["simulation_qpos_training"]
    imported_qvel = sim_data["simulation_qvel_training"]
    imported_qacc = sim_data["simulation_qacc_training"]
    imported_force = sim_data["force_vector_training"]


    # add noise
    imported_qpos += rng.normal(loc=0, scale=args.noise_level, size=imported_qpos.shape)*np.linalg.norm(imported_qpos)/imported_qpos.shape[0]
    imported_qvel += rng.normal(loc=0, scale=args.noise_level, size=imported_qvel.shape)*np.linalg.norm(imported_qvel)/imported_qvel.shape[0]
    imported_qacc += rng.normal(loc=0, scale=args.noise_level, size=imported_qacc.shape)*np.linalg.norm(imported_qacc)/imported_qacc.shape[0]
    imported_force += rng.normal(loc=0, scale=args.noise_level, size=imported_force.shape)*np.linalg.norm(imported_force)/imported_force.shape[0]

    ## XLSINDY dependent

    if args.regression_type == "implicit":

        solution, exp_matrix = xlsindy.simulation.regression_implicite(
            theta_values=imported_qpos,
            velocity_values=imported_qvel,
            acceleration_values=imported_qacc,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=full_catalog,
            regression_function=regression_function,
        )

    elif args.regression_type == "explicit":

        solution, exp_matrix = xlsindy.simulation.regression_explicite(
            theta_values=imported_qpos,
            velocity_values=imported_qvel,
            acceleration_values=imported_qacc,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=full_catalog,
            external_force=imported_force,
            regression_function=regression_function,
        )

    elif args.regression_type == "mixed":

        solution, exp_matrix = xlsindy.simulation.regression_mixed(
            theta_values=imported_qpos,
            velocity_values=imported_qvel,
            acceleration_values=imported_qacc,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=full_catalog,
            external_force=imported_force,
            regression_function=regression_function,
        )

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

    result_dict = {
        "noise_level": args.noise_level,
        "optimization_function": args.optimization_function,
        "random_seed": random_seed,
        "regression_type": args.regression_type,
        "valid": valid_model,
        "results":{}
    }


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

        result_dict["results"]["RMSE_acceleration"] = RMSE_acceleration
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

        trajectory_rng = np.random.default_rng(args.random_seed)

        (simulation_time_g, 
         simulation_qpos_g, 
         simulation_qvel_g, 
         simulation_qacc_g, 
         force_vector_g,
         _) = generate_theorical_trajectory(
             num_coordinates,
             simulation_dict["generation_settings"]["initial_position"],
             simulation_dict["generation_settings"]["initial_condition_randomness"],
             [simulation_dict["generation_settings"]["random_seed"],0], # Ensure same seed as for data generation
             1,
             simulation_dict["generation_settings"]["validation_time"],
             solution,
             full_catalog,
             extra_info,
             time_sym,
             symbols_matrix,
             simulation_dict["generation_settings"]["forces_scale_vector"],
             simulation_dict["generation_settings"]["forces_period"],
             simulation_dict["generation_settings"]["forces_period_shift"]
         )
        
    else: 
        simulation_time_g = None
        simulation_qpos_g = None
        simulation_qvel_g = None
        simulation_qacc_g = None
        force_vector_g = None

    simulation_dict["visualisation"]["validation_group"]["data"].update(
            **json_format_time_series(
                name=args.get_uid(),
                time= simulation_time_g,
                series = {
                    "qpos": simulation_qpos_g,
                    "qvel": simulation_qvel_g,
                    "qacc": simulation_qacc_g,
                    "forces": force_vector_g
                },
                sample= simulation_dict["generation_settings"]["visualisation_sample"],
                mode_solution=args.algorithm,
                solution_vector=solution,
                extra_info=result_dict
            )
        )

        # Generate the batch as a theory one

    if not valid_model:
        print("Skipped model verification, retrieval failed")

    simulation_dict = convert_to_lists(simulation_dict)
    
    print("print model ...")
    with open(args.experiment_file + ".json", "w") as file:
        json.dump(simulation_dict, file, indent=4)

