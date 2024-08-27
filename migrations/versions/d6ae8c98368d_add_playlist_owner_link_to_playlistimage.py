"""Add playlist_owner_link to PlaylistImage

Revision ID: d6ae8c98368d
Revises: 51a674fa2fe0
Create Date: 2024-08-27 10:11:28.611964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6ae8c98368d'
down_revision = '51a674fa2fe0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('playlist_image', schema=None) as batch_op:
        batch_op.add_column(sa.Column('playlist_owner_link', sa.String(length=255), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('playlist_image', schema=None) as batch_op:
        batch_op.drop_column('playlist_owner_link')

    # ### end Alembic commands ###
