
import logging 
import numpy as np

from typing import List, Dict


logger = logging.getLogger(__name__)

def convert_to_lists(d):
    if isinstance(d, dict):
        return {k: convert_to_lists(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_to_lists(i) for i in d]
    elif isinstance(d, np.ndarray):
        return convert_to_lists(d.tolist())
    elif isinstance(d, (np.float32, np.float64)):
        return convert_to_lists(float(d))
    elif isinstance(d,float):
        return float(f"{format(d, '.3e')}")
    else:
        return d
    

def json_format_time_series(
    name:str,
    time:np.ndarray,
    series:Dict[str,np.ndarray],
    sample:int,
    mode_solution:str="mixed",
    solution_vector:list=None,
    solution_label:List[str]=None,
    reference:bool=False,
    extra_info:Dict=None,
    reference_time:np.ndarray=None
):
    """
    Format a time series for json saving.

    Args:
        name (str): the name of the time series.
        time (np.ndarray): the time vector.
        series (Dict[str,np.ndarray]): the dictionary of series to save.
        sample (int): the number of sample to save (used as fallback if reference_time is None).
        reference_time (np.ndarray): reference time vector to map onto (optional).

    Returns:
        dict: the formatted time series.
    """

    series_dict = {}

    if time is not None:
        
        if reference_time is not None:
            # Map time and series onto reference_time
            time_flat = np.array(time).flatten()
            ref_time_flat = np.array( reference_time).flatten()
            
            # Find the overlapping time range
            time_min, time_max = time_flat.min(), time_flat.max()
            ref_time_min, ref_time_max = ref_time_flat.min(), ref_time_flat.max()
            
            # Determine the common time range
            common_start = max(time_min, ref_time_min)
            common_end = min(time_max, ref_time_max)
            
            if common_start >= common_end:
                # No overlap, use the shorter time range
                if time_max <= ref_time_max:
                    # Input time is completely before reference time end
                    target_time = ref_time_flat[ref_time_flat <= time_max]
                else:
                    # Reference time is completely before input time end  
                    target_time = ref_time_flat[ref_time_flat >= time_min]
                    
                if len(target_time) == 0:
                    logger.warning(f"No time overlap found for {name}, using original sampling")
                    # Fallback to original sampling method
                    if len(time_flat) < sample:
                        raise ValueError("Not enough data points to sample from.")
                    indices = np.linspace(0, len(time_flat) - 1, sample, dtype=int)
                    target_time = time_flat[indices]
                    restricted_series = {k: v[indices] for k, v in series.items()}
                else:
                    # Interpolate series data onto target_time
                    restricted_series = {}
                    for key, value in series.items():
                        if value is not None:
                            interpolated_value = np.zeros((len(target_time), value.shape[1]))
                            for i in range(value.shape[1]):
                                interpolated_value[:, i] = np.interp(target_time, time_flat, value[:, i])
                            restricted_series[key] = interpolated_value
            else:
                # There is overlap, use the overlapping reference time points
                mask = (ref_time_flat >= common_start) & (ref_time_flat <= common_end)
                target_time = ref_time_flat[mask]
                
                # Interpolate series data onto target_time
                restricted_series = {}
                for key, value in series.items():
                    if value is not None:
                        interpolated_value = np.zeros((len(target_time), value.shape[1]))
                        for i in range(value.shape[1]):
                            interpolated_value[:, i] = np.interp(target_time, time_flat, value[:, i])
                        restricted_series[key] = interpolated_value
            
            # Update time to be the target_time
            time = target_time
            
        else:
            # Fallback to original sampling method when reference_time is None
            time_flat = time.flatten() if time.ndim > 1 else time
            if len(time_flat) < sample:
                raise ValueError("Not enough data points to sample from.")
            indices = np.linspace(0, len(time_flat) - 1, sample, dtype=int)
            time = time_flat[indices]
            restricted_series = {k: v[indices] for k, v in series.items()}

        # Build series dictionary
        for key, value in restricted_series.items():
            if value is not None:
                for i in range(value.shape[1]):
                    if f"coor_{i}" not in series_dict:
                        series_dict[f"coor_{i}"] = {}
                    series_dict[f"coor_{i}"][key] = value[:, i].tolist()

    data_json = {
        name: {
            "time": time,
            "series": series_dict,
            "reference": reference,
            "solution": {
                mode_solution: {
                    "vector": solution_vector,
                    "label": solution_label
                    } 
            }
        }
    }

    if extra_info is not None:
        data_json[name]["extra_info"] = extra_info

    return data_json