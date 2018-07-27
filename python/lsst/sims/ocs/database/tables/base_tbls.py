from sqlalchemy import Column, Float, Index, Integer, String, Table
from sqlalchemy.types import DATETIME
from sqlalchemy import DDL, event

__all__ = ["create_config", "create_field", "create_observation_exposures",
           "create_observation_history", "create_observation_proposal_history", "create_proposal_field",
           "create_proposal", "create_scheduled_downtime",
           "create_session", "create_slew_activities", "create_slew_final_state",
           "create_slew_history", "create_slew_initial_state", "create_slew_maxspeeds",
           "create_target_exposures", "create_target_history", "create_target_proposal_history",
           "create_unscheduled_downtime"]

def create_config(metadata):
    """Create the Config table.

    This function creates the Config table containing the values for all the configuration parameters of
    the simulation. This table will be created after differences are applied to the configuration.

    Table Description:

    This table contains the configuration information for the given simulation.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The Config table object.
    """
    table = Table("Config", metadata,
                  Column("configId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The numeric identifier for the particular configuration entry."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("paramName", String(512), nullable=False,
                         doc="Fully qualified parameter name from the configuration."),
                  Column("paramValue", String(512), nullable=False,
                         doc="Value of the parameter."))

    Index("fk_Config_Session", table.c.Session_sessionId)

    return table

def create_downtime(name, metadata):
    """Create one of the Downtime tables.

    This function creates one of the Downtime tables.

    Parameters
    ----------
    name : str
        The name of the downtime table.
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        One of the Downtime table objects.
    """
    table = Table(name, metadata,
                  Column("night", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The starting night for the downtime."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("duration", Integer, nullable=False, doc="The length of the downtime (units=days)."),
                  Column("activity", String(128), nullable=False,
                         doc="The description of the activity associated with the downtime."))

    Index("fk_{}_night1".format(name), table.c.night)

    return table

def create_field(metadata):
    """Create Field table.

    This function creates the Field table from the sky tessellation.

    Table Description:

    This table contains all the coordinate information for the "visiting" fields. The field centers
    are determined from a tessellation (or tiling) of the celestial sphere which results in a
    closest-packed set of 5280 hexagons and 12 pentagons inscribed in circular fields having a
    3.5-degree diameter
    (R. H. Hardin, N. J. A. Sloane and W. D. Smith, *Tables of spherical codes with icosahedral symmetry*,
    published electronically at http://NeilSloane.com/icosahedral.codes/).

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The Field table object.
    """
    table = Table("Field", metadata,
                  Column("fieldId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for the given field."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("fov", Float, nullable=False, doc="The field of view of the field (units=degrees)."),
                  Column("ra", Float, nullable=False,
                         doc="The Right Ascension of the field (units=degrees)."),
                  Column("dec", Float, nullable=False, doc="The Declination of the field (units=degrees)."),
                  Column("gl", Float, nullable=False,
                         doc="The Galactic Longitude of the field (units=degrees)."),
                  Column("gb", Float, nullable=False,
                         doc="The Galactic Latitude of the field (units=degrees)."),
                  Column("el", Float, nullable=False,
                         doc="The Ecliptic Longitude of the field (units=degrees)."),
                  Column("eb", Float, nullable=False,
                         doc="The Ecliptic Latitude of the field (units=degrees)."))

    Index("field_fov", table.c.fieldId, table.c.fov)
    Index("fov_gl_gb", table.c.fov, table.c.gl, table.c.gb)
    Index("fov_el_eb", table.c.fov, table.c.el, table.c.eb)
    Index("fov_ra_dec", table.c.fov, table.c.ra, table.c.dec)

    return table

def create_observation_exposures(metadata):
    """Create ObsExposures table.

    This function creates the ObsExposures table from the observation exposures.

    Table Description:

    This table contains all of the individual exposure information for each visit in the
    :ref:`database-tables-obshistory` table. The number of exposures in a visit is determined
    by the visit target's exposure cadence.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The ObsExposure table object.
    """
    table = Table("ObsExposures", metadata,
                  Column("exposureId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for an observation exposure."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("exposureNum", Integer, nullable=False,
                         doc="The order number of the exposure. Starts at 1 for a set of exposures."),
                  Column("exposureStartTime", Float, nullable=False,
                         doc="The UTC start time of the particular exposure (units=seconds)."),
                  Column("exposureTime", Float, nullable=False,
                         doc="The duration of the exposure (units=seconds)."),
                  Column("ObsHistory_observationId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the ObsHistory table."))

    Index("obs_expId_expNum", table.c.exposureId, table.c.exposureNum)
    Index("fk_ObsHistory_observationId", table.c.ObsHistory_observationId)

    return table

def create_observation_history(metadata):
    """Create ObsHistory table.

    This function creates the ObsHistory table for tracking all the observations performed
    by the Sequencer in the simulation run.

    Table Description:

    This table keeps a record of each visit made by the observatory during a simulated survey.
    Multiple proposals can be associated with a single visit leading to duplicate entries in
    this table.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The ObsHistory table object.
    """
    table = Table("ObsHistory", metadata,
                  Column("observationId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for an observation entry."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("night", Integer, nullable=False,
                         doc="The night in the survey for the observation. Starts from 1."),
                  Column("observationStartTime", Float, nullable=False,
                         doc="The UTC start time for the observation (units=seconds). This occurs after the "
                             "slew but before the first exposure."),
                  Column("observationStartMJD", Float, nullable=False,
                         doc="The Modified Julian Date at observation start (units=seconds)."),
                  Column("observationStartLST", Float, nullable=False,
                         doc="The Local Sidereal Time at observation start (units=degrees)"),
                  Column("TargetHistory_targetId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the TargetHistory entry."),
                  Column("Field_fieldId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the Field table."),
                  Column("groupId", Integer, nullable=False,
                         doc="Group Id for the observation. This is non-zero and repeated for field/filter "
                             "combinations collected in sets of N (tuples or sequences). It is zero when N "
                             "equal one."),
                  Column("filter", String(1), nullable=False,
                         doc="The one character name for the band filter."),
                  Column("ra", Float, nullable=False,
                         doc="The Right Ascension of the observation (units=degrees)."),
                  Column("dec", Float, nullable=False,
                         doc="The Declination of the observation (units=degrees)."),
                  Column("angle", Float, nullable=False,
                         doc="The Position Angle of the observation (units=degrees)."),
                  Column("altitude", Float, nullable=False,
                         doc="The altitude of the observation (units=degrees)."),
                  Column("azimuth", Float, nullable=False,
                         doc="The azimuth of the observation (units=degrees)"),
                  Column("numExposures", Integer, nullable=False,
                         doc="The number of exposures taken for the observation."),
                  Column("visitTime", Float, nullable=False,
                         doc="The total time for the observation (units=seconds) including exposure, "
                             "shutter and readout time."),
                  Column("visitExposureTime", Float, nullable=False,
                         doc="The sum of all the exposure times for the observation (units=seconds). No "
                             "shutter and readout time included."),
                  Column("airmass", Float, nullable=False, doc="The airmass of the observation field."),
                  Column("skyBrightness", Float, nullable=False,
                         doc="The calculated skybrightness for the observation field."),
                  Column("cloud", Float, nullable=False,
                         doc="The fraction of clouds present (0: none to 1: total)."),
                  Column("seeingFwhm500", Float, nullable=False,
                         doc="The full-width at half-maximum for seeing observations at 500 nm at zenith."),
                  Column("seeingFwhmGeom", Float, nullable=False,
                         doc="\"Geometrical\" full-width at half-maximum, actual half width at maximum "
                         "brightness. This can be used to represent the FWHM of a double Gaussian "
                         "representing the physical width of a PSF."),
                  Column("seeingFwhmEff", Float, nullable=False,
                         doc="\"Effective\" full-width at half-maximum, typically ~15% larger than "
                         "seeingFwhmGeom. This can be used to calculate SNR for point sources, using "
                         "seeingFwhmEff as the FWHM of a single Gaussian describing the PSF."),
                  Column("fiveSigmaDepth", Float, nullable=False,
                         doc="The magnitude of a point source that would be a 5-sigma detection "
                             "(units=magnitudes)"),
                  Column("moonRA", Float, nullable=False,
                         doc="The right-ascension (units=degrees) of the moon."),
                  Column("moonDec", Float, nullable=False,
                         doc="The declination (units=degrees) of the moon."),
                  Column("moonAlt", Float, nullable=False,
                         doc="The altitude (units=degrees) of the moon."),
                  Column("moonAz", Float, nullable=False,
                         doc="The azimuth (units=degrees) of the moon."),
                  Column("moonDistance", Float, nullable=False,
                         doc="The distance (units=degrees) between the moon and the observation field."),
                  Column("moonPhase", Float, nullable=False,
                         doc="The phase of the moon."),
                  Column("sunRA", Float, nullable=False,
                         doc="The right-ascension (units=degrees) of the sun."),
                  Column("sunDec", Float, nullable=False,
                         doc="The declination (units=degrees) of the sun."),
                  Column("sunAlt", Float, nullable=False,
                         doc="The altitude (units=degrees) of the sun."),
                  Column("sunAz", Float, nullable=False,
                         doc="The azimuth (units=degrees) of the sun."),
                  Column("solarElong", Float, nullable=False,
                         doc="The solar elongation (units=degrees) of the observation field (distance "
                             "between it and sun)."),
                  Column("slew_time", Float, nullable=False,
                         doc="The slew time (units=seconds)."),
                  Column("note", String(40), nullable=False,
                         doc="A note about the observations."),
                  )

    Index("o_filter", table.c.filter)
    Index("fk_ObsHistory_Session1", table.c.Session_sessionId)
    Index("fk_ObsHistory_Field1", table.c.Field_fieldId)
    Index("fk_ObsHistory_Target1", table.c.TargetHistory_targetId)

    return table

def create_observation_proposal_history(metadata):
    """Create the ObsProposalHistory table.

    This function creates the ObsProposalHistory table for listing all proposals that are assigned to
    a given observation.

    Table Description:

    This table records all of the proposals and proposal information for a given observation.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The ObsProposalHistory table object.
    """
    return create_proposal_history("ObsProposalHistory", metadata)

def create_proposal(metadata):
    """Create the Proposal table.

    This function creates the Proposal table for listing the active proposals.

    Table Description:

    This table records all of the active science proposals.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The Proposal table object.
    """
    table = Table("Proposal", metadata,
                  Column("propId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The numeric identifier for the particular proposal."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("propName", String(50), nullable=False, doc="The name of the science proposal."),
                  Column("propType", String(50), nullable=False, doc="The type of the science proposal."))

    Index("fk_Proposal_Session1", table.c.Session_sessionId)

    return table

def create_proposal_field(metadata):
    """Create the ProposalField table.

    This function creates the ProposalField table for listing the fields for
    each science proposal.

    Table Description:

    This table lists all of the field Ids associated with a given science proposal.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The ProposalField table object.
    """
    table = Table("ProposalField", metadata,
                  Column("propFieldId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The numeric identifier for the particular proposal field."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("Proposal_propId", Integer, nullable=False, doc="The science proposal identifier."),
                  Column("Field_fieldId", Integer, nullable=False, doc="The field identifier."))

    Index("fk_Proposal_Field_Session1", table.c.Session_sessionId)
    Index("fk_Proposal_Field_Proposal_Id1", table.c.Proposal_propId)
    Index("fk_Proposal_Field_Field_Id1", table.c.Field_fieldId)

    return table

def create_proposal_history(name, metadata):
    """Create one of the ProposalHistory tables.

    This function creates one of the ProposalHistory tables.

    Parameters
    ----------
    name : str
        The name of the proposal history table.
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        One of the ProposalHistory table objects.
    """
    if "Obs" in name:
        fkc_name = "ObsHistory_observationId"
        index_key_name = "ObsHistory1"
        help_tag = "observation"
    if "Target" in name:
        fkc_name = "TargetHistory_targetId"
        index_key_name = "TargetHistory1"
        help_tag = "target"

    table = Table(name, metadata,
                  Column("propHistId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The numeric identifier for the particular proposal history entry."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("Proposal_propId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the Proposal table."),
                  Column("proposalValue", Float, nullable=False,
                         doc="The value (need + bonus) of the {} assigned by a particular "
                             "proposal.".format(help_tag)),
                  Column("proposalNeed", Float, nullable=False,
                         doc="The need of the {} assigned by a particular proposal.".format(help_tag)),
                  Column("proposalBonus", Float, nullable=False,
                         doc="The bonus of the {} assigned by a particular proposal.".format(help_tag)),
                  Column("proposalBoost", Float, nullable=False,
                         doc="The time-balancing boost assigned by a particular proposal."),
                  Column(fkc_name, Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the "
                             "{} table.".format(index_key_name.rstrip("1"))))

    index_name = "fk_{}_{}".format(name, index_key_name)
    if "Obs" in name:
        Index(index_name, table.c.ObsHistory_observationId, table.c.Session_sessionId)
    if "Target" in name:
        Index(index_name, table.c.TargetHistory_targetId, table.c.Session_sessionId)

    return table

def create_scheduled_downtime(metadata):
    """Create the ScheduledDowntime table.

    This function creates the ScheduledDowntime table for listing the scheduled
    downtime during the survey.

    Table Description:

    This table records all of the scheduled downtime for the entire survey (plus an extra 10 years). The
    actual downtime used in the simulation maybe different depending on the length of the simulation.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The ScheduledDowntime table object.
    """
    return create_downtime("ScheduledDowntime", metadata)

def create_session(metadata, autoincrement=True, session_id_start=1000):
    """Create Session table.

    This function creates the Session table for tracking the various simulations run. For MySQL, it adds
    a post-create command to set the lower limit of the auto increment value.

    Table Description:

    This table contains the log of all simulations (MySQL) or a single simulation (SQLite). Simulation
    runs are identified by the combination of the hostname and session Id: *sessionHost_sessionId*.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.
    autoincrement : bool
        A flag to set auto incrementing on the sessionID column.
    session_id_start : int
        A new starting session Id for counting new simulations.

    Returns
    -------
    sqlalchemy.Table
        The Session table object.
    """
    table = Table("Session", metadata,
                  Column("sessionId", Integer, primary_key=True, autoincrement=autoincrement, nullable=False,
                         doc="Numeric identifier for the current simulation instance."),
                  Column("sessionUser", String(80), nullable=False,
                         doc="Computer username of the simulation runner."),
                  Column("sessionHost", String(80), nullable=False,
                         doc="Computer hostname where the simulation was run."),
                  Column("sessionDate", DATETIME, nullable=False,
                         doc="The UTC date/time of the simulation start."),
                  Column("version", String(25), nullable=True, doc="The version number of the SOCS code."),
                  Column("runComment", String(200), nullable=True,
                         doc="A description of the simulation setup."))

    Index("s_host_user_date_idx", table.c.sessionUser, table.c.sessionHost, table.c.sessionDate, unique=True)

    alter_table = DDL("ALTER TABLE %(table)s AUTO_INCREMENT={};".format(session_id_start))
    event.listen(table, 'after_create', alter_table.execute_if(dialect='mysql'))

    return table

def create_slew_history(metadata):
    """Create SlewHistory table.

    This function creates the SlewHistory table for tracking all the general slew information
    performed by the observatory.

    Table Description:

    This table contains the basic slew information for each visit.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The SlewHistory table object.
    """
    table = Table("SlewHistory", metadata,
                  Column("slewCount", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for a particular slew."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("startDate", Float, nullable=False,
                         doc="The UTC date for the start of the slew (units=seconds)."),
                  Column("endDate", Float, nullable=False,
                         doc="The UTC date for the end of the slew (units=seconds)."),
                  Column("slewTime", Float, nullable=False, doc="The duration of the slew (units=seconds)."),
                  Column("slewDistance", Float, nullable=False,
                         doc="The angular distance traveled on the sky of the slew (units=degrees)."),
                  Column("ObsHistory_observationId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the ObsHistory table."))

    Index("fk_SlewHistory_ObsHistory1", table.c.ObsHistory_observationId)

    return table

def create_slew_activities(metadata):
    """Create the SlewActivities table.

    This function creates the SlewActivities table for tracking the activities during a slew.

    Table Description:

    This table contains all the activities for a given visit's slew. The *SlewHistory_slewCount* column
    points to a given slew in the :ref:`database-tables-slewhistory` table.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The SlewActivities table object.
    """
    table = Table("SlewActivities", metadata,
                  Column("slewActivityId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for a particular slew activity entry."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("activity", String(20), nullable=False,
                         doc="Short description of the slew activity."),
                  Column("activityDelay", Float, nullable=False,
                         doc="The delay time of the slew activity (units=seconds)."),
                  Column("inCriticalPath", String(10), nullable=False,
                         doc="True is slew activity is in the critical path and False if not."),
                  Column("SlewHistory_slewCount", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the SlewHistory table."))

    Index("fk_SlewActivites_SlewHistory1_idx", table.c.SlewHistory_slewCount)

    return table

def create_slew_final_state(metadata):
    """Create the SlewFinalState tables.

    This function creates the SlewFinalState table for tracking the state of the observatory after slewing.

    Table Description:

    This table contains all of the final state information from a given visit's slew. The state
    information is collected after the slew has completed, but before the visit activity has started.
    The *SlewHistory_slewCount* column points to a given slew in the :ref:`database-tables-slewhistory` table.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The SlewFinalState table object.
    """
    return create_slew_state("SlewFinalState", metadata)

def create_slew_initial_state(metadata):
    """Create the SlewInitialState tables.

    This function creates the SlewInitialState table for tracking the state of the observatory before slewing.

    Table Description:

    This table contains all of the initial state information from a given visit's slew. The state
    information is collected before the slew to the given target has started. The *SlewHistory_slewCount*
    column points to a given slew in the :ref:`database-tables-slewhistory` table.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The SlewInitialState table object.
    """
    return create_slew_state("SlewInitialState", metadata)

def create_slew_maxspeeds(metadata):
    """Create the SlewMaxSpeeds table.

    This function creates the SlewMaxSpeeds table for tracking the maximum speeds of observatory
    achieved during a slew.

    Table Description:

    This table contains all of the maximum speeds obtained by the telescope, dome and rotator
    during a given visit's slew. The *SlewHistory_slewCount* column points to a given slew in
    the :ref:`database-tables-slewhistory` table.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The SlewMaxSpeeds table object.
    """
    table = Table("SlewMaxSpeeds", metadata,
                  Column("slewMaxSpeedId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for a particular slew max speeds entry."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("domeAltSpeed", Float, nullable=False,
                         doc="The maximum dome altitude speed achieved during the slew "
                             "(units=degrees/second)."),
                  Column("domeAzSpeed", Float, nullable=False,
                         doc="The maximum dome azimuth speed achieved during the slew "
                             "(units=degrees/second)."),
                  Column("telAltSpeed", Float, nullable=False,
                         doc="The maximum telescope altitude speed achieved during the slew "
                             "(units=degrees/second)."),
                  Column("telAzSpeed", Float, nullable=False,
                         doc="The maximum telescope azimuth speed achieved during the slew "
                             "(units=degrees/second)."),
                  Column("rotatorSpeed", Float, nullable=False,
                         doc="The maximum rotator speed achieved during the slew "
                             "(units=degrees/second)."),
                  Column("SlewHistory_slewCount", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the SlewHistory table."))

    Index("fk_SlewMaxSpeeds_SlewHistory1", table.c.SlewHistory_slewCount)

    return table

def create_slew_state(name, metadata):
    """Create one of the SlewState tables.

    This function creates one of the SlewState tables.

    Parameters
    ----------
    name : str
        The name of the slew state table.
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        One of the SlewState table objects.
    """
    table = Table(name, metadata,
                  Column("slewStateId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for a particular slew state."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("slewStateDate", Float, nullable=False,
                         doc="The UTC date/time of the slew state information (units=seconds)"),
                  Column("targetRA", Float, nullable=False,
                         doc="Current target Right Ascension (units=degrees)."),
                  Column("targetDec", Float, nullable=False,
                         doc="Current target Declination (units=degrees)."),
                  Column("tracking", String(10), nullable=False,
                         doc="Whether or not the telescope is tracking the sky."),
                  Column("altitude", Float, nullable=False,
                         doc="Current target altitude (units=degrees)."),
                  Column("azimuth", Float, nullable=False,
                         doc="Current target azimuth (units=degrees)"),
                  Column("paraAngle", Float, nullable=False,
                         doc="Current parallactic angle of the rotator (units=degrees)."),
                  Column("domeAlt", Float, nullable=False,
                         doc="Current dome altitude (units=degrees)."),
                  Column("domeAz", Float, nullable=False,
                         doc="Current dome azimuth (units=degrees)."),
                  Column("telAlt", Float, nullable=False,
                         doc="Current telescope altitude (units=degrees)."),
                  Column("telAz", Float, nullable=False,
                         doc="Current telescope azimuth (units=degrees)."),
                  Column("rotTelPos", Float, nullable=False,
                         doc="Current position of the telescope rotator (units=degrees)."),
                  Column("rotSkyPos", Float, nullable=False,
                         doc="Current position of the camera on the sky (units=degrees)."),
                  Column("filter", String(1), nullable=False,
                         doc="Band filter for the recorded slew state."),
                  Column("SlewHistory_slewCount", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the SlewHistory table."))

    Index("fk_{}_SlewHistory1".format(name), table.c.SlewHistory_slewCount)

    return table

def create_target_exposures(metadata):
    """Create TargetExposures table.

    This function creates the TargetExposures table from the target exposures.

    Table Description:

    This table contains all of the individual exposure information for each target in the
    :ref:`database-tables-targethistory` table. The number of exposures for a target is determined
    by the requesting proposal's exposure cadence.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The Target Exposure table object.
    """
    table = Table("TargetExposures", metadata,
                  Column("exposureId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for a particular target exposure."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("exposureNum", Integer, nullable=False,
                         doc="The order number of the exposure. Starts at 1 for a set of exposures."),
                  Column("exposureTime", Float, nullable=False,
                         doc="The requested duration of the exposure (units=seconds)."),
                  Column("TargetHistory_targetId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the TargetHistory table."))

    Index("expId_expNum", table.c.exposureId, table.c.exposureNum)
    Index("fk_TargetHistory_targetId", table.c.TargetHistory_targetId)

    return table

def create_target_history(metadata):
    """Create TargetHistory table.

    This function creates the TargetHistory table for tracking all the requested targets from
    the Scheduler in the simulation run.

    Table Description:

    This table keeps a record of the information from the requested targets during a simulated survey.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The TargetHistory table object.
    """
    table = Table("TargetHistory", metadata,
                  Column("targetId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="Numeric identifier for a particular target request."),
                  Column("Session_sessionId", Integer, primary_key=True, autoincrement=False, nullable=False,
                         doc="The simulation run session Id."),
                  Column("Field_fieldId", Integer, nullable=False,
                         doc="Numeric identifier that relates to an entry in the Field table."),
                  Column("groupId", Integer, nullable=False,
                         doc="Group Id for the target. This is non-zero and repeated for field/filter "
                             "combinations collected in sets of N (tuples or sequences). It is zero when N "
                             "equal one."),
                  Column("filter", String(1), nullable=False,
                         doc="Band filter requested by the target."),
                  Column("requestTime", Float, nullable=False,
                         doc="The UTC time (units=seconds) when all of the associated information (airmass "
                             "etc.) was calculated for the target."),
                  Column("requestMJD", Float, nullable=False,
                         doc="The Modified Julian Date (units=seconds) when all of the associated "
                             "information (airmass etc.) was calculated for the target."),
                  Column("ra", Float, nullable=False,
                         doc="Right Ascension of the requested target (units=degrees)."),
                  Column("dec", Float, nullable=False,
                         doc="Declination of the requested target (units=degrees)."),
                  Column("angle", Float, nullable=False,
                         doc="Difference between parallactic angle and rotator angle (units=degrees)."),
                  Column("numExposures", Integer, nullable=False,
                         doc="Number of exposures for the requested target."),
                  Column("requestedExpTime", Float, nullable=False,
                         doc="The total duration of all requested exposures (units=seconds)."),
                  Column("airmass", Float, nullable=False, doc="The airmass of the target."),
                  Column("skyBrightness", Float, nullable=False,
                         doc="The calculated skybrightness for the target."),
                  Column("cloud", Float, nullable=False,
                         doc="The fraction of clouds (0: none to 1: total) for the target."),
                  Column("seeing", Float, nullable=False,
                         doc="The seeing (units=arcseconds) for the target."),
                  Column("slewTime", Float, nullable=False,
                         doc="The calculated slew time (units=seconds) for the target."),
                  Column("cost", Float, nullable=False,
                         doc="The calculated cost for the target."),
                  Column("rank", Float, nullable=False,
                         doc="The rank of the target for the associated proposal. If more than one "
                             "proposal, this is a coadded value."),
                  Column("propBoost", Float, nullable=False,
                         doc="The calculated time-balancing boost for the target."),
                  Column("numRequestingProps", Integer, nullable=False,
                         doc="The total number of proposals requesting this target. More than one means the "
                             "target was in each proposals winner's list."),
                  Column("moonRA", Float, nullable=False,
                         doc="The right-ascension (units=degrees) of the moon."),
                  Column("moonDec", Float, nullable=False,
                         doc="The declination (units=degrees) of the moon."),
                  Column("moonAlt", Float, nullable=False,
                         doc="The altitude (units=degrees) of the moon."),
                  Column("moonAz", Float, nullable=False,
                         doc="The azimuth (units=degrees) of the moon."),
                  Column("moonDistance", Float, nullable=False,
                         doc="The distance (units=degrees) between the moon and the target."),
                  Column("moonPhase", Float, nullable=False,
                         doc="The phase of the moon."),
                  Column("sunRA", Float, nullable=False,
                         doc="The right-ascension (units=degrees) of the sun."),
                  Column("sunDec", Float, nullable=False,
                         doc="The declination (units=degrees) of the sun."),
                  Column("sunAlt", Float, nullable=False,
                         doc="The altitude (units=degrees) of the sun."),
                  Column("sunAz", Float, nullable=False,
                         doc="The azimuth (units=degrees) of the sun."),
                  Column("solarElong", Float, nullable=False,
                         doc="The elongation (units=degrees) of the sun."))

    Index("t_filter", table.c.filter)
    Index("fk_TargetHistory_Session1", table.c.Session_sessionId)
    Index("fk_TargetHistory_Field1", table.c.Field_fieldId)

    return table

def create_target_proposal_history(metadata):
    """Create the TargetProposalHistory table.

    This function creates the TargetProposalHistory table for listing all proposals that are assigned to
    a given target.

    Table Description:

    This table records all of the proposals and proposal information for a given target.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The TargetProposalHistory table object.
    """
    return create_proposal_history("TargetProposalHistory", metadata)

def create_unscheduled_downtime(metadata):
    """Create the UnscheduledDowntime table.

    This function creates the UnscheduledDowntime table for list the unscheduled
    downtime during the survey.

    Table Description:

    This table records all of the unscheduled downtime for the entire survey (plus an extra 10 years). The
    actual downtime used in the simulation maybe different depending on the length of the simulation.

    Parameters
    ----------
    metadata : sqlalchemy.MetaData
        The database object that collects the tables.

    Returns
    -------
    sqlalchemy.Table
        The UnscheduledDowntime table object.
    """
    return create_downtime("UnscheduledDowntime", metadata)
