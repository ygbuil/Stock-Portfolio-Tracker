import numpy as np
import pandas as pd


def calculate_current_quantity(group: pd.DataFrame, quantity_col_name: str) -> pd.DataFrame:
    group["current_quantity"] = np.nan  # Initialize the new column
    iterator = list(reversed(group.index))

    for i in iterator:
        if i == iterator[0]:
            if np.isnan(group.loc[i, quantity_col_name]):
                group.loc[i, "current_quantity"] = 0
            else:
                group.loc[i, "current_quantity"] = group.loc[i, quantity_col_name]
        elif np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "asset_split"] == 0:
            group.loc[i, "current_quantity"] = group.loc[i + 1, "current_quantity"]
        elif not np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "asset_split"] == 0:
            group.loc[i, "current_quantity"] = (
                group.loc[i + 1, "current_quantity"] + group.loc[i, quantity_col_name]
            )
        elif np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "asset_split"] != 0:
            group.loc[i, "current_quantity"] = (
                group.loc[i + 1, "current_quantity"] * group.loc[i, "asset_split"]
            )
        elif not np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "asset_split"] != 0:
            group.loc[i, "current_quantity"] = (
                group.loc[i + 1, "current_quantity"] * group.loc[i, "asset_split"]
                + group.loc[i, quantity_col_name]
            )
        else:
            raise NotImplementedError("Scenario not taken into account.")
    group["current_quantity"] = group.apply(
        lambda x: np.nan if x["current_quantity"] == 0 else x["current_quantity"],
        axis=1,
    )
    return group


def calculate_current_value(df: pd.DataFrame, current_value_column_name: str) -> pd.DataFrame:
    return (
        df.assign(current_value=df["current_quantity"] * df["open_unadjusted_local_currency"])
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
        [True],
    )

    for date in df["date"]:
        df.loc[df["date"] == date, "money_out"] = sum(
            df[(df["date"] < date) & (df["value"] < 0)]["value"],
        )
        if len(df[df["date"] == date - pd.Timedelta(days=1)][current_value_column_name]) > 0:
            latest_current_value = df[df["date"] == date - pd.Timedelta(days=1)][
                current_value_column_name
            ].iloc[0]
        else:
            latest_current_value = 0
        df.loc[df["date"] == date, "money_in"] = (
            sum(df[(df["date"] < date) & (df["value"] > 0)]["value"]) + latest_current_value
        )

    return (
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
        .last()
        .reset_index()
    )[["date", "current_gain", "current_percent_gain"]]


def sort_by_columns(
    df: pd.DataFrame,
    columns: list[str],
    ascending: list[bool],
) -> pd.DataFrame:
    return df.sort_values(
        by=columns,
        ascending=ascending,
    ).reset_index(drop=True)
