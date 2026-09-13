"""Frozen chronological partitions for Phase 5 anomaly research."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnomalyBlock:
    name: str
    train_start: int
    train_end: int
    score_start: int
    score_end: int
    role: str

    @property
    def score_days(self) -> tuple[int, ...]:
        return tuple(range(self.score_start, self.score_end + 1))

    def validate(self) -> None:
        if self.train_start != 1 or self.train_end >= self.score_start:
            raise ValueError("training must end strictly before the score block")
        if self.score_end - self.score_start + 1 != 28:
            raise ValueError("every anomaly block must contain exactly 28 days")


DEVELOPMENT_BLOCKS = (
    AnomalyBlock("development_1_scale_seed", 1, 1465, 1466, 1493, "scale_seed"),
    AnomalyBlock("development_2", 1, 1549, 1550, 1577, "development"),
    AnomalyBlock("development_3", 1, 1633, 1634, 1661, "development"),
    AnomalyBlock("development_4", 1, 1717, 1718, 1745, "development"),
    AnomalyBlock("development_5", 1, 1801, 1802, 1829, "development"),
)
VALIDATION_BLOCK = AnomalyBlock("validation", 1, 1885, 1886, 1913, "validation")
ANOMALY_LOCKBOX = AnomalyBlock("anomaly_lockbox", 1, 1913, 1914, 1941, "lockbox")


def development_blocks() -> tuple[AnomalyBlock, ...]:
    """Return development/validation blocks only; never expose the lockbox."""
    blocks = (*DEVELOPMENT_BLOCKS, VALIDATION_BLOCK)
    for block in blocks:
        block.validate()
    return blocks


def assert_partition_integrity() -> None:
    blocks = (*DEVELOPMENT_BLOCKS, VALIDATION_BLOCK, ANOMALY_LOCKBOX)
    for block in blocks:
        block.validate()
    scored = [day for block in blocks for day in block.score_days]
    if len(scored) != len(set(scored)):
        raise ValueError("anomaly score partitions overlap")
    if max(VALIDATION_BLOCK.score_days) >= min(ANOMALY_LOCKBOX.score_days):
        raise ValueError("validation must precede the anomaly lockbox")
