"""Momentum visual y reversals (dominio puro)."""

from __future__ import annotations

import statistics

from aicos.domain.editorial_pattern_engine.entities import MomentumFlowProfile


def compute_momentum_flow(
    motion: tuple[float, ...],
    energy: tuple[float, ...],
    *,
    high_threshold: float = 0.62,
    min_block_len: int = 2,
) -> MomentumFlowProfile:
    if not motion or not energy or len(motion) != len(energy):
        return MomentumFlowProfile(
            momentum_samples=(),
            mean_momentum=0.0,
            momentum_variance=0.0,
            reversal_count=0,
            sustained_high_blocks=0,
        )
    samples: list[float] = []
    for m, e in zip(motion, energy, strict=True):
        samples.append(max(0.0, min(1.0, 0.45 * m + 0.55 * e)))
    mom = tuple(samples)
    mean_m = statistics.fmean(mom)
    var_m = statistics.pvariance(mom) if len(mom) > 1 else 0.0
    reversals = 0
    for i in range(2, len(mom)):
        d0 = mom[i - 1] - mom[i - 2]
        d1 = mom[i] - mom[i - 1]
        if d0 != 0 and d1 != 0 and (d0 > 0) != (d1 > 0):
            reversals += 1
    # Contar bloques sostenidos altos
    blocks = 0
    run = 0
    for v in mom:
        if v >= high_threshold:
            run += 1
        else:
            if run >= min_block_len:
                blocks += 1
            run = 0
    if run >= min_block_len:
        blocks += 1
    return MomentumFlowProfile(
        momentum_samples=mom,
        mean_momentum=float(mean_m),
        momentum_variance=float(var_m),
        reversal_count=reversals,
        sustained_high_blocks=blocks,
    )
