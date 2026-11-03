"""Pick 30 benchmark tasks from data/test.csv (15 spam, 15 ham) -> bench/tasks.json."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent

if __name__ == "__main__":
    test = pd.read_csv(ROOT / "data" / "test.csv")
    sample = test.groupby("label").sample(15, random_state=7)
    tasks = [{"id": i + 1, "message": row["message"], "label": int(row["label"])}
             for i, (_, row) in enumerate(sample.iterrows())]
    (ROOT / "bench" / "tasks.json").write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(tasks)} tasks (label 1 = spam, 0 = ham)")
