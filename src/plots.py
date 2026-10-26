"""One figure style for the whole project; every figure is saved as PNG and EPS."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "figs"

COLORS = {
    "distance": "#7f7f7f",
    "zscore": "#1f77b4",
    "sscore": "#d62728",
    "bertram": "#2ca02c",
    "kalman": "#9467bd",
    "market": "#000000",
}

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 10, "axes.titlesize": 11,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.alpha": 0.3, "legend.frameon": False,
})


def savefig(fig, name):
    """Save figs/<name>.png and figs/<name>.eps (EPS has no transparency, as LaTeX needs)."""
    FIGS.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGS / f"{name}.png", bbox_inches="tight")
    fig.savefig(FIGS / f"{name}.eps", format="eps", bbox_inches="tight")
    plt.close(fig)
