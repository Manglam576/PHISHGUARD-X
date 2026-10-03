import pandas as pd
from pathlib import Path
import sys

# Allow importing from the parent project directory
sys.path.append(str(Path(__file__).resolve().parents[1]))

from features.url_features import extract_url_features


RAW_PATH = Path("data/raw/PhiUSIIL_Phishing_URL_Dataset.csv")
PROCESSED_PATH = Path("data/processed/url_features.csv")


def main():

    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {RAW_PATH}"
        )

    print("Loading dataset...")

    df = pd.read_csv(RAW_PATH)

    print(f"Original rows: {len(df)}")

    # Keep only the information we actually need.
    data = df[["URL", "label"]].copy()

    print("Extracting URL features...")

    feature_rows = []

    for index, url in enumerate(data["URL"]):

        try:
            features = extract_url_features(url)
            feature_rows.append(features)

        except Exception as e:
            print(f"Error processing row {index}: {e}")
            feature_rows.append(None)

        # Progress every 10,000 rows
        if (index + 1) % 10000 == 0:
            print(f"Processed {index + 1} URLs")

    features_df = pd.DataFrame(feature_rows)

    # Remove rows where feature extraction failed
    valid_mask = features_df.notna().all(axis=1)

    features_df = features_df[valid_mask].reset_index(drop=True)
    labels = data.loc[valid_mask, "label"].reset_index(drop=True)

    # Convert:
    # original 0 = phishing → project 1
    # original 1 = legitimate → project 0
    project_labels = labels.map({
        0: 1,
        1: 0
    })

    # Add label
    features_df["label"] = project_labels

    # Save
    PROCESSED_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    features_df.to_csv(
        PROCESSED_PATH,
        index=False
    )

    print("\nDataset preparation complete.")

    print(f"Saved to: {PROCESSED_PATH}")
    print(f"Rows: {len(features_df)}")
    print(f"Columns: {len(features_df.columns)}")

    print("\nProject label distribution:")
    print(features_df["label"].value_counts())

    print("\nFirst 5 rows:")
    print(features_df.head())


if __name__ == "__main__":
    main()