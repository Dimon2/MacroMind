from __future__ import annotations

from macromind.market.normalized_observation import NormalizedObservation
from macromind.market.normalizers import (
    normalize_macro_datapoint,
    normalize_prediction_snapshot,
)
from macromind.models import DataPoint
from macromind.prediction_markets.models import PredictionMarketSnapshot


class NormalizedFeedService:
    def from_macro_datapoints(self, datapoints: list[DataPoint]) -> list[NormalizedObservation]:
        return [normalize_macro_datapoint(datapoint) for datapoint in datapoints]

    def from_prediction_snapshots(
        self, snapshots: list[PredictionMarketSnapshot]
    ) -> list[NormalizedObservation]:
        return [normalize_prediction_snapshot(snapshot) for snapshot in snapshots]

    def combine(
        self,
        *,
        macro_datapoints: list[DataPoint] | None = None,
        prediction_snapshots: list[PredictionMarketSnapshot] | None = None,
    ) -> list[NormalizedObservation]:
        macro = self.from_macro_datapoints(macro_datapoints or [])
        prediction = self.from_prediction_snapshots(prediction_snapshots or [])
        combined = [*macro, *prediction]
        return sorted(combined, key=lambda item: (item.observation_date, item.source, item.series_key))
