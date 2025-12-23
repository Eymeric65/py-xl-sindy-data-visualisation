from pydantic import BaseModel, Field, computed_field, field_validator
from typing import List, Callable
import hashlib
import numpy as np
from scipy.interpolate import CubicSpline

class DataGenerationParams(BaseModel):

    experiment_folder: str = "None"
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    damping_coefficients: List[float] = Field(default_factory=list)
    """the damping coefficients for the system, this is used to replace the DAMPING value in the environment.xml file"""
    random_seed: List[int] = Field(default_factory=lambda: [0])
    """the random seed of the experiment (only used for force function)"""
    batch_number: int = 1
    """the number of batch to generate, this is used to generate more data mainly in implicit case (default 1)"""
    generation_type: str = "theorical"
    """if true generate the data using mujoco otherwise use the theoritical generator (default true)"""
    max_time: float = 10.0
    """the maximum time for the simulation"""
    initial_condition_randomness: List[float] = Field(default_factory=lambda: [0.0])
    """the randomness of the initial condition, this is used to generate a random initial condition around the initial position for each batch can be a scalar or a list of lenght coordinate times two."""
    initial_position: List[float] = Field(default_factory=list)
    """the initial position of the system"""
    forces_scale_vector: List[float] = Field(default_factory=list)
    """the different scale for the forces vector to be applied, this can mimic an action mask over the system if some entry are 0"""


    ## Non UID fields
    sample_number: int = 1000
    """the number of sample for the trajectory generation"""
    visualisation_sample: int = 1000
    """the number of sample for the visualisation of the trajectory (should be high enough to be smooth)"""
    validation_time: float = 20.0
    """the time for the validation trajectory"""
    max_validation_sample: int = 4000
    """the maximum number of sample for the validation trajectory, if the validation time is too high compared to the max time and the sample number, this will limit the number of sample to avoid memory issues"""
    
    @computed_field
    @property
    def UID(self) -> str:
        """Automatically generated unique identifier based on the UID-relevant fields"""
        model = self.model_dump_json(exclude={"sample_number","visualisation_sample", "validation_time", "max_validation_sample", "UID"})
        return hashlib.md5(model.encode()).hexdigest()

class RegressionParameter(BaseModel):
    optimization_function: str = "lasso_regression"
    """the regression function used in the regression"""
    paradigm: str = "mixed"
    """the name of the algorithm used (for the moment "xlsindy", "sindy" and "mixed" are the only possible)"""
    regression_type: str = "explicit"
    """the type of regression to use (explicit, implicit, mixed)"""
    noise_level: float = 0.0
    """the level of noise introduce in the experiment"""
    random_seed: List[int] = Field(default_factory=lambda: [0])
    """the random seed for the noise"""
    data_ratio: float = 2.0
    """the ratio of data to use (in respect with catalog size)"""

    @computed_field
    @property
    def UID(self) -> str:
        """Automatically generated unique identifier based on the UID-relevant fields"""
        model = self.model_dump_json(exclude={"sample_number","visualisation_sample", "validation_time", "max_validation_sample", "UID"})
        return hashlib.md5(model.encode()).hexdigest()

class RegressionResult(BaseModel):
    """the result of the regression default to a timeouted regression"""

    regression_parameters: RegressionParameter
    """the regression parameters used for the regression"""
    valid:bool = False
    """if the regression was valid or not"""
    regression_time: float|None = None
    """the time taken for the regression"""
    timeout:bool = True
    """if the regression timed out or not"""
    RMSE_acceleration: float|None = None
    """the root mean square error on the acceleration prediction"""
    RMSE_validation_position: float|None = None
    """the root mean square error on the position prediction on the validation trajectory"""

class Series(BaseModel):

    class TimeSeries(BaseModel):
        time: List[float]

        @classmethod
        def from_numpy(cls, data: np.ndarray,sample_number:int=None):
            flatten_time = data.flatten()
            if sample_number is not None:
                sampling_index = np.linspace(0, len(flatten_time)-1, sample_number, dtype=int)
                return cls(time=flatten_time[sampling_index].tolist())
            else:
                return cls(time=flatten_time.tolist())

    class DataSeries(BaseModel):

        class CordinateSeries(BaseModel):
            coordinate_number: int
            data: List[float]

        series: List[CordinateSeries]

        def get_numpy_series(self)-> np.ndarray:
            coord_data = []
            for coord in self.series:
                coord_data.append(coord.data)
            return np.column_stack(coord_data)

        @classmethod
        def from_numpy(cls, data: np.ndarray,sample_number:int=None):
            series = []
            for i in range(data.shape[1]):
                
                if sample_number is not None:
                    sampling_index = np.linspace(0, data.shape[0]-1, sample_number, dtype=int) 
                    series.append(cls.CordinateSeries(
                        coordinate_number=i,
                        data=data[sampling_index,i].tolist()
                    ))
                else:
                    series.append(cls.CordinateSeries(
                        coordinate_number=i,
                        data=data[:,i].tolist()
                    ))
            return cls(series=series)

    time: TimeSeries
    qpos: DataSeries
    qvel: DataSeries
    qacc: DataSeries
    forces: DataSeries
    sample_number: int
    """the number of sample in the trajectory"""

class Solution(BaseModel):
    mode_solution: str
    """the mode used to generate the solution (mixed, explicit, implicit)"""
    solution_vector: List[float]
    solution_label: List[str]

    @field_validator('solution_vector', mode='before')
    @classmethod
    def convert_solution_vector(cls, v):
        """Automatically convert numpy arrays or other array-like objects to list of floats"""
        if isinstance(v, np.ndarray):
            return v.flatten().tolist()
        return v


class TrajectoryData(BaseModel):

    name: str
    """the name of the trajectory"""
    series: Series|None = None
    solutions : List[Solution]|None = None
    reference:bool = False
    regression_result: RegressionResult|None = None

    def get_solution_mode(self)-> List[str]:
        return [sol.mode_solution for sol in self.solutions]

    @classmethod
    def from_numpy(
        cls, 
        name:str,
        time: np.ndarray, 
        qpos: np.ndarray, 
        qvel: np.ndarray, 
        qacc: np.ndarray, 
        forces: np.ndarray,
        mode_solution: str,
        solution_vector: List[float]|np.ndarray,
        solution_label: List[str],
        reference: bool,
        sample_number: int|None=None,
        reference_time: np.ndarray|None=None,
        regression_result: RegressionResult|None=None
    ):
        
        if reference_time is not None:
            # Interpolate all data onto reference_time
            time_flat = np.array(time).flatten()
            ref_time_flat = np.array( reference_time).flatten()

            # Find the overlapping time range
            start_time = max(time_flat[0], ref_time_flat[0])
            end_time = min(time_flat[-1], ref_time_flat[-1])

            # Create a mask for the overlapping time range
            mask = (ref_time_flat >= start_time) & (ref_time_flat <= end_time)
            new_time = ref_time_flat[mask]

            # Interpolate each data series
            cs_qpos = [CubicSpline(time_flat, qpos[:, i]) for i in range(qpos.shape[1])]
            cs_qvel = [CubicSpline(time_flat, qvel[:, i]) for i in range(qvel.shape[1])]
            cs_qacc = [CubicSpline(time_flat, qacc[:, i]) for i in range(qacc.shape[1])]
            cs_forces = [CubicSpline(time_flat, forces[:, i]) for i in range(forces.shape[1])]

            new_qpos = np.column_stack([cs(new_time) for cs in cs_qpos])
            new_qvel = np.column_stack([cs(new_time) for cs in cs_qvel])
            new_qacc = np.column_stack([cs(new_time) for cs in cs_qacc])
            new_forces = np.column_stack([cs(new_time) for cs in cs_forces])

            return cls(
                name=name,
                series=Series(
                    time=Series.TimeSeries.from_numpy(new_time),
                    qpos=Series.DataSeries.from_numpy(new_qpos),
                    qvel=Series.DataSeries.from_numpy(new_qvel),
                    qacc=Series.DataSeries.from_numpy(new_qacc),
                    forces=Series.DataSeries.from_numpy(new_forces),
                    sample_number=len(new_time),
                ),
                solutions=[
                    Solution(
                        mode_solution=mode_solution,
                        solution_vector=solution_vector,
                        solution_label=solution_label
                    )
                ],
                regression_result=regression_result,
                reference=reference
            )
        else:
            return cls(
                name=name,
                series=Series(
                    time=Series.TimeSeries.from_numpy(time, sample_number=sample_number),
                    qpos=Series.DataSeries.from_numpy(qpos, sample_number=sample_number),
                    qvel=Series.DataSeries.from_numpy(qvel, sample_number=sample_number),
                    qacc=Series.DataSeries.from_numpy(qacc, sample_number=sample_number),
                    forces=Series.DataSeries.from_numpy(forces, sample_number=sample_number),
                    sample_number=sample_number if sample_number is not None else len(time),
                ),
                solutions=[
                    Solution(
                        mode_solution=mode_solution,
                        solution_vector=solution_vector,
                        solution_label=solution_label
                    )
                ],
                reference=reference
            )


class Experiment(BaseModel):
    generation_params: DataGenerationParams
    """the data generation parameters used to generate the data"""
    data_path: str
    """the path to the generated data"""

    class ExperimentData(BaseModel):

        class TrajectoryGroup(BaseModel):
            batch_starting_time:List[float]
            trajectories : List[TrajectoryData]

            def get_trajectory_name(self)-> List[str]:
                return [traj.name for traj in self.trajectories]

            def del_trajectory_by_name(self, name:str)-> None:
                self.trajectories = [traj for traj in self.trajectories if traj.name != name]

            def get_trajectory_by_name(self, name:str)-> TrajectoryData|None:
                for traj in self.trajectories:
                    if traj.name == name:
                        return traj
                return None

        validation_group:TrajectoryGroup
        training_group:TrajectoryGroup

    data:ExperimentData




