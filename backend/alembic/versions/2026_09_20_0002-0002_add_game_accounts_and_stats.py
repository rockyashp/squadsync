"""Add game_accounts, player_stats, survey_answers and JSONB telemetry

Revision ID: 0002_add_game_accounts_and_stats
Revises: 0001_initial_tables
Create Date: 2026-09-20 13:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_add_game_accounts_and_stats"
down_revision: Union[str, None] = "0001_initial_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add JSONB columns to existing tables
    op.add_column("users", sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("gamer_profiles", sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("gamer_dna", sa.Column("raw_evaluation", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Rename survey_responses to survey_answers if it exists, or create survey_answers
    # For safety in fresh or existing DBs:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'survey_responses') THEN
                ALTER TABLE survey_responses RENAME TO survey_answers;
                ALTER INDEX IF EXISTS ix_survey_responses_id RENAME TO ix_survey_answers_id;
                ALTER INDEX IF EXISTS ix_survey_responses_user_id RENAME TO ix_survey_answers_user_id;
                ALTER INDEX IF EXISTS ix_survey_responses_question_id RENAME TO ix_survey_answers_question_id;
                ALTER INDEX IF EXISTS ix_survey_responses_category RENAME TO ix_survey_answers_category;
                ALTER INDEX IF EXISTS ix_survey_responses_user_question RENAME TO ix_survey_answers_user_question;
                ALTER TABLE survey_answers RENAME CONSTRAINT uq_survey_response_user_question TO uq_survey_answers_user_question;
                ALTER TABLE survey_answers ADD COLUMN IF NOT EXISTS selected_option_id VARCHAR(100);
                ALTER TABLE survey_answers ADD COLUMN IF NOT EXISTS raw_metadata JSONB;
            ELSE
                CREATE TABLE survey_answers (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question_id VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    selected_option_id VARCHAR(100),
                    answer TEXT NOT NULL,
                    score INTEGER,
                    raw_metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_survey_answers_user_question UNIQUE (user_id, question_id)
                );
                CREATE INDEX ix_survey_answers_id ON survey_answers(id);
                CREATE INDEX ix_survey_answers_user_id ON survey_answers(user_id);
                CREATE INDEX ix_survey_answers_question_id ON survey_answers(question_id);
                CREATE INDEX ix_survey_answers_category ON survey_answers(category);
                CREATE INDEX ix_survey_answers_user_question ON survey_answers(user_id, question_id);
            END IF;
        END $$;
    """)

    # --------------------------------------------------------------------------
    # Table: game_accounts
    # --------------------------------------------------------------------------
    op.create_table(
        "game_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("game_name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("account_identifier", sa.String(length=255), nullable=False),
        sa.Column("in_game_name", sa.String(length=100), nullable=False),
        sa.Column("tagline", sa.String(length=50), nullable=True),
        sa.Column("region", sa.String(length=50), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("raw_profile_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_game_accounts_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_accounts")),
        sa.UniqueConstraint("user_id", "platform", "account_identifier", name="uq_game_accounts_user_platform_identifier"),
    )
    op.create_index(op.f("ix_game_accounts_id"), "game_accounts", ["id"], unique=False)
    op.create_index(op.f("ix_game_accounts_user_id"), "game_accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_game_accounts_game_name"), "game_accounts", ["game_name"], unique=False)
    op.create_index(op.f("ix_game_accounts_platform"), "game_accounts", ["platform"], unique=False)
    op.create_index(op.f("ix_game_accounts_account_identifier"), "game_accounts", ["account_identifier"], unique=False)
    op.create_index("ix_game_accounts_platform_identifier", "game_accounts", ["platform", "account_identifier"], unique=False)
    op.create_index("ix_game_accounts_user_game", "game_accounts", ["user_id", "game_name"], unique=False)

    # --------------------------------------------------------------------------
    # Table: player_stats
    # --------------------------------------------------------------------------
    op.create_table(
        "player_stats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("game_account_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("season", sa.String(length=50), nullable=False),
        sa.Column("game_mode", sa.String(length=50), nullable=False),
        sa.Column("current_rank", sa.String(length=50), nullable=True),
        sa.Column("peak_rank", sa.String(length=50), nullable=True),
        sa.Column("rank_rating", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("matches_played", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("wins", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("losses", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("win_rate", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("kd_ratio", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("kda", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("headshot_pct", sa.Float(), server_default=sa.text("0.0"), nullable=True),
        sa.Column("score_per_round", sa.Float(), server_default=sa.text("0.0"), nullable=True),
        sa.Column("raw_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["game_account_id"], ["game_accounts.id"], name=op.f("fk_player_stats_game_account_id_game_accounts"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_player_stats_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_player_stats")),
        sa.UniqueConstraint("game_account_id", "season", "game_mode", name="uq_player_stats_account_season_mode"),
    )
    op.create_index(op.f("ix_player_stats_id"), "player_stats", ["id"], unique=False)
    op.create_index(op.f("ix_player_stats_game_account_id"), "player_stats", ["game_account_id"], unique=False)
    op.create_index(op.f("ix_player_stats_user_id"), "player_stats", ["user_id"], unique=False)
    op.create_index(op.f("ix_player_stats_season"), "player_stats", ["season"], unique=False)
    op.create_index(op.f("ix_player_stats_game_mode"), "player_stats", ["game_mode"], unique=False)
    op.create_index(op.f("ix_player_stats_current_rank"), "player_stats", ["current_rank"], unique=False)
    op.create_index("ix_player_stats_user_recorded", "player_stats", ["user_id", "recorded_at"], unique=False)
    op.create_index("ix_player_stats_mode_rank", "player_stats", ["game_mode", "current_rank"], unique=False)


def downgrade() -> None:
    op.drop_table("player_stats")
    op.drop_table("game_accounts")
    op.drop_column("gamer_dna", "raw_evaluation")
    op.drop_column("gamer_profiles", "preferences")
    op.drop_column("users", "raw_metadata")
