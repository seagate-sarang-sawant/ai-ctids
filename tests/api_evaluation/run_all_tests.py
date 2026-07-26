"""Run all API evaluation tests.

This script orchestrates the complete evaluation workflow:
1. Prepares test datasets from real data
2. Generates simulated test data
3. Runs API tests with validation set
4. Runs API tests with test set
5. Runs API tests with simulated data
6. Generates comprehensive evaluation report
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd: str, cwd: str = None):
    """Run a shell command and log output."""
    logger.info(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Command failed with return code {result.returncode}")
        logger.error(f"STDERR: {result.stderr}")
        return False
    
    logger.info(f"STDOUT: {result.stdout}")
    return True


def main():
    base_dir = Path(__file__).parent
    project_root = base_dir.parent.parent
    
    logger.info("="*80)
    logger.info("AI-CTIDS API EVALUATION TEST SUITE")
    logger.info("="*80)
    
    # Step 1: Prepare test data from real dataset
    logger.info("\n[1/6] Preparing test datasets from real CICIDS2017 data...")
    if not run_command(
        f"python3 {base_dir}/prepare_test_data.py "
        f"--data-path {project_root}/data/cicids2017.csv "
        f"--output-dir {base_dir}/data "
        f"--n-validation 1000 "
        f"--n-test 1000",
        cwd=str(project_root)
    ):
        logger.error("Failed to prepare test data")
        return
    
    # Step 2: Generate simulated data
    logger.info("\n[2/6] Generating simulated network flow data...")
    if not run_command(
        f"python3 {base_dir}/generate_simulated_data.py "
        f"--n-samples 500 "
        f"--output {base_dir}/data/simulated_flows.csv",
        cwd=str(project_root)
    ):
        logger.error("Failed to generate simulated data")
        return
    
    # Step 3: Test with validation set (batch API)
    logger.info("\n[3/6] Testing API with validation set (batch mode)...")
    if not run_command(
        f"python3 {base_dir}/test_api.py "
        f"--data-path {base_dir}/data/validation_small.csv "
        f"--batch-size 32 "
        f"--output {base_dir}/results_validation_batch.json",
        cwd=str(project_root)
    ):
        logger.error("Failed to test validation set (batch)")
        return
    
    # Step 4: Test with validation set (single API)
    logger.info("\n[4/6] Testing API with validation set (single mode)...")
    if not run_command(
        f"python3 {base_dir}/test_api.py "
        f"--data-path {base_dir}/data/validation_small.csv "
        f"--use-single-api "
        f"--output {base_dir}/results_validation_single.json",
        cwd=str(project_root)
    ):
        logger.error("Failed to test validation set (single)")
        return
    
    # Step 5: Test with test set (batch API)
    logger.info("\n[5/6] Testing API with test set (batch mode)...")
    if not run_command(
        f"python3 {base_dir}/test_api.py "
        f"--data-path {base_dir}/data/test_small.csv "
        f"--batch-size 32 "
        f"--output {base_dir}/results_test_batch.json",
        cwd=str(project_root)
    ):
        logger.error("Failed to test test set")
        return
    
    # Step 6: Test with simulated data
    logger.info("\n[6/6] Testing API with simulated data...")
    if not run_command(
        f"python3 {base_dir}/test_api.py "
        f"--data-path {base_dir}/data/simulated_flows.csv "
        f"--batch-size 32 "
        f"--output {base_dir}/results_simulated.json",
        cwd=str(project_root)
    ):
        logger.error("Failed to test simulated data")
        return
    
    logger.info("\n" + "="*80)
    logger.info("API EVALUATION COMPLETE!")
    logger.info("="*80)
    logger.info("\nResults saved to:")
    logger.info(f"  - {base_dir}/results_validation_batch.json")
    logger.info(f"  - {base_dir}/results_validation_single.json")
    logger.info(f"  - {base_dir}/results_test_batch.json")
    logger.info(f"  - {base_dir}/results_simulated.json")
    logger.info("\nTest data saved to:")
    logger.info(f"  - {base_dir}/data/")


if __name__ == "__main__":
    main()
