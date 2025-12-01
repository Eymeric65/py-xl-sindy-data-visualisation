
python data_generation/util/plot_validation_qpos.py \
    results_backup/396f3105ab61308a891bf8131014e04d.json \
    ./plots/trajectories_comparison_2.png \
    --solution mixed,sindy \
    --noise 0.0 \
    --regression explicit \
    --error


python data_generation/util/plot_validation_qpos.py \
    results_backup/0e35cc88d4b1f5a82f5dc0e90725982d.json \
    ./plots/double_cartpole.png \
    --solution mixed \
    --noise 0.1 \
    --regression mixed 

python data_generation/util/plot_validation_gpos_refined.py \
    results/0e35cc88d4b1f5a82f5dc0e90725982d.json