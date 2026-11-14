"""Saisie libre, compteur facultatif et liaison documentaire stable."""

import unicodedata

import sqlalchemy as sa
from alembic import op

revision = 'e41ac907d256'
down_revision = 'd3164bd2b7a1'
branch_labels = None
depends_on = None


def key(value):
    return ''.join(
        c
        for c in unicodedata.normalize('NFKD', value.casefold())
        if not unicodedata.combining(c) and not c.isspace()
    )


def upgrade():
    with op.batch_alter_table('vehicles') as batch:
        batch.add_column(sa.Column('manual_reference', sa.JSON(), nullable=True))
        batch.alter_column(
            'mileage', existing_type=sa.Integer(), type_=sa.BigInteger(), nullable=True
        )
        batch.alter_column(
            'engine_type', existing_type=sa.String(40), type_=sa.Text(), nullable=True
        )
    connection = op.get_bind()
    vehicles = sa.table(
        'vehicles',
        sa.column('id'),
        sa.column('brand'),
        sa.column('model'),
        sa.column('year'),
        sa.column('manual_reference', sa.JSON()),
    )
    passages = sa.table(
        'manuel_passages', sa.column('brand'), sa.column('model'), sa.column('year')
    )
    known = {}
    for b, m, y in connection.execute(
        sa.select(passages.c.brand, passages.c.model, passages.c.year).distinct()
    ):
        known.setdefault((key(b), key(m), y), []).append(dict(marque=b, modele=m, annee=y))
    for row in connection.execute(
        sa.select(vehicles.c.id, vehicles.c.brand, vehicles.c.model, vehicles.c.year)
    ):
        matches = known.get((key(row.brand), key(row.model), row.year), [])
        if len(matches) == 1:
            connection.execute(
                vehicles.update().where(vehicles.c.id == row.id).values(manual_reference=matches[0])
            )


def downgrade():
    connection = op.get_bind()
    vehicles = sa.table('vehicles', sa.column('mileage'), sa.column('engine_type'))
    connection.execute(vehicles.update().where(vehicles.c.mileage.is_(None)).values(mileage=0))
    connection.execute(
        vehicles.update().where(vehicles.c.engine_type.is_(None)).values(engine_type='')
    )
    with op.batch_alter_table('vehicles') as batch:
        batch.drop_column('manual_reference')
        batch.alter_column(
            'mileage', existing_type=sa.BigInteger(), type_=sa.Integer(), nullable=False
        )
        batch.alter_column(
            'engine_type', existing_type=sa.Text(), type_=sa.String(40), nullable=False
        )
