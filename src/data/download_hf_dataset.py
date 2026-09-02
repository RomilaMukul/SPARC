"""
Utility module for downloading and streaming SPARC telemetry datasets from Hugging Face.
Primary repository: Romila2036/sparc_project
"""

import os
from pathlib import Path
import urllib.request
import pandas as pd

HF_REPO_RAW_URL = "https://huggingface.co/datasets/Romila2036/sparc_project/raw/main/"

def download_hf_dataset(filename: str = "aditya_l1_telemetry.csv", destination_dir: Path | str = "data/processed") -> Path:
    """
    Downloads a dataset file from Hugging Face if not present locally.
    Returns the Path to the downloaded file.
    """
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    if dest_path.exists():
        return dest_path

    url = HF_REPO_RAW_URL + filename
    print(f"[HF DATASET] Downloading {filename} from {url}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"[HF DATASET] Successfully downloaded {filename} to {dest_path}")
    except Exception as e:
        print(f"[HF DATASET WARNING] Could not download {filename} from HF: {e}")

    return dest_path


def load_sparc_dataframe(filepath_or_name: Path | str, default_hf_filename: str = "aditya_l1_telemetry.csv") -> pd.DataFrame:
    """
    Loads a DataFrame from local disk if present, or streams directly from Hugging Face.
    """
    local_path = Path(filepath_or_name)
    if local_path.exists():
        return pd.read_csv(local_path)

    filename = local_path.name if local_path.name else default_hf_filename
    url = HF_REPO_RAW_URL + filename
    print(f"[HF STREAM] Local file '{local_path}' not found. Ingesting directly from HF: {url}")
    try:
        return pd.read_csv(url)
    except Exception as e:
        print(f"[HF STREAM WARNING] Direct stream failed ({e}). Checking local preprocessing...")
        raise FileNotFoundError(f"Could not load dataset locally from {local_path} or remotely from {url}") from e
