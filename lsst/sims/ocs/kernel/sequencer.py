import logging

from ..setup.log import LoggingLevel

class Sequencer(object):
    """Handle the observation of a target.

    This class is responsible for taking a target from the Scheduler and performing the necessary steps to
    make an astronomical observation. It is then responsible for handing that observation back.
    """

    def __init__(self):
        """Initialize the class.
        """
        self.targets_received = 0
        self.observations_made = 0
        self.observation = None
        self.log = logging.getLogger("kernel.Sequencer")
        # Variables that will disappear as more functionality is added.
        self.slew_time = (6.0, "seconds")
        self.visit_time = (34.0, "seconds")

    def initialize(self, sal):
        """Perform initialization steps.

        This function handles gathering the observation telemetry topic from the given :class:`SalManager`.

        Args:
            sal (SalManager): A :class:`SalManager` instance.
        """
        self.observation = sal.set_publish_topic("observationTest")

    def finalize(self):
        """Perform finalization steps.

        This function logs the number or targets received and observations made.
        """
        self.log.info("Number of targets received: {}".format(self.targets_received))
        self.log.info("Number of observations made: {}".format(self.observations_made))

    def observe_target(self, target, th):
        """Observe the given target.

        This function performs the necessary steps to observe the given target. The current steps are:
          * Update the simulation time after "slewing"
          * Copy target information to observation
          * Update the simulation time after "visit"

        Args:
            target (struct): A target telemetry topic containing the current target information.
            th (TimeHandler): An instance of the :class:`TimeHandler`.

        Returns:
            struct: An observation telemetry topic containing the observed target parameters.
        """
        self.log.log(LoggingLevel.EXTENSIVE.value, "Received target {}".format(target.targetId))
        self.targets_received += 1

        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Starting observation {} for target {}.".format(self.observations_made,
                                                                     target.targetId))
        th.update_time(*self.slew_time)

        self.observation.observationId = self.observations_made
        self.observation.observationTime = th.current_timestamp
        self.observation.targetId = target.targetId
        self.observation.fieldId = target.fieldId
        self.observation.filter = target.filter
        self.observation.ra = target.ra
        self.observation.dec = target.dec
        self.observation.num_exposures = target.num_exposures

        th.update_time(*self.visit_time)
        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Observation {} completed at {}.".format(self.observations_made,
                                                              th.current_timestring))
        self.observations_made += 1

        return self.observation
