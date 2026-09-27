"""
GamerDNA service handling role classification orchestration and persistence.
"""

from datetime import datetime, timezone
from typing import Any, Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.survey_response import SurveyResponse
from app.models.user import User
from app.repositories.dna_repository import DNARepository
from app.repositories.survey_repository import SurveyRepository
from app.schemas.dna import (
    GamerDNACardResponse,
    GamerDNAEvaluationResponse,
    GamerDNARead,
    ProfileCardSummary,
)
from app.services.base import BaseService
from app.services.classifier import classifier_engine


class DNAService(BaseService[GamerDNA]):
    """Orchestrates survey answer aggregation, rule-based classification, and GamerDNA persistence."""

    def __init__(
        self,
        db: AsyncSession,
        dna_repo: DNARepository | None = None,
        survey_repo: SurveyRepository | None = None,
    ) -> None:
        super().__init__(db)
        self.dna_repo = dna_repo or DNARepository(db)
        self.survey_repo = survey_repo or SurveyRepository(db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> GamerDNA | None:
        """Retrieve stored GamerDNA for a given user via repository."""
        return await self.dna_repo.get_by_user_id(user_id)

    async def get_by_user_id_or_404(self, user_id: uuid.UUID) -> GamerDNA:
        """Retrieve stored GamerDNA or raise 404."""
        dna = await self.get_by_user_id(user_id)
        if not dna:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gamer DNA not found. Please complete the survey first to generate your DNA profile.",
            )
        return dna

    async def classify_and_store(
        self,
        user_id: uuid.UUID,
        responses: Sequence[SurveyResponse] | None = None,
    ) -> GamerDNAEvaluationResponse:
        """
        Gathers all saved survey responses for the user, runs rule-based classification,
        persists the result in the gamer_dna table, and returns the full evaluation.
        """
        # Fetch user's survey responses if not provided in-memory
        if responses is None:
            responses = await self.survey_repo.get_answers_by_user_id(user_id)

        if not responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No survey responses found for this account. Please submit the Gamer DNA survey first.",
            )

        # Run rule-based classification engine
        classification = classifier_engine.classify(responses)

        # Upsert into gamer_dna table
        existing_dna = await self.dna_repo.get_by_user_id(user_id)

        if existing_dna:
            existing_dna.leadership = classification.scores.get("Leadership", 50)
            existing_dna.communication = classification.scores.get("Communication", 50)
            existing_dna.strategy = classification.scores.get("Strategy", 50)
            existing_dna.teamwork = classification.scores.get("Teamwork", 50)
            existing_dna.aggression = classification.scores.get("Aggression", 50)
            existing_dna.confidence = classification.scores.get("Confidence", 50)
            existing_dna.primary_role = classification.primary_role
            existing_dna.secondary_role = classification.secondary_role
            existing_dna.personality = classification.personality
            existing_dna.reasoning = classification.reasoning
            dna_record = await self.dna_repo.update(existing_dna)
        else:
            now = datetime.now(timezone.utc)
            new_dna = GamerDNA(
                id=uuid.uuid4(),
                user_id=user_id,
                leadership=classification.scores.get("Leadership", 50),
                communication=classification.scores.get("Communication", 50),
                strategy=classification.scores.get("Strategy", 50),
                teamwork=classification.scores.get("Teamwork", 50),
                aggression=classification.scores.get("Aggression", 50),
                confidence=classification.scores.get("Confidence", 50),
                primary_role=classification.primary_role,
                secondary_role=classification.secondary_role,
                personality=classification.personality,
                reasoning=classification.reasoning,
                created_at=now,
                updated_at=now,
            )
            dna_record = await self.dna_repo.create(new_dna)

        return GamerDNAEvaluationResponse(
            primary_role=classification.primary_role,
            secondary_role=classification.secondary_role,
            personality=classification.personality,
            score_breakdown=classification.scores,
            role_affinities=classification.role_affinities,
            reasoning=classification.reasoning,
            gamer_dna=GamerDNARead.model_validate(dna_record),
        )

    async def get_gamer_dna_card(self, user: User) -> GamerDNACardResponse:
        """
        Synthesizes user profile, psychometric scores, role classifications,
        strengths, weaknesses, and tailored playstyle into a frontend-optimized Gamer DNA Card.
        """
        # Fetch user's GamerDNA record
        dna = await self.get_by_user_id_or_404(user.id)

        # Fetch optional GamerProfile
        stmt = select(GamerProfile).where(GamerProfile.user_id == user.id)
        profile_res = await self.db.execute(stmt)
        profile = profile_res.scalar_one_or_none()

        profile_summary = (
            ProfileCardSummary.model_validate(profile) if profile else None
        )

        strengths = self._calculate_strengths(dna)
        weaknesses = self._calculate_weaknesses(dna)
        recommended_playstyle = self._calculate_playstyle(dna)

        return GamerDNACardResponse(
            username=user.username,
            profile=profile_summary,
            primary_role=dna.primary_role,
            secondary_role=dna.secondary_role,
            leadership_score=dna.leadership,
            communication_score=dna.communication,
            strategy_score=dna.strategy,
            aggression_score=dna.aggression,
            teamwork_score=dna.teamwork,
            confidence_score=dna.confidence if getattr(dna, "confidence", None) is not None else 50,
            personality=dna.personality,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_playstyle=recommended_playstyle,
        )

    def _calculate_strengths(self, dna: GamerDNA) -> list[str]:
        """Derives actionable strengths based on top trait scores and role affinity."""
        strengths: list[str] = []
        conf = dna.confidence if getattr(dna, "confidence", None) is not None else 50

        if dna.leadership >= 70:
            strengths.append("Decisive shotcaller who resets squad morale under pressure")
        if dna.communication >= 70:
            strengths.append("Delivers crisp, continuous situational callouts and damage tracking")
        if dna.strategy >= 70:
            strengths.append("Formulates effective counter-utility setups and anti-flank traps")
        if dna.teamwork >= 70:
            strengths.append("Selfless collaborator prioritizing squad economy and crossfire trades")
        if dna.aggression >= 70:
            strengths.append("Relentless forward momentum and high-impact opening duel conversions")
        if conf >= 70:
            strengths.append("High clutch composure and unshakable self-confidence under pressure")

        # Guarantee at least 3 strengths by falling back on role-specific traits
        role_defaults: dict[str, list[str]] = {
            "Leader": ["Natural lobby anchor and draft cohesion facilitator", "Composed under tense late-game round timers"],
            "Support": ["Reliable utility assist and clutch peel execution", "High emotional intelligence and tilt resistance"],
            "Strategist": ["Master of macro rotations and objective timing", "Rapid adaptation against opponent flank patterns"],
            "Duelist": ["Fearless opening duel seeker", "Creates instant space for teammates to flood bomb sites"],
            "Sentinel": ["Impenetrable site lockdown and flank denial", "Patient retake discipline and utility conservation"],
            "Controller": ["Dominates sightlines with surgical smoke deployments", "Dictates battlefield tempo and entry corridors"],
        }

        for fallback in role_defaults.get(dna.primary_role, ["Adaptive team contributor", "Solid mechanical foundation"]):
            if len(strengths) < 3 and fallback not in strengths:
                strengths.append(fallback)

        return strengths[:4]

    def _calculate_weaknesses(self, dna: GamerDNA) -> list[str]:
        """Derives constructive growth areas based on lower scoring traits."""
        weaknesses: list[str] = []
        conf = dna.confidence if getattr(dna, "confidence", None) is not None else 50

        if dna.aggression <= 45:
            weaknesses.append("Can be overly hesitant when capitalizing on sudden offensive openings")
        if dna.strategy <= 45:
            weaknesses.append("Susceptible to mechanical tunneling without tracking opponent utility cooldowns")
        if dna.teamwork <= 45:
            weaknesses.append("Prone to overextending solo outside allied trade distance")
        if dna.communication <= 45:
            weaknesses.append("Relies excessively on silent pings during chaotic engagements")
        if dna.leadership <= 45:
            weaknesses.append("Reluctant to take initiative when a designated shotcaller is missing")
        if conf <= 45:
            weaknesses.append("Prone to self-doubt or hesitation during high-stakes clutch scenarios")

        # Guarantee at least 2 constructive growth areas
        role_weaknesses: dict[str, list[str]] = {
            "Duelist": ["High-risk early pushes can leave team at a player deficit if unassisted", "Patience on defense when holding angles"],
            "Sentinel": ["Reluctant to abandon defensive setups when fast retake rotations are required", "Can struggle when forced into proactive duels"],
            "Leader": ["Vulnerable to tilt when squadmates deviate from coordinated plays", "Over-focusing on teammates' positions at the cost of personal crosshair placement"],
            "Support": ["Excessive self-sacrifice on eco rounds can compromise own survivability", "Needs to take aggressive duels when carries are eliminated"],
            "Strategist": ["Overthinking tactical contingencies can cause delayed execution against hyper-aggressive rushes", "Over-reliance on structured play"],
            "Controller": ["Vulnerable to being caught with utility in hand while smoking choke points", "Requires teammates to actively play around created vision gaps"],
        }

        for fallback in role_weaknesses.get(dna.primary_role, ["Consistency across unfamiliar team comps", "Mid-round decision speed"]):
            if len(weaknesses) < 2 and fallback not in weaknesses:
                weaknesses.append(fallback)

        return weaknesses[:3]

    def _calculate_playstyle(self, dna: GamerDNA) -> str:
        """Generates tailored playstyle recommendation combining roles and traits."""
        p_role = dna.primary_role
        s_role = dna.secondary_role or "Flex"

        playstyle_guides: dict[tuple[str, str], str] = {
            ("Leader", "Strategist"): (
                "Operate as the In-Game Leader (IGL). Establish default spread in the opening 20 seconds, "
                "read the opposing team's defensive gaps, and call decisive site hits layered with synchronized allied utility."
            ),
            ("Leader", "Duelist"): (
                "Play as the Vocal Entry Vanguard. Dictate round tempo by calling team flashes before taking first contact. "
                "Maintain aggressive forward pressure while ensuring squadmates are positioned for immediate trade frags."
            ),
            ("Strategist", "Controller"): (
                "Adopt the Battlefield Architect style. Starve opponent sightlines with precision smokes, "
                "bait out defensive utility, and coordinate patient mid-round rotations to open sites."
            ),
            ("Support", "Sentinel"): (
                "Anchor as the Team's Tactical Lifeline. Establish defensive crossfires with allied carries, "
                "conserve utility for post-plant denials, and guarantee full flank lockdown."
            ),
            ("Duelist", "Leader"): (
                "Act as the Aggressive Spearhead. Use high mobility and mechanical confidence to seize key choke points early, "
                "loudly communicating your entry line so allies can collapse into the contested space."
            ),
            ("Sentinel", "Strategist"): (
                "Command the Defensive Perimeter. Punish predictable enemy pathing with pre-placed traps, "
                "delay site pushes until allied rotations arrive, and lead retake execution."
            ),
        }

        # Check exact pair or provide dynamic role-based synthesis
        guide = playstyle_guides.get((p_role, s_role))
        if not guide:
            guide = (
                f"As a {p_role} with {s_role} adaptability ({dna.personality}), focus on leveraging your "
                f"{'high aggression and tempo' if dna.aggression >= 60 else 'strategic spatial control'}. "
                f"Coordinate closely with your squad to balance entry timing and utility trades."
            )
        return guide
