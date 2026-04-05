"""
VisualizerService
=================
Renders the schedule as a PNG image using Matplotlib.

For single-session results: one table (students × rounds).
For multi-session results: sessions stacked vertically, separated by a
coloured divider row, with continuous student numbering.
"""

from __future__ import annotations

import asyncio
import io
from concurrent.futures import ThreadPoolExecutor

import matplotlib
from matplotlib.transforms import Bbox

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from src.core.algorithm import FullSchedule
from src.core.constraints import GenerateParams

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="visualizer")

_PALETTE = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#bab0ac",
    "#aecbfa",
    "#fdd663",
    "#a8d5a2",
    "#f4a896",
    "#d4a5d5",
    "#80cbc4",
    "#ffcc80",
    "#ef9a9a",
    "#b0bec5",
    "#ffe082",
]

# Colour for session-divider rows in multi-session image
_DIVIDER_COLOR = (0.11, 0.21, 0.34, 1.0)  # same dark blue as header (#1c3557)
_DIVIDER_TEXT_COLOR = "white"


class VisualizerService:

    async def generate_image_async(
        self, schedule: FullSchedule, params: GenerateParams
    ) -> bytes:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._render, schedule, params)

    def _render(self, schedule: FullSchedule, params: GenerateParams) -> bytes:
        k, m = params.n_partners, params.n_rounds
        sizes = params.session_sizes

        partner_color: dict[int, str] = {
            p: _PALETTE[(p - 1) % len(_PALETTE)] for p in range(1, k + 1)
        }

        # --- Build flat table rows ---
        # Each element: (row_label, [cell_text, ...], [cell_color, ...], is_divider)
        rows: list[
            tuple[str, list[str], list[tuple[float, float, float, float]], bool]
        ] = []

        show_text: bool | None = None  # determined after sizing

        student_offset = 0
        for sess_idx, session in enumerate(schedule):
            n_in_sess = sizes[sess_idx]

            # Divider row between sessions (not before the first)
            if sess_idx > 0:
                rows.append(
                    (
                        f"Сесія {sess_idx + 1}",
                        [""] * m,
                        [_DIVIDER_COLOR] * m,
                        True,
                    )
                )

            # First session also gets a header divider
            if sess_idx == 0:
                rows.insert(
                    0,
                    (
                        "Сесія 1",
                        [""] * m,
                        [_DIVIDER_COLOR] * m,
                        True,
                    ),
                )

            for i, partners in enumerate(session):
                label = f"{student_offset + i + 1}"
                rows.append(
                    (
                        label,
                        [str(p) for p in partners],
                        [_hex_to_rgba(partner_color[p], 0.82) for p in partners],
                        False,
                    )
                )

            student_offset += n_in_sess

        total_rows = len(rows)  # includes divider rows

        # --- Dynamic sizing ---
        dpi = 120
        cell_w_in = max(0.30, min(0.65, 9.0 / max(m, 1)))
        cell_h_in = max(0.22, min(0.50, 9.0 / max(total_rows, 1)))

        label_col_w = 0.50
        label_row_h = 0.35
        legend_w = 1.5 if k <= 20 else 0.0
        pad = 0.15  # minimal padding

        fig_w = label_col_w + m * cell_w_in + legend_w + pad * 2
        # Height: just header row + data rows, no title space
        fig_h = label_row_h + total_rows * cell_h_in + pad * 2

        max_px = 2800
        scale = min(1.0, max_px / (fig_w * dpi))
        fig_w *= scale
        fig_h *= scale
        cell_w_in *= scale
        cell_h_in *= scale

        cell_px = min(cell_w_in * dpi, cell_h_in * dpi)
        font_size = max(5, min(11, int(cell_px * 0.42)))
        show_text = (cell_w_in * dpi > 18) and (cell_h_in * dpi > 13)

        # Fill in actual cell text now that we know show_text
        cell_text_all = []
        cell_color_all = []
        row_labels_all = []

        for label, texts, colors, is_div in rows:
            row_labels_all.append(label)
            cell_text_all.append(texts if (show_text and not is_div) else [""] * m)
            cell_color_all.append(colors)

        col_labels = [f"Раунд {r}" for r in range(1, m + 1)]

        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
        fig.patch.set_facecolor("#f0f2f5")
        ax.set_facecolor("#f0f2f5")
        ax.axis("off")

        # Fill the axes completely — table will be scaled to fit
        bbox = Bbox.from_bounds(0, 0, 1, 1)
        ax.set_position(bbox)
        tbl = ax.table(
            cellText=cell_text_all,
            rowLabels=row_labels_all,
            colLabels=col_labels,
            cellColours=cell_color_all,
            cellLoc="center",
            loc="center",
            bbox=bbox,  # fill entire axes area
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(font_size)

        # Style cells
        divider_row_indices = {
            i + 1  # +1 because matplotlib table row 0 = col headers
            for i, (_, _, _, is_div) in enumerate(rows)
            if is_div
        }

        for (row, col), cell in tbl.get_celld().items():
            cell.set_linewidth(0.35)
            cell.set_edgecolor("#9aa0a6")

            cell.get_text().set_horizontalalignment("center")
            cell.get_text().set_x(0.5)

            if row == 0 or col == -1:
                # Column header or row label
                cell.set_facecolor("#1c3557")
                cell.get_text().set_color("white")
                cell.get_text().set_fontweight("bold")
                cell.get_text().set_fontsize(font_size)

            if row in divider_row_indices:
                cell.set_facecolor(_DIVIDER_COLOR)
                cell.get_text().set_color(_DIVIDER_TEXT_COLOR)
                cell.get_text().set_fontweight("bold")
                cell.get_text().set_fontsize(font_size)
                cell.set_edgecolor("#ffffff")

        buf = io.BytesIO()
        plt.savefig(
            buf,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.05,
            facecolor=fig.get_facecolor(),
        )
        plt.close(fig)
        buf.seek(0)
        return buf.read()


def _hex_to_rgba(
    hex_color: str, alpha: float = 1.0
) -> tuple[float, float, float, float]:
    r, g, b = mcolors.to_rgb(hex_color)
    return (r, g, b, alpha)
