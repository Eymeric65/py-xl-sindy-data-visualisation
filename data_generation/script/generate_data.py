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

from data_generation.script.util import generate_theorical_trajectory

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

    def get_json(self) -> str: 
        """Generate a JSON string from parameters."""
        return json.dumps(vars(self), sort_keys=True)

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
    
    # Batch generation of data


    # Batch generation
    if args.generation_type == "mujoco" : # Mujoco Generation
        

        # Initialise 
        simulation_time_g = np.empty((0,1))
        simulation_qpos_g = np.empty((0,num_coordinates))
        simulation_qvel_g = np.empty((0,num_coordinates))
        simulation_qacc_g = np.empty((0,num_coordinates))
        force_vector_g = np.empty((0,num_coordinates))

        if len(args.initial_position)==0:
            args.initial_position = np.zeros((num_coordinates,2))

        rng = np.random.default_rng(args.random_seed)

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
        
        for i in tqdm(range(args.batch_number),desc="Generating batches", unit="batch"):

            # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
            simulation_time_m = []
            simulation_qpos_m = []
            simulation_qvel_m = []
            simulation_qacc_m = []
            force_vector_m = []

            # Initial condition
            initial_condition = np.array(args.initial_position).reshape(num_coordinates,2) + extra_info["initial_condition"]

            if len(args.initial_condition_randomness) == 1:
                initial_condition += rng.normal(
                    loc=0, scale=args.initial_condition_randomness, size=initial_condition.shape
                )
            else:
                initial_condition += rng.normal(
                    loc=0, scale=np.reshape(args.initial_condition_randomness,initial_condition.shape)
                )

            initial_qpos,initial_qvel = initial_condition[:,0].reshape(1,-1),initial_condition[:,1].reshape(1,-1)

            initial_qpos,initial_qvel,_ = inverse_mujoco_transform(initial_qpos,initial_qvel,None)

            mujoco_data.qpos = initial_qpos
            mujoco_data.qvel = initial_qvel
            mujoco_data.time = 0.0
            
            forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
                component_count=num_coordinates,
                scale_vector=args.forces_scale_vector,
                time_end=args.max_time,
                period=args.forces_period,
                period_shift=args.forces_period_shift,
                augmentations=10, # base is 40
                random_seed=[args.random_seed,i],
            )


            mujoco.set_mjcb_control(
                random_controller(forces_function)
            )  # use this for the controller, could be made easier with using directly the data from mujoco.

            pbar_2 = tqdm(
                total=args.max_time,
                desc="Running Mujoco simulation",
                unit="s",
                leave=False,
                miniters=1,
            )
            while mujoco_data.time < args.max_time:
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

    elif args.generation_type == "theorical": # Theorical generation

        (simulation_time_g, 
         simulation_qpos_g, 
         simulation_qvel_g, 
         simulation_qacc_g, 
         force_vector_g) = generate_theorical_trajectory(
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

    raw_sample_number = len(simulation_time_g)
    logger.info( f"Raw simulation len {raw_sample_number}")

    # Reduce the data to the desired lenght

    subsample = raw_sample_number // args.sample_number

    if subsample == 0 :
        subsample =1

    truncation = 20

    simulation_time_g = simulation_time_g[truncation:-truncation:subsample]
    simulation_qpos_g = simulation_qpos_g[truncation:-truncation:subsample]
    simulation_qvel_g = simulation_qvel_g[truncation:-truncation:subsample]
    simulation_qacc_g = simulation_qacc_g[truncation:-truncation:subsample]
    force_vector_g = force_vector_g[truncation:-truncation:subsample]

    data = {
        "simulation_time": simulation_time_g,
        "simulation_qpos": simulation_qpos_g,
        "simulation_qvel": simulation_qvel_g,
        "simulation_qacc": simulation_qacc_g,
        "force_vector": force_vector_g,
    }

    # Save pickle file

    filename = f"results/{args.get_uid()}.pkl"
    with open(filename,'wb') as f : 
        pickle.dump(data, f)
    logger.info(f"Data saved with uid {args.get_uid()}")

    settings_dict = json.loads(args.get_json())

    data = {
        "generation_settings" : settings_dict,
        "data_path" : filename,
        "results" : {}
        }

    # Save json file
    json_filename = f"results/{args.get_uid()}.json"
    with open(json_filename,'w') as f :
        json.dump(data, f, indent=4)
    logger.info(f"Settings saved with uid {args.get_uid()}")



