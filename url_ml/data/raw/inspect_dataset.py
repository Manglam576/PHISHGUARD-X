import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/raw/PhiUSIIL_Phishing_URL_Dataset.csv")


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print("\nDataset shape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nLabel distribution:")
    print(df["label"].value_counts())

    print("\nMissing values:")
    print(df.isnull().sum().sum())


if __name__ == "__main__":
    main()