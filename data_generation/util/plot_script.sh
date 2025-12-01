# Nice experiment 396f3105ab61308a891bf8131014e04d Noise 0.0

uv run data_generation/util/plot_validation_qpos.py \
    results/396f3105ab61308a891bf8131014e04d.json \
    --noise-level 0.0 \
    --solution "mixed,sindy" 

python ./data_generation/util/plot_validation_qpos_v2.py \
    results/396f3105ab61308a891bf8131014e04d.json \
    -c "mixed,mixed,0.0,lasso_regression,UNI-SINDy" \
    -c "sindy,explicit,0.0,lasso_regression,SINDy" \
    --error

python data_generation/util/plot_validation_qpos_v2.py \
    results/0e35cc88d4b1f5a82f5dc0e90725982d.json \
    -c "mixed,explicit,0.01,lasso_regression,UNI-SINDy"