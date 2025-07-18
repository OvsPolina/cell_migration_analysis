import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema, Check

def is_slice_continuous(df: pd.DataFrame) -> bool:
    # For each group by "Track n", check that "Slice n" passes `is_slice_continuous`
    for _, group in df.groupby("Track n"):
        slices = group["Slice n"].dropna().sort_values().astype(int)
        expected = list(range(slices.min(), slices.max() + 1))
        if slices.tolist() != expected:
            return False
    return True

def is_int_or_float(series):
    return series.apply(lambda x: isinstance(x, (int, float))).all()

input_schema = DataFrameSchema({
    "Track n": Column(pa.Float, nullable=False),
    "Slice n": Column(pa.Float, nullable=False),
    "X": Column(pa.Float, nullable=False),
    "Y": Column(pa.Float, nullable=False),
    },
    checks=[
        Check(is_slice_continuous ,error="Doubled Track n. Make sure each track has unique id.")
    ])
