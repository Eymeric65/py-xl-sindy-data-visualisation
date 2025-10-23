#!/usr/bin/env bash

# Launch this script from the root of the repository.

## Mixed force input

## 1 force scale 

## Cartpole
python -m data_generation.script.generate_data \
    --random-seed 1 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 3 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Pendulum
python -m data_generation.script.generate_data \
    --random-seed 4 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 7 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Cartpole double
python -m data_generation.script.generate_data \
    --random-seed 8 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 10 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## 1 force scale 

## Cartpole
python -m data_generation.script.generate_data \
    --random-seed 11 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 13 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Pendulum
python -m data_generation.script.generate_data \
    --random-seed 14 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 16 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Cartpole double
python -m data_generation.script.generate_data \
    --random-seed 17 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 19 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## 1 force scale (only for cartpole double)

## Cartpole double
python -m data_generation.script.generate_data \
    --random-seed 20 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 22 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## no force

## Cartpole
python -m data_generation.script.generate_data \
    --random-seed 23 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 20 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 10 \
    --forces-scale-vector 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 25 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 20 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 10 \
    --forces-scale-vector 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Pendulum
python -m data_generation.script.generate_data \
    --random-seed 26 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 20 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 10 \
    --forces-scale-vector 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 28 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 20 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 10 \
    --forces-scale-vector 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Cartpole double
python -m data_generation.script.generate_data \
    --random-seed 29 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 20 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 10 \
    --forces-scale-vector 0 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 31 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 20 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 10 \
    --forces-scale-vector 0 0 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Full Force

## Cartpole
python -m data_generation.script.generate_data \
    --random-seed 32 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 34 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Pendulum
python -m data_generation.script.generate_data \
    --random-seed 35 \
    --damping-coefficients -1.8 -1.8 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 37 \
    --damping-coefficients -1.2 -1.2 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Cartpole double
python -m data_generation.script.generate_data \
    --random-seed 38 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 


python -m data_generation.script.generate_data \
    --random-seed 40 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 99 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 


python -m data_generation.script.generate_data \
    --random-seed 100 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 5 0 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 101 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 


python -m data_generation.script.generate_data \
    --random-seed 102 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0 5 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 101 \
    --damping-coefficients -1.8 -1.8 -1.8 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 


python -m data_generation.script.generate_data \
    --random-seed 102 \
    --damping-coefficients -1.2 -1.2 -1.2 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 5 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## No damping solution

python -m data_generation.script.generate_data \
    --random-seed 50 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 145 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 51 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 52 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Pendulum

python -m data_generation.script.generate_data \
    --random-seed 53 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 120 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 54 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 55 \
    --damping-coefficients -0.0 -0.0 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/double_pendulum_pm" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

## Cartpole double


python -m data_generation.script.generate_data \
    --random-seed 56 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.05 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 

python -m data_generation.script.generate_data \
    --random-seed 57 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.05 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

python -m data_generation.script.generate_data \
    --random-seed 58 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.05 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

python -m data_generation.script.generate_data \
    --random-seed 59 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.0 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

python -m data_generation.script.generate_data \
    --random-seed 60 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.05 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

python -m data_generation.script.generate_data \
    --random-seed 61 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.0 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0  \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

python -m data_generation.script.generate_data \
    --random-seed 62 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.0 0.0 0.0 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

python -m data_generation.script.generate_data \
    --random-seed 62 \
    --damping-coefficients -0.0 -0.0 -0.0 \
    --batch-number 15 \
    --generation-type "mujoco" \
    --experiment-folder "data_generation/mujoco_align_data/cart_pole_double" \
    --max-time 15 \
    --forces-scale-vector 0.05 0.0 0.05 \
    --initial-condition-randomness 0.05 \
    --initial-position 0.0 0 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000  

