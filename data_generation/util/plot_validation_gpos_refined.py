from pydantic import BaseModel

class GenerationSettings(BaseModel):

    batch_number:int
    damping_coefficients:list[float]
    experiment_folder:str
    forces_period:float
    forces_period_shift:float
    forces_scale_vector:list[float]
    generation_type:str
    initial_condition_randomness:list[float]
    initial_position:list[float]
    max_time:float
    max_validation_sample:int
    random_seed:list[int]
    sample_number:int
    validation_time:float
    visualisation_sample:int

class ExperimentData(BaseModel):

    time:list[float]|None = None

    class CoordinateSeries(BaseModel):
        qpos:list[float]
        qvel:list[float]
        qacc:list[float]
        forces:list[float]

    series:dict[str,CoordinateSeries]
    reference:bool

    class SolutionData(BaseModel):
        vector:list[list[float]]|None = None
        label:list[str]|None = None

    solution:dict[str,SolutionData]
    

    class ExtraInfo(BaseModel):
        noise_level:float
        optimization_function:str
        random_seed:list[int]
        regression_type:str
        valid:bool
        regression_time:float|None
        timeout:bool

        class Result(BaseModel):

            RMSE_acceleration:float|None = None

        results:Result

    extra_info:ExtraInfo|None = None

class ExperimentFile(BaseModel):

    generation_settings:GenerationSettings
    data_path:str

    class Visualisation(BaseModel):

        class VisualisationGroup(BaseModel):
            data:dict[str,ExperimentData]
            batch_starting_times:list[float]|None = None

        training_group:VisualisationGroup
        validation_group:VisualisationGroup

    visualisation:Visualisation

def load_experiment_file(file_path: str) -> ExperimentFile:
    import json

    with open(file_path, 'r') as f:
        data = json.load(f)

    experiment_file = ExperimentFile(**data)
    return experiment_file

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python plot_validation_gpos_refined.py <experiment_file.json>")
        sys.exit(1)

    experiment_file_path = sys.argv[1]
    experiment_data = load_experiment_file(experiment_file_path)

    print(experiment_data)
