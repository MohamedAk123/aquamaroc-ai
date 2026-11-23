"""Source de capacité, nécessaire avant tout taux agrégé pondéré."""

import sqlalchemy as sa
from alembic import op

revision = "0002_capacity_provenance"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reservoirs", sa.Column("capacity_source", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("reservoirs", "capacity_source")
