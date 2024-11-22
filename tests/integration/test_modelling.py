"""Integration test for modelling."""

import pickle
from pathlib import Path

from loguru import logger

from stock_portfolio_tracker import modelling

ARTIFACTS_PATH = Path("tests/integration/artifacts")


def test_modelling() -> None:
    """Test the entire module package."""
    logger.info("Read artifacts.")

    config, portfolio_data, asset_prices, asset_dividends, benchmark = _read_artifacts(
        ["config", "portfolio_data", "asset_prices", "asset_dividends", "benchmark"],
    )

    logger.info("Start of modelling.")
    outputs = modelling.model_data(
        portfolio_data,
        benchmark,
        asset_prices,
        asset_dividends,
    )

    expected_outputs = _read_artifacts(
        [
            "portfolio_evolution",
            "assets_distribution",
            "benchmark_val_evolution_abs",
            "assets_vs_benchmark",
            "benchmark_gain_evolution",
            "dividends_company",
            "dividends_year",
        ],
    )

    assert all(
        output.equals(expected_output)
        for output, expected_output in zip(outputs, expected_outputs, strict=False)
    )


def _read_artifacts(artifact_names: list[str]) -> list:
    artifacts_loaded = []

    for artifact_name in artifact_names:
        with Path.open(ARTIFACTS_PATH / Path(f"{artifact_name}.pkl"), "rb") as file:
            artifacts_loaded.append(pickle.load(file))  # noqa: S301

    return artifacts_loaded
