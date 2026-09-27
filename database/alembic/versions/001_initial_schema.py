"""Initial database schema migration creating six persistent entities

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-09-24 23:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create cameras table
    op.create_table(
        'cameras',
        sa.Column('camera_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('location', sa.String(length=256), nullable=True),
        sa.Column('stream_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('camera_id')
    )

    # 2. Create detections table
    op.create_table(
        'detections',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('camera_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('class', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_detection_confidence_range'),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.camera_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_detections_camera_ts', 'detections', ['camera_id', sa.text('timestamp DESC')])

    # 3. Create tracks table
    op.create_table(
        'tracks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('camera_id', sa.String(length=64), nullable=False),
        sa.Column('track_id', sa.String(length=128), nullable=False),
        sa.Column('class', sa.String(length=64), nullable=False),
        sa.Column('bbox', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tracking_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.camera_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tracks_camera_track', 'tracks', ['camera_id', 'track_id'])
    op.create_index('idx_tracks_timestamp', 'tracks', [sa.text('timestamp DESC')])

    # 4. Create anpr_records table (Soft reference on track_id - NO foreign key)
    op.create_table(
        'anpr_records',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('track_id', sa.String(length=128), nullable=True),
        sa.Column('vehicle_reference', sa.String(length=512), nullable=True),
        sa.Column('plate_text', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('evidence_reference', sa.String(length=512), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_anpr_confidence_range'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_anpr_plate_text', 'anpr_records', ['plate_text'])
    op.create_index('idx_anpr_track_id', 'anpr_records', ['track_id'])

    # 5. Create events table
    op.create_table(
        'events',
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('camera_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('object_track', sa.String(length=128), nullable=False),
        sa.Column('zone_rule', sa.String(length=128), nullable=False),
        sa.Column('evidence_reference', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("event_type IN ('virtual_fence', 'night_movement', 'dwell_presence', 'suspicious_rule')", name='check_event_type_valid'),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.camera_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index('idx_events_camera_ts', 'events', ['camera_id', sa.text('timestamp DESC')])
    op.create_index('idx_events_type_ts', 'events', ['event_type', sa.text('timestamp DESC')])
    op.create_index('idx_events_object_track', 'events', ['object_track'])

    # 6. Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='UNREAD', nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('reference', sa.String(length=512), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name='check_alert_priority_valid'),
        sa.CheckConstraint("status IN ('UNREAD', 'ACKNOWLEDGED', 'RESOLVED')", name='check_alert_status_valid'),
        sa.ForeignKeyConstraint(['event_id'], ['events.event_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alerts_status_priority_ts', 'alerts', ['status', 'priority', sa.text('timestamp DESC')])
    op.create_index('idx_alerts_event_id', 'alerts', ['event_id'])

def downgrade() -> None:
    op.drop_index('idx_alerts_event_id', table_name='alerts')
    op.drop_index('idx_alerts_status_priority_ts', table_name='alerts')
    op.drop_table('alerts')

    op.drop_index('idx_events_object_track', table_name='events')
    op.drop_index('idx_events_type_ts', table_name='events')
    op.drop_index('idx_events_camera_ts', table_name='events')
    op.drop_table('events')

    op.drop_index('idx_anpr_track_id', table_name='anpr_records')
    op.drop_index('idx_anpr_plate_text', table_name='anpr_records')
    op.drop_table('anpr_records')

    op.drop_index('idx_tracks_timestamp', table_name='tracks')
    op.drop_index('idx_tracks_camera_track', table_name='tracks')
    op.drop_table('tracks')

    op.drop_index('idx_detections_camera_ts', table_name='detections')
    op.drop_table('detections')

    op.drop_table('cameras')
