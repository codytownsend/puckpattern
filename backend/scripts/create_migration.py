#!/usr/bin/env python3
"""
Script to generate a new Alembic migration based on the current models.
"""
import os
import sys
import subprocess
import argparse

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)


def create_migration(message: str = "auto-generated migration"):
    """
    Generate a new Alembic migration.
    
    Args:
        message: Migration message
    """
    # Get the alembic directory
    alembic_dir = os.path.join(parent_dir, "alembic")
    
    # Change to parent directory to run alembic
    os.chdir(parent_dir)
    
    # Run alembic command
    cmd = ["alembic", "revision", "--autogenerate", "-m", message]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error generating migration:")
        print(result.stderr)
        sys.exit(1)
    
    print(result.stdout)
    print("Migration generated successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate new Alembic migration")
    parser.add_argument("-m", "--message", type=str, default="auto-generated migration",
                       help="Migration message")
    
    args = parser.parse_args()
    create_migration(args.message)