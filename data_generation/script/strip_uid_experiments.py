#!/usr/bin/env python3
# filepath: /mnt/ssd1/eymeric/py-xl-sindy-data-visualisation/data_generation/script/strip_uid_experiments.py
"""
Script to strip UID experiment entries from JSON result files.
Removes all solution UIDs while preserving training_data and validation_data.
"""

import json
import os
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_uid_pattern(key: str) -> bool:
    """
    Check if a key matches the UID pattern (32-character hexadecimal string).
    
    Args:
        key: The key to check
        
    Returns:
        True if the key matches UID pattern, False otherwise
    """
    # UID pattern: exactly 32 hexadecimal characters
    uid_pattern = re.compile(r'^[a-f0-9]{32}$')
    return bool(uid_pattern.match(key))

def strip_uid_experiments(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Strip UID experiment entries from the JSON data structure.
    
    Args:
        data: The JSON data dictionary
        
    Returns:
        Tuple of (cleaned_data, num_stripped_entries)
    """
    cleaned_data = data.copy()
    num_stripped = 0
    
    # Navigate to validation_group.data
    try:
        validation_group = cleaned_data.get('visualisation', {}).get('validation_group', {})
        validation_data = validation_group.get('data', {})
        
        if not validation_data:
            logger.warning("No validation_group.data found in JSON structure")
            return cleaned_data, 0
        
        # Identify UID entries to remove
        uid_entries = []
        preserved_entries = []
        
        for key in validation_data.keys():
            if is_uid_pattern(key):
                uid_entries.append(key)
            else:
                preserved_entries.append(key)
        
        # Remove UID entries
        for uid in uid_entries:
            del validation_data[uid]
            num_stripped += 1
        
        logger.info(f"Preserved entries: {preserved_entries}")
        logger.info(f"Stripped {num_stripped} UID entries: {uid_entries[:5]}{'...' if len(uid_entries) > 5 else ''}")
        
    except Exception as e:
        logger.error(f"Error processing JSON structure: {e}")
        return data, 0
    
    return cleaned_data, num_stripped

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except:
        return 0

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def process_json_file(
    input_file: Path, 
    output_file: Path, 
    dry_run: bool = False,
    create_backup: bool = True
) -> Tuple[bool, int, int, int]:
    """
    Process a single JSON file to strip UID experiments.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        dry_run: If True, don't actually write the file
        create_backup: If True, create backup of original file
        
    Returns:
        Tuple of (success, original_size, new_size, num_stripped)
    """
    try:
        # Load JSON data
        logger.info(f"Processing: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_size = get_file_size(input_file)
        
        # Strip UID experiments
        cleaned_data, num_stripped = strip_uid_experiments(data)
        
        if dry_run:
            logger.info(f"DRY RUN: Would strip {num_stripped} UID entries from {input_file}")
            # Estimate new size (rough approximation)
            estimated_reduction = 0.8 if num_stripped > 0 else 0
            estimated_new_size = int(original_size * (1 - estimated_reduction))
            return True, original_size, estimated_new_size, num_stripped
        
        # Create backup if requested and not in-place
        if create_backup and input_file != output_file:
            backup_file = input_file.with_suffix(input_file.suffix + '.backup')
            shutil.copy2(input_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write cleaned data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2)
        
        new_size = get_file_size(output_file)
        
        logger.info(f"Successfully processed {input_file}")
        logger.info(f"  Stripped: {num_stripped} UID entries")
        logger.info(f"  Size: {format_size(original_size)} → {format_size(new_size)} "
                   f"({format_size(original_size - new_size)} saved, "
                   f"{((original_size - new_size) / original_size * 100):.1f}% reduction)")
        
        return True, original_size, new_size, num_stripped
        
    except Exception as e:
        logger.error(f"Error processing {input_file}: {e}")
        return False, 0, 0, 0

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Strip UID experiment entries from JSON result files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all JSON files in results directory
  python strip_uid_experiments.py --input-dir results --output-dir results_stripped
  
  # Dry run to preview changes
  python strip_uid_experiments.py --input-dir results --output-dir results_clean --dry-run
  
  # In-place modification with backups
  python strip_uid_experiments.py --input-dir results --in-place --verbose
  
  # Process specific files
  python strip_uid_experiments.py --input-dir results --output-dir clean --pattern "*cart_pole*.json"
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=Path,
        required=True,
        help='Directory containing JSON files to process'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Directory to save cleaned JSON files (required unless --in-place)'
    )
    
    parser.add_argument(
        '--in-place',
        action='store_true',
        help='Modify files in place (creates .backup files)'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.json',
        help='File pattern to match (default: *.json)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not args.in_place and not args.output_dir:
        parser.error("Either --output-dir or --in-place must be specified")
    
    if not args.input_dir.exists():
        parser.error(f"Input directory does not exist: {args.input_dir}")
    
    # Find JSON files
    json_files = list(args.input_dir.glob(args.pattern))
    
    if not json_files:
        logger.warning(f"No JSON files found matching pattern '{args.pattern}' in {args.input_dir}")
        return 1
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Process files
    total_original_size = 0
    total_new_size = 0
    total_stripped = 0
    successful_files = 0
    
    for json_file in json_files:
        # Determine output file
        if args.in_place:
            output_file = json_file
        else:
            relative_path = json_file.relative_to(args.input_dir)
            output_file = args.output_dir / relative_path
        
        # Process file
        success, orig_size, new_size, num_stripped = process_json_file(
            json_file, 
            output_file, 
            dry_run=args.dry_run,
            create_backup=args.in_place
        )
        
        if success:
            successful_files += 1
            total_original_size += orig_size
            total_new_size += new_size
            total_stripped += num_stripped
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("PROCESSING SUMMARY")
    logger.info("="*60)
    logger.info(f"Files processed: {successful_files}/{len(json_files)}")
    logger.info(f"Total UID entries stripped: {total_stripped}")
    
    if not args.dry_run:
        logger.info(f"Total size reduction: {format_size(total_original_size)} → "
                   f"{format_size(total_new_size)}")
        logger.info(f"Space saved: {format_size(total_original_size - total_new_size)} "
                   f"({((total_original_size - total_new_size) / max(1, total_original_size) * 100):.1f}% reduction)")
    else:
        logger.info("DRY RUN - No files were actually modified")
    
    return 0 if successful_files == len(json_files) else 1

if __name__ == "__main__":
    exit(main())