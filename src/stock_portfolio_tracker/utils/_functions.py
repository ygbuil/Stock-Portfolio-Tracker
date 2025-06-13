import pickle
import shutil
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger


def delete_current_artifacts(directory: Path) -> None:
    """Delete all files and subdirectories in the specified directory except for `.gitkeep`.

    Args:
        directory: The path to the directory where files and folders should be deleted.
    """
    logger.info(f"Deleting existing artifacts in: {directory}")

    for item in directory.iterdir():
        if item.name == ".gitkeep":
            continue  # Skip .gitkeep file

        if item.is_file():
            item.unlink()
            logger.info(f"Deleted file: {item}")
        elif item.is_dir():
            shutil.rmtree(item)
            logger.info(f"Deleted directory: {item}")

    logger.info("Cleanup completed.")


def multithreader(func: Callable[..., Any], args: list[tuple[Any, ...]]) -> list[Any]:
    """Spawns multiple threads in parallel, efective for I/O bound operations such as API calls.

    Args:
        func: Function to parallelize.
        args: Arguments for the function, for each thread:
            [("NVDA", 01-01-2020, 01-01-2024), ("PYPL", 01-01-2020, 01-01-2024), ...]

    Returns:
        List with the result of each function.
    """
    result = []

    with ThreadPoolExecutor() as executor:
        # create a list of tasks to be submitted to the Tread Pool
        futures = [executor.submit(func, *curr_args) for curr_args in args]

        # append tasks to result as they are being completed
        for future in as_completed(futures):
            result.append(future.result())  # noqa: PERF401

    return result


def parse_underscore_text(text: str) -> str:
    """Parse snake case text to normal readable text.

    Args:
        text: Snake case text.

    Returns:
        The parsed text with underscores replaced by spaces and the first letter capitalized.
    """
    return f"{text[0].upper()}{text[1:]}".replace("_", " ")


def load_pickle(file_path: Path, file_name: str) -> pd.DataFrame | Any:
    """Read saved artifacts.

    Args:
        file_path: Path to the directory containing the artifacts.
        file_name: Name of the file containing the artifacts.

    Returns:
        Artifact object.
    """
    with Path.open(file_path / file_name, "rb") as file:
        return pickle.load(file)  # noqa: S301
