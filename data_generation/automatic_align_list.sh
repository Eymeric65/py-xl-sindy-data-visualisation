
cpulimit -l 2000 -- python -m data_generation.script.automatic_align \
    --max-workers 1 \
    --algorithms "mixed" \
    --noise-levels 0.0 0.01 0.1 0.001 \
    --random-seed 1 \
    --data-ratio 2 \
    --verbose

cpulimit -l 2000 -- python -m data_generation.script.automatic_align \
    --max-workers 1 \
    --regression-types "explicit" \
    --noise-levels 0.0 0.01 0.1 0.001 \
    --random-seed 1 \
    --data-ratio 2 \
    --experiment-folders "cart_pole" "double_pendulum_pm"

cpulimit -l 2000 -- python -m data_generation.script.automatic_align \
    --max-workers 4 \
    --noise-levels 0.0 0.01 0.1 0.001 \
    --random-seed 1 \
    --data-ratio 2 \
    --experiment-folders "cart_pole" "double_pendulum_pm"

## The one of the paper final 

cpulimit -l 2000 -- python -m data_generation.script.automatic_align \
    --max-workers 4     \
    --noise-levels 0.0 0.01 0.1 0.001     \
    --random-seed 1     \
    --data-ratio 2 \
    --optimization-function "proximal_gradient_descent" \
    --verbose