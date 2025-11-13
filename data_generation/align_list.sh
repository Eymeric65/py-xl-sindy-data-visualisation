#!/usr/bin/env bash

# Launch this script from the root of the repository.

python -m data_generation.script.align_data \
    --experiment-file "results/87d4f0dd47db5bb21fcd22ee71c1c6cd" \
    --optimization-function "lasso_regression" \
    --algorithm "mixed" \
    --regression-type "explicit" \
    --random-seed 1 \
    --noise-level 0.0 \
    --skip-already-done

python -m data_generation.script.align_data \
    --experiment-file "results/87d4f0dd47db5bb21fcd22ee71c1c6cd" \
    --optimization-function "lasso_regression_rapids" \
    --algorithm "mixed" \
    --regression-type "explicit" \
    --random-seed 1 \
    --noise-level 0.0 \
    --data-ratio 10 \
    --no-skip-already-done

python -m data_generation.script.align_data \
    --experiment-file "results/87d4f0dd47db5bb21fcd22ee71c1c6cd" \
    --optimization-function "lasso_regression" \
    --algorithm "mixed" \
    --regression-type "explicit" \
    --random-seed 1 \
    --noise-level 0.1 \
    --skip-already-done

python -m data_generation.script.align_data \
    --experiment-file "results/87d4f0dd47db5bb21fcd22ee71c1c6cd" \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --regression-type "explicit" \
    --random-seed 1 \
    --noise-level 0.0 \
    --skip-already-done

python -m data_generation.script.align_data \
    --experiment-file "results/87d4f0dd47db5bb21fcd22ee71c1c6cd" \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --regression-type "mixed" \
    --random-seed 1 \
    --noise-level 0.0 \
    --skip-already-done
    
    

## Test 

5a5ba2b386a8e7abcdaa6fe9ca268947

python -m data_generation.script.align_data \
    --experiment-file "results/5a5ba2b386a8e7abcdaa6fe9ca268947" \
    --optimization-function "lasso_regression" \
    --algorithm "mixed" \
    --regression-type "mixed" \
    --random-seed 1 \
    --noise-level 0.0 \
    --skip-already-done