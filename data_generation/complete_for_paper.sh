sh data_generation/generate_list.sh


cpulimit -l 2000 -- python -m data_generation.script.automatic_align \
    --max-workers 4 \
    --noise-levels 0.0 0.01 0.1 0.001 \
    --random-seed 1 \
    --data-ratio 2 \
    --optimization-function "lasso_regression" 

## The one of the paper final 

cpulimit -l 2000 -- python -m data_generation.script.automatic_align \
    --max-workers 4     \
    --noise-levels 0.0 0.01 0.1 0.001     \
    --random-seed 1     \
    --data-ratio 2 \
    --optimization-function "proximal_gradient_descent" 