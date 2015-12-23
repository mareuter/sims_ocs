from sqlalchemy import Column, Float, Index, Integer, String, Table
from sqlalchemy.types import DATETIME
from sqlalchemy import DDL, event

def create_session(metadata, autoincrement=True):
    """Create Session table.

    This function creates the Session table for tracking the various simulations run. For MySQL, it adds
    a post-create command to set the lower limit of the auto increment value.

    Args:
        metadata (sqlalchemy.MetaData): The database object that collects the tables.
        autoincrement (bool): A flag to set auto incrementing on the sessionID column.

    Returns:
        (sqlalchemy.Table): The Session table object.
    """
    table = Table("Session", metadata,
                  Column("sessionID", Integer, primary_key=True, autoincrement=autoincrement, nullable=False),
                  Column("sessionUser", String(80), nullable=False),
                  Column("sessionHost", String(80), nullable=False),
                  Column("sessionDate", DATETIME, nullable=False),
                  Column("version", String(25), nullable=True),
                  Column("runComment", String(200), nullable=True))

    Index("s_host_user_date_idx", table.c.sessionUser, table.c.sessionHost, table.c.sessionDate, unique=True)

    alter_table = DDL("ALTER TABLE %(table)s AUTO_INCREMENT=1000;")
    event.listen(table, 'after_create', alter_table.execute_if(dialect='mysql'))

    return table

def create_field(metadata):
    """Create Field table.

    This function creates the Field table from the sky tesellation.

    Args:
        metadata (sqlalchemy.MetaData): The database object that collects the tables.

    Returns:
        (sqlalchemy.Table): The Field table object.
    """
    table = Table("Field", metadata,
                  Column("ID", Integer, primary_key=True, nullable=False),
                  Column("fov", Float, nullable=False),
                  Column("ra", Float, nullable=False),
                  Column("dec", Float, nullable=False),
                  Column("gl", Float, nullable=False),
                  Column("gb", Float, nullable=False),
                  Column("el", Float, nullable=False),
                  Column("eb", Float, nullable=False))

    Index("field_fov", table.c.ID, table.c.fov)
    Index("fov_gl_gb", table.c.fov, table.c.gl, table.c.gb)
    Index("fov_el_eb", table.c.fov, table.c.el, table.c.eb)
    Index("fov_ra_dec", table.c.fov, table.c.ra, table.c.dec)

    return table

def create_target_history(metadata):
    """Create TargetHistory table.

    This function creates the TargetHistory table for tracking all the requested targets from
    the Scheduler in the simulation run.

    Args:
        metadata (sqlalchemy.MetaData): The database object that collects the tables.

    Returns:
        (sqlalchemy.Table): The TargetHistory table object.
    """
    table = Table("TargetHistory", metadata,
                  Column("targetID", Integer, primary_key=True),
                  Column("Session_sessionID", Integer, primary_key=True),
                  Column("fieldID", Integer),
                  Column("filter", String(1)),
                  Column("ra", Float),
                  Column("dec", Float),
                  Column("angle", Float),
                  Column("num_exposures", Integer))

    Index("s_filter", table.c.filter)
    Index("fk_TargetHistory_Session1", table.c.Session_sessionID)
    Index("fk_TargetHistory_Field1", table.c.fieldID)

    return table

def create_observation(metadata):
    pass
