from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

StressPhase = Literal["detection", "recovery", "stress", "mini_crisis", "false_alarm"]


@dataclass(frozen=True)
class StressEpisode:
    date: date
    phase: StressPhase
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "phase": self.phase,
            "note": self.note,
        }


STRESS_EPISODES: tuple[StressEpisode, ...] = (
    StressEpisode(date(2008, 9, 15), "detection", "Lehman"),
    StressEpisode(date(2009, 3, 9), "recovery", "GFC low"),
    StressEpisode(date(2020, 3, 16), "detection", "COVID panic"),
    StressEpisode(date(2020, 3, 23), "recovery", "COVID low"),
    StressEpisode(date(2022, 6, 15), "stress", "75bp hike"),
    StressEpisode(date(2022, 10, 12), "recovery", "bear low"),
    StressEpisode(date(2023, 3, 10), "mini_crisis", "SVB"),
    StressEpisode(date(2011, 8, 5), "false_alarm", "US downgrade"),
    StressEpisode(date(2015, 8, 24), "false_alarm", "China scare"),
    StressEpisode(date(2018, 12, 24), "false_alarm", "Fed panic"),
)

_EPISODES_BY_DATE: dict[date, StressEpisode] = {ep.date: ep for ep in STRESS_EPISODES}


def episode_for_date(d: date) -> StressEpisode | None:
    return _EPISODES_BY_DATE.get(d)


def list_episodes() -> dict[str, Any]:
    episodes = [ep.to_dict() for ep in STRESS_EPISODES]
    return {
        "schema_version": "1.0",
        "count": len(episodes),
        "episodes": episodes,
    }
