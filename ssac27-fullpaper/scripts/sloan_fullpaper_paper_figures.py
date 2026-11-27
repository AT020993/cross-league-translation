"""Figures for the SSAC27 full paper (Submission 47), drawn from committed results.

Called by scripts/render_sloan_fullpaper.py with the loaded inputs ``d``; every
plotted value is read from a committed summary or table, and each figure's
sentence title is checked against every plotted row before it is saved. No
figure computes a number that is not in a committed file (Amendment 16, rule 7).

Main text
Figure 1  European League Equivalents: the domestic EFF/36 in each league that
          the league-aware forecast treats like a 16 in Spain's ACB. When the
          league-changes test (E30) has outputs, a second panel shows its 45
          league pairs (``fig_equivalents_and_moves``).
Figure 2  League biases of a forecast blind to the source league, and of the
          league-aware forecast (E24).
Figure 3  The mechanism: the ladder of Table 1 as a picture.
Figure 4  The ladder on a conditional estimated reducible-error scale.
Figure 5  The Equivalents in each yearly refit (E19).
Figure 6  The forecast-gap guide as a curve (E20).
Figure 7  Coverage of the 80% error bands by source league and season (E8, E22).
Figure 8  What the same player keeps, skill by skill, under both estimators (E15a).

The frozen 2026-27 test, only once it is scored (Amendment 25, rule 1)
          Every registered paired contrast beside its 2020-2025 estimate
          (``fig_frozen_test``). It has no sentence title: its form, its rows and
          its caption were registered before scoring, and it is drawn whatever
          the test shows. The renderer hands it every value and every word.

Appendix
Figure A1 The robustness forest of the first draft.
Figure A2 Decision terms: cross-league vs same-league pair ordering, and the
          right share of translation's changed comparisons.
"""

# ruff: noqa: E501 -- figure strings
from __future__ import annotations

from pathlib import Path

FOCAL, COMP, GREY, LIGHT = "#1f5f8b", "#9aa3ab", "#5f6b75", "#e9edf1"
#: Text, axis lines and guide lines.
INK, AXIS, GRID = "#1b2733", "#7b8791", "#e3e7eb"
#: The one accent colour: what a figure asks the reader to look at first.
ACCENT = "#c8721a"
#: The focal colour, lighter: rows that a figure shows but its title does not name.
SOFT = "#9db9cf"
#: The typeface of the figures. Its files ship with the code (SIL Open Font License 1.1, see
#: the licence beside them), so the figures do not depend on the fonts of the machine.
FONT_NAME = "Source Sans Pro"
FONT_DIR = Path(__file__).resolve().parent / "fonts" / "source-sans-pro"
TIER_SHADES = {1: "#f3f6f9", 2: "#e6ecf2", 3: "#d8e1ea"}

LEAGUE_NAMES = {
    "spain-acb": "Spain (ACB)",
    "france-pro-a": "France (Pro A)",
    "italy-lba": "Italy (LBA)",
    "greece-a1": "Greece (A1)",
    "israel-bsl": "Israel (Winner League)",
    "turkey-bsl": "Turkey (BSL)",
    "aba-league": "Adriatic (ABA)",
    "germany-bbl": "Germany (BBL)",
    "lithuania-lkl": "Lithuania (LKL)",
    "vtb": "VTB United League",
}


class FigureClaimError(ValueError):
    """A sentence title would be false for at least one plotted row."""


def style():
    """The figures' common look: one open sans-serif face that ships with the code (so every
    machine draws the same letters), a role-mapped size ladder (9/8/7.5 pt), outward ticks,
    light spines, frameless legends, 300 dpi."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    known = {f.fname for f in font_manager.fontManager.ttflist}
    for file in sorted(FONT_DIR.glob("*.ttf")):
        if str(file) not in known:
            font_manager.fontManager.addfont(str(file))
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [FONT_NAME, "DejaVu Sans"],
            "font.size": 9,
            "text.color": INK,
            "axes.titlesize": 9.5,
            "axes.titleweight": "semibold",
            "axes.titlecolor": INK,
            "axes.labelsize": 9,
            "axes.labelcolor": INK,
            "legend.fontsize": 8,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 8,
            "xtick.color": AXIS,
            "ytick.color": AXIS,
            "xtick.labelcolor": INK,
            "ytick.labelcolor": INK,
            "axes.edgecolor": AXIS,
            "axes.linewidth": 0.6,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlelocation": "left",
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "lines.solid_capstyle": "round",
            "legend.frameon": False,
            "savefig.dpi": 300,
            "pdf.fonttype": 42,
            "svg.hashsalt": "ssac27",
        }
    )
    return plt


def value_grid(ax, axis="x"):
    """Light guide lines along the value axis, behind everything drawn."""
    ax.grid(True, axis=axis, zorder=0)
    ax.set_axisbelow(True)


def headline(fig, text, x=0.012, ha="left"):
    """The figure's sentence title: the one finding, in the heavier weight."""
    import matplotlib.pyplot as plt

    fig.suptitle(
        text,
        x=x,
        y=0.995,
        ha=ha,
        fontsize=plt.rcParams["axes.titlesize"],
        fontweight="semibold",
    )


def panel_name(ax, text):
    """The name of a panel under a headline: lighter than the headline."""
    ax.set_title(text, loc="left", fontweight="normal", color=GREY)


def minus(text: str) -> str:
    """A printed value with a true minus sign."""
    return text.replace("-", "\u2212")


def spread(positions, gap):
    """Label positions that keep their order and stand at least ``gap`` apart, each as near
    to its own value as that allows (labels at the ends of lines that end close together)."""
    order = sorted(range(len(positions)), key=lambda i: positions[i])
    placed = [positions[i] for i in order]
    for _ in range(200):
        moved = False
        for j in range(len(placed) - 1):
            short = gap - (placed[j + 1] - placed[j])
            if short > 1e-9:
                placed[j] -= short / 2
                placed[j + 1] += short / 2
                moved = True
        if not moved:
            break
    out = [0.0] * len(positions)
    for j, i in enumerate(order):
        out[i] = placed[j]
    return out


class FigureOverflow(ValueError):
    """Something drawn reaches the edge of the image and is cut off."""


def check_nothing_cut_off(path: Path, frame: int = 2, dark: float = 0.78) -> None:
    """Refuse a saved figure that has ink in the outermost pixels of the image.

    The figures are saved at their set size (no tight bounding box), so a legend or a label that
    is wider than the figure is cut off at the edge without an error. Found on 24 November 2026:
    the legend of Figure 1 had lost the start of its first entry and the end of its last. A
    figure that fits leaves a margin, so ink in the outer ``frame`` pixels means a cut."""
    import matplotlib.image

    image = matplotlib.image.imread(path)[..., :3].mean(axis=2)
    edges = {
        "left": image[:, :frame],
        "right": image[:, -frame:],
        "top": image[:frame, :],
        "bottom": image[-frame:, :],
    }
    cut = [side for side, pixels in edges.items() if (pixels < dark).any()]
    if cut:
        raise FigureOverflow(
            f"{Path(path).name}: ink in the outer {frame} pixels at the {' and the '.join(cut)} edge "
            "of the image; something drawn there may be cut off"
        )


def check_text_inside(fig, name: str, slack: float = 0.5) -> None:
    """Refuse a figure in which a legend or a drawn label reaches beyond the figure.

    The pixel check above can miss a cut (a gap between letters at the edge, a pale band, a label
    wholly outside the image). This one asks the layout itself: every legend, title, axis label,
    drawn tick label and free text must lie inside the figure. Text clipped to its axes is left
    out, since it cannot be drawn outside them."""
    fig.canvas.draw()
    box = fig.bbox
    items = [*fig.texts, *fig.legends]
    for ax in fig.axes:
        items += [
            ax.title,
            ax._left_title,
            ax._right_title,
            ax.xaxis.label,
            ax.yaxis.label,
        ]
        items += [
            t
            for t in ax.texts
            if not (t.get_clip_on() and t.get_clip_box() is not None)
        ]
        if ax.get_legend() is not None:
            items.append(ax.get_legend())
        for axis in (ax.xaxis, ax.yaxis):
            if not axis.get_visible():
                continue
            low, high = sorted(axis.get_view_interval())
            for tick in (*axis.get_major_ticks(), *axis.get_minor_ticks()):
                if low <= tick.get_loc() <= high:
                    items += [tick.label1, tick.label2]
    outside = []
    for item in items:
        if not item.get_visible() or (
            hasattr(item, "get_text") and not item.get_text().strip()
        ):
            continue
        e = item.get_window_extent()
        if (
            e.x0 < box.x0 - slack
            or e.x1 > box.x1 + slack
            or e.y0 < box.y0 - slack
            or e.y1 > box.y1 + slack
        ):
            outside.append(
                item.get_text()[:40] if hasattr(item, "get_text") else "legend"
            )
    if outside:
        raise FigureOverflow(
            f"{name}: reaches beyond the figure and would be cut off: {'; '.join(outside)}"
        )


#: The two checks below guard the author's render. The public reproduction switches them off: it
#: re-draws the figures to compare them, on a machine whose fonts may be wider.
EDGE_CHECKS = True


def _save(fig, path: Path):
    fig.savefig(path, metadata={"Software": None})
    import matplotlib.pyplot as plt

    try:
        if EDGE_CHECKS:
            # after the file is written, so that the check leaves the drawing as it was
            check_text_inside(fig, Path(path).name)
    finally:
        plt.close(fig)
    if EDGE_CHECKS:
        check_nothing_cut_off(path)
    return path


# --------------------------------------------------------------------- figure 1
def _draw_equivalents(plt, ax, rows, counts, xmax=21.0, print_values=False):
    """The Equivalents ladder on ``ax``. rows: exchange_rate_acb16.csv dicts;
    counts: e17_league_counts.csv dicts.

    ``print_values`` prints, right of the panel, the two equivalents that each row draws, each
    behind a small copy of its marker (filled: EuroLeague; open: EuroCup). They are the plotted
    values, read from the same rows and rounded as Table 1 rounds them (one decimal). The
    reference row prints nothing there: its value is the label "reference: 16"."""
    import matplotlib.transforms as mtransforms

    by = {}
    for r in rows:
        by.setdefault(r["source_league"], {})[r["destination"]] = r
    n = {c["source_league"]: int(c["e9_training"]) for c in counts}
    order = sorted(
        by,
        key=lambda k: (
            int(by[k]["euroleague"]["e9_tier"]),
            float(by[k]["euroleague"]["acb16_equivalent_eff36"]),
        ),
    )
    # claim check: every tier-3 league needs about a 19 (18.5-19.5) in both competitions
    for k in order:
        if int(by[k]["euroleague"]["e9_tier"]) == 3 and k != "aba-league":
            for dst in ("euroleague", "eurocup"):
                v = float(by[k][dst]["acb16_equivalent_eff36"])
                if not 18.5 <= v < 19.5:
                    raise FigureClaimError(
                        f"{k} {dst} equivalent {v:.2f} is not about 19"
                    )
    ys = {k: i for i, k in enumerate(order)}
    xmin = 14.0 if print_values else 14.3
    # tier bands
    for tier in (1, 2, 3):
        members = [ys[k] for k in order if int(by[k]["euroleague"]["e9_tier"]) == tier]
        ax.axhspan(
            min(members) - 0.5,
            max(members) + 0.5,
            color=TIER_SHADES[tier],
            lw=0,
            zorder=0,
        )
        ax.text(
            # with the values printed the panel is narrower: the tier is then named at the left
            # edge, where no interval of a tier's first row reaches
            (xmin + 0.14) if print_values else (xmax - 0.06),
            min(members) - 0.5 + 0.1,
            f"Tier {tier}",
            ha="left" if print_values else "right",
            va="top",
            fontsize=7.5,
            color=GREY,
        )
    ax.axvline(16, color=GREY, lw=0.7, ls="--", zorder=1)
    for k in order:
        y = ys[k]
        for dst, dy, face in (("euroleague", -0.15, FOCAL), ("eurocup", 0.15, "white")):
            r = by[k][dst]
            v, lo, hi = (
                float(r[c]) for c in ("acb16_equivalent_eff36", "ci95_low", "ci95_high")
            )
            if k == "spain-acb":
                ax.plot(
                    [v], [y + dy], "o", ms=5, mfc=face, mec=FOCAL, mew=1.0, zorder=3
                )
                continue
            ax.plot([lo, hi], [y + dy, y + dy], color=FOCAL, lw=1.2, zorder=2)
            ax.plot([v], [y + dy], "o", ms=5, mfc=face, mec=FOCAL, mew=1.0, zorder=3)
            if print_values:
                # points to the right of the panel's edge, at the height of the row
                at = 6.0 if dst == "euroleague" else 28.5

                def beside(points):
                    return mtransforms.blended_transform_factory(
                        ax.transAxes, ax.transData
                    ) + mtransforms.ScaledTranslation(
                        points / 72, 0, ax.figure.dpi_scale_trans
                    )

                ax.plot(
                    [1],
                    [y],
                    "o",
                    ms=3.4,
                    mfc=face,
                    mec=FOCAL,
                    mew=0.8,
                    transform=beside(at),
                    clip_on=False,
                    zorder=3,
                )
                ax.text(
                    1,
                    y,
                    f"{v:.1f}",
                    transform=beside(at + 4.0),
                    ha="left",
                    va="center",
                    fontsize=7.5,
                    color=INK,
                )
    ax.set_yticks(
        range(len(order)),
        [f"{LEAGUE_NAMES[k]}  (n = {n[k]})" for k in order],
    )
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(xmin, xmax)
    ax.set_xticks([15, 16, 17, 18, 19, 20])
    ax.set_xlabel("Domestic EFF/36 with the same forecast as 16 in Spain's ACB")
    ax.text(
        # (with the values printed the panel is narrower: the label starts clear of Spain's markers)
        16.4 if print_values else 16.25,
        -0.05,
        "reference: 16",
        fontsize=7.5,
        color=GREY,
        va="center",
    )
    ax.plot([], [], "o", mfc=FOCAL, mec=FOCAL, ms=5, label="EuroLeague arrival")
    ax.plot([], [], "o", mfc="white", mec=FOCAL, ms=5, label="EuroCup arrival")
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.0),
        ncol=2,
        handletextpad=0.3,
        columnspacing=1.2,
        borderaxespad=0.2,
    )


def fig_equivalents(rows, counts, out: Path) -> Path:
    """rows: exchange_rate_acb16.csv dicts; counts: e17_league_counts.csv dicts."""
    plt = style()
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    _draw_equivalents(plt, ax, rows, counts)
    ax.set_title(
        "Conditional equivalents when career history equals domestic rate",
        pad=16,
    )
    fig.subplots_adjust(left=0.27, right=0.98, bottom=0.14, top=0.86)
    return _save(fig, out / "fig1_equivalents.png")


#: Columns of the league-pair table of E30 (Amendment 14, S-f) that the second panel of
#: Figure 1 reads (written by scripts/sloan_fullpaper_league_changes.py as s_f_league_pairs.csv).
E30_PAIR_COLUMNS = (
    "league_lower_equivalent",
    "league_higher_equivalent",
    "predicted_change",
    "half_difference",
    "n_up",
    "n_down",
)
E30_POSITIVE_CASES = ("clear", "positive_named_limit")


def e30_panel_title(case: str, slope: float, low: float, high: float) -> str:
    """The title of the league-pair panel: it says no more than the registered case licenses
    (Amendment 14, "What the paper may say"; Amendment 17, rule 7 for an interval above 1)."""
    if case in E30_POSITIVE_CASES:
        if low <= 1 <= high:
            return "The test: league changes\nmoved as the table predicts"
        if high < 1:
            size = f"at about {slope:.2f} of its size"
        else:
            size = "by more than its size"
        return f"The test: league changes\nmoved the table's way,\n{size}"
    return {
        "positive_not_separable": "The test: a positive slope\nthat chance could produce",
        "null": "The test: the table did not\npredict league changes",
        "against": "The test: league changes\nmoved against the table",
    }[case]


#: The colour of the league pairs marked as a group in the second panel of Figure 1.
MARKED_COLOR = "#c8721a"


def fig_equivalents_and_moves(
    rows, counts, pair_rows, e30, out: Path, marked=None, notes=None, print_values=True
) -> Path:
    """Figure 1 with its second panel, drawn only when the E30 outputs exist (Amendment 19, rule 13).

    Left: the Equivalents ladder. Right: the 45 league pairs of E30 (S-f): for each pair, half
    the difference between the mean unexplained change of moves towards the league with the
    higher equivalent and of moves the other way, against the change the table predicts. Marker
    area follows the number of moves.

    The line is NOT a fit to the 45 points: it is the registered slope from all league changes,
    drawn through the origin, with its 95% interval as a band; the legend says so. The panel
    prints the slope, its interval, the number of league changes and the number of players, all
    read from the E30 summary. ``marked`` is (league code, league name): the league whose
    removal lowers the slope most; the pairs that include it are marked as a group. No single
    pair is named. ``notes`` (Amendment 20, rule 4) is {"lowest": the slope without that league,
    "refit": the slope with the table refitted only on earlier arrivals}: the first is printed
    beside the group it marks, the second under the counts; the panel prints no other number. The
    panel title names the registered case; it never says more than the case licenses.

    ``print_values``: the left panel prints the two equivalents of each row beside it (see
    ``_draw_equivalents``); the panel is drawn narrower to make room, and the right panel keeps
    its size. The legend under the panels explains the right panel only: its three line entries
    stand under that panel, and the two marker entries to their left. No word of the figure
    changes.
    """
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    plt = style()
    code, name = marked if marked else (None, None)
    pts = [
        (
            float(r["predicted_change"]),
            float(r["half_difference"]),
            int(r["n_up"]) + int(r["n_down"]),
            code is not None
            and code in (r["league_lower_equivalent"], r["league_higher_equivalent"]),
        )
        for r in pair_rows
    ]
    if len(pts) != 45:
        raise FigureClaimError(f"the league-pair panel needs 45 pairs, got {len(pts)}")
    if any(g < 0 for g, _, _, _ in pts):
        raise FigureClaimError(
            "each pair is drawn from the lower to the higher equivalent: g must not be negative"
        )
    if code is not None and sum(1 for *_, hit in pts if hit) != 9:
        raise FigureClaimError(
            f"nine of the 45 league pairs include one league; {code} is in "
            f"{sum(1 for *_, hit in pts if hit)}"
        )
    case, slope = e30["case"], float(e30["slope"])
    low, high = float(e30["ci_low"]), float(e30["ci_high"])
    positive = case in E30_POSITIVE_CASES
    if positive and not low > 0:
        raise FigureClaimError("a positive case needs an interval above zero")
    if case == "null" and not low <= 0 <= high:
        raise FigureClaimError("a null case needs an interval that includes zero")
    if case == "against" and not high < 0:
        raise FigureClaimError("the 'against' case needs an interval below zero")
    fig, (a1, a2) = plt.subplots(
        1,
        2,
        figsize=(6.5, 4.15),
        gridspec_kw={"wspace": 0.3, "width_ratios": [1, 1.05]},
    )
    _draw_equivalents(
        plt,
        a1,
        rows,
        counts,
        xmax=20.9 if print_values else 21.3,
        print_values=print_values,
    )
    a1.set_xlabel("Domestic EFF/36 with the same\nforecast as 16 in Spain's ACB")
    a1.set_title(
        "The table: equivalents when\ncareer history equals domestic rate", pad=16
    )
    top = max(g for g, *_ in pts) * 1.06
    biggest = max(n for _, _, n, _ in pts)
    a2.fill_between(
        [0, top],
        [0, low * top],
        [0, high * top],
        color=FOCAL,
        alpha=0.18,
        lw=0,
        zorder=1,
    )
    a2.plot([0, top], [0, top], color=GREY, lw=0.7, ls="--", zorder=1)
    a2.axhline(0, color=GREY, lw=0.6, zorder=1)
    a2.plot([0, top], [0, slope * top], color=FOCAL, lw=1.3, zorder=2)
    for hit, color in ((False, COMP), (True, MARKED_COLOR)):
        sel = [q for q in pts if q[3] is hit]
        a2.scatter(
            [g for g, *_ in sel],
            [e for _, e, _, _ in sel],
            s=[5 + 30 * n / biggest for _, _, n, _ in sel],
            marker="D" if hit else "o",
            facecolor=color,
            edgecolor="white",
            linewidth=0.3,
            alpha=0.92,
            zorder=4 if hit else 3,
        )
    a2.set_xlim(-0.08, top)
    a2.margins(y=0.08)
    counts_text = f"{int(e30['n_moves']):,} league changes"
    if e30.get("n_players") is not None:
        counts_text += f"\n{int(e30['n_players']):,} players"
    if notes is not None:
        if code is None:
            raise FigureClaimError(
                "the slope without a league is printed beside the group it marks"
            )
        counts_text += f"\n{float(notes['refit']):.2f} with the table refitted\non earlier arrivals"
    stats = f"slope {slope:.2f}\n95% interval {low:.2f} to {high:.2f}\n{counts_text}"
    # room for the printed values under the points on the right of the panel, so that no
    # point, line or band runs through them
    share = 0.06 + 0.065 * (stats.count("\n") + 1)
    y_low, y_high = a2.get_ylim()
    beside = [e for g, e, _, _ in pts if g > 0.3 * top]
    if beside:
        y_low = min(y_low, (min(beside) - 0.12 - share * y_high) / (1 - share))
    a2.set_ylim(y_low, y_high)
    a2.text(
        0.985,
        0.03,
        stats,
        transform=a2.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        linespacing=1.25,
    )
    a2.set_xlabel("Change predicted by EuroCup\nequivalents (EFF/36)")
    a2.set_ylabel("Observed change beyond\na stayer's forecast (EFF/36)")
    a2.set_title(e30_panel_title(case, slope, low, high), pad=8)
    handles = [
        Line2D([], [], color=FOCAL, lw=1.3),
        Patch(facecolor=FOCAL, alpha=0.18, lw=0),
        Line2D([], [], color=GREY, lw=0.7, ls="--"),
    ]
    band = "its 95% interval"
    if notes is not None and notes.get("redrawn") is not None:
        # Amendment 21, rule 2: the interval with the table values redrawn, as text and named
        # as such; it is not drawn
        wide_low, wide_high = (float(v) for v in notes["redrawn"])
        band += (
            f"\n({wide_low:.2f} to {wide_high:.2f} with the table"
            "\nvalues redrawn; not drawn)"
        )
    labels = [
        "registered slope, through the origin\n(not a fit to these points)",
        band,
        "slope 1: the table's size",
    ]
    dot = {"ls": "", "ms": 4.5, "mec": "white", "mew": 0.3}
    # the marker entries first, so that they fill the left column and the three line entries
    # stand in the right column, under the panel that draws those lines (the left panel has a
    # dashed line of its own, the reference at 16, which the entry "slope 1" does not explain)
    marker_handles, marker_labels = [], []
    if code is not None:
        marker_handles.append(Line2D([], [], marker="D", mfc=MARKED_COLOR, **dot))
        marker_labels.append(
            f"pairs with {name}"
            + (
                f" (slope without {name}: {float(notes['lowest']):.2f})"
                if notes
                else ""
            )
        )
        marker_handles.append(Line2D([], [], marker="o", mfc=COMP, **dot))
        marker_labels.append("other pairs (marker area: moves)")
    else:
        marker_handles.append(Line2D([], [], marker="o", mfc=COMP, **dot))
        marker_labels.append("league pairs (marker area: moves)")
    # (the band that stood empty between the axis titles and the legend is used: the panels are
    # about a tenth taller than before, at the same figure size)
    fig.subplots_adjust(left=0.268, right=0.985, bottom=0.335, top=0.839)
    # two legends side by side, each in one column (three columns at this size are wider than
    # the figure and were cut off at both edges of the image, 24 November 2026); the words of
    # the entries are unchanged
    look = {
        "ncol": 1,
        "fontsize": 7.5,
        "handlelength": 1.15,
        "handletextpad": 0.5,
        "labelspacing": 0.35,
        "borderaxespad": 0.0,
        "borderpad": 0.0,
    }
    left_edge = a2.get_position().x0
    fig.legend(
        handles,
        labels,
        loc="upper left",
        bbox_to_anchor=(left_edge - 0.012, 0.192),
        **look,
    )
    fig.legend(
        marker_handles,
        marker_labels,
        loc="upper right",
        bbox_to_anchor=(left_edge - 0.045, 0.192),
        **look,
    )
    if print_values:
        # the left panel gives up width for its printed values; the right panel keeps its place
        box = a1.get_position()
        column = 49.0 / 72 / fig.get_figwidth()  # the printed values, in figure widths
        left = 0.25
        a1.set_position([left, box.y0, box.x1 - column - left, box.height])
    return _save(fig, out / "fig1_equivalents.png")


# --------------------------------------------------------------------- figure 2
def fig_avoidable(reducible_rows, flex_reducible, out: Path) -> Path:
    """Ladder scaled by estimated reducible error under the normal-noise reference."""
    plt = style()
    share = {r["arm"]: 100 * r["share_of_reducible_removed"] for r in reducible_rows}
    models = flex_reducible["models"]
    ci = {
        k: [100 * x for x in v["ci95_percentile"]]
        for k, v in models.items()
        if "ci95_percentile" in v
    }
    for arm in ("scheduled_history", "source_ridge_10", "source_ridge_10_scheduled"):
        if abs(share[arm] - 100 * models[arm]["share_of_reducible_removed"]) > 1e-6:
            raise FigureClaimError(
                f"E17 and E16 disagree on the avoidable share of {arm}"
            )
    for arm in ("gbm", "gbm_z", "ridge", "ridge_z"):
        share[arm] = 100 * models[arm]["share_of_reducible_removed"]
    steps = [
        ("History only", "history_only", "scheduled_history"),
        (
            "+ destination",
            "history_destination_slope",
            "history_destination_slope_scheduled",
        ),
        ("+ one number per league", "source_ridge_10", "source_ridge_10_scheduled"),
        ("+ pair-specific slopes", "cell_slope_10", "cell_slope_10_scheduled"),
        ("Ridge, 30 features", "ridge", "ridge_z"),
        ("Boosted trees, 30 features", "gbm", "gbm_z"),
    ]
    best = max(share[a] for _, w, z in steps for a in (w, z))
    if share["source_ridge_10"] != best:
        raise FigureClaimError(
            "a plotted forecast removes more avoidable error than one number per league"
        )
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    value_grid(ax)
    for i, (label, w, z) in enumerate(steps):
        for arm, color, dy in ((w, COMP, -0.14), (z, FOCAL, 0.14)):
            if arm in ci:
                ax.plot(ci[arm], [i + dy] * 2, color=color, lw=1.2, alpha=0.9, zorder=2)
            ax.plot(
                [share[arm]],
                [i + dy],
                "o",
                color=color,
                ms=5.5,
                mec="white",
                mew=0.5,
                zorder=3,
            )
    ax.axvline(0, color=GREY, lw=0.8, zorder=1)
    ax.axvspan(best, 34, color=LIGHT, lw=0, zorder=0)
    ax.text(
        33.6,
        3.0,
        f"{100 - best:.0f}% remains under this\nnoise reference and these models →",
        ha="right",
        va="center",
        fontsize=7.5,
        color=GREY,
    )
    ax.set_yticks(range(len(steps)), [s[0] for s in steps])
    ax.set_ylim(len(steps) - 0.45, -0.6)
    ax.set_xlim(-8, 34)
    ax.set_xticks([0, 5, 10, 15, 20, 25, 30])
    ax.set_xlabel("Estimated reducible-error share removed (%), relative to history")
    ax.plot([], [], "o", color=COMP, ms=5.5, label="without translation")
    ax.plot([], [], "o", color=FOCAL, ms=5.5, label="with translation")
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.0),
        ncol=2,
        handletextpad=0.3,
        borderaxespad=0.2,
    )
    ax.set_title(
        "Model comparison under the normal-noise reference",
        pad=17,
    )
    fig.subplots_adjust(left=0.24, right=0.98, bottom=0.17, top=0.84)
    return _save(fig, out / "fig2_avoidable.png")


# --------------------------------------------------------------------- figure 3
def fig_decisions(pair_rows, out: Path) -> Path:
    """pair_rows: e10_pair_types.csv dicts (scope all_pools)."""
    plt = style()

    def get(pt, q, models):
        r = next(
            r
            for r in pair_rows
            if r["scope"] == "all_pools"
            and r["pair_type"] == pt
            and r["quantity"] == q
            and r["models"] == models
        )
        return (
            float(r["point"]),
            float(r["ci95_low"]),
            float(r["ci95_high"]),
            int(r["pairs"]),
        )

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.5, 3.5), gridspec_kw={"hspace": 1.0})
    value_grid(a1)
    value_grid(a2)
    rows = [
        ("League-aware", "history_only__source_ridge_10", FOCAL),
        ("History + translation", "history_only__scheduled_history", COMP),
    ]
    labels, y = [], 0
    for pt, name in (("cross", "cross-league"), ("same", "same-league")):
        for label, key, color in rows:
            p, lo, hi, n = get(pt, "d1diff", key)
            a1.plot([100 * lo, 100 * hi], [y, y], color=color, lw=1.5, zorder=2)
            a1.plot(
                [100 * p], [y], "o", color=color, ms=6, mec="white", mew=0.5, zorder=3
            )
            a1.text(
                100 * hi + 0.05,
                y,
                minus(f"{100 * p:+.2f}"),
                ha="left",
                va="center",
                fontsize=7.5,
                color=FOCAL if color == FOCAL else GREY,
            )
            labels.append(f"{label}, {name}")
            y += 1
        y += 0.4
    a1.axvline(0, color=GREY, lw=0.8, zorder=1)
    a1.set_yticks([0, 1, 2.4, 3.4], labels)
    a1.set_ylim(3.9, -0.6)
    a1.set_xlim(right=a1.get_xlim()[1] + 0.22)
    a1.set_xlabel(
        "Change in pairs ordered correctly, vs history only (percentage points)"
    )
    a1.set_title(
        "Knowing the leagues helps rank candidates from different leagues", loc="left"
    )
    rows2 = [
        ("Added to history only", "history_only__scheduled_history", COMP),
        ("Added to league-aware", "source_ridge_10__source_ridge_10_scheduled", FOCAL),
    ]
    labels2, y = [], 0
    for pt, name in (("all", "all pairs"), ("cross", "cross-league")):
        for label, key, color in rows2:
            p, lo, hi, n = get(pt, "right_share", key)
            if label.startswith("Added to league-aware") and not lo <= 0.5 <= hi:
                raise FigureClaimError(
                    "translation's changes on the league-aware forecast differ from a coin flip"
                )
            a2.plot([100 * lo, 100 * hi], [y, y], color=color, lw=1.5, zorder=2)
            a2.plot(
                [100 * p], [y], "o", color=color, ms=6, mec="white", mew=0.5, zorder=3
            )
            a2.text(
                100 * hi + 0.4,
                y,
                f"{100 * p:.1f}%",
                ha="left",
                va="center",
                fontsize=7.5,
                color=FOCAL if color == FOCAL else GREY,
            )
            labels2.append(f"{label}, {name}")
            y += 1
        y += 0.4
    a2.axvline(50, ls="--", color=GREY, lw=0.8, zorder=1)
    a2.text(50.5, -0.45, "coin flip", fontsize=7.5, color=GREY, va="center")
    a2.set_yticks([0, 1, 2.4, 3.4], labels2)
    a2.set_ylim(3.9, -0.6)
    a2.set_xlim(43, 67)
    a2.set_xlabel("Changed comparisons that translation gets right (%)")
    a2.set_title(
        "Once the leagues are known, translation's changes are\nnot distinguishable from a coin flip",
        loc="left",
    )
    fig.subplots_adjust(left=0.30, right=0.98, bottom=0.11, top=0.93)
    return _save(fig, out / "fig3_decisions.png")


# --------------------------------------------------------------------- figure 4
def fig_bias(e11_rows, out: Path) -> Path:
    plt = style()
    rows = sorted(e11_rows, key=lambda r: float(r["signed_error_history_only"]))
    licensed = {r["source_league"] for r in rows if r["licence"] == "bias"}
    if licensed != {"spain-acb", "italy-lba"}:
        raise FigureClaimError(f"licensed bias leagues changed: {sorted(licensed)}")
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    for i, r in enumerate(rows):
        for arm, color, dy in (
            ("history_only", COMP, -0.15),
            ("source_ridge_10", FOCAL, 0.15),
        ):
            p = float(r[f"signed_error_{arm}"])
            lo, hi = float(r[f"ci95_low_{arm}"]), float(r[f"ci95_high_{arm}"])
            ax.plot([lo, hi], [i + dy] * 2, color=color, lw=1.0)
            ax.plot([p], [i + dy], "o", color=color, ms=4.5)
    ax.axvline(0, color=GREY, lw=0.7)
    ax.set_yticks(
        range(len(rows)),
        [
            f"{LEAGUE_NAMES[r['source_league']]}{' *' if r['source_league'] in licensed else ''}  (n = {r['arrivals']})"
            for r in rows
        ],
    )
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlabel(
        "Mean signed error, EFF/36 (forecast − actual; below 0 = league underrated)"
    )
    ax.plot([], [], "o", color=COMP, ms=4.5, label="league-blind (history only)")
    ax.plot(
        [], [], "o", color=FOCAL, ms=4.5, label="league-aware (one number per league)"
    )
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.0),
        ncol=2,
        handletextpad=0.3,
        borderaxespad=0.2,
    )
    ax.set_title(
        "A league-blind forecast underrates arrivals from Spain and Italy", pad=16
    )
    fig.subplots_adjust(left=0.3, right=0.98, bottom=0.15, top=0.85)
    return _save(fig, out / "fig4_bias.png")


def fig_league_bias(e24_rows, out: Path, league_order=None) -> Path:
    """Figure 2: re-based league biases of the destination-aware and league-aware forecasts (E24).
    ``league_order``: the league codes in the order of the Equivalents table and of Figure 1; without
    it the leagues are ordered by the bias of the forecast that is blind to the source league."""
    plt = style()
    blind, aware = "history_destination_slope", "source_ridge_10"
    if league_order is None:
        rows = sorted(e24_rows, key=lambda r: r[f"rebased_{blind}"])
    else:
        if sorted(league_order) != sorted(r["source_league"] for r in e24_rows):
            raise FigureClaimError(
                "the league order does not name the leagues of E24 once each"
            )
        rows = sorted(
            e24_rows, key=lambda r: list(league_order).index(r["source_league"])
        )
    licensed = {r["source_league"] for r in rows if r["licence"] == "licensed"}
    under = {
        r["source_league"]
        for r in rows
        if r["source_league"] in licensed and r[f"rebased_{blind}"] < 0
    }
    if under != {"spain-acb", "italy-lba"} or licensed - under != {"germany-bbl"}:
        raise FigureClaimError(f"licensed bias leagues changed: {sorted(licensed)}")
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    value_grid(ax)
    reach = max(r[f"rebased_ci95_high_{arm}"] for r in rows for arm in (blind, aware))
    column = reach + 0.2
    for i, r in enumerate(rows):
        for arm, color, dy in ((blind, COMP, -0.15), (aware, FOCAL, 0.15)):
            p = r[f"rebased_{arm}"]
            lo, hi = r[f"rebased_ci95_low_{arm}"], r[f"rebased_ci95_high_{arm}"]
            ax.plot([lo, hi], [i + dy] * 2, color=color, lw=1.3, zorder=2)
            ax.plot(
                [p], [i + dy], "o", color=color, ms=5.5, mec="white", mew=0.5, zorder=3
            )
        # the two plotted values, printed: without the league numbers, then with them
        ax.text(
            column + 0.42,
            i,
            minus(f"{r[f'rebased_{blind}']:+.2f}"),
            ha="right",
            va="center",
            fontsize=7.5,
            color=GREY,
        )
        ax.text(
            column + 0.49,
            i,
            "\u2192 " + minus(f"{r[f'rebased_{aware}']:+.2f}"),
            ha="left",
            va="center",
            fontsize=7.5,
            color=FOCAL,
        )
    ax.axvline(0, color=GREY, lw=0.8, zorder=1)
    for x, side, words in (
        (-0.08, "right", "\u2190 forecast too low for the league"),
        (0.08, "left", "too high \u2192"),
    ):
        ax.text(x, -0.78, words, ha=side, va="center", fontsize=7.5, color=GREY)
    ax.set_yticks(
        range(len(rows)),
        [
            f"{LEAGUE_NAMES[r['source_league']]}{' *' if r['source_league'] in licensed else ''}  (n = {r['arrivals']})"
            for r in rows
        ],
    )
    for label, r in zip(ax.get_yticklabels(), rows):
        if r["source_league"] in licensed:
            label.set_fontweight("semibold")
    ax.set_ylim(len(rows) - 0.5, -1.15)
    ax.set_xlim(right=column + 1.12)
    ax.set_xticks([t for t in ax.get_xticks() if t <= reach + 0.3])
    ax.set_xlim(right=column + 1.12)
    ax.set_xlabel(
        "Signed error against the average arrival, EFF/36 (below 0 = league underrated)",
        loc="left",
    )
    handles = [
        ax.plot([], [], "o", color=COMP, ms=5.5)[0],
        ax.plot([], [], "o", color=FOCAL, ms=5.5)[0],
    ]
    fig.legend(
        handles,
        [
            "knows the destination, not the source league",
            "league-aware (one number per league)",
        ],
        loc="upper left",
        bbox_to_anchor=(0.005, 0.935),
        ncol=2,
        handletextpad=0.3,
    )
    headline(
        fig, "A source-blind forecast underrates Spain and Italy and overrates Germany"
    )
    fig.subplots_adjust(left=0.3, right=0.985, bottom=0.15, top=0.85)
    return _save(fig, out / "fig4_bias.png")


# --------------------------------------------------------------------- figure 3
MECHANISM_RUNGS = (
    ("History only\n(blind to both leagues)", "history_only", "scheduled_history"),
    (
        "+ destination",
        "history_destination_slope",
        "history_destination_slope_scheduled",
    ),
    (
        "+ one number per league\n(league-aware)",
        "source_ridge_10",
        "source_ridge_10_scheduled",
    ),
)


def fig_mechanism(recipes, out: Path) -> Path:
    """The ladder of Table 1 as a picture: forecast error without and with translation,
    and translation's gain, as the forecast learns the leagues (recipe R1, pool A)."""
    plt = style()
    base = recipes["results"]["A"]["R1"]
    rows = []
    for label, left, right in MECHANISM_RUNGS:
        c = base["ladder"][f"{left}->{right}"]["player_club_season"]
        rows.append(
            (
                label,
                base["metrics"][left]["mae"],
                base["metrics"][right]["mae"],
                c["difference"],
                c["ci95"],
            )
        )
    blind, aware = rows[0], rows[-1]
    if not blind[4][0] > 0:
        raise FigureClaimError(
            "translation's gain over a league-blind forecast is not above zero"
        )
    if not aware[4][0] < 0 < aware[4][1]:
        raise FigureClaimError(
            "translation's increment on the league-aware forecast excludes zero"
        )
    fig, (a1, a2) = plt.subplots(
        1, 2, figsize=(6.5, 2.5), sharey=True, gridspec_kw={"wspace": 0.08}
    )

    for i, (_, without, with_z, gain, ci) in enumerate(rows):
        a1.plot([without, with_z], [i, i], color=LIGHT, lw=2.2, zorder=1)
        a1.plot([without], [i], "o", color=COMP, ms=6.5, mec="white", mew=0.5, zorder=3)
        a1.plot([with_z], [i], "o", color=FOCAL, ms=6.5, mec="white", mew=0.5, zorder=3)
        a1.text(
            (without + with_z) / 2,
            i - 0.2,
            f"{without:.3f} \u2192 {with_z:.3f}",
            ha="center",
            va="bottom",
            fontsize=7.5,
        )
        a2.plot(ci, [i, i], color=FOCAL, lw=1.6, zorder=2)
        a2.plot([gain], [i], "o", color=FOCAL, ms=6.5, mec="white", mew=0.5, zorder=3)
        a2.text(
            ci[0],
            i - 0.2,
            minus(f"{gain:+.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"),
            ha="left",
            va="bottom",
            fontsize=7.5,
            zorder=4,
            # the zero line must not run through a printed value
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6},
        )
    a1.set_yticks(range(len(rows)), [r[0] for r in rows])
    a1.set_ylim(len(rows) - 0.5, -0.6)
    a1.margins(x=0.2)
    a1.set_xlabel("MAE, EFF/36 (lower is better)")
    panel_name(a1, "Forecast error")
    value_grid(a1)
    value_grid(a2)
    a1.plot([], [], "o", color=COMP, ms=6.5, label="without translation")
    a1.plot([], [], "o", color=FOCAL, ms=6.5, label="with translation")
    a2.axvline(0, color=GREY, lw=0.7, ls="--", zorder=1)
    a2.margins(x=0.16)
    # right-aligned: centred under this panel the label ran 7 pixels past the edge of the image
    a2.set_xlabel("Gain from translation, EFF/36 (above 0 helps)", loc="right")
    panel_name(a2, "What translation adds")
    a2.tick_params(axis="y", length=0)
    a1.legend(
        loc="lower right",
        handletextpad=0.3,
        borderaxespad=0.1,
        fontsize=7.5,
    )
    headline(
        fig,
        "Translation helps a league-blind forecast and adds nothing detectable on top of the league numbers",
    )
    fig.subplots_adjust(left=0.215, right=0.985, bottom=0.2, top=0.82)
    return _save(fig, out / "fig_mechanism.png")


# --------------------------------------------------------------------- figure 5
TIER_COLORS = {1: "#1f5f8b", 2: "#6f9fc4", 3: "#b0563b"}
#: The league names written at the ends of the lines.
LEAGUE_SHORT = {
    "spain-acb": "Spain",
    "france-pro-a": "France",
    "italy-lba": "Italy",
    "greece-a1": "Greece",
    "israel-bsl": "Israel",
    "turkey-bsl": "Turkey",
    "aba-league": "Adriatic",
    "germany-bbl": "Germany",
    "lithuania-lkl": "Lithuania",
    "vtb": "VTB",
}


def fig_stability(refit_rows, exchange_rows, summary, out: Path) -> Path:
    """E19: the Equivalents in each yearly refit, coloured by the tier of the full fit.

    refit_rows: e19_equivalents_by_refit.csv; exchange_rows: exchange_rate_acb16.csv
    (the tiers); summary: the committed E19 summary, whose sentence is the title.
    """
    plt = style()
    tier = {
        r["source_league"]: int(r["e9_tier"])
        for r in exchange_rows
        if r["destination"] == "euroleague"
    }
    seasons = sorted(
        {int(float(r["refit_season"])) for r in refit_rows if r["refit_season"]}
    )
    value = {}
    for r in refit_rows:
        if r["refit_season"]:
            key = (r["destination"], r["source_league"], int(float(r["refit_season"])))
            value[key] = float(r["acb16_equivalent_eff36"])
    for dst in ("euroleague", "eurocup"):
        for s in seasons:
            low = max(value[(dst, k, s)] for k in tier if tier[k] == 1)
            high = min(value[(dst, k, s)] for k in tier if tier[k] == 3)
            if not high > low:
                raise FigureClaimError(
                    f"{dst} refit {s}: a tier-3 league does not need a higher rate than every tier-1 league"
                )
    if summary["tier3_higher"] != summary["comparisons"]:
        raise FigureClaimError("the E19 summary no longer says 'in every yearly refit'")
    fig, axes = plt.subplots(
        1, 2, figsize=(6.5, 3.0), sharey=True, gridspec_kw={"wspace": 0.34}
    )
    leagues = sorted(tier, key=lambda k: (tier[k], k))
    for ax, dst, name in zip(
        axes, ("euroleague", "eurocup"), ("EuroLeague arrivals", "EuroCup arrivals")
    ):
        value_grid(ax, "y")
        for k in leagues:
            ys = [value[(dst, k, s)] for s in seasons]
            ax.plot(
                seasons,
                ys,
                "-o",
                color=TIER_COLORS[tier[k]],
                lw=1.2,
                ms=3,
                alpha=0.95,
                zorder=2 + tier[k],
            )
        # each line is named at its right end; names of lines that end close together are
        # moved apart and keep their order
        ends = [value[(dst, k, seasons[-1])] for k in leagues]
        for k, end, at in zip(leagues, ends, spread(ends, 0.3)):
            ax.annotate(
                LEAGUE_SHORT[k],
                xy=(seasons[-1], end),
                xytext=(seasons[-1] + 0.32, at),
                fontsize=7.5,
                color=TIER_COLORS[tier[k]],
                va="center",
                ha="left",
                annotation_clip=False,
                arrowprops={
                    "arrowstyle": "-",
                    "color": TIER_COLORS[tier[k]],
                    "lw": 0.5,
                    "shrinkA": 0.5,
                    "shrinkB": 2,
                },
            )
        ax.axhline(16, color=GREY, lw=0.7, ls="--", zorder=1)
        panel_name(ax, name)
        ax.set_xticks(seasons, [f"{s}–{str(s + 1)[-2:]}" for s in seasons])
        ax.tick_params(axis="x", labelsize=7)
        ax.set_xlabel("Season the table was refitted for")
        ax.margins(x=0.06)
    axes[0].set_ylabel("Domestic EFF/36 with the same\nforecast as 16 in Spain's ACB")
    axes[1].tick_params(axis="y", length=0)
    handles = [
        axes[0].plot([], [], "-o", color=TIER_COLORS[t], lw=1.2, ms=3)[0]
        for t in (1, 2, 3)
    ]
    fig.legend(
        handles,
        ["Tier 1 leagues", "Tier 2 leagues", "Tier 3 leagues"],
        loc="upper left",
        bbox_to_anchor=(0.005, 0.935),
        ncol=3,
        handletextpad=0.4,
        columnspacing=1.2,
    )
    headline(
        fig,
        "In every yearly refit, every tier-3 league needed a higher rate than every tier-1 league",
    )
    fig.subplots_adjust(left=0.105, right=0.9, bottom=0.16, top=0.77)
    return _save(fig, out / "fig_stability.png")


# --------------------------------------------------------------------- figure 6
def fig_gap_guide(e20, out: Path) -> Path:
    """E20 as a curve: how often the higher forecast was the better player, by forecast gap."""
    plt = style()
    arms = (
        ("history_only", "history only (blind to both leagues)", COMP, -0.07),
        ("source_ridge_10", "league-aware forecast", FOCAL, 0.07),
    )
    series = {}
    for arm, *_ in arms:
        rows = sorted(
            (r for r in e20["bins"] if r["arm"] == arm and r["pair_type"] == "all"),
            key=lambda r: r["bin"],
        )
        shares = [r["share_correct"] for r in rows]
        if shares != sorted(shares):
            raise FigureClaimError(
                f"{arm}: accuracy does not rise with the forecast gap"
            )
        series[arm] = rows
    labels = [
        r["gap_eff36"].replace(" to ", "–").replace(" or more", "+")
        for r in series["source_ridge_10"]
    ]
    trust = e20["licence"]["trust"]
    if not (trust["0.60"]["licensed"] and trust["0.70"]["licensed"]):
        raise FigureClaimError("the forecast-gap thresholds are not licensed")
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    for arm, name, color, dx in arms:
        rows = series[arm]
        xs = [r["bin"] + dx for r in rows]
        for x, r in zip(xs, rows):
            ax.plot(
                [x, x],
                [100 * r["ci95_low"], 100 * r["ci95_high"]],
                color=color,
                lw=1.0,
                zorder=2,
            )
        ax.plot(
            xs,
            [100 * r["share_correct"] for r in rows],
            "-o",
            color=color,
            lw=1.2,
            ms=5.5,
            mec="white",
            mew=0.5,
            label=name,
            zorder=3,
        )
    # the six shares of the league-aware forecast, printed: the numbers a club would use
    for r in series["source_ridge_10"]:
        ax.text(
            r["bin"] + 0.16,
            100 * r["share_correct"] - 2.6,
            # as Table A25 prints them (one decimal): the caption calls them that table's values
            f"{100 * r['share_correct']:.1f}%",
            ha="left",
            va="center",
            fontsize=8,
            fontweight="semibold",
            color=FOCAL,
            zorder=4,
        )
    value_grid(ax, "y")
    ax.axhline(50, color=GREY, lw=0.7, ls="--", zorder=1)
    ax.text(len(labels) - 0.55, 51.2, "coin flip", fontsize=7.5, color=GREY, ha="right")
    labels = [
        f"{label}\n{r['pairs']:,} pairs"
        for label, r in zip(labels, series["source_ridge_10"])
    ]
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlim(-0.45, len(labels) - 0.55)
    ax.set_ylim(45, 100)
    ax.set_yticks([50, 60, 70, 80, 90, 100])
    ax.set_xlabel("Gap between two forecasts (EFF/36)")
    ax.set_ylabel("Pairs in which the higher\nforecast was the better player (%)")
    ax.legend(loc="upper left", handletextpad=0.4)
    ax.set_title("The larger the gap between two forecasts, the more often it is right")
    fig.subplots_adjust(left=0.12, right=0.985, bottom=0.235, top=0.9)
    return _save(fig, out / "fig_gap_guide.png")


# --------------------------------------------------------------------- figure 7
def fig_bands(e22, out: Path) -> Path:
    """E8/E22: share of arrivals inside the 80% error band, by source league and by season."""
    plt = style()
    rows = sorted(
        (r for r in e22["leagues"] if abs(r["level"] - 0.80) < 1e-9),
        key=lambda r: -r["coverage"],
    )
    if e22["licence"]["leagues_off_nominal"] or any(
        not r["wilson95_low"] <= 0.80 <= r["wilson95_high"] for r in rows
    ):
        raise FigureClaimError(
            "a league's 80% band coverage is distinguishable from 80%"
        )
    seasons = sorted(e22["by_season"]["0.80"].items(), key=lambda kv: int(kv[0]))
    pooled = e22["pooled"]["0.80"]
    fig, (a1, a2) = plt.subplots(
        1, 2, figsize=(6.5, 2.9), gridspec_kw={"wspace": 0.1, "width_ratios": [1.1, 1]}
    )
    for i, r in enumerate(rows):
        a1.plot(
            [100 * r["wilson95_low"], 100 * r["wilson95_high"]],
            [i, i],
            color=FOCAL,
            lw=1.3,
            zorder=2,
        )
        a1.plot(
            [100 * r["coverage"]],
            [i],
            "o",
            color=FOCAL,
            ms=5.5,
            mec="white",
            mew=0.5,
            zorder=3,
        )
        a1.text(
            101.5,
            i,
            # as Table A12 prints them (one decimal)
            f"{100 * r['coverage']:.1f}%",
            ha="left",
            va="center",
            fontsize=7.5,
            color=FOCAL,
        )
    value_grid(a1)
    a1.axvline(80, color=GREY, lw=0.8, ls="--", zorder=1)
    a1.set_yticks(
        range(len(rows)),
        [f"{LEAGUE_NAMES[r['source_league']]}  (n = {r['n']})" for r in rows],
    )
    a1.set_ylim(len(rows) - 0.5, -0.6)
    a1.set_xlim(55, 109)
    a1.set_xticks([60, 70, 80, 90, 100])
    a1.set_xlabel("Arrivals inside the 80% band (%)")
    panel_name(a1, "By source league")
    xs = range(len(seasons))
    a2.plot(
        xs,
        [100 * v["coverage"] for _, v in seasons],
        "-o",
        color=FOCAL,
        lw=1.2,
        ms=5.5,
        mec="white",
        mew=0.5,
        zorder=3,
    )
    shares = [100 * v["coverage"] for _, v in seasons]
    for x, share in zip(xs, shares):
        # a value is printed under its point where the line arrives from above
        near = [shares[j] for j in (x - 1, x + 1) if 0 <= j < len(shares)]
        under = all(share < other for other in near)
        at = share + (-2.6 if under else 2.6)
        # a value whose place under its point lies on a grid line (every 10%) is printed left of
        # the point, clear of the line and of the axis label beside it
        beside = under and (at % 10) < 3.0
        a2.text(
            x - 0.16 if beside else x,
            share - 0.2 if beside else at,
            # as the text prints the seasons' range (one decimal)
            f"{share:.1f}%",
            ha="right" if beside else "center",
            va="center" if beside else ("top" if under else "bottom"),
            fontsize=7.5,
            color=FOCAL,
        )
    value_grid(a2, "y")
    a2.axhline(80, color=GREY, lw=0.8, ls="--", zorder=1)
    a2.set_xticks(
        xs, [f"{int(s)}–{str(int(s) + 1)[-2:]}\nn = {v['n']}" for s, v in seasons]
    )
    a2.set_ylim(55, 100)
    a2.set_xlim(-0.4, len(seasons) - 0.6)
    a2.yaxis.tick_right()
    a2.spines["right"].set_visible(True)
    a2.spines["left"].set_visible(False)
    a2.set_xlabel("Destination season")
    a2.tick_params(axis="x", labelsize=7)
    panel_name(a2, "By season")
    headline(
        fig,
        f"No league's 80% band coverage is distinguishable from 80% (all arrivals: {100 * pooled['coverage']:.1f}%, n = {pooled['n']})",
    )
    fig.subplots_adjust(left=0.265, right=0.94, bottom=0.2, top=0.84)
    return _save(fig, out / "fig_bands.png")


# --------------------------------------------------------------------- figure 8
def fig_skills(retention_rows, out: Path) -> Path:
    """E15a: what the same player keeps of each box-score line in continental play,
    under the two registered ways of averaging (mean of ratios; ratio of sums)."""
    plt = style()
    rows = [r for r in retention_rows if r["subset_type"] == "pooled"]
    by = {r["component"]: r for r in rows}
    tov, pts = by["tov"], by["pts"]
    if not (
        float(tov["ci_low"]) > float(pts["ci_high"])
        and float(tov["ratio_of_sums_ci_low"]) > float(pts["ratio_of_sums_ci_high"])
    ):
        raise FigureClaimError(
            "'keeps more of his turnovers than his points' does not hold under both estimators"
        )
    rows = sorted(rows, key=lambda r: -float(r["retention"]))
    fig, ax = plt.subplots(figsize=(6.5, 3.1))
    value_grid(ax)
    for i, r in enumerate(rows):
        # the two rows that the title names are drawn in full colour, the others lighter
        named = r["component"] in ("tov", "pts")
        color = FOCAL if named else SOFT
        for cols, filled, dy in (
            (("retention", "ci_low", "ci_high"), True, -0.16),
            (
                ("ratio_of_sums", "ratio_of_sums_ci_low", "ratio_of_sums_ci_high"),
                False,
                0.16,
            ),
        ):
            v, lo, hi = (float(r[c]) for c in cols)
            ax.plot([lo, hi], [i + dy] * 2, color=color, lw=1.3, zorder=2)
            ax.plot(
                [v],
                [i + dy],
                "o",
                ms=5,
                mfc=color if filled else "white",
                mec=color,
                mew=1.0,
                zorder=3,
            )
    ax.axvline(1.0, color=GREY, lw=0.8, ls="--", zorder=1)
    ax.set_yticks(
        range(len(rows)),
        [r["label"][0].upper() + r["label"][1:] for r in rows],
    )
    for label, r in zip(ax.get_yticklabels(), rows):
        if r["component"] in ("tov", "pts"):
            label.set_fontweight("semibold")
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.margins(x=0.06)
    ax.set_xlabel(
        "Continental rate as a share of the domestic rate, same player and season (1 = unchanged)"
    )
    ax.plot([], [], "o", mfc=FOCAL, mec=FOCAL, ms=5, label="average of player ratios")
    ax.plot([], [], "o", mfc="white", mec=FOCAL, ms=5, label="ratio of sums")
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.0),
        ncol=2,
        handletextpad=0.3,
        columnspacing=1.2,
        borderaxespad=0.2,
    )
    ax.set_title(
        "The same player keeps more of his turnovers than his points, under both estimators",
        pad=16,
    )
    fig.subplots_adjust(left=0.2, right=0.985, bottom=0.15, top=0.86)
    return _save(fig, out / "fig_skills.png")


# --------------------------------------------------------------------- figure A1
def _get(data, path):
    node = data
    for part in path.split("/"):
        node = node[part]
    return node


def fig_robustness(r, rb, recipe_names, outcome_names, out: Path) -> Path:
    """The first draft's Figure 2: translation's increment over the league-aware forecast."""
    plt = style()
    items = []
    for k in _get(r, "recipes"):
        c = _get(
            r,
            f"results/A/{k}/ladder/source_ridge_10->source_ridge_10_scheduled/player_club_season",
        )
        parent = _get(r, f"results/A/{k}/metrics/source_ridge_10/mae")
        items.append(
            (
                "Factor recipe (EFF/36)",
                recipe_names[k],
                c["difference"] / parent,
                c["ci95"][0] / parent,
                c["ci95"][1] / parent,
            )
        )
    for o in ("O2", "O3", "O4"):
        c = _get(rb, f"e3/{o}/contrasts/offsets10_increment")
        p = c["mae_left"]
        ci = c["player_club_season"]["ci95"]
        items.append(
            (
                "Other outcomes",
                outcome_names[o],
                c["difference"] / p,
                ci[0] / p,
                ci[1] / p,
            )
        )
    for dst, name in (("euroleague", "EuroLeague only"), ("eurocup", "EuroCup only")):
        c = _get(rb, f"e4/anchor/{dst}/contrasts/offsets10_increment")
        p = c["mae_left"]
        ci = c["player_club_season"]["ci95"]
        items.append(
            (
                "Other samples and models",
                name,
                c["difference"] / p,
                ci[0] / p,
                ci[1] / p,
            )
        )
    for path, name in (
        ("e5/extended", "Seven seasons (2019–2025)"),
        ("e5b/with_age", "Age-aware forecasts"),
    ):
        c = _get(rb, f"{path}/contrasts/offsets10_increment")
        p = c["mae_left"]
        ci = c["player_club_season"]["ci95"]
        items.append(
            (
                "Other samples and models",
                name,
                c["difference"] / p,
                ci[0] / p,
                ci[1] / p,
            )
        )
    if max(100 * it[4] for it in items) >= 2:
        raise FigureClaimError(
            "Figure A1 title would be false: an upper bound reaches 2%"
        )
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    y, ticks, labels, last = 0, [], [], None
    for group, label, est, lo, hi in items:
        if group != last:
            y += 0.4 if last is not None else 0
            ax.text(
                -1.93,
                y,
                group,
                fontsize=8,
                fontweight="semibold",
                va="center",
                ha="left",
            )
            y += 0.9
        ax.plot([100 * lo, 100 * hi], [y, y], color=FOCAL, lw=1.5, zorder=2)
        ax.plot(
            [100 * est], [y], "o", color=FOCAL, ms=5.5, mec="white", mew=0.5, zorder=3
        )
        shown = f"{100 * est:+.2f}"
        ax.text(
            2.95,
            y,
            minus("0.00%" if float(shown) == 0 else shown + "%"),
            ha="right",
            va="center",
            fontsize=7.5,
            color=FOCAL,
        )
        ticks.append(y)
        labels.append(label)
        last = group
        y += 1
    # the margin: a pale band with its two edges drawn, so that it reads as a range
    ax.axvspan(-2, 2, color=LIGHT, alpha=0.75, lw=0, zorder=0)
    for edge in (-2, 2):
        ax.axvline(edge, color=GREY, lw=0.7, ls=(0, (3, 3)), zorder=1)
    ax.axvline(0, color=GREY, lw=0.8, zorder=1)
    ax.set_yticks(ticks, labels)
    ax.set_xlim(-2.5, 3.05)
    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_ylim(y + 0.4, -0.6)
    ax.set_xlabel("What translation adds, % of the league-aware forecast's error")
    ax.text(
        1.93,
        0.01,
        "translation helps →",
        ha="right",
        va="bottom",
        fontsize=7.5,
        color=GREY,
        transform=ax.get_xaxis_transform(),
    )
    ax.text(
        -1.93,
        0.01,
        "← translation hurts",
        ha="left",
        va="bottom",
        fontsize=7.5,
        color=GREY,
        transform=ax.get_xaxis_transform(),
    )
    ax.set_title("No check in this panel shows translation adding 2% or more")
    fig.subplots_adjust(left=0.42, right=0.98, bottom=0.12, top=0.93)
    return _save(fig, out / "figA1_robustness.png")


# --------------------------------------------------------------------- frozen test
def fig_frozen_test(
    rows, blocks, n, out: Path, name: str = "fig_frozen_test.png"
) -> Path:
    """Every registered paired contrast of the frozen 2026-27 test (Amendment 25, rule 1).

    ``rows`` come from the renderer (``p1_figure_rows``) in their registered order, each with its
    estimate, interval, detectable difference, earlier estimate, and the text and reading printed
    beside it. Nothing is computed, selected, dropped or reordered here, and the figure carries no
    title that states a finding: it is drawn in the same form whatever the test shows.
    """
    plt = style()
    from matplotlib.lines import Line2D

    if not rows:
        raise FigureClaimError("the frozen test has no contrast to draw")
    order = [r["block"] for r in rows]
    if order != sorted(order, key=list(blocks).index):
        raise FigureClaimError(
            "the rows of the frozen test are not in their registered blocks"
        )
    # one linear axis for every row: positions run downwards, with a header line above each block
    y, positions, headers, last = 0.0, [], [], None
    for row in rows:
        if row["block"] != last:
            y += 0.3 if last is not None else 0.0
            headers.append((y, blocks[row["block"]]))
            y += 0.75
            last = row["block"]
        positions.append(y)
        y += 1.0
    fig, ax = plt.subplots(figsize=(6.5, 0.38 * y + 1.15))
    ax.axvline(0, color=GREY, lw=0.7, zorder=1)
    for pos, row in zip(positions, rows):
        d = row["detectable"]
        ax.plot(
            [-d, d], [pos, pos], color=LIGHT, lw=6.5, solid_capstyle="butt", zorder=1.5
        )
        ax.plot(row["ci95"], [pos - 0.13, pos - 0.13], color=FOCAL, lw=1.4, zorder=3)
        ax.plot([row["difference"]], [pos - 0.13], "o", color=FOCAL, ms=4.5, zorder=4)
        earlier = row["earlier"]
        if earlier is not None:
            ax.plot(
                earlier["ci95"], [pos + 0.2, pos + 0.2], color=COMP, lw=0.9, zorder=2
            )
            ax.plot(
                [earlier["difference"]],
                [pos + 0.2],
                "D",
                mfc="white",
                mec=COMP,
                mew=0.9,
                ms=3.4,
                zorder=2.5,
            )
        ax.text(
            1.015,
            pos,
            f"{row['text']}\n{row['reading']}",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=6.5,
            linespacing=1.15,
        )
    from matplotlib.transforms import blended_transform_factory

    left_edge = blended_transform_factory(fig.transFigure, ax.transData)
    for pos, label in headers:
        ax.text(
            0.012,
            pos,
            label,
            transform=left_edge,
            ha="left",
            va="center",
            fontsize=7,
            fontweight="bold",
            zorder=5,
            # the zero line must not run through a header
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2},
        )
    ax.set_yticks(positions, [r["label"] for r in rows])
    ax.tick_params(axis="y", length=0, labelsize=6.5)
    ax.set_ylim(y - 0.45, -0.55)
    ax.spines["left"].set_visible(False)
    low = min(min(r["ci95"][0], -r["detectable"]) for r in rows)
    high = max(max(r["ci95"][1], r["detectable"]) for r in rows)
    for r in rows:
        if r["earlier"] is not None:
            low, high = (
                min(low, r["earlier"]["ci95"][0]),
                max(high, r["earlier"]["ci95"][1]),
            )
    pad = 0.05 * (high - low)
    ax.set_xlim(low - pad, high + pad)
    ax.set_xlabel(
        "Paired difference in mean absolute error, EFF/36\n(right of zero: the first-named forecast was the more accurate)"
    )
    handles = [
        Line2D(
            [],
            [],
            color=FOCAL,
            marker="o",
            ms=4.5,
            lw=1.4,
            label=f"2026\u201327 newcomers (n = {n:,}), 95% interval",
        ),
        Line2D(
            [],
            [],
            color=COMP,
            marker="D",
            mfc="white",
            mew=0.9,
            ms=3.4,
            lw=0.9,
            label="same contrast, arrivals of 2020\u20132025 (exploratory)",
        ),
        Line2D(
            [],
            [],
            color=LIGHT,
            lw=6.5,
            label="differences too small to detect at this n (80% power)",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.012, 0.995),
        ncol=1,
        labelspacing=0.25,
        fontsize=6.5,
        handletextpad=0.8,
        handlelength=2.2,
        columnspacing=1.4,
        borderaxespad=0.0,
    )
    top = 1 - 0.62 / fig.get_figheight()
    bottom = 0.62 / fig.get_figheight()
    fig.subplots_adjust(left=0.365, right=0.775, bottom=bottom, top=top)
    return _save(fig, out / name)
