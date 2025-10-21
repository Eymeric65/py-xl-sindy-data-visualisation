import pandas as pd

# Load the CSV file into a pandas DataFrame
df = pd.read_csv('graphs_analysis/results_database.csv')

# Display the first few rows
print(df.head())

df["combo_type"] = df["catalog_type"] + " x " + df["solution_type"]

df["not_completed"] = False
df.loc[df['end_simulation_time'] < 20.0, "not_completed"] = True

df["rank"] = -1
df["Wins_WC"] = False

experiment_list = df['experiment_id'].unique()


# failed experiment 

filtered_df = df[df['valid']== True]
filtered_df = filtered_df[filtered_df['timeout']== False]

# Simulation not completed

filtered_df= filtered_df[filtered_df['not_completed']== False]

for experiment_id in experiment_list:

    unique_noise = filtered_df[filtered_df['experiment_id'] == experiment_id]['noise_level'].unique()

    for noise in unique_noise:

        subset = filtered_df[(filtered_df['experiment_id'] == experiment_id) & (filtered_df['noise_level'] == noise)]

        df.loc[subset.index, 'rank'] = subset['validation_error'].rank(method='dense', ascending=True).astype(int)

        if df.loc[subset.index,'rank'].max() == 1 :
            df.loc[subset.index, 'Wins_WC'] = True


# Resulting table

# Get unique combo types
combo_types = df['combo_type'].unique()

# Initialize results list
results = []

# Load original dataframe to count failures

for combo in combo_types:
    # Count not valid
    not_valid = len(df[(df['combo_type'] == combo) & (df['valid'] == False)])
    
    # Count timeout
    timeout_count = len(df[(df['combo_type'] == combo) & (df['timeout'] == True)])
    
    # Count not completed
    not_completed = len(df[(df['combo_type'] == combo) & (df['not_completed'] == True)])

    # Count ranks from the filtered df
    combo_df = df[df['combo_type'] == combo]
    wins_wc = len(combo_df[combo_df['Wins_WC'] == True])
    rank_1 = len(combo_df[combo_df['rank'] == 1])
    rank_2 = len(combo_df[combo_df['rank'] == 2])
    rank_greater_2 = len(combo_df[combo_df['rank'] > 2])

    win_rate = (rank_1 + rank_2 + rank_greater_2) / len(combo_df)

    results.append({
        'combo_type': combo,
        'not_valid': not_valid,
        'timeout': timeout_count,
        'not_completed': not_completed,
        '1st_rank': rank_1,
        '2nd_rank': rank_2,
        '2nd>': rank_greater_2,
        'Wins_WC': wins_wc,
        'win_rate': win_rate
    })

result_table = pd.DataFrame(results).sort_values(by=['1st_rank', '2nd_rank', '2nd>'], ascending=False)
print(result_table.to_latex(index=False))