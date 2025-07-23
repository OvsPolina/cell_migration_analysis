# This code uses pandera library to validate the input data in the application


import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema, Check

def is_slice_continuous(df: pd.DataFrame) -> bool:
    """
    Checks that for each 'Track n', the 'Slice n' values form a continuous sequence
    (i.e., no missing or duplicated slice numbers within a track).

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        bool: True if all 'Track n' groups have continuous 'Slice n' values, False otherwise.
    """
    # For each track n
    for _, group in df.groupby("Track n"):
        # Sort and drop NaN values
        slices = group["Slice n"].dropna().sort_values().astype(int)
        # Create thelist of expected values in the slice column (continuous)
        expected = list(range(slices.min(), slices.max() + 1))
        if slices.tolist() != expected:
            return False
    return True

input_schema = DataFrameSchema({
    "Track n": Column(pa.Float, nullable=False),
    "Slice n": Column(pa.Float, nullable=False),
    "X": Column(pa.Float, nullable=False),
    "Y": Column(pa.Float, nullable=False),
    },
    checks=[
        Check(is_slice_continuous ,error="Doubled Track n. Make sure each track has unique id.")
    ])
