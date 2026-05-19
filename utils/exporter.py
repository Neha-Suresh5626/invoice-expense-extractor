import pandas as pd

def generate_excel(data):

    df = pd.DataFrame([data])

    output_path = "outputs/invoice_data.xlsx"

    df.to_excel(output_path, index=False)

    return output_path