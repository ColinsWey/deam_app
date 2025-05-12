"""Initial reports tables

Revision ID: 20240512
Revises: 
Create Date: 2024-05-12 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240512'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем enum для типов отчетов
    report_type = postgresql.ENUM('pdf', 'xlsx', name='reporttype', create_type=True)
    report_type.create(op.get_bind())
    
    # Создаем таблицу шаблонов отчетов
    op.create_table(
        'report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('pdf', 'xlsx', name='reporttype'), nullable=False),
        sa.Column('template_path', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_report_templates_id'), 'report_templates', ['id'], unique=False)
    
    # Создаем таблицу для хранения истории сгенерированных отчетов
    op.create_table(
        'report_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.Enum('pdf', 'xlsx', name='reporttype'), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_history_id'), 'report_history', ['id'], unique=False)


def downgrade() -> None:
    # Удаляем таблицы
    op.drop_index(op.f('ix_report_history_id'), table_name='report_history')
    op.drop_table('report_history')
    op.drop_index(op.f('ix_report_templates_id'), table_name='report_templates')
    op.drop_table('report_templates')
    
    # Удаляем enum
    op.execute('DROP TYPE reporttype') 