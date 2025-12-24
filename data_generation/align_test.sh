python -m data_generation.script.v2.align_data \
    --experiment-file results_test/0ac9a5bceb8702162e1358cb032d81ad \
    --no-skip-already-done  \
    --regression-parameters.optimization-function lasso_regression \
    --regression-parameters.paradigm sindy \
    --regression-parameters.regression-type mixed \
    --regression-parameters.noise-level 0.0 \
    --regression-parameters.random-seed 1 \
    --regression-parameters.data-ratio 1.5

python -m data_generation.script.v2.align_data \
    --experiment-file results_test/0ac9a5bceb8702162e1358cb032d81ad \
    --no-skip-already-done  \
    --regression-parameters.optimization-function lasso_regression \
    --regression-parameters.paradigm mixed \
    --regression-parameters.regression-type mixed \
    --regression-parameters.noise-level 0.0 \
    --regression-parameters.random-seed 1 \
    --regression-parameters.data-ratio 1.5

python -m data_generation.script.v2.align_data \
    --experiment-file results_test/0ac9a5bceb8702162e1358cb032d81ad \
    --no-skip-already-done  \
    --regression-parameters.optimization-function lasso_regression \
    --regression-parameters.paradigm mixed \
    --regression-parameters.regression-type explicit \
    --regression-parameters.noise-level 0.0 \
    --regression-parameters.random-seed 1 \
    --regression-parameters.data-ratio 1.5



