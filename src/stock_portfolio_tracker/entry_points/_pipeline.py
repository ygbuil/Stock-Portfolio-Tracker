"""Main module to execute the project."""

import click
from loguru import logger

from stock_portfolio_tracker import modelling, preprocessing, reporting
from stock_portfolio_tracker.utils import timer


@click.command()
@click.option("--config-file-name")
@click.option("--transactions-file-name")
def pipeline(config_file_name: str, transactions_file_name: str) -> None:
    """Entry point for pipeline.

    :param config_file_name: File name for config.
    :param transactions_file_name: File name for transactions.
    """
    _pipeline(config_file_name, transactions_file_name)


@timer
def _pipeline(config_file_name: str, transactions_file_name: str) -> None:
    """Execute the project end to end.

    :param config_file_name: File name for config.
    :param transactions_file_name: File name for transactions.
    """
    logger.info("Start of execution.")

    logger.info("Start of preprocess.")
    config, portfolio_data, asset_prices, asset_dividends, benchmark_prices, benchmark_dividends = (
        preprocessing.preprocess(
            config_file_name,
            transactions_file_name,
        )
    )

    logger.info("Start of modelling.")
    (
        portfolio_evolution,
        assets_distribution,
        benchmark_val_evolution_abs,
        assets_vs_benchmark,
        benchmark_gain_evolution,
        dividends_company,
        dividends_year,
    ) = modelling.model_data(
        portfolio_data,
        benchmark_prices,
        asset_prices,
        asset_dividends,
    )

    logger.info("Start of generate reports.")
    reporting.generate_reports(
        config,
        portfolio_evolution,
        assets_distribution,
        benchmark_val_evolution_abs,
        assets_vs_benchmark,
        benchmark_gain_evolution,
        dividends_company,
        dividends_year,
    )

    logger.info("End of execution.")
