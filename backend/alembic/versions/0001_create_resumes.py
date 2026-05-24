"""Initial migration – create the `resumes` table.

Generated manually to avoid needing the alembic CLI.
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "0001_create_resumes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("content_json", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("uploaded_at", sa.DateTime, server_default=sa.func.now()),
    )
    # Optional: add an index on uploaded_at for sorting
    op.create_index("ix_resumes_uploaded_at", "resumes", ["uploaded_at"])


def downgrade():
    op.drop_index("ix_resumes_uploaded_at", table_name="resumes")
    op.drop_table("resumes")
