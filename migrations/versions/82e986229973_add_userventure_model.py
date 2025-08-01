"""Add UserVenture model

Revision ID: 82e986229973
Revises: f2594475ac7d
Create Date: 2025-07-18 19:46:57.555892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82e986229973'
down_revision = 'f2594475ac7d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_venture',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('venture_type', sa.String(length=50), nullable=False),
    sa.Column('added_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'venture_type', name='_user_venture_uc')
    )
    with op.batch_alter_table('donation_record', schema=None) as batch_op:
        batch_op.alter_column('tier',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=20),
               nullable=False)
        batch_op.alter_column('paypal_transaction_id',
               existing_type=sa.VARCHAR(length=10),
               type_=sa.String(length=100),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('donation_record', schema=None) as batch_op:
        batch_op.alter_column('paypal_transaction_id',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=10),
               existing_nullable=True)
        batch_op.alter_column('tier',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=50),
               nullable=True)

    op.drop_table('user_venture')
    # ### end Alembic commands ###
