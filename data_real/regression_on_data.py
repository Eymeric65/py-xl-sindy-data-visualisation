import xlsindy
import sympy as sp
import numpy as np
import pandas as pd
import glob
import os
import time
import matplotlib.pyplot as plt
from scipy import signal
from generate_trajectory import generate_theoretical_trajectory

robot_file = 'robot_data_20251226_175038.csv'
data_ratio = 10.2

angle_offset=0
## The transformation used to convert from the real robot data to the mujoco simulation data.
def mujoco_transform(pos, vel, acc):

    pos = -np.cumsum(pos, axis=1) + angle_offset
    vel = -np.cumsum(vel, axis=1)
    acc = -np.cumsum(acc, axis=1)

    return pos, vel, acc

def inverse_mujoco_transform(tpos, tvel, tacc):
    """
    Given outputs of mujoco_transform (tpos, tvel, tacc),
    recover the original pos, vel, acc (all shape (batch, n)).
    """
    # Undo the negated cumsum (and offset for angles)
    S_pos = -(tpos - angle_offset)
    S_vel = -tvel
    if tacc is not None:
        S_acc = -tacc

    # invert cumulative sum by taking differences (with zero prepended)
    pos = np.diff(S_pos, axis=1, prepend=np.zeros((S_pos.shape[0],1)))
    vel = np.diff(S_vel, axis=1, prepend=np.zeros((S_vel.shape[0],1)))
    if tacc is not None:
        acc = np.diff(S_acc, axis=1, prepend=np.zeros((S_acc.shape[0],1)))

    if tacc is not None:
        return pos, vel, acc
    else:
        return pos, vel, None


## Create the catalog (Mandatory part)
time_sym = sp.symbols("t")

num_coordinates = 2

symbols_matrix = xlsindy.symbolic_util.generate_symbolic_matrix(
    num_coordinates, time_sym
)

function_catalog_1 = [lambda x: symbols_matrix[2, x]]
function_catalog_2 = [
    lambda x: sp.sin(symbols_matrix[1, x]),
    lambda x: sp.cos(symbols_matrix[1, x]),
]

friction_function = np.array(
    [[symbols_matrix[2, x] for x in range(num_coordinates)]]
)

catalog_part1 = np.array(
    xlsindy.symbolic_util.generate_full_catalog(
        function_catalog_1, num_coordinates, 2
    )
)
catalog_part2 = np.array(
    xlsindy.symbolic_util.generate_full_catalog(
        function_catalog_2, num_coordinates, 2
    )
)
cross_catalog = np.outer(catalog_part2, catalog_part1)

lagrange_catalog = np.concatenate(
    (cross_catalog.flatten(), catalog_part1, catalog_part2)
) 

friction_catalog = (
    friction_function.flatten()
)  # Contain only \dot{q}_1 \dot{q}_2

expand_matrix = np.ones((len(friction_catalog), num_coordinates), dtype=int)


catalog_repartition = xlsindy.catalog.CatalogRepartition(
    [
        xlsindy.catalog_base.ExternalForces(
            [[1], [2]], symbols_matrix
        ),
        xlsindy.catalog_base.Lagrange(
            lagrange_catalog, symbols_matrix, time_sym
        ),
        xlsindy.catalog_base.Classical(
            friction_catalog, expand_matrix
        ),
    ]
)

## Import the data from the real robot

# Load all robot data CSV files
data_files = glob.glob("robot_data_*.csv")
if not data_files:
    raise FileNotFoundError("No robot data files found matching 'robot_data_*.csv'")

print(f"Found {len(data_files)} data file(s):")
for file in sorted(data_files):
    print(f"  - {file}")

# Load and concatenate all CSV files with proper time offset
df_list = []
time_offset = 0.0

truncate = 10

for file in sorted(data_files):
    df_temp = pd.read_csv(file)

    df_temp = df_temp[truncate:-truncate]
    
    # Add time offset to make time continuous
    if time_offset > 0:
        df_temp['time'] = df_temp['time'] + time_offset
    
    # Update offset for next file (add a small gap between files)
    time_offset = df_temp['time'].max() + 0.01  # 10ms gap between sessions
    
    df_list.append(df_temp)

df = pd.concat(df_list, ignore_index=True)
print(f"Loaded total of {len(df)} data points from {len(data_files)} file(s)")
print(f"Total time span: {df['time'].min():.2f}s to {df['time'].max():.2f}s")

# Extract module names (assumes format: position_ModuleName, velocity_ModuleName, etc.)
modules_name = ["Shoulder","Elbow"]  # Same as in gather_data.py
n_coordinates = len(modules_name)

# Extract time
train_time = df['time'].values
m_time = len(train_time)

# Initialize arrays with shape (m_time, n_coordinates)
train_position = np.zeros((m_time, n_coordinates))
train_velocity = np.zeros((m_time, n_coordinates))
train_forces = np.zeros((m_time, n_coordinates))

# Fill the arrays
for i, module in enumerate(modules_name):
    train_position[:, i] = df[f'position_{module}'].values
    train_velocity[:, i] = df[f'velocity_{module}'].values
    train_forces[:, i] = df[f'effort_{module}'].values

# Compute acceleration using numerical derivative
# Using central differences for interior points, forward/backward for edges

# Simple method: use numpy gradient
train_acceleration = np.zeros((m_time, n_coordinates))
for i in range(n_coordinates):
    train_acceleration[:, i] = np.gradient(train_velocity[:, i], train_time)

# Apply low-pass Butterworth filter to remove noise from acceleration
dt_mean = np.mean(np.diff(train_time))
fs = 1.0 / dt_mean  # Sampling frequency
cutoff = 5.0  # Cutoff frequency in Hz (adjust as needed)
order = 4  # Filter order

# Design Butterworth filter
nyquist = fs / 2.0
normal_cutoff = cutoff / nyquist
b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)

# Apply filter to acceleration
train_acceleration_filtered = np.zeros_like(train_acceleration)
for i in range(n_coordinates):
    train_acceleration_filtered[:, i] = signal.filtfilt(b, a, train_acceleration[:, i])

train_acceleration = train_acceleration_filtered
print(f"Acceleration filtered with {order}th order Butterworth filter (cutoff: {cutoff} Hz)")

print(f"Data shape:")
print(f"  position: {train_position.shape}")
print(f"  velocity: {train_velocity.shape}")
print(f"  acceleration: {train_acceleration.shape}")
print(f"  forces: {train_forces.shape}")
print(f"  time points: {m_time}")
print(f"  coordinates: {n_coordinates}")

## Apply mujoco transformation
train_position, train_velocity, train_acceleration = mujoco_transform(
    train_position, train_velocity, train_acceleration
)

## sampling to data ratio
catalog_size = catalog_repartition.catalog_length


# Sample uniformly n samples from the imported arrays
n_samples = int(catalog_size * data_ratio)
total_samples = train_position.shape[0]



if n_samples < total_samples:

    # Evenly spaced sampling (deterministic, uniform distribution)
    sample_indices = np.linspace(truncate, total_samples - 1 - truncate, n_samples, dtype=int)
    
    # Apply sampling to all arrays
    t_position = train_position[sample_indices]
    t_velocity = train_velocity[sample_indices]
    t_acceleration = train_acceleration[sample_indices]
    t_forces = train_forces[sample_indices]
    t_train_time = train_time[sample_indices]
    
    print(f"Sampled {n_samples} points uniformly from {total_samples} total samples")
else:
    print(f"Using all {total_samples} samples (requested {n_samples})")

pre_knowledge_indices = np.array([0,1]) + catalog_repartition.starting_index_by_type("ExternalForces")
pre_knowledge_mask = np.zeros((catalog_repartition.catalog_length,))
pre_knowledge_mask[pre_knowledge_indices] = 1.0

print(sample_indices)

start_time = time.perf_counter()

solution, exp_matrix = xlsindy.simulation.regression_mixed(
    theta_values=t_position,
    velocity_values=t_velocity,
    acceleration_values=t_acceleration,
    time_symbol=time_sym,
    symbol_matrix=symbols_matrix,
    catalog_repartition=catalog_repartition,
    external_force=t_forces,
    #regression_function=regression_function,#Lasso by default
    pre_knowledge_mask=pre_knowledge_mask
)

regression_time = time.perf_counter() - start_time

print(f"Regression completed in {regression_time:.2f} seconds")

threshold = 1e-2  # Adjust threshold value as needed
solution = np.where(np.abs(solution)/np.linalg.norm(solution) < threshold, 0, solution)

##--------------------------------

final_equation=[]
catalog_label = catalog_repartition.label()
print("Identified model terms:")
for idx, coeff in enumerate(solution.flatten()):
    if coeff != 0:
        print(f"  Coefficient: {coeff:.6f} | Term: {catalog_label[idx]}")
        final_equation.append((coeff, catalog_label[idx]))

##--------------------------------
for term in final_equation:
    print(f"{term[0]:+.6f} * {term[1]}")

model_acceleration_func, valid_model = (
    xlsindy.dynamics_modeling.generate_acceleration_function(
        solution, 
        catalog_repartition,
        symbols_matrix,
        time_sym,
        lambdify_module="jax",
    )
)

if valid_model:
    component_count = 2
    print("Valid model generated.")
    time_end = 100.0
    random_seed = 42
    scale_vector = [0.5 for _ in range(component_count)]

    forces_function = xlsindy.dynamics_modeling.sinusoidal_force_generator(
        component_count=component_count,
        scale_vector=scale_vector,
        time_end=time_end,
        num_frequencies=5,
        freq_range=(0.01,1.0),
        random_seed=random_seed,
    )

    initial_position = [ 
        train_position[0,0],
        train_velocity[0,1],
        train_position[0,1],
        train_velocity[0,1]
        ]

    (simulation_time_g, 
    simulation_qpos_g, 
    simulation_qvel_g, 
    simulation_qacc_g, 
    force_vector_g,
    _) = generate_theoretical_trajectory(
        num_coordinates,
        initial_position,
        0,
        [0], # Ensure same seed as for data generation
        1,
        time_end,
        solution,
        catalog_repartition,
        time_sym,
        symbols_matrix,
        scale_vector,
    )

    # Split data into training and validation
    # Use the sampled data for training, and generate validation from model
    
    # Validation data from simulation
    val_qpos = simulation_qpos_g 
    val_qvel = simulation_qvel_g
    val_qacc = simulation_qacc_g
    val_time = simulation_time_g
    
    # Calculate acceleration/forces ratio (avoid division by zero)
    train_acc_force_ratio = np.divide(train_acceleration, train_forces, 
                                      where=np.abs(train_forces)>1e-6, 
                                      out=np.zeros_like(train_acceleration))
    val_acc_force_ratio = np.divide(val_qacc, force_vector_g, 
                                    where=np.abs(force_vector_g)>1e-6, 
                                    out=np.zeros_like(val_qacc))
    
    # Create plots
    fig, axes = plt.subplots(5, n_coordinates, figsize=(12, 16))
    fig.suptitle('Training vs Validation Data Comparison', fontsize=16)
    
    data_labels = ['Position (qpos)', 'Velocity (qvel)', 'Acceleration (qacc)', 'Forces', 'Acc/Force Ratio']
    train_data = [train_position, train_velocity, train_acceleration, train_forces, train_acc_force_ratio]
    val_data = [val_qpos, val_qvel, val_qacc, force_vector_g, val_acc_force_ratio]
    
    for row_idx, (label, train_arr, val_arr) in enumerate(zip(data_labels, train_data, val_data)):
        for col_idx, module in enumerate(modules_name):
            ax = axes[row_idx, col_idx]
            
            # Plot training data
            ax.plot(train_time, train_arr[:, col_idx], 'b-', label='Training', alpha=0.7, linewidth=1.5)
            
            # Plot validation data
            ax.plot(val_time, val_arr[:, col_idx], 'r--', label='Validation', alpha=0.7, linewidth=1.5)
            
            ax.set_xlabel('Time (s)')
            ax.set_ylabel(label)
            ax.set_title(f'{module} q_{col_idx} - {label}')
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_vs_validation.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 'training_vs_validation.png'")
    plt.show()
    
else:
    print("Model validation failed - plotting training data only")
    
    # Calculate acceleration/forces ratio (avoid division by zero)
    train_acc_force_ratio = np.divide(train_acceleration, train_forces, 
                                      where=np.abs(train_forces)>1e-6, 
                                      out=np.zeros_like(train_acceleration))
    
    fig, axes = plt.subplots(5, n_coordinates, figsize=(12, 16))
    fig.suptitle('Training Data (Regression Failed)', fontsize=16)
    
    data_labels = ['Position (qpos)', 'Velocity (qvel)', 'Acceleration (qacc)', 'Forces', 'Acc/Force Ratio']
    train_data = [train_position, train_velocity, train_acceleration, train_forces, train_acc_force_ratio]
    
    for row_idx, (label, train_arr) in enumerate(zip(data_labels, train_data)):
        for col_idx, module in enumerate(modules_name):
            ax = axes[row_idx, col_idx]
            
            # Plot training data
            ax.plot(train_time, train_arr[:, col_idx], 'b-', label='Training', alpha=0.7, linewidth=1.5)
            
            ax.set_xlabel('Time (s)')
            ax.set_ylabel(label)
            ax.set_title(f'{module} q_{col_idx} - {label}')
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_data_only.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 'training_data_only.png'")
    plt.show()
