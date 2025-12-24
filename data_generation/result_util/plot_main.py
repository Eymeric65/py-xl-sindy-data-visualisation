from .plot_util import import_data, filter_data, RegressionAlgorithm, ComboRegistry,Combo,System, generate_boxplot_data, plot_boxplot, plot_success_rate
import seaborn as sns
import pandas as pd

# Use seaborn deep palette colors
DEEP_PALETTE = sns.color_palette("deep", 10)

COMBOS_EXPLICIT = ComboRegistry([
    Combo(
        pretty_name="UNI-SINDy (new)",
        paradigm="mixed",
        regression_type="mixed",
        color="#{:02x}{:02x}{:02x}".format(int(DEEP_PALETTE[0][0]*255), int(DEEP_PALETTE[0][1]*255), int(DEEP_PALETTE[0][2]*255))
    ),
    Combo(
        pretty_name="XlSINDy",
        paradigm="xlsindy",
        regression_type="explicit",
        color="#{:02x}{:02x}{:02x}".format(int(DEEP_PALETTE[3][0]*255), int(DEEP_PALETTE[3][1]*255), int(DEEP_PALETTE[3][2]*255))
    ),
    Combo(
        pretty_name="SINDy",
        paradigm="sindy",
        regression_type="explicit",
        color="#{:02x}{:02x}{:02x}".format(int(DEEP_PALETTE[2][0]*255), int(DEEP_PALETTE[2][1]*255), int(DEEP_PALETTE[2][2]*255))
    ),
])

COMBOS_IMPLICIT = ComboRegistry([
    Combo(
        pretty_name="UNI-SINDy (new)",
        paradigm="mixed",
        regression_type="mixed",
        color="#{:02x}{:02x}{:02x}".format(int(DEEP_PALETTE[0][0]*255), int(DEEP_PALETTE[0][1]*255), int(DEEP_PALETTE[0][2]*255))
    ),
    Combo(
        pretty_name="SINDy-PI",
        paradigm="sindy",
        regression_type="implicit",
        color="#{:02x}{:02x}{:02x}".format(int(DEEP_PALETTE[9][0]*255), int(DEEP_PALETTE[9][1]*255), int(DEEP_PALETTE[9][2]*255))
    ),
])

# Pretty names for experiment types
SYSTEMS = {
    "cartpole": System(pretty_name='Cartpole', name='cart_pole'),
    "cartpole_double": System(pretty_name='Double Pendulum on Cartpole', name='cart_pole_double'),
    "double_pendulum_pm": System(pretty_name='Double Pendulum', name='double_pendulum_pm')
}

def batch_plot(
        data: pd.DataFrame,
        output_folder: str,
        combos: ComboRegistry,
        systems: list[System]|None=None,
        **kwargs
        ):
    
    filtered_data = filter_data(
        data,
        **kwargs
    )



    # Filter by system for individual plots

    # Generate BPSystemData structures
    bp_data_combined = generate_boxplot_data(
        filtered_data,
        combo_registry=combos,
        system_name="All Systems"
    )
    
    if systems is not None:
        bp_data_filtered_by_system = [
            generate_boxplot_data(
                filter_data(filtered_data, system_filter=system),
                  combo_registry=combos,
                  system_name=system.pretty_name
            ) for system in systems
        ]

    for style in ['dark_background', 'white_background']:

        plot_boxplot(
            filename="noise_comparison_combined",
            box_plot_data=[bp_data_combined],
            style=style,
            output_dir=output_folder
        )

        plot_success_rate(
            filename="success_rate_combined",
            box_plot_data=[bp_data_combined],
            style=style,
            output_dir=output_folder
        )

        if systems is not None:
            
            plot_boxplot(
                filename=f"noise_comparison",
                box_plot_data=bp_data_filtered_by_system,
                style=style,
                output_dir=output_folder
            )

            plot_success_rate(
                filename=f"success_rate",
                box_plot_data=bp_data_filtered_by_system,
                style=style,
                output_dir=output_folder
            )


if __name__ == "__main__":

    # Example usage showing sequential pipeline
    data_file = 'results_database.csv'
    
    # Step 1: Import data
    data = import_data(data_file)
    print(f"Loaded {len(data)} experiments")

    # Step 2: Filter data (you can chain multiple filters or create custom ones)
    algo_name = "lasso_regression"
    end_time_threshold = 18

    # No damping experiments with explicit forcing
    batch_plot(
        data,
        output_folder="plots_no_damping_explicit",
        algo_filter=RegressionAlgorithm(pretty_name="Lasso", name=algo_name),
        end_time_treshold=end_time_threshold,
        no_damping=True,
        force_mode="explicit",
        combos=COMBOS_EXPLICIT,
        systems=[
            SYSTEMS["cartpole"],
            SYSTEMS["cartpole_double"],
            SYSTEMS["double_pendulum_pm"]
        ]
    )

    # Damping experiments with explicit forcing
    batch_plot(
        data,
        output_folder="plots_damping_explicit",
        algo_filter=RegressionAlgorithm(pretty_name="Lasso", name=algo_name),
        end_time_treshold=end_time_threshold,
        no_damping=False,
        force_mode="explicit",
        combos=COMBOS_EXPLICIT,
        systems=[
            SYSTEMS["cartpole"],
            SYSTEMS["cartpole_double"],
            SYSTEMS["double_pendulum_pm"]
        ]
    )

    # Damping experiments with implicit forcing
    batch_plot(
        data,
        output_folder="plots_damping_implicit",
        algo_filter=RegressionAlgorithm(pretty_name="Lasso", name=algo_name),
        end_time_treshold=end_time_threshold,
        no_damping=False,
        force_mode="implicit",
        combos=COMBOS_IMPLICIT,
        systems=[
            SYSTEMS["cartpole"],
            SYSTEMS["cartpole_double"],
            SYSTEMS["double_pendulum_pm"]
        ]
    )

    # Damping experiments mixed forcing
    batch_plot(
        data,
        output_folder="plots_damping_mixed",
        algo_filter=RegressionAlgorithm(pretty_name="Lasso", name=algo_name),
        end_time_treshold=end_time_threshold,
        no_damping=False,
        force_mode=None,
        combos=COMBOS_EXPLICIT,
        systems=[
            SYSTEMS["cartpole"],
            SYSTEMS["cartpole_double"],
            SYSTEMS["double_pendulum_pm"]
        ]
    )