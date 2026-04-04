"""
Input validation and hard system limits.

Sessions are computed automatically: S = ceil(N / K).
Each session has at most K students, so the per-session algorithm
always satisfies the n_in_session ≤ K requirement internally.

  Max edges in flow graph  ≈ K*K   ≤  200*200  = 40 000
  Max flow value           ≈ K*M   ≤  200*50   = 10 000
  Max edges to colour      ≈ K*M   ≤  10 000
"""

import math
from dataclasses import dataclass

MAX_STUDENTS: int = 1000  # N  (raised: sessions remove the N≤K ceiling)
MAX_PARTNERS: int = 200  # K
MAX_ROUNDS: int = 50  # M
MIN_VALUE: int = 1


@dataclass(frozen=True)
class GenerateParams:
    n_students: int  # N  — total students across all sessions
    n_partners: int  # K  — partners (tables) in the room
    n_rounds: int  # M  — rounds per session

    @property
    def n_sessions(self) -> int:
        """Number of sessions required: ceil(N / K)."""
        return math.ceil(self.n_students / self.n_partners)

    @property
    def session_sizes(self) -> list[int]:
        """
        Number of students in each session.
        All sessions have K students except possibly the last one.
        """
        k, s = self.n_partners, self.n_sessions
        sizes = [k] * (s - 1)
        sizes.append(self.n_students - k * (s - 1))
        return sizes


class ValidationError(ValueError):
    """Raised when user-supplied arguments fail validation."""


def parse_and_validate(n_raw: str, k_raw: str, m_raw: str) -> GenerateParams:
    """
    Parse string arguments and return a validated :class:`GenerateParams`.

    Raises :class:`ValidationError` with a user-friendly message on failure.
    """
    try:
        n = int(n_raw)
        k = int(k_raw)
        m = int(m_raw)
    except ValueError:
        raise ValidationError(
            "N, K та M повинні бути цілими числами (наприклад: /generate 10 15 3)."
        )

    _check_range("N (студенти)", n, MIN_VALUE, MAX_STUDENTS)
    _check_range("K (партнери)", k, MIN_VALUE, MAX_PARTNERS)
    _check_range("M (раунди)", m, MIN_VALUE, MAX_ROUNDS)

    if m > k:
        raise ValidationError(
            f"M ({m}) не може перевищувати K ({k}): кожен студент повинен відвідувати "
            "різних партнерів, а доступно лише K партнерів за сесію."
        )

    return GenerateParams(n_students=n, n_partners=k, n_rounds=m)


def _check_range(label: str, value: int, lo: int, hi: int) -> None:
    if value < lo:
        raise ValidationError(f"{label} повинно бути ≥ {lo} (отримано {value}).")
    if value > hi:
        raise ValidationError(f"{label} не може перевищувати {hi} (отримано {value}).")
