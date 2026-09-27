"""
Feature representations, normalization utilities, and dense vector encoders
for the Gamer Role Classification Engine.
"""

from dataclasses import dataclass, field
from typing import Any

from app.core.role_classifier.config import (
    RoleClassificationConfig,
    StatNormalizationBenchmarks,
    default_classification_config,
)


@dataclass
class GamerDNAVector:
    """
    Psychometric trait vector (0.0 to 100.0 scale) derived from the Gamer DNA survey.
    """
    leadership: float = 50.0
    communication: float = 50.0
    strategy: float = 50.0
    teamwork: float = 50.0
    aggression: float = 50.0
    confidence: float = 50.0

    def to_normalized_dict(self) -> dict[str, float]:
        """Returns traits normalized to [0.0, 1.0]."""
        return {
            "leadership": max(0.0, min(100.0, float(self.leadership))) / 100.0,
            "communication": max(0.0, min(100.0, float(self.communication))) / 100.0,
            "strategy": max(0.0, min(100.0, float(self.strategy))) / 100.0,
            "teamwork": max(0.0, min(100.0, float(self.teamwork))) / 100.0,
            "aggression": max(0.0, min(100.0, float(self.aggression))) / 100.0,
            "confidence": max(0.0, min(100.0, float(self.confidence))) / 100.0,
        }

    def to_list(self) -> list[float]:
        """Returns traits as an ordered float list [0.0 - 1.0]."""
        nd = self.to_normalized_dict()
        return [
            nd["leadership"],
            nd["communication"],
            nd["strategy"],
            nd["teamwork"],
            nd["aggression"],
            nd["confidence"],
        ]


@dataclass
class OfficialGameStats:
    """
    Official competitive telemetry and in-game performance metrics.
    """
    win_rate: float = 50.0  # Percentage (0.0 to 100.0)
    kd_ratio: float = 1.0
    kda: float = 2.0
    matches_played: int = 50
    headshot_pct: float | None = None
    score_per_round: float | None = None
    rank: str | None = None
    rank_rating: int | None = None
    favorite_heroes_or_agents: list[str] = field(default_factory=list)

    def normalize(self, benchmarks: StatNormalizationBenchmarks | None = None) -> dict[str, float]:
        """
        Normalizes game statistics into standard [0.0, 1.0] features.
        """
        bm = benchmarks or default_classification_config.benchmarks

        # KD normalization: clamp between min and elite
        kd_norm = (max(bm.kd_min, min(bm.kd_elite, float(self.kd_ratio))) - bm.kd_min) / (
            bm.kd_elite - bm.kd_min
        )

        # Win rate normalization
        wr_norm = (max(bm.win_rate_min, min(bm.win_rate_elite, float(self.win_rate))) - bm.win_rate_min) / (
            bm.win_rate_elite - bm.win_rate_min
        )

        # KDA normalization
        kda_norm = (max(bm.kda_min, min(bm.kda_elite, float(self.kda))) - bm.kda_min) / (
            bm.kda_elite - bm.kda_min
        )

        # Headshot % normalization (default to 0.5 if missing)
        if self.headshot_pct is not None:
            hs_val = float(self.headshot_pct)
            hs_norm = (max(bm.hs_min, min(bm.hs_elite, hs_val)) - bm.hs_min) / (
                bm.hs_elite - bm.hs_min
            )
        else:
            hs_norm = 0.5

        # Sample size factor: 0.0 for 0 matches up to 1.0 for 50+ matches
        sample_factor = min(1.0, max(0.1, float(self.matches_played) / bm.min_matches_full_confidence))

        return {
            "kd_norm": round(kd_norm, 4),
            "win_rate_norm": round(wr_norm, 4),
            "kda_norm": round(kda_norm, 4),
            "headshot_norm": round(hs_norm, 4),
            "sample_factor": round(sample_factor, 4),
        }


@dataclass
class GamerRoleFeatures:
    """
    Consolidated feature container representing all 4 inputs required for classification:
    1. Gamer DNA feature vector
    2. Official game statistics
    3. Preferred roles
    4. Preferred games
    """
    dna: GamerDNAVector = field(default_factory=GamerDNAVector)
    stats: OfficialGameStats = field(default_factory=OfficialGameStats)
    preferred_roles: list[str] = field(default_factory=list)
    preferred_games: list[str] = field(default_factory=list)

    def to_dense_vector(self) -> list[float]:
        """
        Encodes the multi-signal inputs into a dense 1D float vector.
        Designed specifically for seamless drop-in replacement by Machine Learning
        models (e.g. XGBoost, Random Forest, PyTorch/ONNX classifier).

        Vector layout (14 dimensions):
        [0-5]: Normalized DNA traits (leadership, comms, strategy, teamwork, aggression, confidence)
        [6-10]: Normalized stats (kd_norm, win_rate_norm, kda_norm, headshot_norm, sample_factor)
        [11]: Stated preference density
        [12]: Preferred games count factor
        [13]: Hero/Agent affinity density
        """
        dna_feats = self.dna.to_list()
        stat_norms = self.stats.normalize()
        stats_feats = [
            stat_norms["kd_norm"],
            stat_norms["win_rate_norm"],
            stat_norms["kda_norm"],
            stat_norms["headshot_norm"],
            stat_norms["sample_factor"],
        ]

        pref_density = min(1.0, len(self.preferred_roles) / 4.0)
        games_factor = min(1.0, len(self.preferred_games) / 3.0)
        hero_density = min(1.0, len(self.stats.favorite_heroes_or_agents) / 5.0)

        return dna_feats + stats_feats + [pref_density, games_factor, hero_density]

    def to_feature_dict(self) -> dict[str, float]:
        """
        Produces an interpretable key-value map of features for feature importance,
        explainability, and rule condition auditing.
        """
        dna_norm = self.dna.to_normalized_dict()
        stat_norm = self.stats.normalize()
        res = {f"dna_{k}": v for k, v in dna_norm.items()}
        res.update({f"stats_{k}": v for k, v in stat_norm.items()})
        res["preferred_roles_count"] = float(len(self.preferred_roles))
        res["preferred_games_count"] = float(len(self.preferred_games))
        return res
