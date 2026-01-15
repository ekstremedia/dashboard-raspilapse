"""Graphs service for running db_graphs.py and listing generated graphs."""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def get_graphs_dir() -> Path:
    """Get the graphs directory path."""
    return Path("/home/pi/raspilapse/graphs")


def list_graphs() -> List[Dict]:
    """List all available graph images."""
    graphs_dir = get_graphs_dir()
    graphs = []

    if not graphs_dir.exists():
        return graphs

    for f in sorted(graphs_dir.glob("*.png")):
        stat = f.stat()
        graphs.append(
            {
                "filename": f.name,
                "name": f.stem.replace("_", " ").title(),
                "path": f"/graphs/image/{f.name}",
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
        )

    return graphs


def run_graphs_generator(time_range: str = "24h") -> Tuple[bool, str]:
    """Run the db_graphs.py script to generate graphs."""
    script_path = Path("/home/pi/raspilapse/scripts/db_graphs.py")

    if not script_path.exists():
        return False, "db_graphs.py script not found"

    # Build command
    cmd = ["/usr/bin/python3", str(script_path)]

    # Add time range argument (positional, no dash prefix)
    if time_range == "--all":
        cmd.append("--all")
    elif time_range and time_range != "24h":
        cmd.append(time_range)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd="/home/pi/raspilapse",
        )

        output = result.stdout + result.stderr

        if result.returncode == 0:
            return True, output
        else:
            return False, f"Script failed: {output}"

    except subprocess.TimeoutExpired:
        return False, "Script timed out after 2 minutes"
    except Exception as e:
        return False, f"Error running script: {str(e)}"
