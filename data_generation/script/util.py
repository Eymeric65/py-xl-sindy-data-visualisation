"""
Some util used in generate data, align data and so one.
Not really something that should go in xlsindy.
"""
import contextlib
import logging 
import numpy as np

from typing import List, Dict

import xlsindy
from tqdm import tqdm

import sympy as sp

import mujoco
import json

logger = logging.getLogger(__name__)

def generate_theorical_trajectory(
    num_coordinates: int,
    initial_position: np.ndarray,
    initial_condition_randomness: np.ndarray,
    random_seed: List[int],
    batch_number: int,
    max_time: float,
    solution_vector: np.ndarray,
    solution_catalog: xlsindy.catalog.CatalogRepartition,
    system_extra_info: dict,
    time_symb: sp.Symbol,
    symbols_matrix: np.ndarray,
    forces_scale_vector: np.ndarray,
    forces_period: np.ndarray,
    forces_period_shift: np.ndarray,
):
    """
    [INFO] maybe I should but this function inside the main library.
    Generate a theortical trajectory using theorical background.

    Args:

    Returns:
    """
    
    simulation_time_g = np.empty((0,1))
    simulation_qpos_g = np.empty((0,num_coordinates))
    simulation_qvel_g = np.empty((0,num_coordinates))
    simulation_qacc_g = np.empty((0,num_coordinates))
    force_vector_g = np.empty((0,num_coordinates))
    batch_starting_times = []

    if len(initial_position)==0:
        initial_position = np.zeros((num_coordinates,2))

    rng = np.random.default_rng(random_seed)

    model_acceleration_func, valid_model = xlsindy.dynamics_modeling.generate_acceleration_function(
    solution_vector,
    solution_catalog,
    symbols_matrix,
    time_symb,
    lambdify_module="numpy"
    )
    
    for i in tqdm(range(batch_number),desc="Generating batches", unit="batch"):

        # Record batch starting time
        batch_start_time = 0.0 if len(simulation_time_g) == 0 else np.max(simulation_time_g)
        batch_starting_times.append(float(batch_start_time))

        # Initial condition
        initial_condition = np.array(initial_position).reshape(num_coordinates,2) + system_extra_info["initial_condition"]

        if len(initial_condition_randomness) == 1:
            initial_condition += rng.normal(
                loc=0, scale=initial_condition_randomness, size=initial_condition.shape
            )
        else:
            initial_condition += rng.normal(
                loc=0, scale=np.reshape(initial_condition_randomness,initial_condition.shape)
            )

        # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
        forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
            component_count=num_coordinates,
            scale_vector=forces_scale_vector,
            time_end=max_time,
            period=forces_period,
            period_shift=forces_period_shift,
            augmentations=10, # base is 40
            random_seed=[random_seed,i],
        )

        model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function(model_acceleration_func,forces_function) 
        logger.info("Theorical initialized")
        try:
            simulation_time_m, phase_values = xlsindy.dynamics_modeling.run_rk45_integration(model_dynamics_system, initial_condition, max_time, max_step=0.005)
        except Exception as e:
            logger.error(f"An error occurred on the RK45 integration: {e}")
        logger.info("Theorical simulation done")

        simulation_qpos_m = phase_values[:, ::2]
        simulation_qvel_m = phase_values[:, 1::2]

        simulation_qacc_m = np.gradient(simulation_qvel_m, simulation_time_m, axis=0, edge_order=1)

        force_vector_m = forces_function(simulation_time_m.T).T

        if len(simulation_qvel_g) >0:
            simulation_time_m += np.max(simulation_time_g)

        # Concatenate the data
        simulation_time_g = np.concatenate((simulation_time_g, simulation_time_m.reshape(-1, 1)), axis=0)
        simulation_qpos_g = np.concatenate((simulation_qpos_g, simulation_qpos_m), axis=0)
        simulation_qvel_g = np.concatenate((simulation_qvel_g, simulation_qvel_m), axis=0)
        simulation_qacc_g = np.concatenate((simulation_qacc_g, simulation_qacc_m), axis=0)
        force_vector_g = np.concatenate((force_vector_g, force_vector_m), axis=0)

    return simulation_time_g, simulation_qpos_g, simulation_qvel_g, simulation_qacc_g, force_vector_g, batch_starting_times

#Used for mujoco ref : https://github.com/google-deepmind/mujoco/issues/1014
@contextlib.contextmanager
def temporary_callback(setter, callback):
  setter(callback)
  yield
  setter(None)

def generate_mujoco_trajectory(
    num_coordinates: int,
    initial_position: np.ndarray,
    initial_condition_randomness: np.ndarray,
    random_seed: List[int],
    batch_number: int,
    max_time: float,
    xml_content: str,
    forces_scale_vector: np.ndarray,
    forces_period: np.ndarray,
    forces_period_shift: np.ndarray,
    extra_info: dict,
    mujoco_transform,
    inverse_mujoco_transform,
):
    """
    Generate a MuJoCo trajectory using physics simulation.
    
    This function creates realistic trajectories by simulating the system dynamics
    using MuJoCo physics engine with applied forces and initial conditions.

    Args:
        num_coordinates (int): Number of coordinates in the system.
        initial_position (np.ndarray): Initial position configuration.
        initial_condition_randomness (np.ndarray): Randomness to add to initial conditions.
        random_seed (List[int]): Random seed for reproducibility.
        batch_number (int): Number of trajectory batches to generate.
        max_time (float): Maximum simulation time per batch.
        xml_content (str): MuJoCo XML model definition.
        forces_scale_vector (np.ndarray): Scaling factors for applied forces.
        forces_period (np.ndarray): Period parameters for force generation.
        forces_period_shift (np.ndarray): Phase shift parameters for force generation.
        extra_info (dict): Additional system information including initial conditions.
        mujoco_transform: Function to transform MuJoCo data to desired coordinate system.
        inverse_mujoco_transform: Function to transform desired coordinates to MuJoCo format.

    Returns:
        tuple: (simulation_time_g, simulation_qpos_g, simulation_qvel_g, simulation_qacc_g, force_vector_g)
            - simulation_time_g (np.ndarray): Time vector for all batches.
            - simulation_qpos_g (np.ndarray): Position trajectories for all batches.
            - simulation_qvel_g (np.ndarray): Velocity trajectories for all batches.
            - simulation_qacc_g (np.ndarray): Acceleration trajectories for all batches.
            - force_vector_g (np.ndarray): Applied forces for all batches.
    """
    
    # Initialise 
    simulation_time_g = np.empty((0,1))
    simulation_qpos_g = np.empty((0,num_coordinates))
    simulation_qvel_g = np.empty((0,num_coordinates))
    simulation_qacc_g = np.empty((0,num_coordinates))
    force_vector_g = np.empty((0,num_coordinates))
    batch_starting_times = []

    if len(initial_position)==0:
        initial_position = np.zeros((num_coordinates,2))

    rng = np.random.default_rng(random_seed)

    # initialize Mujoco environment and controller
    mujoco_model = mujoco.MjModel.from_xml_string(xml_content)
    mujoco_data = mujoco.MjData(mujoco_model)

    def random_controller(forces_function):

        def ret(model, data):

            forces = forces_function(data.time)
            data.qfrc_applied = forces

            force_vector_m.append(forces.copy())

            simulation_time_m.append(data.time)
            simulation_qpos_m.append(data.qpos.copy())
            simulation_qvel_m.append(data.qvel.copy())
            simulation_qacc_m.append(data.qacc.copy())

        return ret
    
    
    for i in tqdm(range(batch_number),desc="Generating batches", unit="batch"):

        # Record batch starting time
        batch_start_time = 0.0 if len(simulation_time_g) == 0 else np.max(simulation_time_g)
        batch_starting_times.append(float(batch_start_time))

        # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
        simulation_time_m = []
        simulation_qpos_m = []
        simulation_qvel_m = []
        simulation_qacc_m = []
        force_vector_m = []

        # Initial condition
        initial_condition = np.array(initial_position).reshape(num_coordinates,2) + extra_info["initial_condition"]

        if len(initial_condition_randomness) == 1:
            initial_condition += rng.normal(
                loc=0, scale=initial_condition_randomness, size=initial_condition.shape
            )
        else:
            initial_condition += rng.normal(
                loc=0, scale=np.reshape(initial_condition_randomness,initial_condition.shape)
            )

        initial_qpos,initial_qvel = initial_condition[:,0].reshape(1,-1),initial_condition[:,1].reshape(1,-1)

        initial_qpos,initial_qvel,_ = inverse_mujoco_transform(initial_qpos,initial_qvel,None)

        mujoco_data.qpos = initial_qpos
        mujoco_data.qvel = initial_qvel
        mujoco_data.time = 0.0
        
        forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
            component_count=num_coordinates,
            scale_vector=forces_scale_vector,
            time_end=max_time,
            period=forces_period,
            period_shift=forces_period_shift,
            augmentations=10, # base is 40
            random_seed=[random_seed,i],
        )

        with temporary_callback(mujoco.set_mjcb_control, random_controller(forces_function)):

            pbar_2 = tqdm(
                total=max_time,
                desc="Running Mujoco simulation",
                unit="s",
                leave=False,
                miniters=1,
            )
            while mujoco_data.time < max_time:
                mujoco.mj_step(mujoco_model, mujoco_data)
                pbar_2.update(mujoco_data.time - pbar_2.n)
            pbar_2.close()
            

            # turn the result into a numpy array, and transform the data if needed
        simulation_qpos_m, simulation_qvel_m, simulation_qacc_m = mujoco_transform(
            np.array(simulation_qpos_m), np.array(simulation_qvel_m), np.array(simulation_qacc_m)
        )
        simulation_time_m = np.array(simulation_time_m).reshape(-1, 1)
        force_vector_m = np.array(force_vector_m)

        if len(simulation_qvel_g) >0:
            simulation_time_m += np.max(simulation_time_g)

        # Concatenate the data
        simulation_time_g = np.concatenate((simulation_time_g, simulation_time_m), axis=0)
        simulation_qpos_g = np.concatenate((simulation_qpos_g, simulation_qpos_m), axis=0)
        simulation_qvel_g = np.concatenate((simulation_qvel_g, simulation_qvel_m), axis=0)
        simulation_qacc_g = np.concatenate((simulation_qacc_g, simulation_qacc_m), axis=0)
        force_vector_g = np.concatenate((force_vector_g, force_vector_m), axis=0)

    del mujoco_model, mujoco_data

    return simulation_time_g, simulation_qpos_g, simulation_qvel_g, simulation_qacc_g, force_vector_g, batch_starting_times

def convert_to_lists(d):
    if isinstance(d, dict):
        return {k: convert_to_lists(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_to_lists(i) for i in d]
    elif isinstance(d, np.ndarray):
        return convert_to_lists(d.tolist())
    elif isinstance(d, (np.float32, np.float64)):
        return convert_to_lists(float(d))
    elif isinstance(d,float):
        return float(f"{format(d, '.3e')}")
    else:
        return d
    

def json_format_time_series(
    name:str,
    time:np.ndarray,
    series:Dict[str,np.ndarray],
    sample:int,
    mode_solution:str="mixed",
    ideal_solution_vector:list=None,
    solution_label:List[str]=None,
    reference:bool=False,
    extra_info:Dict=None
):
    """
    Format a time series for json saving.

    Args:
        name (str): the name of the time series.
        time (np.ndarray): the time vector.
        series (List[np.ndarray]): the list of series to save.
        sample (int): the number of sample to save.

    Returns:
        dict: the formatted time series.
    """

    # Uniformly sample 'sample' points from time and each series entry
    if len(time) < sample:
        raise ValueError("Not enough data points to sample from.")
    indices = np.linspace(0, len(time) - 1, sample, dtype=int)

    time = time[indices]
    restricted_series = {k: v[indices] for k, v in series.items()}

    series_dict = {}

    for key, value in restricted_series.items():

        for i in range(value.shape[1]):

            if f"coor_{i}" not in series_dict:
                series_dict[f"coor_{i}"] = {}

            series_dict[f"coor_{i}"][key] = value[:, i].tolist()

    data_json = {
        name: {
            "time": time,
            "series": series_dict,
            "reference": reference,
            "solution": {
                mode_solution: {
                    "vector": ideal_solution_vector,
                    "label": solution_label
                    } 
            }
        }
    }



    if extra_info is not None:
        data_json[name]["extra_info"] = extra_info

    return data_json