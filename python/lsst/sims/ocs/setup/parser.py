import argparse

from lsst.sims.ocs import __version__

__all__ = ["create_parser"]

def create_parser():
    """Create the argument parser for the main driver script.
    """
    description = ["The Operations Simulator v4 is designed to operate the LSST Scheduler via"]
    description.append("the Simulated Observatory Control System (SOCS).")

    parser = argparse.ArgumentParser(usage="opsim4 [options]",
                                     description=" ".join(description),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-c", "--startup-comment", dest="startup_comment", nargs='*',
                        default="No comment was entered.",
                        help="Enter a comment for the simulation session. NOTE: Do not use an equal sign "
                             "with the long option!")
    parser.add_argument("--frac-duration", dest="frac_duration", type=float, default=-1,
                        help="Temporary flag to set the fractional duration for the survey in units of "
                        "years.")
    parser.add_argument("--no-sched", dest="no_scheduler", action="store_true",
                        help="Flag to make program not wait for Scheduler.")
    parser.add_argument("--scheduler-timeout", dest="scheduler_timeout", type=int, default=60,
                        help="Override the 60 second DDS message timeouts in the Scheduler main loop.")
    parser.add_argument("--profile", dest="profile", action="store_true", help="Run the profiler on SOCS and"
                        "Scheduler code.")

    sqlite_group_descr = ["This group of arguments is for dealing with a SQLite database."]
    sqlite_group = parser.add_argument_group("sqlite", " ".join(sqlite_group_descr))
    sqlite_group.add_argument("--save-dir", dest="sqlite_save_dir", help="A directory to save all the "
                              "SQLite simulation output including session tracking database.")
    sqlite_group.add_argument("--session-save-dir", dest="sqlite_session_save_dir",
                              help="An alternate directory to save just the SQLite session "
                              "tracking database.")
    sqlite_group.add_argument("-s", "--session-id-start", dest="session_id_start",
                              help="Set a new value for the starting session ID.")

    tracking_group_descr = ["This group of arguments controls the tracking of the simulation session."]
    track_grp = parser.add_argument_group("tracking", " ".join(tracking_group_descr))
    track_grp.add_argument("-t", "--track", dest="track_session", action="store_true",
                           help="Flag to track the current simulation in the central OpSim tracking "
                           "database.")
    track_grp.add_argument("--tracking-db", dest="tracking_db", help="Option to set an alternative URL "
                           "for the OpSim tracking database.")
    track_grp.add_argument("--session-code", dest="session_code", choices=["science", "code_dev", "system",
                                                                           "engineering"],
                           default="science", help="Set the type of simulation session for "
                           "the OpSim tracking database.")

    config_group_descr = ["This group of arguments controls the configuration of the simulated survey."]
    conf_grp = parser.add_argument_group("config", " ".join(config_group_descr))
    conf_grp.add_argument("--config", dest="config", nargs='*', help="Provide a set of override files for "
                          "the survey configuration. If a directory is provided, it is assumed all of the "
                          "configuration files reside there.")
    conf_grp.add_argument("--save-config", dest="save_config", action="store_true",
                          help="If set, a config_<session Id> directory that will contain the "
                          "saved configuration will be created at the location of --save-config-dir.")
    conf_grp.add_argument("--config-save-path", dest="config_save_path", default='$PWD',
                          help="Set the path to the configuration save directory. The default "
                          "will be to save in the execution directory.")

    log_group_descr = ["This group of arguments controls the logging of the application."]
    logging = parser.add_argument_group("logging", " ".join(log_group_descr))
    logging.add_argument("-l", "--log-path", dest="log_path", default="log",
                         help="Set the path to write log files for the application. If none, is provided, "
                         "the application will assume a directory named log in the running directory.")
    logging.add_argument("-v", "--verbose", dest="verbose", action='count', default=0,
                         help="Set the verbosity for the console and file logging. Default is to log nothing "
                         "to the console and debug to the log file. More than two levels are ignored for the "
                         "console and more than five are ignored for the log file. NOTE: Please do not use "
                         "more than three flags for long runs as it will generate LOTS of output.")

    return parser
