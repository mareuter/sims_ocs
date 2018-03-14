from builtins import object
from builtins import range
import logging

from lsst.sims.ocs.environment.scheduled_downtime import ScheduledDowntime
from lsst.sims.ocs.environment.unscheduled_downtime import UnscheduledDowntime
from lsst.sims.ocs.setup import LoggingLevel

class DowntimeHandler(object):
    """Coordinate the handling of all the downtime information.

    This class handles the coordination between the scheduled and unscheduled
    downtime information.

    Attributes
    ----------
    scheduled : :class:`.ScheduledDowntime`
        The scheduled downtime information instance.
    unscheduled : :class:`.UnscheduledDowntime`
        The unscheduled downtime information instance.
    current_scheduled : tuple or None
        The set of current scheduled downtime information.
    current_unscheduled : tuple or None
        The set of current unscheduled downtime information.
    downtime_days : set
        The holder for the list of downtime days.
    log : Logger
        The handle for the logger.
    """

    def __init__(self):
        """Initialize the class.
        """
        self.scheduled = ScheduledDowntime()
        self.unscheduled = UnscheduledDowntime()
        self.current_scheduled = None
        self.current_unscheduled = None
        self.downtime_days = set()
        self.log = logging.getLogger("kernel.DowntimeHandler")

    def downtime_range(self, dt):
        """Get the downtime day range and start night.

        Parameters
        ----------
        dt : tuple
            The collection of downtime information (start, length, description)

        Returns
        -------
        set, int
            The list of downtime days as a set and the downtime start night.
        """
        if dt is None:
            return set(), -1
        else:
            return set(list(range(dt[0], dt[0] + dt[1]))), dt[0]

    def initialize(self, config):
        """Perform initialization steps.

        Parameters
        ----------
        config : :class:`.Downtime`
            Downtime configuration instance.
        """
        self.scheduled.initialize(config.scheduled_downtime_db)
        self.unscheduled.initialize(config.unscheduled_downtime_use_random_seed)
        config.unscheduled_downtime_random_seed = self.unscheduled.seed

    def get_downtime(self, night):
        """Determine if there is downtime for the given night.

        This function looks at the given downtime and determines if there are any
        downtime days. If downtime is identified, then this number will return a
        decreasing number of days until no more downtime if found.

        Parameters
        ----------
        night : int
            The night to check the downtime information for.

        Returns
        -------
        int
            The number of downtime nights.
        """
        self.update()
        try:
            self.downtime_days.remove(night)
            return len(self.downtime_days) + 1
        except KeyError:
            return 0

    def update(self):
        """Update the lsit of downtime days.
        """
        if len(self.downtime_days):
            return

        if self.current_scheduled is None:
            self.current_scheduled = self.scheduled()
        if self.current_unscheduled is None:
            self.current_unscheduled = self.unscheduled()

        if self.current_scheduled is None and self.current_unscheduled is None:
            return

        usdt, usdt_start = self.downtime_range(self.current_unscheduled)
        sdt, sdt_start = self.downtime_range(self.current_scheduled)

        if sdt_start < usdt_start:
            if sdt.isdisjoint(usdt):
                self.downtime_days.update(sdt)
                self.current_scheduled = None
            else:
                if sdt.issuperset(usdt):
                    self.log.log(LoggingLevel.EXTENSIVE.value,
                                 "Completely overlapping unscheduled downtime")
                else:
                    partial = len(sdt.intersection(usdt))
                    self.log.log(LoggingLevel.EXTENSIVE.value,
                                 "Partial overlapping unscheduled downtime: {}".format(partial))

                self.downtime_days.update(sdt)
                self.downtime_days.update(usdt)
                self.current_scheduled = None
                self.current_unscheduled = None

        if usdt_start < sdt_start:
            if usdt.isdisjoint(sdt):
                self.downtime_days.update(usdt)
                self.current_unscheduled = None
            else:
                if usdt.issuperset(sdt):
                    self.log.log(LoggingLevel.EXTENSIVE.value,
                                 "Completely overlapping scheduled downtime")
                else:
                    partial = len(usdt.intersection(sdt))
                    self.log.log(LoggingLevel.EXTENSIVE.value,
                                 "Partial overlapping scheduled downtime: {}".format(partial))

                self.downtime_days.update(sdt)
                self.downtime_days.update(usdt)
                self.current_scheduled = None
                self.current_unscheduled = None

        if sdt_start == usdt_start:
            self.downtime_days.update(sdt)
            self.downtime_days.update(usdt)
            self.current_scheduled = None
            self.current_unscheduled = None

    def write_downtime_to_db(self, db):
        """Write all the downtime information to the survey database.

        Parameters
        ----------
        db : :class:`.SocsDatabase`
            The instance of the survey database.
        """
        for sched_down in self.scheduled.downtimes:
            db.append_data("scheduled_downtime", sched_down)
        for unsched_down in self.unscheduled.downtimes:
            db.append_data("unscheduled_downtime", unsched_down)
        db.write()
        db.clear_data()
