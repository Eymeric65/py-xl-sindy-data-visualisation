#!/usr/bin/env bash

# Launch this script from the root of the repository.

python -m data_generation.script.align_data \
    --experiment-file "results/0a25fa5db7bcb8cafb152f79f36db501" \
    --optimization-function "lasso_regression" \
    --algorithm "mixed" \
    --regression-type "explicit" \
    --random-seed 1 \
    --noise-level 0.0 \
    --skip-already-done

python -m data_generation.script.align_data \
    --experiment-file "results/0a25fa5db7bcb8cafb152f79f36db501" \
    --optimization-function "lasso_regression" \
    --algorithm "mixed" \
    --regression-type "explicit" \
    --random-seed 1 \
    --noise-level 0.1 \
    --skip-already-done
    