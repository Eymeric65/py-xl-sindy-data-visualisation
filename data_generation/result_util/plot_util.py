"""
The general util for plotting data from the database of experiment. (For tendencies, detail plot are located in other files)
"""

import pandas as pd 

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns

from pydantic import BaseModel,ConfigDict
from typing import Iterator
from pathlib import Path

import numpy as np
import ast

class Combo(BaseModel):
    pretty_name:str
    paradigm:str
    regression_type:str
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
        self.paradigm = [c.paradigm for c in combos]
        self.regression_type = [c.regression_type for c in combos]

    def __iter__(self) -> Iterator[Combo]:
        return iter(self._combos)

# Use seaborn deep palette colors
DEEP_PALETTE = sns.color_palette("deep", 10)

TARGET_COMBOS = ComboRegistry([
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
    # Combo(
    #     pretty_name="XlSINDy-PI (new)",
    #     paradigm="xlsindy",
    #     regression_type="implicit",
    #     color="#{:02x}{:02x}{:02x}".format(int(DEEP_PALETTE[4][0]*255), int(DEEP_PALETTE[4][1]*255), int(DEEP_PALETTE[4][2]*255))
    # ),
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

WHITE_BACKGROUND_THEME={
    "boxplot":{
        "meanprops":{
            "marker":"D",
            "markerfacecolor":"white",
            "markeredgecolor":"black",
            "markersize":6,
        },
        "medianprops":{
            "color":"#2c3e50",
            "linewidth":2.5
        },
        "whiskerprops":{
            "linewidth":1.5,
            "linestyle":"-"
        },
        "capprops":{
            "linewidth":1.5
        }
    },
    "annotation_bbox":{
        "bbox":{
            "boxstyle":'round,pad=0.5', 
            "facecolor":'white', 
            "alpha":0.95, 
            "edgecolor":'#bdc3c7', 
            "linewidth":1.5
        }
    }
}

BLACK_BACKGROUND_THEME={
    "boxplot":{
        "meanprops":{
            "marker":"D",
            "markerfacecolor":"#2c3e50",
            "markeredgecolor":"white",
            "markersize":6,
        },
        "medianprops":{
            "color":"white",
            "linewidth":2.5
        },
        "whiskerprops":{
            "linewidth":1.5,
            "linestyle":"-"
        },
        "capprops":{
            "linewidth":1.5
        }
    },
    "annotation_bbox":{
        "bbox":{
            "boxstyle":'round,pad=0.5', 
            "facecolor":'#2c3e50', 
            "alpha":0.95, 
            "edgecolor":'#7f8c8d', 
            "linewidth":1.5
        }
    }
}

def import_data(file_path: str) -> pd.DataFrame:
    """
    Import data from a CSV file into a pandas DataFrame.
    Header is this : 
     - experiment_id
     - trajectory_name
     - paradigm
     - regression_type
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
    algo_filter: RegressionAlgorithmRegistry|RegressionAlgorithm|None=None,
    no_damping:bool=True,
    force_mode:str|None=None
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

    #print(f"Starting with {len(data)} entries")

    if force_mode is not None:
        if force_mode == "explicit":
            data = data[data['force_scale_vector'].apply(
                lambda x: all([ coef != 0.0 for coef in ast.literal_eval(x)])
            )]
        elif force_mode == "implicit":
            data = data[data['force_scale_vector'].apply(
                lambda x: all([ coef == 0.0 for coef in ast.literal_eval(x)])
            )]

    #print(f"Filtered data to {len(data)} entries before damping check")

    if no_damping:
        print("Applying no damping filter")
        # Parse damping_coefficients string and filter for all zeros        
        data = data[data['damping_coefficients'].apply(
            lambda x: all([ coef == 0.0 for coef in ast.literal_eval(x)])
        )]

    #print(f"Filtered data to {len(data)} entries after damping check")

    if len(data) == 0:
        return data

    if combo_filter is not None:
        data = data[
            (data['paradigm'].isin([combo_filter.paradigm] if isinstance(combo_filter, Combo) else combo_filter.paradigm)) &
            (data['regression_type'].isin([combo_filter.regression_type] if isinstance(combo_filter, Combo) else combo_filter.regression_type)) 
        ]

    #print(f"Filtered data to {len(data)} entries after combo check")

    if algo_filter is not None:
        data = data[
            (data['optimizer'].isin([algo_filter.name] if isinstance(algo_filter, RegressionAlgorithm) else algo_filter.name))
        ]

    #print(f"Filtered data to {len(data)} entries before system check")

    if system_filter is not None:
        data = data[
            (data['experiment_type'].isin([system_filter.name] if isinstance(system_filter, System) else system_filter.name))
        ]

    #print(f"Filtered data to {len(data)} entries before time check")

    if end_time_treshold is not None:
        data = data[
            (data['end_simulation_time'] >= end_time_treshold)
        ]

    #print(f"Filtered data to {len(data)} entries before validity")

    data = data[
        (data['valid'] == True) &
        (data['timeout'] == False) 
    ]

    #print(f"Filtered data to {len(data)} entries")

    return data


def generate_boxplot_data(
        filtered_data: pd.DataFrame,
        combo_registry: ComboRegistry,
        system_name: str = "System"
        ) -> BPSystemData:
    """
    Generate box plot data structure from pre-filtered data.

    Args:
        filtered_data (pd.DataFrame): Pre-filtered data ready for processing.
        combo_registry (ComboRegistry): Registry of combos to process.
        system_name (str): Name of the system for display purposes.
    Returns:
        BPSystemData: The generated box plot data structure.
    """
    
    if len(filtered_data) == 0:
        return BPSystemData(
            valid_experiment_number=0,
            system_registry=System(pretty_name=system_name, name=system_name),
            combo_data=[]
        )

    combo_data_list:list[BPComboData] = []

    for combo in combo_registry:
        noise_data_list:list[BPNoiseData] = []

        # Filter for this specific combo
        combo_data = filtered_data[
            (filtered_data['paradigm'] == combo.paradigm) &
            (filtered_data['regression_type'] == combo.regression_type)
        ]

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

    # Calculate valid_experiment_number from experiments that actually contributed data to any combo
    all_experiment_ids = set()
    for combo_data in combo_data_list:
        for noise_data in combo_data.noise_data:
            if len(noise_data.validation_errors) > 0:
                # Get the experiment IDs for this combo and noise level
                combo_filtered = filtered_data[
                    (filtered_data['paradigm'] == combo_data.combo.paradigm) &
                    (filtered_data['regression_type'] == combo_data.combo.regression_type) &
                    (filtered_data['noise_level'] == noise_data.noise_level)
                ]
                all_experiment_ids.update(combo_filtered['experiment_id'].unique())

    bp_system_data = BPSystemData(
        valid_experiment_number=len(all_experiment_ids),
        system_registry=System(pretty_name=system_name, name=system_name),
        combo_data=combo_data_list
    )
    return bp_system_data

def apply_style(style_name: str)->dict:
    """
    Apply a specific style to matplotlib plots with seaborn enhancements.

    Args:
        style_name (str): The name of the style to apply.
    Returns:
        dict: The style dictionary applied.
    Raises:
        ValueError: If the style_name is not recognized.
    """

    if style_name == "white_background":
        sns.set_style("whitegrid")
        sns.set_context("notebook", font_scale=1.1, rc={"lines.linewidth": 2.5})
        sns.set_palette("deep")
        plt.style.use('default')
        return WHITE_BACKGROUND_THEME
    elif style_name == "dark_background":
        plt.style.use('dark_background')
        sns.set_style("darkgrid")
        sns.set_context("notebook", font_scale=1.1, rc={"lines.linewidth": 2.5})
        sns.set_palette("deep")
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

    output_file_eps = output_path / (filename + ".eps")
    plt.savefig(output_file_eps, dpi=300, bbox_inches='tight',transparent=True)
    print(f"Saved combined plot: {output_file_eps}")
    
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

    # Filter out systems with absolutely no data (no validation errors at all)
    box_plot_data = [system_data for system_data in box_plot_data 
                     if any(len(nd.validation_errors) > 0 
                           for cd in system_data.combo_data 
                           for nd in cd.noise_data)]
    
    if len(box_plot_data) == 0:
        print("No data to plot for boxplot")
        return

    n_rows = len(box_plot_data)

    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 6.5*n_rows**0.5), squeeze=False)
    
    fig.suptitle('Validation Error Comparison (Log Scale)', fontsize=20, fontweight='bold', y=0.995)

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
                    Patch(facecolor=(gray_val, gray_val, gray_val), alpha=0.8, label=f'Noise: {noise}', edgecolor='black', linewidth=0.5)
                )
            ax.legend(handles=legend_elements, loc='upper right', fontsize=12, frameon=True, 
                     fancybox=True, shadow=True, framealpha=0.95)

        # Prepare data for each combo across all noise levels
        all_plot_data = []
        all_positions = []
        all_colors = []
        all_y_max_values = []  # Track y_max values for calculating average position
        zero_rate_positions = []  # Track positions where success rate is 0

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
                    all_y_max_values.append(y_pos)

                    success_rate = (len(noise_data.validation_errors) / system_data.valid_experiment_number * 100) if system_data.valid_experiment_number > 0 else 0

                else:
                    success_rate = 0
                    y_pos = None  # Will be set to average later

                # Store position and success rate for later labeling
                if success_rate > 0 and y_pos is not None:
                    ax.text(position + local_position, y_pos, f'{success_rate:.0f}%', 
                        ha='center', va='bottom', fontsize=10, style='italic', fontweight='bold',
                        **style_dict['annotation_bbox'])
                elif success_rate == 0:
                    # Store position for zero labels to be added after calculating average
                    zero_rate_positions.append(position + local_position)
                    all_y_max_values.append(None)  # Placeholder
            


            x_ticks.append(position + (local_position) / 2)
            x_labels.append(combo_data.combo.pretty_name)

            position += local_position +  2 # Extra space between combos

        # Calculate average y position for zero success rate labels from ALL data points in subplot
        all_errors = []
        for data_list in all_plot_data:
            all_errors.extend(data_list)
        avg_y_pos = np.mean(all_errors) if len(all_errors) > 0 else 1e0
        
        # Add zero success rate labels at average position
        for pos in zero_rate_positions:
            ax.text(pos, avg_y_pos, '0%', 
                ha='center', va='bottom', fontsize=10, style='italic', fontweight='bold',
                **style_dict['annotation_bbox'])

        ax.set_xlim(1, position + 1)

        print(len(all_plot_data), "boxplots to plot")
        print(len(all_positions), "positions for boxplots")
        if (len(all_plot_data) ==0):
            continue
        # Create boxplot
        box = ax.boxplot(
            all_plot_data, 
            positions=all_positions, 
            widths=0.65,
            patch_artist=True,
            showmeans=True,
            **style_dict['boxplot']
        )

        # Color the boxes with enhanced styling
        for patch, color in zip(box['boxes'], all_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
            patch.set_edgecolor('#2c3e50')
            patch.set_linewidth(1.2)

        # Set log scale
        ax.set_yscale('log')
        
        # Set x-axis ticks and labels (centered on each group of 4 noise levels)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, fontsize=11)

        if row_idx == n_rows - 1:
            ax.set_xlabel('Method (noise levels: 0.0, 0.001, 0.01, 0.1 - only systems converging over full validation period)', fontsize=9)
        
        # Set y-axis
        ax.set_ylabel(f'{system_data.system_registry.pretty_name}\nValidation Error (log)', fontsize=12, fontweight='bold')
        
        # Add enhanced grid
        ax.grid(True, alpha=0.4, axis='y', which='major', linestyle='-', linewidth=0.8)
        ax.grid(True, alpha=0.2, axis='y', which='minor', linestyle=':', linewidth=0.5)
        ax.tick_params(axis='y', labelsize=11)
        ax.tick_params(axis='x', labelsize=11)

        # Add n_max annotation in bottom right corner (consistent position with success rate plot)
        ax.text(0.98, 0.04, f'$n_{{max}}={system_data.valid_experiment_number}$', 
                transform=ax.transAxes, 
                fontsize=11, 
                verticalalignment="bottom", 
                horizontalalignment="right",
                **style_dict['annotation_bbox']
                )
    
    # Add margins to prevent label cropping
    plt.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.06)
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

    # Filter out systems with absolutely no data (no validation errors at all)
    box_plot_data = [system_data for system_data in box_plot_data 
                     if any(len(nd.validation_errors) > 0 
                           for cd in system_data.combo_data 
                           for nd in cd.noise_data)]
    
    if len(box_plot_data) == 0:
        print("No data to plot for success rate")
        return

    n_rows = len(box_plot_data)

    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 6.5*n_rows**0.5), squeeze=False)
    
    fig.suptitle('Success Rate Comparison', fontsize=20, fontweight='bold', y=0.995)

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
                    Patch(facecolor=(gray_val, gray_val, gray_val), alpha=0.8, label=f'Noise: {noise}', edgecolor='black', linewidth=0.5)
                )
            ax.legend(handles=legend_elements, loc='upper right', fontsize=12, frameon=True,
                     fancybox=True, shadow=True, framealpha=0.95)

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

        ax.set_xlim(1, position + 1)

        # Create enhanced bar chart
        bars = ax.bar(
            all_positions, 
            height=all_plot_data,
            width=0.65,
            color=all_colors,
            alpha=0.85,
            edgecolor='#2c3e50',
            linewidth=1.2
        )
        
        # Add value labels on top of bars
        for i, (pos, val) in enumerate(zip(all_positions, all_plot_data)):
            if val > 0:
                ax.text(pos, val + 1, f'{val:.0f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Set x-axis ticks and labels (centered on each group of 4 noise levels)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, fontsize=11)

        if row_idx == n_rows - 1:
            ax.set_xlabel('Method (noise levels: 0.0, 0.01, 0.1, 0.2 - only systems converging over full validation period)', fontsize=9)
        
        # Set y-axis with enhanced styling
        ax.set_ylabel(f'{system_data.system_registry.pretty_name}\nSuccess Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylim(0, 105)  # Set y-axis from 0 to 105%
        
        # Add enhanced grid
        ax.grid(True, alpha=0.4, axis='y', which='major', linestyle='-', linewidth=0.8)
        ax.grid(True, alpha=0.2, axis='y', which='minor', linestyle=':', linewidth=0.5)
        ax.tick_params(axis='y', labelsize=11)
        ax.tick_params(axis='x', labelsize=11)

        # Add n_max annotation in bottom right corner (consistent position with boxplot)
        ax.text(0.98, 0.04, f'$n_{{max}}={system_data.valid_experiment_number}$', 
                transform=ax.transAxes, 
                fontsize=11, 
                verticalalignment="bottom", 
                horizontalalignment="right",
                **style_dict['annotation_bbox']
                )
    
    # Add margins to prevent label cropping
    plt.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.06)
    plot_to_file(output_path=output_path, filename=filename+"_"+style)



