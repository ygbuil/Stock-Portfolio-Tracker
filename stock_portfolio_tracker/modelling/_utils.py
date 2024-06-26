import numpy as np
import pandas as pd


def calculate_current_quantity(group: pd.DataFrame, quantity_col_name: str) -> pd.DataFrame:
    group = (
        group.assign(
            current_quantity=np.nan,
            asset_split=lambda df: df["asset_split"].replace(0, 1),
            **{quantity_col_name: group[quantity_col_name].replace(np.nan, 0)},
        )
        .sort_values(["date"], ascending=False)
        .reset_index(drop=True)
    )

    iterator = list(reversed(group.index))

    # iterate from older to newer date
    for i in iterator:
        # if first day
        if i == iterator[0]:
            if np.isnan(group.loc[i, quantity_col_name]):
                group.loc[i, "current_quantity"] = 0
            else:
                group.loc[i, "current_quantity"] = group.loc[i, quantity_col_name]
        else:
            # current_quantity = quantity_purchased_or_sold + (yesterdays_quantity * asset_split) # noqa: ERA001 E501
            group.loc[i, "current_quantity"] = (
                group.loc[i, quantity_col_name]
                + group.loc[i + 1, "current_quantity"] * group.loc[i, "asset_split"]
            )

    return group.assign(
        asset_split=lambda df: df["asset_split"].replace(1, 0),
        **{quantity_col_name: group[quantity_col_name].replace(0, np.nan)},
        current_quantity=lambda df: df["current_quantity"].replace(0, np.nan),
    )


def calculate_current_value(df: pd.DataFrame, current_value_column_name: str) -> pd.DataFrame:
    return (
        df.assign(current_value=df["current_quantity"] * df["close_unadjusted_local_currency"])
        .rename(columns={"current_value": current_value_column_name})
        .groupby(["date", "asset_ticker"])
        .first()  # get the latest current state when there are multiple transactions at the same day for a ticker # noqa: E501
        .sort_values(by=["asset_ticker", "date"], ascending=[True, False])
        .reset_index()
    )


def calculate_current_percent_gain(
    df: pd.DataFrame,
    current_value_column_name: str,
) -> pd.DataFrame:
    df = sort_by_columns(
        df,
        ["date"],
        [False],
    ).assign(
        money_out=np.nan,
        money_in=np.nan,
        value=lambda df: df["value"].replace(np.nan, 0),
        **{current_value_column_name: lambda df: df[current_value_column_name].replace(np.nan, 0)},
    )

    iterator = list(reversed(df.index))
    curr_money_in = 0

    for i in iterator:
        if i == iterator[0]:
            df.loc[i, "money_out"] = min(df.loc[i, "value"], 0)
        else:
            df.loc[i, "money_out"] = df.loc[i + 1, "money_out"] + min(df.loc[i, "value"], 0)

        curr_money_in += max(0, df.loc[i, "value"])
        df.loc[i, "money_in"] = df.loc[i, current_value_column_name] + curr_money_in

    df = (
        df.assign(
            current_gain=lambda df: df["money_out"] + df["money_in"],
            current_percent_gain=lambda df: df.apply(
                lambda x: round((abs(x["money_in"] / x["money_out"]) - 1) * 100, 2)
                if x["money_out"] != 0
                else 0,
                axis=1,
            ),
        )
        .groupby("date")
        .first()
        .reset_index()
    )[["date", "current_gain", "current_percent_gain"]]

    df.loc[0, "current_gain"] = 0
    df.loc[0, "current_percent_gain"] = 0

    return sort_by_columns(
        df,
        ["date"],
        [False],
    )


def calculat_portfolio_current_positions(
    portfolio_model: pd.DataFrame,
    portfolio_data: pd.DataFrame,
) -> pd.DataFrame:
    asset_portfolio_current_positions = portfolio_model[
        portfolio_model["date"] == portfolio_data.end_date
    ][["date", "asset_ticker", "current_quantity", "current_position_value"]].reset_index(drop=True)

    return (
        asset_portfolio_current_positions.assign(
            percent=round(
                asset_portfolio_current_positions["current_position_value"]
                / asset_portfolio_current_positions["current_position_value"].sum()
                * 100,
                2,
            ),
            current_position_value=round(
                asset_portfolio_current_positions["current_position_value"],
                2,
            ),
        )
        .sort_values(["current_position_value"], ascending=False)
        .reset_index(drop=True)
    )


def sort_by_columns(
    df: pd.DataFrame,
    columns: list[str],
    ascending: list[bool],
) -> pd.DataFrame:
    return df.sort_values(
        by=columns,
        ascending=ascending,
    ).reset_index(drop=True)
