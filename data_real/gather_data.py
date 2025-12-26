import xlsindy
import hebi
import time
import numpy as np
import logging
import pandas as pd
from datetime import datetime 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

print("Setting up data gathering script.")

logger.info("Starting data gathering script.")

lookup = hebi.Lookup()

# Wait 2 seconds for the module list to populate
time.sleep(2.0)

# Setup 
family_name = "X5-1"
modules_name = ["Shoulder","Elbow"]

group = lookup.get_group_from_names([family_name], modules_name)

logger.info(f"Group found: {group is not None}")

if group is None:
    logger.error('Group not found: Did you forget to set the module family and name above?')
    exit(1)

component_count = group.size

logger.info(f"Group size: {component_count}")

# Do not change regression_on_data rely on it

#scale_vector = [.3, 2.]
scale_vector = [0.5, .3]

#scale_vector = [0., 0.]


time_end = 5.0
random_seed = 54

forces_function = xlsindy.dynamics_modeling.sinusoidal_force_generator(
    component_count=component_count,
    scale_vector=scale_vector,
    time_end=time_end,
    num_frequencies=20,
    freq_range=(0.01,0.8),
    random_seed=random_seed,
)

logger.info("Force function created.")

group_command = hebi.GroupCommand(group.size)
group_feedback = hebi.GroupFeedback(group.size)

start = time.time()

logger.info("Starting main control loop.")
t=0.0

# Initialize lists to store data
data_records = []

while t < time_end:
    # Even though we don't use the feedback, getting feedback conveniently
    # limits the loop rate to the feedback frequency
    feedback = group.get_next_feedback(reuse_fbk=group_feedback)
    t = time.time() - start
    command = np.empty(group.size,np.float64)

    forces = forces_function(t)

    logger.debug(f"At time {t:.2f}, computed forces: {forces}")

    command[0] = forces[0]  # Shoulder
    command[1] = forces[1]  # Elbow
    #command = np.array([[ -amp * sin(freq * t),0 ]])
    print(f"t: {t:.2f}, command: {command}")
    group_command.effort = command
    group.send_command(group_command)

    # Collect data if feedback is available

    if feedback is not None:
        record = {
            'time': t,
        }
        # Store position, velocity, and effort for each component
        for i in range(component_count):
            record[f'position_{modules_name[i]}'] = feedback.position[i]
            record[f'velocity_{modules_name[i]}'] = feedback.velocity[i]
            record[f'effort_{modules_name[i]}'] = command[i]
            #record[f'effort_{modules_name[i]}'] = feedback.effort[i]
        
        data_records.append(record)

# Create DataFrame from collected data
df = pd.DataFrame(data_records)

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"robot_data_{timestamp}.csv"

# Save to CSV
df.to_csv(filename, index=False)
logger.info(f"Data saved to {filename}")
print(f"Data collection complete. Saved {len(df)} records to {filename}")

# Also save as pickle for faster loading if needed
pickle_filename = f"robot_data_{timestamp}.pkl"
df.to_pickle(pickle_filename)
logger.info(f"Data also saved to {pickle_filename}")

