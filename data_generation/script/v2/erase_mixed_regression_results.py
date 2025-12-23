""" Temporary script to erased mixed regression results from existing JSON files.
"""

import argparse
import json
import os
from typing import Dict, Any, List, Tuple

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "results")
RESULTS_DIR = os.path.normpath(RESULTS_DIR)


def is_mixed_regression(parameters: Dict[str, Any]) -> bool:
    """
    Returns True if both `paradigm` and `regression_type` are set to "mixed".
    Missing keys are treated as not mixed.
    """
    paradigm = parameters.get("paradigm")
    reg_type = parameters.get("regression_type")
    return paradigm == "mixed" and reg_type == "mixed"


def process_trajectories(trajectories: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Remove `regression_result` from trajectories where parameters are mixed.

    Returns (checked_count, removed_count).
    """
    checked = 0
    removed = 0
    erase_index = []
    for i,traj in enumerate(trajectories):
        rr = traj.get("regression_result")
        if rr is None:
            continue
        checked += 1
        params = rr.get("regression_parameters", {}) if isinstance(rr, dict) else {}
        if is_mixed_regression(params):
            # Erase the regression result completely
            erase_index.append(i)
            removed += 1

    for i in reversed(erase_index):
        del trajectories[i]
    
    return checked, removed


def process_file(path: str, dry_run: bool, backup: bool) -> Tuple[int, int, bool]:
    """Process a single JSON file. Returns (checked, removed, modified)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Skipping {path}: {e}")
        return 0, 0, False

    checked_total = 0
    removed_total = 0

    data_obj = data.get("data", {})

    # validation group
    vg = data_obj.get("validation_group")
    if isinstance(vg, dict) and isinstance(vg.get("trajectories"), list):
        c, r = process_trajectories(vg["trajectories"])
        checked_total += c
        removed_total += r

    # training group
    tg = data_obj.get("training_group")
    if isinstance(tg, dict) and isinstance(tg.get("trajectories"), list):
        c, r = process_trajectories(tg["trajectories"])
        checked_total += c
        removed_total += r

    modified = removed_total > 0
    if modified and not dry_run:
        if backup:
            try:
                with open(path + ".bak", "w", encoding="utf-8") as bf:
                    json.dump(data, bf, indent=4)
            except Exception as e:
                print(f"[WARN] Could not write backup for {path}: {e}")
        # Write updated data
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to write changes to {path}: {e}")
            modified = False

    return checked_total, removed_total, modified


def find_result_files(root: str) -> List[str]:
    files = []
    if not os.path.isdir(root):
        return files
    for name in os.listdir(root):
        if not name.endswith(".json"):
            continue
        files.append(os.path.join(root, name))
    return files


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Erase `regression_result` from results/*.json when both "
            "RegressionParameter.paradigm and regression_type are 'mixed'."
        )
    )
    parser.add_argument(
        "--results-dir",
        default=RESULTS_DIR,
        help="Directory containing results JSON files (default: repo results/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify files; only report what would change",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Write a .bak backup beside any modified file",
    )

    args = parser.parse_args()

    results_dir = os.path.abspath(args.results_dir)
    files = find_result_files(results_dir)

    if not files:
        print(f"[INFO] No JSON files found in {results_dir}")
        return

    total_checked = 0
    total_removed = 0
    total_modified = 0

    for path in sorted(files):
        checked, removed, modified = process_file(path, args.dry_run, args.backup)
        total_checked += checked
        total_removed += removed
        total_modified += 1 if modified else 0
        if removed:
            action = "would remove" if args.dry_run else "removed"
            print(f"[OK] {action} {removed} regression_result(s) in {os.path.basename(path)}")

    print(
        f"[SUMMARY] files={len(files)} checked={total_checked}"
        f" removed={total_removed} modified={total_modified} dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
