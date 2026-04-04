"""
SchedulerService
================
Bridges the pure-functional algorithm core with the async bot layer.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.core.algorithm import FullSchedule, generate_schedule
from src.core.constraints import GenerateParams

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="recruiter")
_MAX_MSG_CHARS = 4_000
_COL_WIDTH = 6
_LABEL_WIDTH = 3


class SchedulerService:
    async def generate_async(self, params: GenerateParams) -> FullSchedule:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, generate_schedule, params)

    def format_schedule(
        self, schedule: FullSchedule, params: GenerateParams
    ) -> list[str]:
        """
        Render the full multi-session schedule as plain-text message chunks.
        """
        n, k, m = params.n_students, params.n_partners, params.n_rounds
        s_count = params.n_sessions
        sizes = params.session_sizes

        intro = (
            f"Розклад швидкого рекрутингу\n"
            f"Студенти: {n}  Партнери: {k}  Раунди: {m}  Сесії: {s_count}\n"
        )

        all_lines: list[str] = [intro]

        # Global student counter so student numbers are continuous across sessions
        student_offset = 0

        for sess_idx, session in enumerate(schedule):
            n_in_sess = sizes[sess_idx]
            sep = "─" * 38
            header = (
                f"{sep}\n"
                f"СЕСІЯ {sess_idx + 1}  ({n_in_sess} студентів)\n"
                f"{sep}\n"
                + " " * _LABEL_WIDTH
                + "".join(f"{('Р' + str(r+1)):>{_COL_WIDTH}}" for r in range(m))
            )
            all_lines.append(header)

            for i, partners in enumerate(session):
                student_num = student_offset + i + 1
                cells = "".join(f"{p:>{_COL_WIDTH}}" for p in partners)
                all_lines.append(f"{('С' + str(student_num)):<{_LABEL_WIDTH}}{cells}")

            student_offset += n_in_sess

        return _split_chunks(all_lines, _MAX_MSG_CHARS)


def _split_chunks(lines: list[str], limit: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        need = len(line) + 1
        if current and current_len + need > limit:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += need

    if current:
        chunks.append("\n".join(current))

    return chunks
