#!/usr/bin/env python3
"""
Regression Time Analysis

This script analyzes regression times from experiment JSON files to provide
statistical insights for timeout configuration.

The script processes all JSON files in the results directory and extracts
regression_time values from the extra_info sections, then computes:
- Descriptive statistics (mean, median, std, min, max)
- Quartiles (Q1, Q3) and percentiles (90th, 95th, 99th)
- Analysis by catalog type, solution type, and noise level
- Histogram and distribution plots
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import warnings

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def extract_regression_times_from_file(json_file: Path) -> List[Dict[str, Any]]:
    """
    Extract regression times and metadata from a single JSON file.
    
    Args:
        json_file: Path to the JSON file
        
    Returns:
        List of dictionaries containing regression time data
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        times_data = []
        
        # Navigate through the JSON structure to find solutions
        if 'visualisation' in data and 'validation_group' in data['visualisation']:
            validation_data = data['visualisation']['validation_group']['data']
            
            for solution_id, solution_data in validation_data.items():
                if 'extra_info' in solution_data:
                    extra_info = solution_data['extra_info']
                    
                    # Extract regression time and metadata
                    if 'regression_time' in extra_info:
                        record = {
                            'experiment_id': json_file.stem,
                            'solution_id': solution_id,
                            'regression_time': extra_info['regression_time'],
                            'noise_level': extra_info.get('noise_level', None),
                            'optimization_function': extra_info.get('optimization_function', None),
                            'regression_type': extra_info.get('regression_type', None),
                            'valid': extra_info.get('valid', None),
                        }
                        
                        # Try to extract catalog type from solution structure
                        if 'solution' in solution_data:
                            solution_keys = list(solution_data['solution'].keys())
                            if solution_keys:
                                record['catalog_type'] = solution_keys[0]
                        
                        times_data.append(record)
        
        return times_data
    
    except Exception as e:
        logging.error(f"Error processing file {json_file}: {e}")
        return []


def load_all_regression_times(results_dir: str) -> pd.DataFrame:
    """
    Load regression times from all JSON files in the results directory.
    
    Args:
        results_dir: Path to the directory containing result JSON files
        
    Returns:
        DataFrame with regression time data
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    json_files = list(results_path.glob("*.json"))
    logging.info(f"Found {len(json_files)} JSON files to process")
    
    all_times_data = []
    
    for json_file in json_files:
        logging.debug(f"Processing {json_file}")
        file_data = extract_regression_times_from_file(json_file)
        all_times_data.extend(file_data)
    
    df = pd.DataFrame(all_times_data)
    logging.info(f"Extracted {len(df)} regression time records")
    
    return df


def compute_statistics(times: np.ndarray) -> Dict[str, float]:
    """
    Compute comprehensive statistics for regression times.
    
    Args:
        times: Array of regression times
        
    Returns:
        Dictionary containing statistical measures
    """
    if len(times) == 0:
        return {}
    
    stats = {
        'count': len(times),
        'mean': np.mean(times),
        'median': np.median(times),
        'std': np.std(times),
        'min': np.min(times),
        'max': np.max(times),
        'q1': np.percentile(times, 25),
        'q3': np.percentile(times, 75),
        'iqr': np.percentile(times, 75) - np.percentile(times, 25),
        'p90': np.percentile(times, 90),
        'p95': np.percentile(times, 95),
        'p99': np.percentile(times, 99),
        'p99_9': np.percentile(times, 99.9),
    }
    
    return stats


def analyze_regression_times(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of regression times.
    
    Args:
        df: DataFrame with regression time data
        
    Returns:
        Dictionary containing analysis results
    """
    analysis = {}
    
    # Filter for valid regression times
    valid_times = df[df['regression_time'].notna() & (df['regression_time'] > 0)]
    times = valid_times['regression_time'].values
    
    # Overall statistics
    analysis['overall'] = compute_statistics(times)
    
    # Analysis by catalog type
    analysis['by_catalog_type'] = {}
    if 'catalog_type' in df.columns:
        for catalog_type in df['catalog_type'].dropna().unique():
            catalog_times = df[df['catalog_type'] == catalog_type]['regression_time']
            catalog_times = catalog_times[catalog_times.notna() & (catalog_times > 0)].values
            analysis['by_catalog_type'][catalog_type] = compute_statistics(catalog_times)
    
    # Analysis by solution/regression type
    analysis['by_regression_type'] = {}
    if 'regression_type' in df.columns:
        for reg_type in df['regression_type'].dropna().unique():
            reg_times = df[df['regression_type'] == reg_type]['regression_time']
            reg_times = reg_times[reg_times.notna() & (reg_times > 0)].values
            analysis['by_regression_type'][reg_type] = compute_statistics(reg_times)
    
    # Analysis by optimization function
    analysis['by_optimization_function'] = {}
    if 'optimization_function' in df.columns:
        for opt_func in df['optimization_function'].dropna().unique():
            opt_times = df[df['optimization_function'] == opt_func]['regression_time']
            opt_times = opt_times[opt_times.notna() & (opt_times > 0)].values
            analysis['by_optimization_function'][opt_func] = compute_statistics(opt_times)
    
    # Analysis by noise level
    analysis['by_noise_level'] = {}
    if 'noise_level' in df.columns:
        for noise_level in sorted(df['noise_level'].dropna().unique()):
            noise_times = df[df['noise_level'] == noise_level]['regression_time']
            noise_times = noise_times[noise_times.notna() & (noise_times > 0)].values
            analysis['by_noise_level'][noise_level] = compute_statistics(noise_times)
    
    # Analysis by validity
    analysis['by_validity'] = {}
    if 'valid' in df.columns:
        for validity in [True, False]:
            valid_subset = df[df['valid'] == validity]['regression_time']
            valid_subset = valid_subset[valid_subset.notna() & (valid_subset > 0)].values
            analysis['by_validity'][validity] = compute_statistics(valid_subset)
    
    return analysis


def generate_report(analysis: Dict[str, Any], output_file: str) -> None:
    """Generate a comprehensive text report of regression time analysis."""
    
    def format_stats(stats: Dict[str, float], indent: str = "") -> str:
        """Format statistics dictionary into readable text."""
        if not stats:
            return f"{indent}No data available\n"
        
        lines = []
        lines.append(f"{indent}Count: {stats['count']}")
        lines.append(f"{indent}Mean: {stats['mean']:.3f}s")
        lines.append(f"{indent}Median: {stats['median']:.3f}s")
        lines.append(f"{indent}Std Dev: {stats['std']:.3f}s")
        lines.append(f"{indent}Min: {stats['min']:.3f}s")
        lines.append(f"{indent}Max: {stats['max']:.3f}s")
        lines.append(f"{indent}Q1 (25th): {stats['q1']:.3f}s")
        lines.append(f"{indent}Q3 (75th): {stats['q3']:.3f}s")
        lines.append(f"{indent}IQR: {stats['iqr']:.3f}s")
        lines.append(f"{indent}90th percentile: {stats['p90']:.3f}s")
        lines.append(f"{indent}95th percentile: {stats['p95']:.3f}s")
        lines.append(f"{indent}99th percentile: {stats['p99']:.3f}s")
        lines.append(f"{indent}99.9th percentile: {stats['p99_9']:.3f}s")
        return "\n".join(lines) + "\n"
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("REGRESSION TIME ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(format_stats(analysis['overall']))
        
        # Timeout recommendations
        if analysis['overall']:
            stats = analysis['overall']
            f.write("TIMEOUT RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Conservative (99.9th percentile + buffer): {stats['p99_9'] * 1.5:.1f}s\n")
            f.write(f"Aggressive (99th percentile + buffer): {stats['p99'] * 1.2:.1f}s\n")
            f.write(f"Balanced (95th percentile + buffer): {stats['p95'] * 1.5:.1f}s\n")
            f.write(f"Fast (90th percentile + buffer): {stats['p90'] * 2.0:.1f}s\n\n")
        
        # Analysis by catalog type
        f.write("ANALYSIS BY CATALOG TYPE\n")
        f.write("-" * 40 + "\n")
        for catalog_type, stats in analysis['by_catalog_type'].items():
            f.write(f"{catalog_type}:\n")
            f.write(format_stats(stats, "  "))
        
        # Analysis by regression type
        f.write("ANALYSIS BY REGRESSION TYPE\n")
        f.write("-" * 40 + "\n")
        for reg_type, stats in analysis['by_regression_type'].items():
            f.write(f"{reg_type}:\n")
            f.write(format_stats(stats, "  "))
        
        # Analysis by optimization function
        f.write("ANALYSIS BY OPTIMIZATION FUNCTION\n")
        f.write("-" * 40 + "\n")
        for opt_func, stats in analysis['by_optimization_function'].items():
            f.write(f"{opt_func}:\n")
            f.write(format_stats(stats, "  "))
        
        # Analysis by noise level
        f.write("ANALYSIS BY NOISE LEVEL\n")
        f.write("-" * 40 + "\n")
        for noise_level, stats in analysis['by_noise_level'].items():
            f.write(f"Noise level {noise_level}:\n")
            f.write(format_stats(stats, "  "))
        
        # Analysis by validity
        f.write("ANALYSIS BY VALIDITY\n")
        f.write("-" * 40 + "\n")
        for validity, stats in analysis['by_validity'].items():
            f.write(f"Valid = {validity}:\n")
            f.write(format_stats(stats, "  "))


def create_visualizations(df: pd.DataFrame, output_dir: str) -> None:
    """Create visualization plots for regression time analysis."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Filter for valid times
    valid_times = df[df['regression_time'].notna() & (df['regression_time'] > 0)]
    
    if len(valid_times) == 0:
        logging.warning("No valid regression times found for visualization")
        return
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Overall distribution histogram
    plt.figure(figsize=(12, 8))
    plt.subplot(2, 2, 1)
    plt.hist(valid_times['regression_time'], bins=50, alpha=0.7, edgecolor='black')
    plt.xlabel('Regression Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Regression Times')
    plt.grid(True, alpha=0.3)
    
    # 2. Log-scale histogram for better visibility of distribution
    plt.subplot(2, 2, 2)
    plt.hist(valid_times['regression_time'], bins=50, alpha=0.7, edgecolor='black')
    plt.xlabel('Regression Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Regression Times (Log Scale)')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    
    # 3. Box plot by catalog type
    if 'catalog_type' in valid_times.columns and valid_times['catalog_type'].notna().any():
        plt.subplot(2, 2, 3)
        catalog_data = valid_times[valid_times['catalog_type'].notna()]
        if len(catalog_data) > 0:
            sns.boxplot(data=catalog_data, x='catalog_type', y='regression_time')
            plt.xlabel('Catalog Type')
            plt.ylabel('Regression Time (seconds)')
            plt.title('Regression Times by Catalog Type')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
    
    # 4. Box plot by regression type
    if 'regression_type' in valid_times.columns and valid_times['regression_type'].notna().any():
        plt.subplot(2, 2, 4)
        reg_type_data = valid_times[valid_times['regression_type'].notna()]
        if len(reg_type_data) > 0:
            sns.boxplot(data=reg_type_data, x='regression_type', y='regression_time')
            plt.xlabel('Regression Type')
            plt.ylabel('Regression Time (seconds)')
            plt.title('Regression Times by Regression Type')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path / 'regression_times_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. Detailed analysis plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Cumulative distribution
    axes[0, 0].hist(valid_times['regression_time'], bins=100, cumulative=True, 
                    density=True, alpha=0.7, edgecolor='black')
    axes[0, 0].set_xlabel('Regression Time (seconds)')
    axes[0, 0].set_ylabel('Cumulative Probability')
    axes[0, 0].set_title('Cumulative Distribution of Regression Times')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Q-Q plot for normality assessment
    from scipy import stats
    stats.probplot(valid_times['regression_time'], dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title('Q-Q Plot (Normal Distribution)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Times by noise level
    if 'noise_level' in valid_times.columns and valid_times['noise_level'].notna().any():
        noise_data = valid_times[valid_times['noise_level'].notna()]
        if len(noise_data) > 0:
            sns.boxplot(data=noise_data, x='noise_level', y='regression_time', ax=axes[1, 0])
            axes[1, 0].set_xlabel('Noise Level')
            axes[1, 0].set_ylabel('Regression Time (seconds)')
            axes[1, 0].set_title('Regression Times by Noise Level')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].grid(True, alpha=0.3)
    
    # Scatter plot of time vs noise level (if available)
    if 'noise_level' in valid_times.columns and valid_times['noise_level'].notna().any():
        noise_data = valid_times[valid_times['noise_level'].notna()]
        if len(noise_data) > 0:
            axes[1, 1].scatter(noise_data['noise_level'], noise_data['regression_time'], 
                              alpha=0.6, s=20)
            axes[1, 1].set_xlabel('Noise Level')
            axes[1, 1].set_ylabel('Regression Time (seconds)')
            axes[1, 1].set_title('Regression Time vs Noise Level')
            axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path / 'regression_times_detailed.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Visualizations saved to {output_path}")


def main():
    """Main entry point for the regression time analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze regression times from experiment JSON files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Directory containing result JSON files'
    )
    
    parser.add_argument(
        '--output-csv',
        default='regression_times.csv',
        help='Output CSV file for raw regression time data'
    )
    
    parser.add_argument(
        '--output-report',
        default='regression_time_report.txt',
        help='Output text file for comprehensive analysis report'
    )
    
    parser.add_argument(
        '--output-plots',
        default='.',
        help='Directory for output visualization plots'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Load regression time data
        logging.info("Loading regression time data...")
        df = load_all_regression_times(args.results_dir)
        
        if df.empty:
            logging.error("No regression time data found!")
            return 1
        
        # Save raw data
        df.to_csv(args.output_csv, index=False)
        logging.info(f"Saved raw data to {args.output_csv}")
        
        # Analyze regression times
        logging.info("Analyzing regression times...")
        analysis = analyze_regression_times(df)
        
        # Generate report
        generate_report(analysis, args.output_report)
        logging.info(f"Saved analysis report to {args.output_report}")
        
        # Create visualizations
        logging.info("Creating visualizations...")
        create_visualizations(df, args.output_plots)
        
        # Print summary to console
        if analysis['overall']:
            stats = analysis['overall']
            logging.info(f"\nRegression Time Analysis Summary:")
            logging.info(f"Total records: {stats['count']}")
            logging.info(f"Mean time: {stats['mean']:.3f}s")
            logging.info(f"Median time: {stats['median']:.3f}s")
            logging.info(f"95th percentile: {stats['p95']:.3f}s")
            logging.info(f"99th percentile: {stats['p99']:.3f}s")
            logging.info(f"Max time: {stats['max']:.3f}s")
            
            # Timeout recommendations
            logging.info(f"\nTimeout Recommendations:")
            logging.info(f"Conservative: {stats['p99_9'] * 1.5:.1f}s")
            logging.info(f"Balanced: {stats['p95'] * 1.5:.1f}s")
            logging.info(f"Aggressive: {stats['p90'] * 2.0:.1f}s")
        
        return 0
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())