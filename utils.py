import pandas as pd
import matplotlib.pyplot as plt


def dataframe_to_image(df: pd.DataFrame, path: str = "table.png"):
    fig, ax = plt.subplots(figsize=(len(df.columns) * 2, len(df) * 0.6 + 1))
    ax.axis("off")
    table = ax.table(
        cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.auto_set_column_width(col=list(range(len(df.columns))))
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path
