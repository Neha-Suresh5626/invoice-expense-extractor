import pandas as pd
import os


def export_to_excel(data, filepath):

    df = pd.DataFrame([data])

    if os.path.exists(filepath):

        existing_df = pd.read_excel(filepath)

        updated_df = pd.concat(
            [existing_df, df],
            ignore_index=True
        )

        updated_df.to_excel(filepath, index=False)

    else:

        df.to_excel(filepath, index=False)