from dataclasses import dataclass


@dataclass(frozen=True)
class DataPoint:
    """Each data point taken (timestamp, dec, a, b)"""

    timestamp: float
    dec: float
    a: float
    b: float

    def to_tuple(self) -> tuple[float, float, float, float]:
        return self.timestamp, self.dec, self.a, self.b
