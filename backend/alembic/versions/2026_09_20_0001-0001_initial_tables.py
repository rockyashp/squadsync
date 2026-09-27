"""create initial tables for users, gamer_profiles, survey_responses, gamer_dna

Revision ID: 0001_initial_tables
Revises: 
Create Date: 2026-09-20 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 1. Table: users
    # --------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # --------------------------------------------------------------------------
    # 2. Table: gamer_profiles
    # --------------------------------------------------------------------------
    op.create_table(
        "gamer_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("favorite_game", sa.String(length=100), nullable=True),
        sa.Column("rank", sa.String(length=50), nullable=True),
        sa.Column("preferred_role", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=20), server_default="en", nullable=True),
        sa.Column("region", sa.String(length=50), nullable=True),
        sa.Column("gaming_schedule", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_gamer_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gamer_profiles")),
    )
    op.create_index(op.f("ix_gamer_profiles_id"), "gamer_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_gamer_profiles_user_id"), "gamer_profiles", ["user_id"], unique=True)
    op.create_index(op.f("ix_gamer_profiles_favorite_game"), "gamer_profiles", ["favorite_game"], unique=False)
    op.create_index(op.f("ix_gamer_profiles_preferred_role"), "gamer_profiles", ["preferred_role"], unique=False)
    op.create_index(op.f("ix_gamer_profiles_region"), "gamer_profiles", ["region"], unique=False)

    # --------------------------------------------------------------------------
    # 3. Table: survey_responses
    # --------------------------------------------------------------------------
    op.create_table(
        "survey_responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_survey_responses_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_responses")),
        sa.UniqueConstraint("user_id", "question_id", name="uq_survey_response_user_question"),
    )
    op.create_index(op.f("ix_survey_responses_id"), "survey_responses", ["id"], unique=False)
    op.create_index(op.f("ix_survey_responses_user_id"), "survey_responses", ["user_id"], unique=False)
    op.create_index(op.f("ix_survey_responses_question_id"), "survey_responses", ["question_id"], unique=False)
    op.create_index("ix_survey_responses_user_question", "survey_responses", ["user_id", "question_id"], unique=False)

    # --------------------------------------------------------------------------
    # 4. Table: gamer_dna
    # --------------------------------------------------------------------------
    op.create_table(
        "gamer_dna",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("leadership", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("communication", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("teamwork", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("strategy", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("aggression", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("primary_role", sa.String(length=50), nullable=False),
        sa.Column("secondary_role", sa.String(length=50), nullable=True),
        sa.Column("personality", sa.String(length=100), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_gamer_dna_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gamer_dna")),
    )
    op.create_index(op.f("ix_gamer_dna_id"), "gamer_dna", ["id"], unique=False)
    op.create_index(op.f("ix_gamer_dna_user_id"), "gamer_dna", ["user_id"], unique=True)
    op.create_index(op.f("ix_gamer_dna_primary_role"), "gamer_dna", ["primary_role"], unique=False)
    op.create_index(op.f("ix_gamer_dna_personality"), "gamer_dna", ["personality"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("gamer_dna")
    op.drop_table("survey_responses")
    op.drop_table("gamer_profiles")
    op.drop_table("users")
