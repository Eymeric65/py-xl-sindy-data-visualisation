#!/usr/bin/env python3
"""
Solution Ranking Analysis

This script analyzes the ranking performance of different solution combinations
(catalog_type × solution_type) across experiments and noise levels.
For each experiment_id and no        f.write(f"{'Rank':<6}{'Combo':<25}{'Win Rate':<12}{'1st Wins':<8}{'Total':<8}{'1st':<8}{'2nd':<8}{'3rd':<8}\n")
        f.write("-" * 80 + "\n")
        
        for idx, (_, row) in enumerate(performance_ranking.iterrows()):
            rank_1 = row.get('rank_1_count', 0)
            rank_2 = row.get('rank_2_count', 0)  
            rank_3 = row.get('rank_3_count', 0)
            
            f.write(f"{idx+1:<6}{row['combo']:<25}{row['win_rate']:<12.3f}{row['first_place_wins']:<8}"
                   f"{row['total_appearances']:<8}{rank_1:<8}{rank_2:<8}{rank_3:<8}\n")combination, it determines rankings
based on validation error and tracks:
- How many times each combo ranks 1st, 2nd, 3rd, etc.
- How many times each combo wins without competition (solo wins or tied wins)
"""

import pandas as pd
import numpy as np
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_database(file_path: str) -> pd.DataFrame:
    """Load the compiled results database."""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Loaded database with {len(df)} solutions from {file_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to load database from {file_path}: {e}")
        raise


def calculate_rankings_for_group(group_df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    """
    Calculate rankings for a single experiment_id × noise_level group.
    
    Args:
        group_df: DataFrame containing solutions for one experiment_id and noise_level
        
    Returns:
        Dictionary with ranking information for each combo
    """
    # Filter for valid solutions with validation errors
    valid_solutions = group_df[
        (group_df['valid'] == True) & 
        (group_df['validation_error'].notna())
    ].copy()
    
    if len(valid_solutions) == 0:
        return {}
    
    # Create combo identifier
    valid_solutions['combo'] = (
        valid_solutions['catalog_type'].astype(str) + ' × ' + 
        valid_solutions['solution_type'].astype(str)
    )
    
    # Sort by validation error (ascending = better)
    valid_solutions = valid_solutions.sort_values('validation_error')
    
    # Calculate rankings with proper tie handling
    rankings = {}
    
    # Check if this is a "win without competition" scenario
    unique_errors = valid_solutions['validation_error'].nunique()
    total_solutions = len(valid_solutions)
    
    # Win without competition: only 1 unique error value (all solutions tied)
    # OR only 1 solution total
    win_without_competition = (unique_errors == 1) or (total_solutions == 1)
    
    # Group by validation error to handle ties
    error_groups = valid_solutions.groupby('validation_error')
    
    current_rank = 1
    for error_value, error_group in error_groups:
        # All solutions in this group have the same error value (tied)
        tied_combos = error_group['combo'].tolist()
        tied_count = len(tied_combos)
        
        # Assign the same rank to all tied solutions
        for combo in tied_combos:
            if combo not in rankings:
                rankings[combo] = {
                    'ranks': [],
                    'wins_without_competition': 0,
                    'total_appearances': 0,
                    'best_error': float('inf'),
                    'worst_error': 0
                }
            
            rankings[combo]['ranks'].append(current_rank)
            rankings[combo]['total_appearances'] += 1
            rankings[combo]['best_error'] = min(rankings[combo]['best_error'], error_value)
            rankings[combo]['worst_error'] = max(rankings[combo]['worst_error'], error_value)
            
            # Check if this is a win without competition
            if current_rank == 1 and win_without_competition:
                # It's a first place AND there's no real competition
                rankings[combo]['wins_without_competition'] += 1
        
        # Move to next rank position (increment by 1, not by tied_count)
        current_rank += 1
    
    return rankings


def analyze_experiment_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze statistics by experiment_id including failed, timeout, and successful counts.
    
    Args:
        df: DataFrame with experiment results
        
    Returns:
        DataFrame with experiment statistics
    """
    experiment_stats = []
    
    # Group by experiment_id to get statistics for each experiment
    for experiment_id, exp_group in df.groupby('experiment_id'):
        total_attempts = len(exp_group)
        
        # Count different types of outcomes
        successful = len(exp_group[exp_group['valid'] == True])
        timeout_failed = len(exp_group[exp_group['timeout'] == True])
        other_failed = total_attempts - successful - timeout_failed
        total_failed = timeout_failed + other_failed
        
        experiment_stats.append({
            'experiment_id': experiment_id,
            'total_attempts': total_attempts,
            'successful': successful,
            'timeout_failed': timeout_failed,
            'other_failed': other_failed,
            'total_failed': total_failed,
            'success_rate': successful / total_attempts if total_attempts > 0 else 0,
            'timeout_rate': timeout_failed / total_attempts if total_attempts > 0 else 0,
            'failure_rate': total_failed / total_attempts if total_attempts > 0 else 0
        })
    
    # Convert to DataFrame and sort by failure rate (descending)
    exp_stats_df = pd.DataFrame(experiment_stats)
    exp_stats_df = exp_stats_df.sort_values('failure_rate', ascending=False)
    
    return exp_stats_df


def analyze_all_rankings(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Analyze rankings across all experiment_id × noise_level combinations.
    
    Returns:
        Tuple of (results_dataframe, summary_statistics)
    """
    # Filter for valid solutions
    valid_df = df[(df['valid'] == True) & (df['validation_error'].notna())].copy()
    
    if len(valid_df) == 0:
        logging.error("No valid solutions with validation errors found!")
        return pd.DataFrame(), {}
    
    # Get all unique combinations
    all_combos = set()
    experiment_noise_pairs = []
    
    # Group by experiment_id and noise_level
    grouped = valid_df.groupby(['experiment_id', 'noise_level'])
    
    logging.info(f"Analyzing {len(grouped)} experiment×noise combinations...")
    
    # Collect all ranking data
    all_rankings = defaultdict(lambda: defaultdict(list))
    wins_without_competition_counts = defaultdict(int)
    first_place_counts = defaultdict(int)
    appearance_counts = defaultdict(int)
    total_attempt_counts = defaultdict(int)
    timeout_counts = defaultdict(int)
    rank_counts = defaultdict(lambda: defaultdict(int))
    
    # Also need to track all attempts (including failures) by looking at the full dataset
    full_grouped = df.groupby(['experiment_id', 'noise_level'])
    
    for (exp_id, noise_level), full_group in full_grouped:
        experiment_noise_pairs.append((exp_id, noise_level))
        
        # Count total attempts (including failures) for each combo
        full_group['combo'] = (
            full_group['catalog_type'].astype(str) + ' × ' + 
            full_group['solution_type'].astype(str)
        )
        
        for idx, (_, row_data) in enumerate(full_group.iterrows()):
            combo = row_data['combo']
            all_combos.add(combo)
            total_attempt_counts[combo] += 1
            
            # Check for timeout in the database
            if 'timeout' in row_data and row_data['timeout'] == True:
                timeout_counts[combo] += 1
        
        # Calculate rankings for valid solutions only
        valid_group = full_group[
            (full_group['valid'] == True) & 
            (full_group['validation_error'].notna())
        ]
        
        if len(valid_group) > 0:
            group_rankings = calculate_rankings_for_group(valid_group)
            
            for combo, rank_info in group_rankings.items():
                # Track successful appearances (ranked)
                appearance_counts[combo] += rank_info['total_appearances']
                
                # Track wins without competition (separate from first places)
                wins_without_competition_counts[combo] += rank_info['wins_without_competition']
                
                # Track rank frequencies
                for rank in rank_info['ranks']:
                    rank_counts[combo][rank] += 1
                    # Track first place wins (for win rate calculation)
                    if rank == 1:
                        first_place_counts[combo] += 1
    
    # Convert to results DataFrame
    results = []
    for combo in sorted(all_combos):
        # Parse combo back to catalog_type and solution_type
        try:
            catalog_type, solution_type = combo.split(' × ')
        except ValueError:
            catalog_type = solution_type = combo
        
        # Calculate successful rankings and failures
        successful_rankings = appearance_counts[combo]
        total_attempts = total_attempt_counts[combo]
        timeout_failures = timeout_counts[combo]
        other_failures = total_attempts - successful_rankings - timeout_failures
        
        row = {
            'catalog_type': catalog_type,
            'solution_type': solution_type,
            'combo': combo,
            'total_attempts': total_attempts,
            'total_appearances': successful_rankings,
            'timeout_failures': timeout_failures,
            'other_failures': other_failures,
            'failed_attempts': total_attempts - successful_rankings,
            'first_place_wins': first_place_counts[combo],
            'wins_without_competition': wins_without_competition_counts[combo],
            'win_rate': first_place_counts[combo] / max(1, total_attempts),
        }
        
        # Add rank counts (1st, 2nd, 3rd, etc.)
        max_rank = max(rank_counts[combo].keys()) if rank_counts[combo] else 0
        for rank in range(1, max_rank + 1):
            row[f'rank_{rank}_count'] = rank_counts[combo].get(rank, 0)
            row[f'rank_{rank}_rate'] = rank_counts[combo].get(rank, 0) / max(1, appearance_counts[combo])
        
        # Add count for ranks greater than 3rd
        ranks_greater_than_3 = sum(count for rank, count in rank_counts[combo].items() if rank > 3)
        row['rank_greater_than_3_count'] = ranks_greater_than_3
        row['rank_greater_than_3_rate'] = ranks_greater_than_3 / max(1, appearance_counts[combo])
        
        results.append(row)
    
    results_df = pd.DataFrame(results)
    
    # Summary statistics
    summary = {
        'total_experiment_noise_combinations': len(experiment_noise_pairs),
        'total_unique_combos': len(all_combos),
        'total_rankings_analyzed': sum(appearance_counts.values()),
        'total_attempts_analyzed': sum(total_attempt_counts.values()),
        'combos_analyzed': sorted(all_combos)
    }
    
    return results_df, summary


def generate_ranking_report(results_df: pd.DataFrame, summary: Dict[str, Any], experiment_stats_df: pd.DataFrame, output_file: str) -> None:
    """Generate a comprehensive text report of the ranking analysis."""
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SOLUTION RANKING ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary section
        f.write("SUMMARY STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total experiment×noise combinations analyzed: {summary['total_experiment_noise_combinations']}\n")
        f.write(f"Total unique catalog×solution combinations: {summary['total_unique_combos']}\n")
        f.write(f"Total individual attempts: {summary['total_attempts_analyzed']}\n")
        f.write(f"Total successful rankings: {summary['total_rankings_analyzed']}\n\n")
        
        # Experiment statistics section
        f.write("EXPERIMENT STATISTICS (ranked by failure percentage)\n")
        f.write("-" * 50 + "\n")
        f.write(f"{'Experiment ID':<35}{'Failed':<8}{'Timeout':<9}{'Success':<9}{'Total':<7}{'Fail %':<8}\n")
        f.write("-" * 76 + "\n")
        
        for _, row in experiment_stats_df.iterrows():  # Show every experiment
            f.write(f"{row['experiment_id']:<35}{row['other_failed']:<8}{row['timeout_failed']:<9}"
                   f"{row['successful']:<9}{row['total_attempts']:<7}{row['failure_rate']:<8.1%}\n")
        
        # if len(experiment_stats_df) > 20:
        #     f.write(f"... and {len(experiment_stats_df) - 20} more experiments\n")
        
        f.write("\n")
        
        # Overall performance ranking
        f.write("OVERALL PERFORMANCE RANKING (by number of 1st place wins)\n")
        f.write("-" * 60 + "\n")
        
        # Sort by number of 1st place wins (absolute problem-solving ability), then by win rate
        performance_ranking = results_df.sort_values(['first_place_wins', 'win_rate'], ascending=False)
        
        f.write(f"{'Rank':<6}{'Combo':<25}{'Win Rate':<12}{'Wins WC':<8}{'Total':<8}{'1st':<8}{'2nd':<8}{'3rd':<8}{'>3rd':<8}{'Timeout':<8}{'Other Fail':<10}\n")
        f.write("-" * 106 + "\n")
        
        for idx, (_, row) in enumerate(performance_ranking.iterrows()):
            rank_1 = row.get('rank_1_count', 0)
            rank_2 = row.get('rank_2_count', 0)  
            rank_3 = row.get('rank_3_count', 0)
            rank_gt3 = row.get('rank_greater_than_3_count', 0)
            timeouts = row.get('timeout_failures', 0)
            other_fails = row.get('other_failures', 0)
            
            f.write(f"{idx+1:<6}{row['combo']:<25}{row['win_rate']:<12.3f}{row['wins_without_competition']:<8}"
                   f"{row['total_attempts']:<8}{rank_1:<8}{rank_2:<8}{rank_3:<8}{rank_gt3:<8}{timeouts:<8}{other_fails:<10}\n")
        
        f.write("\n")
        
        # Detailed breakdown by combo
        f.write("DETAILED BREAKDOWN BY COMBINATION\n")
        f.write("-" * 40 + "\n\n")
        
        for _, row in performance_ranking.iterrows():
            f.write(f"Combination: {row['combo']}\n")
            f.write(f"  Total Attempts: {row['total_attempts']}\n")
            f.write(f"  Successful Rankings: {row['total_appearances']}\n")
            f.write(f"  Timeout Failures: {row['timeout_failures']}\n")
            f.write(f"  Other Failures: {row['other_failures']}\n")
            f.write(f"  Total Failed Attempts: {row['failed_attempts']}\n")
            f.write(f"  First Place Wins: {row['first_place_wins']}\n")
            f.write(f"  Wins Without Competition: {row['wins_without_competition']}\n")
            f.write(f"  Win Rate: {row['win_rate']:.1%}\n")
            f.write("  Rank Distribution:\n")
            
            # Show all available ranks (exclude the special rank_greater_than_3_count column)
            rank_cols = [col for col in row.index if col.startswith('rank_') and col.endswith('_count') and 'greater' not in col]
            rank_numbers = sorted([int(col.split('_')[1]) for col in rank_cols])
            
            for rank_num in rank_numbers:
                count = row.get(f'rank_{rank_num}_count', 0)
                rate = row.get(f'rank_{rank_num}_rate', 0)
                if count > 0:
                    f.write(f"    {rank_num}{'st' if rank_num==1 else 'nd' if rank_num==2 else 'rd' if rank_num==3 else 'th'} place: {count} times ({rate:.1%})\n")
            
            f.write("\n")
        
        # Analysis by catalog type
        f.write("ANALYSIS BY CATALOG TYPE\n")
        f.write("-" * 30 + "\n")
        catalog_summary = results_df.groupby('catalog_type').agg({
            'first_place_wins': 'sum',
            'wins_without_competition': 'sum',
            'total_appearances': 'sum',
            'win_rate': 'mean'
        }).sort_values('win_rate', ascending=False)
        
        for catalog_type, stats in catalog_summary.iterrows():
            overall_rate = stats['first_place_wins'] / max(1, stats['total_appearances'])
            f.write(f"{catalog_type}:\n")
            f.write(f"  Total First Place Wins: {stats['first_place_wins']}\n")
            f.write(f"  Total Wins Without Competition: {stats['wins_without_competition']}\n")
            f.write(f"  Total Appearances: {stats['total_appearances']}\n") 
            f.write(f"  Overall Win Rate: {overall_rate:.1%}\n")
            f.write(f"  Average Win Rate: {stats['win_rate']:.1%}\n\n")
        
        # Analysis by solution type
        f.write("ANALYSIS BY SOLUTION TYPE\n")
        f.write("-" * 30 + "\n")
        solution_summary = results_df.groupby('solution_type').agg({
            'first_place_wins': 'sum',
            'wins_without_competition': 'sum',
            'total_appearances': 'sum',
            'win_rate': 'mean'
        }).sort_values('win_rate', ascending=False)
        
        for solution_type, stats in solution_summary.iterrows():
            overall_rate = stats['first_place_wins'] / max(1, stats['total_appearances'])
            f.write(f"{solution_type}:\n")
            f.write(f"  Total First Place Wins: {stats['first_place_wins']}\n")
            f.write(f"  Total Wins Without Competition: {stats['wins_without_competition']}\n")
            f.write(f"  Total Appearances: {stats['total_appearances']}\n")
            f.write(f"  Overall Win Rate: {overall_rate:.1%}\n") 
            f.write(f"  Average Win Rate: {stats['win_rate']:.1%}\n\n")


def main():
    """Main entry point for the ranking analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze solution ranking performance across experiments and noise levels",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--database',
        default='results_database.csv',
        help='Path to the compiled results database CSV file'
    )
    
    parser.add_argument(
        '--output-csv',
        default='ranking_analysis.csv',
        help='Output CSV file for detailed ranking data'
    )
    
    parser.add_argument(
        '--output-report',
        default='ranking_report.txt',
        help='Output text file for comprehensive ranking report'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load database
    try:
        df = load_database(args.database)
    except Exception:
        return 1
    
    # Analyze rankings
    logging.info("Starting ranking analysis...")
    results_df, summary = analyze_all_rankings(df)
    
    if results_df.empty:
        logging.error("No ranking data generated!")
        return 1
    
    # Analyze experiment statistics
    logging.info("Analyzing experiment statistics...")
    experiment_stats_df = analyze_experiment_statistics(df)
    
    # Save results
    results_df.to_csv(args.output_csv, index=False)
    logging.info(f"Saved detailed results to {args.output_csv}")
    
    # Generate and save report
    generate_ranking_report(results_df, summary, experiment_stats_df, args.output_report)
    logging.info(f"Saved comprehensive report to {args.output_report}")
    
    # Print summary to console
    logging.info(f"\nRanking Analysis Summary:")
    logging.info(f"Analyzed {summary['total_experiment_noise_combinations']} experiment×noise combinations")
    logging.info(f"Found {summary['total_unique_combos']} unique catalog×solution combinations")
    logging.info(f"Processed {summary['total_rankings_analyzed']} individual rankings")
    
    # Show top performers
    top_performers = results_df.nlargest(3, 'win_rate')
    logging.info(f"\nTop 3 Performers by Win Rate:")
    for idx, (_, row) in enumerate(top_performers.iterrows()):
        logging.info(f"  {idx+1}. {row['combo']}: {row['win_rate']:.1%} ({row['first_place_wins']}/{row['total_appearances']})")
    
    return 0


if __name__ == '__main__':
    exit(main())