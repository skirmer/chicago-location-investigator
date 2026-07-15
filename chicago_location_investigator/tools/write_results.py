import pandas as pd
from pathlib import Path
from datetime import datetime



def write_results_file(response, outputname):
    """Write the API results to file, for later user access."""

    OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(response).to_csv(f"{OUTPUT_DIR}/{outputname}_{datetime.now():%Y%m%d_%H%M%S}.csv", index=False)

    print(f"File written to {OUTPUT_DIR}/{outputname}_{datetime.now():%Y%m%d_%H%M%S}.csv")
