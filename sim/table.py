from datetime import timedelta
import pandas as pd


def format_before_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    # Compute relative day/hour from min timestamp
    t0 = df["t"].min()
    rel = df["t"] - t0
    def fmt_time(delta: pd.Timedelta) -> str:
        d = delta.days
        h = int(delta.seconds // 3600)
        m = int((delta.seconds % 3600) // 60)
        return f"Day {d} {h:02d}:{m:02d}"
    out = pd.DataFrame({
        "time": [fmt_time(x) for x in rel],
        "actor_from": df["actor"],
        "actor_to": df["target"],
        "action": df["action"],
        "channel": df.get("channel", ""),
    })
    return out
