"""
The general util for plotting data from the database of experiment. (For tendencies, detail plot are located in other files)
"""

import pandas as pd 

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from pydantic import BaseModel,ConfigDict
from typing import Iterator
from pathlib import Path

import numpy as np

class Combo(BaseModel):
    pretty_name:str
    catalog_type:str
    solution_type:str
    color:str

class RegressionAlgorithm(BaseModel):
    pretty_name:str
    name:str

class RegressionAlgorithmRegistry(BaseModel):
    def __init__(self,registry_name:str,algorithms:list[RegressionAlgorithm]):
        self._algorithms = algorithms
        self.registry_name = registry_name
        self.name = [a.name for a in algorithms]

    def __iter__(self) -> Iterator[RegressionAlgorithm]:
        return iter(self._algorithms)

class System(BaseModel):
    pretty_name:str
    name:str

class SystemRegistry:
    
    def __init__(self,pretty_name:str,systems:list[System]):
        self._systems = systems
        self.pretty_name = pretty_name
        self.name = [s.name for s in systems]

    def __iter__(self) -> Iterator[System]:
        return iter(self._systems)

class BPNoiseData(BaseModel):
    noise_level:float
    validation_errors: list[float]

class BPComboData(BaseModel):
    combo: Combo
    noise_data: list[BPNoiseData]

    def get_by_noise_level(self,noise_level:float)->BPNoiseData|None:
        for nd in self.noise_data:
            if nd.noise_level == noise_level:
                return nd
        return None

class BPSystemData(BaseModel):   

    model_config = ConfigDict(arbitrary_types_allowed=True)

    valid_experiment_number:int
    system_registry:SystemRegistry|System
    combo_data: list[BPComboData]

class ComboRegistry:
    def __init__(self,combos:list[Combo]):
        self._combos = combos
        self.catalog_type = [c.catalog_type for c in combos]
        self.solution_type = [c.solution_type for c in combos]

    def __iter__(self) -> Iterator[Combo]:
        return iter(self._combos)

TARGET_COMBOS = ComboRegistry([
    Combo(
        pretty_name="UNI-SINDy (new)",
        catalog_type="mixed",
        solution_type="mixed",
        color="#3498db"
    ),
    Combo(
        pretty_name="XlSINDy",
        catalog_type="xlsindy",
        solution_type="explicit",
        color="#e74c3c"
    ),
    Combo(
        pretty_name="SINDy",
        catalog_type="sindy",
        solution_type="explicit",
        color="#2ecc71"
    ),
    Combo(
        pretty_name="XlSINDy-PI (new)",
        catalog_type="xlsindy",
        solution_type="implicit",
        color="#602ecc"
    ),
    Combo(
        pretty_name="SINDy-PI",
        catalog_type="sindy",
        solution_type="implicit",
        color="#9b59b6"
    ),
])

# Pretty names for experiment types
SYSTEMS = {
    "cartpole": System(pretty_name='Cartpole', name='cart_pole'),
    "cartpole_double": System(pretty_name='Double Pendulum on Cartpole', name='cart_pole_double'),
    "double_pendulum_pm": System(pretty_name='Double Pendulum', name='double_pendulum_pm')
}

WHITE_BACKGROUND_THEME={
    "boxplot":{
        "meanprops":{
            "marker":"D",
            "markerfacecolor":"white",
            "markeredgecolor":"black",
            "markersize":5,
        },
        "medianprops":{
            "color":"black",
            "linewidth":2
        }
    },
    "annotation_bbox":{
        "bbox":{
            "boxstyle":'round,pad=0.4', 
            "facecolor":'white', 
            "alpha":0.8, 
            "edgecolor":'gray', 
            "linewidth":1
        }
    }
}

BLACK_BACKGROUND_THEME={
    "boxplot":{
        "meanprops":{
            "marker":"D",
            "markerfacecolor":"black",
            "markeredgecolor":"white",
            "markersize":5,
        },
        "medianprops":{
            "color":"white",
            "linewidth":2
        }
    },
    "annotation_bbox":{
        "bbox":{
            "boxstyle":'round,pad=0.4', 
            "facecolor":'black', 
            "alpha":0.8, 
            "edgecolor":'gray', 
            "linewidth":1
        }
    }
}

def import_data(file_path: str) -> pd.DataFrame:
    """
    Import data from a CSV file into a pandas DataFrame.
    Header is this : 
     - experiment_id
     - solution_id
     - catalog_type
     - solution_type
     - optimizer
     - noise_level
     - valid
     - timeout
     - experiment_type
     - validation_error
     - end_simulation_time

    Args:
        file_path (str): The path to the CSV file.
    Returns:
        pd.DataFrame: The imported data as a DataFrame.
    """

    data = pd.read_csv(file_path)
    return data

def filter_data(
    data: pd.DataFrame, 
    combo_filter:ComboRegistry|Combo|None=None,
    system_filter:SystemRegistry|System|None=None,
    end_time_treshold:float|None=None,
    algo_filter: RegressionAlgorithmRegistry|RegressionAlgorithm|None=None
    ) -> pd.DataFrame:
    """
    Filter data for a specific experiment type.

    Args:
        data (pd.DataFrame): The input data.
        combo_filter (ComboRegistry): The combo filter to apply.
        end_time_treshold (float): The minimum end simulation time to include.
    Returns:
        pd.DataFrame: The filtered data.
    """

    if combo_filter is not None:
        data = data[
            (data['catalog_type'].isin([combo_filter.catalog_type] if isinstance(combo_filter, Combo) else combo_filter.catalog_type)) &
            (data['solution_type'].isin([combo_filter.solution_type] if isinstance(combo_filter, Combo) else combo_filter.solution_type)) 
        ]

    if algo_filter is not None:
        data = data[
            (data['optimizer'].isin([algo_filter.name] if isinstance(algo_filter, RegressionAlgorithm) else algo_filter.name))
        ]


    if system_filter is not None:
        data = data[
            (data['experiment_type'].isin([system_filter.name] if isinstance(system_filter, System) else system_filter.name))
        ]

    if end_time_treshold is not None:
        data = data[
            (data['end_simulation_time'] >= end_time_treshold)
        ]

    return data[
        (data['valid'] == True) &
        (data['timeout'] == False) 
    ]


def generate_boxplot_data(
        data: pd.DataFrame,
        system_registry:SystemRegistry|System|None = None, 
        algo_filter: RegressionAlgorithmRegistry|RegressionAlgorithm|None = None, 
        combo_filter: ComboRegistry|Combo|None = None,
        end_time_treshold:float|None = None
        ) -> BPSystemData:
    """
    Generate box plot data for a specific experiment type and combo.

    Args:
        data (pd.DataFrame): The input data.
        experiment_type (str): The type of experiment to filter.
        combo (dict): The combo dictionary with 'catalog_type' and 'solution_type'.
    Returns:
        BoxPlotData: The generated box plot data.
    """

    filtered_data = filter_data(
        data, 
        combo_filter=combo_filter, 
        system_filter=system_registry, 
        end_time_treshold=end_time_treshold,
        algo_filter=algo_filter
        )

    print(len(filtered_data), "experiments after filtering")

    combo_data_list:list[BPComboData] = []

    for combo in combo_filter:
        noise_data_list:list[BPNoiseData] = []

        combo_data = filter_data(filtered_data,combo_filter=combo)

        grouped_by_noise = combo_data.groupby('noise_level')

        for noise_level, group in grouped_by_noise:
            validation_errors = group['validation_error'].tolist()
            noise_data = BPNoiseData(
                noise_level=noise_level,
                validation_errors=validation_errors
            )
            noise_data_list.append(noise_data)

        bp_combo_data = BPComboData(
            combo=combo,
            noise_data=noise_data_list
        )
        combo_data_list.append(bp_combo_data)

    bp_system_data = BPSystemData(
        valid_experiment_number=len(filtered_data['experiment_id'].unique()),
        system_registry=system_registry,
        combo_data=combo_data_list
    )
    return bp_system_data

def apply_style(style_name: str)->dict:
    """
    Apply a specific style to matplotlib plots.

    Args:
        style_name (str): The name of the style to apply.
    Returns:
        dict: The style dictionary applied.
    Raises:
        ValueError: If the style_name is not recognized.
    """

    if style_name == "white_background":
        plt.style.use('default')
        return WHITE_BACKGROUND_THEME
    elif style_name == "dark_background":
        plt.style.use('dark_background')
        return BLACK_BACKGROUND_THEME
    else:
        raise ValueError(f"Style '{style_name}' is not recognized.")

def plot_to_file(output_path:Path,filename:str):
    
    plt.tight_layout()
    # Save combined figure
    output_file_png = output_path / (filename + ".png")
    plt.savefig(output_file_png, dpi=300, bbox_inches='tight',transparent=True)
    print(f"Saved combined plot: {output_file_png}")

    output_file_svg = output_path / (filename + ".svg")
    plt.savefig(output_file_svg, dpi=300, bbox_inches='tight',transparent=True)
    print(f"Saved combined plot: {output_file_svg}")
    
    plt.close()


    
def plot_boxplot(filename:str, box_plot_data: list[BPSystemData],output_dir: str="plots", style: str="white_background"):
    """
    Plot box plots for the given box plot data.

    Args:
        box_plot_data (list[BoxPlotData]): The box plot data to plot.
        style (str): The style to apply to the plots.
    """

    style_dict = apply_style(style)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    n_rows = len(box_plot_data)

    fig, axes = plt.subplots(n_rows, 1, figsize=(12, 6*n_rows**0.5), squeeze=False)
    
    fig.suptitle('Validation Error Comparison (Log Scale)', fontsize=18, fontweight='bold', y=0.995)

    all_noise_levels = set()

    for system_data in box_plot_data:
        for combo_data in system_data.combo_data:
            for noise_data in combo_data.noise_data:
                all_noise_levels.add(noise_data.noise_level)

    all_noise_levels = sorted(list(all_noise_levels))

    for row_idx, system_data in enumerate(box_plot_data):

        ax = axes[row_idx, 0]
        
        # Add legend only for first subplot showing noise levels with gradient
        if row_idx == 0:
            
            # Create gradient colors for legend (using gray as neutral)
            legend_elements = []
            for noise_idx, noise in enumerate(all_noise_levels):
                factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
                gray_val = 1 - factor * 0.6  # Range from light to dark gray
                legend_elements.append(
                    Patch(facecolor=(gray_val, gray_val, gray_val), alpha=0.7, label=f'Noise: {noise}')
                )
            ax.legend(handles=legend_elements, loc='upper left', fontsize=11, frameon=True)

        # Prepare data for each combo across all noise levels
        all_plot_data = []
        all_positions = []
        all_colors = []

        position=2

        x_ticks = []
        x_labels = []
        
        # For each combo, add all noise levels with gradient colors
        for combo_idx, combo_data in enumerate(system_data.combo_data):
            # Generate color gradient from light to dark for this combo
            base_color = combo_data.combo.color
            # Convert hex to RGB
            r = int(base_color[1:3], 16) / 255
            g = int(base_color[3:5], 16) / 255
            b = int(base_color[5:7], 16) / 255

            local_position = -1
            
            for noise_idx, noise_level in enumerate(all_noise_levels):

                noise_data = combo_data.get_by_noise_level(noise_level)

                local_position += 1

                if noise_data is not None:
                    

                    all_plot_data.append(noise_data.validation_errors)
                    # Position: combo_idx * 5 + noise_idx (with spacing between combos)
                    all_positions.append(position + local_position)

                    # Create gradient: lighter (0.3) to darker (1.0)
                    factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
                    color = (
                        1 - factor * (1 - r),
                        1 - factor * (1 - g),
                        1 - factor * (1 - b)
                    )
                    all_colors.append(color)

                    y_max = max(noise_data.validation_errors)
                    upper_quartile = np.percentile(noise_data.validation_errors, 75)
                    # Use upper_quartile * 2 if max is more than 50x the upper_quartile, otherwise use max * 1.5
                    y_pos = upper_quartile * 2 if y_max > 50 * upper_quartile else y_max * 1.5

                    success_rate = (len(noise_data.validation_errors) / system_data.valid_experiment_number * 100) if system_data.valid_experiment_number > 0 else 0

                else:
                    y_pos = 1e0
                    success_rate = 0

                ax.text(position + local_position, y_pos, f'{success_rate:.0f}%', 
                    ha='center', va='bottom', fontsize=10, style='italic', fontweight='bold',
                    **style_dict['annotation_bbox'])
            


            x_ticks.append(position + (local_position) / 2)
            x_labels.append(combo_data.combo.pretty_name)

            position += local_position +  2 # Extra space between combos

        ax.set_xlim(1, position -1 )

        # Create boxplot
        box = ax.boxplot(
            all_plot_data, 
            positions=all_positions, 
            widths=0.6,
            patch_artist=True,
            **style_dict['boxplot']
        )

        # Color the boxes
        for patch, color in zip(box['boxes'], all_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        # Set log scale
        ax.set_yscale('log')
        
        # Set x-axis ticks and labels (centered on each group of 4 noise levels)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, fontsize=11)

        if row_idx == n_rows - 1:
            ax.set_xlabel('Method (noise levels: 0.0, 0.001, 0.01, 0.1 - only systems converging over full validation period)', fontsize=9)
        
        # Set y-axis
        ax.set_ylabel(f'{system_data.system_registry.pretty_name}\nValidation Error (log)', fontsize=11, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y', which='both')
        ax.tick_params(axis='y', labelsize=10)

        # Add n_max annotation in bottom right corner
        ax.text(0.98, 0.08, f'$n_{{max}}={system_data.valid_experiment_number}$', 
                transform=ax.transAxes, 
                fontsize=11, 
                verticalalignment="bottom", 
                horizontalalignment="right",
                **style_dict['annotation_bbox']
                )
        
    plot_to_file(output_path=output_path, filename=filename+"_"+style)

def plot_success_rate(filename:str, box_plot_data: list[BPSystemData],output_dir: str="plots", style: str="white_background"):
    """
    Plot box plots for the given box plot data.

    Args:
        box_plot_data (list[BoxPlotData]): The box plot data to plot.
        style (str): The style to apply to the plots.
    """

    style_dict = apply_style(style)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    n_rows = len(box_plot_data)

    fig, axes = plt.subplots(n_rows, 1, figsize=(10, 6*n_rows**0.5), squeeze=False)
    
    fig.suptitle('Success rate Comparison', fontsize=18, fontweight='bold', y=0.995)

    all_noise_levels = set()

    for system_data in box_plot_data:
        for combo_data in system_data.combo_data:
            for noise_data in combo_data.noise_data:
                all_noise_levels.add(noise_data.noise_level)

    all_noise_levels = sorted(list(all_noise_levels))


    for row_idx, system_data in enumerate(box_plot_data):

        ax = axes[row_idx, 0]
        
        # Add legend only for first subplot showing noise levels with gradient
        if row_idx == 0:
            
            # Create gradient colors for legend (using gray as neutral)
            legend_elements = []
            for noise_idx, noise in enumerate(all_noise_levels):
                factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
                gray_val = 1 - factor * 0.6  # Range from light to dark gray
                legend_elements.append(
                    Patch(facecolor=(gray_val, gray_val, gray_val), alpha=0.7, label=f'Noise: {noise}')
                )
            ax.legend(handles=legend_elements, loc='upper right', fontsize=11, frameon=True)

        # Prepare data for each combo across all noise levels
        all_plot_data = []
        all_positions = []
        all_colors = []

        position=2

        x_ticks = []
        x_labels = []
        
        # For each combo, add all noise levels with gradient colors
        for combo_idx, combo_data in enumerate(system_data.combo_data):
            # Generate color gradient from light to dark for this combo
            base_color = combo_data.combo.color
            # Convert hex to RGB
            r = int(base_color[1:3], 16) / 255
            g = int(base_color[3:5], 16) / 255
            b = int(base_color[5:7], 16) / 255

            local_position = -1
            
            for noise_idx, noise_level in enumerate(all_noise_levels):

                noise_data = combo_data.get_by_noise_level(noise_level)

                local_position += 1

                if noise_data is not None:
                    
                    success_rate = (len(noise_data.validation_errors) / system_data.valid_experiment_number * 100) if system_data.valid_experiment_number > 0 else 0
                else:
                    success_rate = 0

                # Create gradient: lighter (0.3) to darker (1.0)
                factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
                color = (
                    1 - factor * (1 - r),
                    1 - factor * (1 - g),
                    1 - factor * (1 - b)
                )

                all_colors.append(color)

                all_plot_data.append(success_rate)
                # Position: combo_idx * 5 + noise_idx (with spacing between combos)
                all_positions.append(position + local_position)

            x_ticks.append(position + (local_position) / 2)
            x_labels.append(combo_data.combo.pretty_name)

            position += local_position +  2 # Extra space between combos

        ax.set_xlim(1, position -1 )

        # Create boxplot
        box = ax.bar(
            all_positions, 
            height=all_plot_data,
            width=0.6,
            color=all_colors,
            # **style_dict['boxplot']
        )

        # Color the boxes
        # for patch, color in zip(box['boxes'], all_colors):
        #     patch.set_facecolor(color)
        #     patch.set_alpha(0.7)

        # Set x-axis ticks and labels (centered on each group of 4 noise levels)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, fontsize=11)

        if row_idx == n_rows - 1:
            ax.set_xlabel('Method (noise levels: 0.0, 0.001, 0.01, 0.1 - only systems converging over full validation period)', fontsize=9)
        
        # Set y-axis
        ax.set_ylabel(f'{system_data.system_registry.pretty_name}\nSuccess rate (%)', fontsize=11, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y', which='both')
        ax.tick_params(axis='y', labelsize=10)

        # Add n_max annotation in bottom right corner
        ax.text(0.98, 0.08, f'$n_{{max}}={system_data.valid_experiment_number}$', 
                transform=ax.transAxes, 
                fontsize=11, 
                verticalalignment="top", 
                horizontalalignment="right",
                **style_dict['annotation_bbox']
                )
        
    plot_to_file(output_path=output_path, filename=filename+"_"+style)


if __name__ == "__main__":

    # Example usage
    data_file = 'results_database.csv'
    data = import_data(data_file)

    algo_name = "lasso_regression"
    algo_pretty_name = "Lasso"

    all_system_registry = SystemRegistry(
        pretty_name="All systems",
        systems=SYSTEMS.values()
    )

    end_time_threshold = 5

    # Boxplot noise data

    bp_data_combined = generate_boxplot_data(
        data,
        system_registry= all_system_registry, 
        algo_filter = RegressionAlgorithm(
            pretty_name=algo_pretty_name,
            name=algo_name
        ), 
        combo_filter = TARGET_COMBOS,
        end_time_treshold= end_time_threshold
        )
    
    bp_data_cartpole = generate_boxplot_data(
        data,
        system_registry= SYSTEMS["cartpole"], 
        algo_filter = RegressionAlgorithm(
            pretty_name=algo_pretty_name,
            name=algo_name
        ), 
        combo_filter = TARGET_COMBOS,
        end_time_treshold= end_time_threshold
        )
    
    bp_data_cartpole_double = generate_boxplot_data(
        data,
        system_registry= SYSTEMS["cartpole_double"], 
        algo_filter = RegressionAlgorithm(
            pretty_name=algo_pretty_name,
            name=algo_name
        ), 
        combo_filter = TARGET_COMBOS,
        end_time_treshold= end_time_threshold
        )

    bp_data_double_pendulum_pm = generate_boxplot_data(
        data,
        system_registry= SYSTEMS["double_pendulum_pm"], 
        algo_filter = RegressionAlgorithm(
            pretty_name=algo_pretty_name,
            name=algo_name
        ), 
        combo_filter = TARGET_COMBOS,
        end_time_treshold= end_time_threshold
        )
    
    ## Plot 

    for style in ['dark_background', 'white_background']:

        plot_boxplot(
            filename="noise_comparison_combined",
            box_plot_data=[
                bp_data_combined
                ],
            style=style
        )

        plot_boxplot(
            filename="noise_comparison",
            box_plot_data=[
                bp_data_cartpole,
                bp_data_cartpole_double,
                bp_data_double_pendulum_pm
                ],
            style=style
        )


        plot_success_rate(
            filename="success_rate",
            box_plot_data=[
                bp_data_cartpole,
                bp_data_cartpole_double,
                bp_data_double_pendulum_pm
                ],
            style=style
        )

        plot_success_rate(
            filename="success_rate_combined",
            box_plot_data=[
                bp_data_combined
                ],
            style=style
        )

