// TypeScript types matching the Python dataclass.py structure

export interface DataGenerationParams {
  experiment_folder: string;
  damping_coefficients: number[];
  random_seed: number[];
  batch_number: number;
  generation_type: string;
  max_time: number;
  initial_condition_randomness: number[];
  initial_position: number[];
  forces_scale_vector: number[];
  sample_number: number;
  visualisation_sample: number;
  validation_time: number;
  max_validation_sample: number;
  UID: string;
}

export interface RegressionParameter {
  optimization_function: string;
  paradigm: string;
  regression_type: string;
  noise_level: number;
  random_seed: number[];
  data_ratio: number;
  UID: string;
}

export interface RegressionResult {
  regression_parameters: RegressionParameter;
  valid: boolean;
  regression_time: number | null;
  timeout: boolean;
  RMSE_acceleration: number | null;
  RMSE_validation_position: number | null;
}

export interface CoordinateSeries {
  coordinate_number: number;
  data: number[];
}

export interface DataSeries {
  series: CoordinateSeries[];
}

export interface TimeSeries {
  time: number[];
}

export interface Series {
  time: TimeSeries;
  qpos: DataSeries;
  qvel: DataSeries;
  qacc: DataSeries;
  forces: DataSeries;
  sample_number: number;
}

export interface Solution {
  mode_solution: string;
  solution_vector: number[];
  solution_label: string[];
}

export interface TrajectoryData {
  name: string;
  series: Series | null;
  solutions: Solution[] | null;
  reference: boolean;
  regression_result: RegressionResult | null;
}

export interface TrajectoryGroup {
  batch_starting_time: number[];
  trajectories: TrajectoryData[];
}

export interface ExperimentData {
  validation_group: TrajectoryGroup;
  training_group: TrajectoryGroup;
}

export interface Experiment {
  generation_params: DataGenerationParams;
  data_path: string;
  data: ExperimentData;
}

// Helper types for the flattened data structure used in visualization
export interface FlatDataPoint {
  time: number;
  [key: string]: number; // Dynamic keys like "coor_0.qpos", "1.coor_0.qpos", etc.
}

export interface GroupedLines {
  [varType: string]: {
    [coordinate: string]: string[];
  };
}
