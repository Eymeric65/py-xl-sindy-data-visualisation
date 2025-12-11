"""
Docstring for data_generation.script.v2.create_generate_experiment_file

exemple of output:
python -m data_generation.script.v2.generate_data \
    --random-seed 1 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0 0.5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --sample-number 20000 \
    --max-validation-sample 5000

"""

FIXED_ARGS = {
    "batch_number": 5,
    "generation_type": "mujoco",
    "max_time": 10.0,
    "initial_condition_randomness": [3.0],
    "sample_number": 10000,
    "max_validation_sample": 5000
}

INITIAL_POSITIONS = {
    "cart_pole": [
        [0.0, 0.0],
    ],
    "double_pendulum": [
        [0.0, 0.0],
    ],
    "cart_pole_double": [
        [0.0, 0.0, 0.0],
    ],
}

DAMPING_COEFFICIENTS = {
    "cart_pole": [
        [0.0,0.0],
        [-0.5,-0.5],
        [-1.0,-1.0],
        [-2.0,-2.0]
        ],
    "double_pendulum": [
        [0.0,0.0],
        [-0.5,-0.5],
        [-1.0,-1.0],
        [-2.0,-2.0]
        ],
    "cart_pole_double": [
        [0.0,0.0,0.0],
        [-0.5,-0.5,-0.5],
        [-1.0,-1.0,-1.0],
        [-2.0,-2.0,-2.0]
        ],
}

FORCE_SCALE_VECTORS = {
    "cart_pole": [
        [0.0, 0.0],
        [0.0, 0.5],
        [0.5, 0.0],
        [0.5, 0.5]
    ],
    "double_pendulum": [
        [0.0, 0.0],
        [0.0, 0.5],
        [0.5, 0.0],
        [0.5, 0.5]
    ],
    "cart_pole_double": [
        [0.0, 0.0,0.0],
        [0.0, 0.5,0.0],
        [0.0, 0.0,0.5],
        [0.5, 0.0,0.0],
        [0.5, 0.5,0.0],
        [0.0, 0.5,0.5],
        [0.5, 0.0,0.5],
        [0.5, 0.5,0.5]
        ],
}

RANDOM_SEEDS = [1, 2, 3, 4, 5]

EXPERIMENT_FOLDERS = {
    "cart_pole": "data_generation/mujoco_align_data/cart_pole",
    "double_pendulum": "data_generation/mujoco_align_data/double_pendulum_pm",
    "cart_pole_double": "data_generation/mujoco_align_data/cart_pole_double",
}


def format_list(values):
    """Format a list of values for command line arguments"""
    return " ".join(str(v) for v in values)


def generate_command(experiment_name, random_seed, damping_coef, initial_pos, force_scale):
    """Generate a single command string for the given configuration"""
    args = []
    
    # Random seed
    args.append(f"--params.random-seed {random_seed}")
    
    # Damping coefficients
    args.append(f"--params.damping-coefficients {format_list(damping_coef)}")
    
    # Fixed args
    args.append(f"--params.batch-number {FIXED_ARGS['batch_number']}")
    args.append(f"--params.generation-type \"{FIXED_ARGS['generation_type']}\"")
    args.append(f"--params.max-time {FIXED_ARGS['max_time']}")
    args.append(f"--params.sample-number {FIXED_ARGS['sample_number']}")
    args.append(f"--params.max-validation-sample {FIXED_ARGS['max_validation_sample']}")
    
    # Experiment folder
    args.append(f"--params.experiment-folder \"{EXPERIMENT_FOLDERS[experiment_name]}\"")
    
    # Initial condition randomness
    args.append(f"--params.initial-condition-randomness {format_list(FIXED_ARGS['initial_condition_randomness'])}")
    
    # Initial position (need to duplicate each value to match qpos, qvel format)
    initial_pos_full = []
    for val in initial_pos:
        initial_pos_full.extend([val, 0.0])
    args.append(f"--params.initial-position {format_list(initial_pos_full)}")
    
    # Force scale vector
    args.append(f"--params.forces-scale-vector {format_list(force_scale)}")
    
    # Build full command
    command = f"python -m data_generation.script.v2.generate_data {' '.join(args)}"
    return command


def main():
    """Generate all experiment commands and save to file"""
    commands = []
    
    for experiment_name in EXPERIMENT_FOLDERS.keys():
        print(f"Generating commands for {experiment_name}...")
        
        damping_coeffs = DAMPING_COEFFICIENTS[experiment_name]
        initial_positions = INITIAL_POSITIONS[experiment_name]
        force_scale_vectors = FORCE_SCALE_VECTORS[experiment_name]
        
        for random_seed in RANDOM_SEEDS:
            for damping_coef in damping_coeffs:
                for initial_pos in initial_positions:
                    for force_scale in force_scale_vectors:
                        command = generate_command(
                            experiment_name,
                            random_seed,
                            damping_coef,
                            initial_pos,
                            force_scale
                        )
                        commands.append(command)
    
    # Save to file
    output_file = "data_generation/generate_all_experiments.sh"
    with open(output_file, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated experiment commands\n")
        f.write(f"# Total commands: {len(commands)}\n\n")
        
        for i, cmd in enumerate(commands, 1):
            f.write(f"# Command {i}/{len(commands)}\n")
            f.write(f"{cmd}\n\n")
    
    print(f"\nGenerated {len(commands)} commands")
    print(f"Output saved to: {output_file}")
    print(f"\nTo run all experiments, execute: bash {output_file}")


if __name__ == "__main__":
    main()

