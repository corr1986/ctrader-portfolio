"""Asset grafici del brand XybridFX: immagine profilo e banner per X.

Stesso tema scuro di render.py. Il monogramma è una "X" formata da due
curve che si incrociano: equity (verde) e balance (blu), come nel recap.
"""
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "#0d1117"
FG = "#e6edf3"
GREEN = "#3fb950"
BLUE = "#58a6ff"
GREY = "#8b949e"
GRID = "#21262d"


def _wiggle(x, seed):
    """Rumore leggero per far somigliare le linee a curve di mercato."""
    rng = np.random.default_rng(seed)
    noise = np.cumsum(rng.normal(0, 0.018, x.size))
    return noise - np.linspace(noise[0], noise[-1], x.size)


def make_profile_image(out_path: str, size_px: int = 800) -> None:
    """Monogramma quadrato: X di curve verde/blu su fondo scuro."""
    fig = plt.figure(figsize=(size_px / 100, size_px / 100), dpi=100,
                     facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    x = np.linspace(0.12, 0.88, 300)
    t = (x - x[0]) / (x[-1] - x[0])
    rising = 0.20 + 0.60 * t**1.15 + _wiggle(x, 7)
    falling = 0.80 - 0.60 * t**0.9 + _wiggle(x, 21)

    ax.plot(x, falling, color=BLUE, linewidth=9, alpha=0.85,
            solid_capstyle="round")
    ax.plot(x, rising, color=GREEN, linewidth=11, solid_capstyle="round")
    ax.fill_between(x, rising, 0.06, color=GREEN, alpha=0.10)

    # punto finale della curva equity, come un prezzo live
    ax.scatter([x[-1]], [rising[-1]], s=260, color=GREEN, zorder=5)
    ax.scatter([x[-1]], [rising[-1]], s=90, color=BG, zorder=6)

    fig.savefig(out_path, facecolor=BG)
    plt.close(fig)


def make_banner(out_path: str, width_px: int = 1500, height_px: int = 500) -> None:
    """Banner profilo X: wordmark + tagline + motivo equity curve."""
    fig = plt.figure(figsize=(width_px / 100, height_px / 100), dpi=100,
                     facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 1)

    # griglia sottile da terminale
    for gy in np.arange(0.1, 1.0, 0.16):
        ax.axhline(gy, color=GRID, linewidth=0.7)
    for gx in np.arange(0.15, 3.0, 0.27):
        ax.axvline(gx, color=GRID, linewidth=0.7)

    # curva equity di sfondo, tenuta bassa per non sporcare il testo
    x = np.linspace(0, 3, 700)
    t = x / 3
    curve = 0.07 + 0.17 * t**1.3 + _wiggle(x, 11) * 0.7
    ax.plot(x, curve, color=GREEN, linewidth=3, alpha=0.55)
    ax.fill_between(x, curve, 0, color=GREEN, alpha=0.06)

    ax.text(1.5, 0.62, "XybridFX", color=FG, fontsize=64,
            fontweight="bold", ha="center", va="center", family="DejaVu Sans")
    ax.text(1.5, 0.40, "Real money. Fully automated. Verifiable.",
            color=GREY, fontsize=21, ha="center", va="center")
    ax.text(1.5, 0.27, "Every trade published hourly — losing weeks included.",
            color=GREY, fontsize=13.5, ha="center", va="center", alpha=0.85)

    fig.savefig(out_path, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    import os
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out_dir, exist_ok=True)
    make_profile_image(os.path.join(out_dir, "profile.png"))
    make_banner(os.path.join(out_dir, "banner.png"))
    print("Asset generati in", out_dir)
