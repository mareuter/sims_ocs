from builtins import object
from builtins import range
import logging
import math
import time
import collections

from scheduler_config.constants import CONFIG_DIRECTORY

from lsst.ts.astrosky.model import Sun

from lsst.ts.astrosky.model import version as astrosky_version
from lsst.ts.dateloc import version as dateloc_version
from lsst.ts.observatory.model import version as obs_mod_version

from lsst.sims.survey.fields import FieldsDatabase, FieldSelection

from lsst.ts.schedulerConfig import SimulationConfig as SchedulerConfig
from lsst.ts.schedulerConfig import ConfigurationCommunicator
from lsst.sims.ocs.database.tables import write_config, write_field
from lsst.sims.ocs.database.tables import write_proposal, write_proposal_field
from lsst.sims.ocs.environment import CloudInterface, SeeingInterface
from lsst.sims.ocs.kernel import DowntimeHandler, ObsProposalHistory
from lsst.sims.ocs.kernel import ProposalInfo, ProposalFieldInfo
from lsst.sims.ocs.kernel import Sequencer, TargetProposalHistory, TimeHandler
from lsst.sims.ocs.sal import SalManager, topic_strdict
from lsst.sims.ocs.setup import LoggingLevel
from lsst.sims.ocs.utilities.constants import DAYS_IN_YEAR, SECONDS_IN_MINUTE
from lsst.sims.ocs.utilities.socs_exceptions import SchedulerTimeoutError
from lsst.ts.scheduler import SALUtils
from lsst.sims.utils import m5_flat_sed

__all__ = ["Simulator"]

FilterSwap = collections.namedtuple('FilterSwap', 'need_swap filter_to_unmount filter_to_mount')

class Simulator(object):
    """Main class for the survey simulation.

    This class is responsible for setting up, running and shutting down the LSST survey simulation.

    Attributes
    ----------
    opts : argparse.Namespace
        The options returned by the ArgumentParser instance.
    conf : :class:`.SimulationConfig`
        The simulation configuration instance.
    db : :class:`.SocsDatabase`
        The simulation database instance.
    fractional_duration : float
        The length in years for the simulated survey.
    time_handler : :class:`.TimeHandler`
        The simulation time handling instance.
    log : logging.Logger
        The logging instance.
    sal : :class:`.SalManager`
        The instance that manages interactions with the SAL.
    seq : :class:`.Sequencer`
        The sequencer instance.
    dh : :class:`.DowntimeHandler`
        The downtime handler instance.
    conf_comm : :class:`.ConfigurationCommunicator`
        The configuration communicator instance.
    cloud_model : :class:`.CloudModel`
        The cloud model instance.
    seeing_model : :class:`.SeeingModel`
        The seeing model instance.
    field_database : lsst.sims.survey.fields.FieldsDatabase
        The instance of the fields database.
    field_selection : lsst.sims.survey.fields.FieldSelection
        The instance of the field selector.
    """

    def __init__(self, options, database, driver=None):
        """Initialize the class.

        Parameters
        ----------
        options : argparse.Namespace
            The instance returned by ArgumentParser containing the command-line options.
        configuration : :class:`.SimulationConfig`
            The simulation configuration instance.
        database : :class:`.SocsDatabase`
            The simulation database instance.
        """

        self.log = logging.getLogger("kernel.Simulator")
        self.opts = options
        self.conf = SchedulerConfig()
        self.config_path = None
        self.valid_settings = ''

        # Read defaults...
        if driver is None:
            self.conf.load(None)
        elif options.config_path is not None:
            self.conf.load([options.config_path])
            self.config_path = options.config_path
        else:
            self.log.debug('Using default configuration path: {}'.format(str(CONFIG_DIRECTORY)))
            self.conf.load([str(CONFIG_DIRECTORY)])
            self.config_path = str(CONFIG_DIRECTORY)
        self.conf.load_proposals()

        self.db = database

        self.summary_state_enum = {'DISABLE': 0,
                                   'ENABLE': 1,
                                   'FAULT': 2,
                                   'OFFLINE': 3,
                                   'STANDBY': 4}

        self.state_names = ['OFFLINE', 'STANDBY', 'DISABLE', 'ENABLE']
        self.state_transition = [3, 4, 0, 1]
        self.scheduler_state = 3
        # Setup SAL interface communication if needed
        if driver is None:
            self.sal = SalManager()
            self.no_dds_comm = False
        else:
            self.driver = driver
            self.no_dds_comm = True
            self.sal = None

        if self.opts.frac_duration > 0:
            self.fractional_duration = self.opts.frac_duration
        else:
            self.fractional_duration = self.conf.survey.duration

        self.time_handler = None
        self.seq = None

        self.dh = DowntimeHandler()
        self.conf_comm = ConfigurationCommunicator(no_dds_comm=self.no_dds_comm)
        self.sun = Sun()
        self.cloud_interface = None
        self.seeing_interface = None
        self.field_database = FieldsDatabase()
        self.field_selection = FieldSelection()
        self.obs_site_info = None
        self.wait_for_scheduler = not self.opts.no_scheduler
        self.observation_proposals_counted = 1
        self.target_proposals_counted = 1
        self.socs_timeout = 180.0  # seconds
        if self.opts.scheduler_timeout > self.socs_timeout:
            self.socs_timeout = self.opts.scheduler_timeout
            self.conf_comm.socs_timeout = self.socs_timeout

        self.scheduler_summary_state = None
        self.scheduler_valid_settings = None

        self.comm_time = None
        self.target = None
        self.cloud = None
        self.seeing = None
        self.filter_swap = None
        self.interested_proposal = None


    @property
    def duration(self):
        """int: The duration of the simulation in days.
        """
        return math.floor(self.fractional_duration * DAYS_IN_YEAR)

    def end_night(self):
        """Perform actions at the end of the night.
        """
        self.db.write()
        self.seq.end_night()

    def finalize(self):
        """Perform finalization steps.

        This function handles finalization of the :class:`.SalManager` and :class:`.Sequencer` instances.
        """
        self.seq.finalize()
        if not self.no_dds_comm:
            self.sal.finalize()
        self.log.info("Ending simulation")

    def gather_proposal_history(self, phtype, topic):
        """Gather the proposal history from the current target.

        Parameters
        ----------
        phtype : str
            The type of the proposal history (target or observation).
        topic : :class:`scheduler_targetC` or :class:`scheduler_interestedProposalC`
            The topic instance to gather the observation proposal information from.
        """
        if phtype == "observation":
            for i in range(topic.numProposals):
                self.db.append_data("observation_proposal_history",
                                    ObsProposalHistory(self.observation_proposals_counted,
                                                       int(topic.proposalIds[i]),
                                                       topic.proposalValues[i],
                                                       topic.proposalNeeds[i],
                                                       topic.proposalBonuses[i],
                                                       topic.proposalBoosts[i],
                                                       topic.observationId))
                self.observation_proposals_counted += 1
        if phtype == "target":
            for i in range(topic.numProposals):
                self.db.append_data("target_proposal_history",
                                    TargetProposalHistory(self.target_proposals_counted,
                                                          int(topic.proposalId[i]),
                                                          -1,
                                                          -1,
                                                          -1,
                                                          -1,
                                                          topic.targetId))
                self.target_proposals_counted += 1

    def get_target_from_scheduler(self):
        """Get target from scheduler.

        This function provides the mechanism for getting the target from the
        Scheduler. Currently, a while loop is required to do this.
        """
        if self.no_dds_comm:
            target = self.driver.select_next_target().get_copy()
            SALUtils.wtopic_target(self.target, target, self.seq.sky_model)
        else:
            lasttime = time.time()
            while self.wait_for_scheduler:
                rcode = self.sal.manager.getEvent_target(self.target)
                if rcode == 0 and self.target.numExposures != 0:
                    break
                else:
                    tf = time.time()
                    if (tf - lasttime) > self.socs_timeout:
                        raise SchedulerTimeoutError("The Scheduler is not serving targets!")

    def initialize(self):
        """Perform initialization steps.

        This function handles initialization of the :class:`.SalManager` and :class:`.Sequencer` instances and
        gathering the necessary telemetry topics.
        """
        self.log.info("Initializing simulation")
        self.log.info("Simulation Session Id = {}".format(self.db.session_id))
        if not self.no_dds_comm:
            self.sal.initialize()

            self.scheduler_summary_state = self.sal.set_subscribe_logevent("summaryState")
            self.scheduler_valid_settings = self.sal.set_subscribe_logevent("validSettings")

            self.target = self.sal.set_subscribe_logevent("target")
            self.filter_swap = self.sal.set_subscribe_logevent("needFilterSwap")

            self.comm_time = self.sal.set_publish_topic("timeHandler")
            self.cloud = self.sal.set_publish_topic("bulkCloud")
            self.seeing = self.sal.set_publish_topic("seeing")

            self.interested_proposal = self.sal.set_subscribe_topic("interestedProposal")

            # Listen for the scheduler state
            self.log.debug('Configuring the scheduler...')
            # This is len(self.state_transition)-2 so the Scheduler will wait disabled while we finish
            # configuring SOCS
            for i in range(len(self.state_transition)-2):
                self.scheduler_state = self.state_transition[i]
                self.log.debug('Listening for scheduler state...')
                self.listen_scheduler_state()
                self.log.debug('Received state %s ' % self.scheduler_summary_state.summaryState)

                if self.scheduler_summary_state.summaryState == self.summary_state_enum["STANDBY"]:
                    self.log.debug('Listening to valid settings...')
                    self.listen_scheduler_settings()
                    self.valid_settings = self.scheduler_valid_settings.packageVersions.split(',')
                    for setting in self.valid_settings:
                        self.log.debug('{}'.format(setting))

                if self.scheduler_summary_state.summaryState == self.scheduler_state:
                    self.log.debug('Scheduler.state: %s -> %s' % (self.state_names[i],
                                                                  self.state_names[i + 1]))

                    # Ok! Scheduler in expected state
                    # Send command to go to next level
                    self.send_scheduler_to(self.state_transition[i+1])
                else:
                    raise Exception("Could not cycle Scheduler...")

            self.log.debug('Listening for scheduler state...')
            self.listen_scheduler_state()
            self.log.debug('Received state %s ' % self.scheduler_summary_state.summaryState)
            self.scheduler_state = self.scheduler_summary_state.summaryState
            if self.scheduler_state == self.summary_state_enum['DISABLE']:
                # Scheduler is disable! Now is time to initialize the configuration!
                self.log.debug('Scheduler DISABLE, get configuration...')
                self.conf_comm.initialize(self.sal, self.conf)
            else:
                raise Exception("Scheduler %s, expected DISABLE." % self.scheduler_state)

        else:
            from SALPY_scheduler import scheduler_timeHandlerC
            from SALPY_scheduler import scheduler_logevent_targetC
            from SALPY_scheduler import scheduler_bulkCloudC
            from SALPY_scheduler import scheduler_seeingC
            from SALPY_scheduler import scheduler_logevent_needFilterSwapC
            from SALPY_scheduler import scheduler_interestedProposalC

            self.comm_time = scheduler_timeHandlerC()
            self.target = scheduler_logevent_targetC()
            self.cloud = scheduler_bulkCloudC()
            self.seeing = scheduler_seeingC()
            self.filter_swap = scheduler_logevent_needFilterSwapC()
            self.interested_proposal = scheduler_interestedProposalC()
            self.conf_comm.initialize(self.sal, self.conf)

        self.time_handler = TimeHandler(self.conf.survey.start_date)
        self.cloud_interface = CloudInterface(self.time_handler)
        self.seeing_interface = SeeingInterface(self.time_handler)
        self.cloud_interface.initialize(self.conf.environment.cloud_db)
        self.seeing_interface.initialize(self.conf.environment, self.conf.observatory.filters)

        self.seq = Sequencer(self.conf_comm.config.observing_site, self.conf_comm.config.survey.idle_delay,
                             no_dds=self.no_dds_comm)

        self.seq.initialize(self.sal, self.conf_comm.config.observatory)
        self.dh.initialize(self.conf.downtime)
        self.dh.write_downtime_to_db(self.db)

        self.log.info("Finishing simulation initialization")

    def run(self):
        """Run the simulation.
        """
        self.log.info("Starting simulation")

        start_night = 1
        if self.no_dds_comm:
            self.scheduler_state = self.summary_state_enum['ENABLE']  # set scheduler state to enable...
            self.configure_driver()
            # Taking COLD/WARM start into consideration
            if self.driver.night > 0:
                # Not sure I actually need to do this... But I think I do need to wal the timestamp over each night
                for night in range(self.driver.night):
                    self.start_night(night+1)
                    self.driver.update_time(self.time_handler.current_timestamp, night+1)
                    self.driver.start_night(self.time_handler.current_timestamp, night+1)
                    self.log.debug("Timestamp: %.6f", self.time_handler.current_timestamp)
                    delta_t = self.end_of_night - self.time_handler.current_timestamp + 60.
                    self.log.debug("End of night: %.6f (delta_t = %.2f)", self.end_of_night, delta_t)
                    self.time_handler.update_time(delta_t,
                                                  'seconds')
                    self.log.debug("Timestamp: %.6f", self.time_handler.current_timestamp)
                    self.end_night()
                    self.start_day()
                    start_night += 1
        # TODO: Implement COLD/WARM start in dds mode...
        # else:
        #     self.conf_comm.run()

        self.save_configuration()
        self.save_proposal_information()
        self.save_field_information()

        # Note that if you are cold starting and the duration is smaller than the cold start database, you won't
        # run any simulation.
        self.log.debug("Duration = {}".format(self.duration))
        for night in range(start_night, int(self.duration) + 1):
            self.start_night(night)
            if self.no_dds_comm:
                self.driver.update_time(self.time_handler.current_timestamp, night)
                self.driver.start_night(self.time_handler.current_timestamp, night)

            if self.scheduler_state != self.summary_state_enum['ENABLE']:
                self.log.info('Enabling scheduler...')
                self.send_scheduler_to(1)  # enable the scheduler
                self.listen_scheduler_state()
                self.log.debug('Received state %s ' % self.scheduler_summary_state.summaryState)
                self.scheduler_state = self.scheduler_summary_state.summaryState
                if self.scheduler_state != self.summary_state_enum['ENABLE']:
                    # Scheduler not enable! Issue exception
                    raise Exception("Scheduler %s, expected ENABLE." % self.scheduler_state)

            while self.time_handler.current_timestamp < self.end_of_night:

                if not self.no_dds_comm:
                    self.comm_time.timestamp = self.time_handler.current_timestamp
                    self.sal.put(self.comm_time)

                self.log.log(LoggingLevel.EXTENSIVE.value,
                             "Timestamp sent: {:.6f}".format(self.time_handler.current_timestamp))

                observatory_state = self.seq.get_observatory_state(self.time_handler.current_timestamp)
                self.log.log(LoggingLevel.EXTENSIVE.value,
                             "Observatory State: {}".format(topic_strdict(observatory_state)))
                if self.no_dds_comm:
                    self.driver.update_time(self.time_handler.current_timestamp, night)
                    driver_observatory_state = SALUtils.rtopic_observatory_state(observatory_state)
                    self.driver.update_internal_conditions(driver_observatory_state, night)
                    self.cloud.bulkCloud = self.cloud_interface.get_cloud(self.time_handler.time_since_start)
                    self.seeing.seeing = self.seeing_interface.get_seeing(self.time_handler.time_since_start)
                    self.driver.update_external_conditions(self.cloud.bulkCloud, self.seeing.seeing)
                else:
                    self.sal.put(observatory_state)

                    self.cloud_interface.set_topic(self.time_handler, self.cloud)
                    self.sal.put(self.cloud)

                    self.seeing_interface.set_topic(self.time_handler, self.seeing)
                    self.sal.put(self.seeing)

                self.get_target_from_scheduler()

                observation, slew_info, exposure_info = self.seq.observe_target(self.target,
                                                                                self.time_handler)
                # Add a few more things to the observation
                observation.night = night
                elapsed_time = self.time_handler.time_since_given(observation.observationStartTime)
                observation.cloud = self.cloud_interface.get_cloud(elapsed_time)
                seeing_values = self.seeing_interface.calculate_seeing(elapsed_time, observation.filter,
                                                                   observation.airmass)
                observation.seeingFwhm500 = seeing_values[0]
                observation.seeingFwhmGeom = seeing_values[1]
                observation.seeingFwhmEff = seeing_values[2]

                visit_exposure_time = sum([observation.exposureTimes[i]
                                           for i in range(observation.numExposures)])
                observation.fiveSigmaDepth = m5_flat_sed(observation.filter,
                                                           observation.skyBrightness,
                                                           observation.seeingFwhmEff,
                                                           visit_exposure_time,
                                                           observation.airmass)

                observation.note = self.target.note
                observation.numProposals = self.target.numProposals
                for i in range(self.target.numProposals):
                    observation.proposalIds[i] = self.target.proposalId[i]
                self.log.log(LoggingLevel.EXTENSIVE.value, "tx: observation")
                if self.no_dds_comm:
                    driver_observation = SALUtils.rtopic_observation(observation)
                    self.log.debug('%i: %s', observation.numProposals, observation.proposalIds)
                    self.log.debug('%i: %s', driver_observation.num_props,
                                   driver_observation.propid_list)
                    target_list = self.driver.register_observation(driver_observation)
                    SALUtils.wtopic_interestedProposal(self.interested_proposal,
                                                       observation.targetId,
                                                       target_list)
                else:
                    self.sal.put(observation)

                    # Wait for interested proposal information
                    lastconfigtime = time.time()
                    while self.wait_for_scheduler:
                        rcode = self.sal.manager.getNextSample_interestedProposal(self.interested_proposal)
                        if rcode == 0 and self.interested_proposal.numProposals >= 0:
                            self.log.log(LoggingLevel.EXTENSIVE.value, "Received interested proposal.")
                            break
                        else:
                            tf = time.time()
                            if (tf - lastconfigtime) > 5.0:
                                self.log.log(LoggingLevel.EXTENSIVE.value,
                                             "Failed to receive interested proposal due to timeout.")
                                break

                if self.wait_for_scheduler and observation.targetId != -1:
                    self.db.append_data("target_history", self.target)
                    self.db.append_data("observation_history", observation)
                    self.gather_proposal_history("target", self.target)
                    self.gather_proposal_history("observation", self.interested_proposal)
                    for slew_type, slew_data in slew_info.items():
                        self.log.log(LoggingLevel.TRACE.value, "{}, {}".format(slew_type, type(slew_data)))
                        if isinstance(slew_data, list):
                            for data in slew_data:
                                self.db.append_data(slew_type, data)
                        else:
                            self.db.append_data(slew_type, slew_data)
                    for exposure_type in exposure_info:
                        self.log.log(LoggingLevel.TRACE.value, "Adding {} to DB".format(exposure_type))
                        self.log.log(LoggingLevel.TRACE.value,
                                     "Number of exposures being added: "
                                     "{}".format(len(exposure_info[exposure_type])))
                        for exposure in exposure_info[exposure_type]:
                            self.db.append_data(exposure_type, exposure)

            self.end_night()
            if self.no_dds_comm:
                self.driver.end_night(self.time_handler.current_timestamp, night)
            self.start_day()

    def save_configuration(self):
        """Save the configuration information to the DB.
        """
        c = self.conf.config_list()
        c.extend(self.seq.sky_brightness_config())
        if not self.no_dds_comm:
            c.append(("scheduler/version", self.opts.scheduler_version))
        c.append(("dateloc/version", dateloc_version.__version__))
        c.append(("astrosky_model/version", astrosky_version.__version__))
        c.append(("observatory_model/version", obs_mod_version.__version__))
        config_list = [write_config((i + 1, x[0], x[1]), self.db.session_id) for i, x in enumerate(c)]
        self.db.write_table("config", config_list)

    def save_field_information(self):
        """Save the field information to the DB.
        """
        query = self.field_selection.get_all_fields()
        fields = self.field_database.get_field_set(query)
        field_list = [write_field(field, self.db.session_id) for field in sorted(fields)]
        self.db.write_table("field", field_list)

    def save_proposal_information(self):
        """Save the active proposal information to the DB.
        """
        proposals = []
        prop_count = 0
        for i, general in enumerate(self.conf_comm.survey_topology['general']):
            proposals.append(write_proposal(ProposalInfo(i+1, general, "General"),
                                            self.db.session_id))
            prop_count += 1

        for i, sequence in enumerate(self.conf_comm.survey_topology['sequence']):
            proposals.append(write_proposal(ProposalInfo(prop_count+i+1, sequence, "Sequence"),
                                            self.db.session_id))
            prop_count += 1

        self.db.write_table("proposal", proposals)

    def start_day(self):
        """Perform actions at the start of day.

        This function performs all actions at the start of day. This involves:

        * Sending a timestamp to the Scheduler
        * Checking if the Scheduler requests a filter swap
        * Peforming the filter swap if requested
        """
        if not self.no_dds_comm:
            self.comm_time.timestamp = self.time_handler.current_timestamp
            self.sal.put(self.comm_time)
        self.log.debug("Start of day {} at {}".format(self.comm_time.night,
                                                      self.time_handler.current_timestring))
        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Daytime Timestamp sent: {:.6f}".format(self.time_handler.current_timestamp))

        if self.no_dds_comm:
            filter_swap = self.driver.get_need_filter_swap()
            self.filter_swap.needSwap = filter_swap[0]
            self.filter_swap.filterToUnmount = filter_swap[1]
        else:
            self.filter_swap = self.sal.set_subscribe_logevent("needFilterSwap")
            lastconfigtime = time.time()
            while self.wait_for_scheduler:
                rcode = self.sal.manager.getEvent_needFilterSwap(self.filter_swap)
                if rcode == 0 and self.filter_swap.filterToUnmount != '':
                    break
                else:
                    tf = time.time()
                    if (tf - lastconfigtime) > 5.0:
                        break

        self.seq.start_day(self.filter_swap)

    def start_night(self, night):
        """Perform actions at the start of the night.

        Parameters
        ----------
        night : int
            The current night.
        """
        self.log.info("Night {}".format(night))
        self.seq.start_night(night, self.duration)
        self.comm_time.night = night

        self.log.debug("Timestamp: %.6f", self.time_handler.current_timestamp)

        self.seq.sky_model.update(self.time_handler.current_timestamp)
        (set_timestamp,
         rise_timestamp) = self.seq.sky_model.get_night_boundaries(self.conf.sched_driver.night_boundary)

        self.log.debug("Set timestamp: %.6f", set_timestamp)
        self.log.debug("Rise timestamp: %.6f", rise_timestamp)

        delta = set_timestamp - self.time_handler.current_timestamp
        self.time_handler.update_time(delta, "seconds")
        self.log.debug("Timestamp: %.6f", self.time_handler.current_timestamp)

        self.log.debug("Start of night {} at {}".format(night, self.time_handler.current_timestring))

        self.end_of_night = rise_timestamp

        end_of_night_str = self.time_handler.future_timestring(0, "seconds", timestamp=self.end_of_night)
        self.log.debug("End of night {} at {}".format(night, end_of_night_str))

        self.db.clear_data()

        down_days = self.dh.get_downtime(night)
        if down_days:
            self.log.info("Observatory is down: {} days.".format(down_days))
            if not self.no_dds_comm:
                self.comm_time.is_down = True
                self.comm_time.down_duration = down_days
                self.comm_time.timestamp = self.time_handler.current_timestamp
            self.log.log(LoggingLevel.EXTENSIVE.value,
                         "Downtime Start Night Timestamp sent: {:.6f}"
                         .format(self.time_handler.current_timestamp))
            if not self.no_dds_comm:
                self.sal.put(self.comm_time)
            observatory_state = self.seq.get_observatory_state(self.time_handler.current_timestamp)
            self.log.log(LoggingLevel.EXTENSIVE.value,
                         "Downtime Observatory State: {}".format(topic_strdict(observatory_state)))
            if not self.no_dds_comm:
                self.sal.put(observatory_state)

            delta = math.fabs(self.time_handler.current_timestamp - self.end_of_night) + SECONDS_IN_MINUTE
            self.time_handler.update_time(delta, "seconds")
        elif not self.no_dds_comm:
            self.comm_time.isDown = False
            self.comm_time.downDuration = down_days

    def write_proposal_fields(self, prop_fields):
        """Transform the proposal field information and write to the survey database.

        Parameters
        ----------
        prop_fields : dict
            The set of proposal fields information.
        """
        num_proposal_fields = 1
        data = []
        for prop_id, field_ids in prop_fields.items():
            for field_id in field_ids:
                data.append(write_proposal_field(ProposalFieldInfo(num_proposal_fields,
                                                                   prop_id, field_id),
                                                 self.db.session_id))
                num_proposal_fields += 1
        self.db.write_table("proposal_field", data)

    def configure_driver(self):
        """When running with no DDS communication layer, this function can be used to configure the driver.

        """
        self.driver.configure_duration(self.conf.survey.full_duration)
        self.log.info("run: rx scheduler config survey_duration=%.1f" % (self.conf.survey.full_duration))

        SALUtils.wtopic_driver_config(self.conf_comm.sched_driver_conf, self.conf)
        config_dict = SALUtils.rtopic_driver_config(self.conf_comm.sched_driver_conf)
        self.log.info("run: rx driver config=%s" % config_dict)
        self.driver.configure(config_dict)

        SALUtils.wtopic_location_config(self.conf_comm.obs_site_conf, self.conf)
        config_dict = SALUtils.rtopic_location_config(self.conf_comm.obs_site_conf)
        self.driver.configure_location(config_dict)
        self.log.info("run: rx site config=%s" % config_dict)

        SALUtils.wtopic_telescope_config(self.conf_comm.tel_conf, self.conf)
        config_dict = SALUtils.rtopic_telescope_config(self.conf_comm.tel_conf)
        self.driver.configure_telescope(config_dict)
        self.log.info("run: rx telescope config=%s" % config_dict)

        SALUtils.wtopic_dome_config(self.conf_comm.dome_conf, self.conf)
        config_dict = SALUtils.rtopic_dome_config(self.conf_comm.dome_conf)
        self.driver.configure_dome(config_dict)
        self.log.info("run: rx dome config=%s" % config_dict)

        SALUtils.wtopic_rotator_config(self.conf_comm.rot_conf, self.conf)
        config_dict = SALUtils.rtopic_rotator_config(self.conf_comm.rot_conf)
        self.driver.configure_rotator(config_dict)
        self.log.info("run: rx rotator config=%s" % config_dict)

        SALUtils.wtopic_camera_config(self.conf_comm.cam_conf, self.conf)
        config_dict = SALUtils.rtopic_camera_config(self.conf_comm.cam_conf)
        self.driver.configure_camera(config_dict)
        self.log.info("run: rx camera config=%s" % config_dict)

        SALUtils.wtopic_slew_config(self.conf_comm.slew_conf, self.conf)
        config_dict = SALUtils.rtopic_slew_config(self.conf_comm.slew_conf)
        self.driver.configure_slew(config_dict)
        self.log.info("run: rx slew config=%s" % config_dict)

        SALUtils.wtopic_optics_config(self.conf_comm.olc_conf, self.conf)
        config_dict = SALUtils.rtopic_optics_config(self.conf_comm.olc_conf)
        self.driver.configure_optics(config_dict)
        self.log.info("run: rx optics config=%s" % config_dict)

        SALUtils.wtopic_park_config(self.conf_comm.park_conf, self.conf)
        config_dict = SALUtils.rtopic_park_config(self.conf_comm.park_conf)
        self.driver.configure_park(config_dict)
        self.log.info("run: rx park config=%s" % (config_dict))

        self.log.debug('Configuring scheduler')

        survey_topology = self.driver.configure_scheduler(config=self.conf,
                                                          config_path=self.config_path)

        self.log.debug('%s', survey_topology)

        if survey_topology is not None:
            self.conf_comm.num_proposals = survey_topology.num_props

            self.conf_comm.survey_topology['general'] = survey_topology.general_propos
            self.conf_comm.survey_topology['sequence'] = survey_topology.sequence_propos

    def send_scheduler_to(self, state):
        """
        Tell Scheduler to go to specified state.

        :return:
        """
        accepted = -1
        self.log.debug('Send Scheduler to %i state' % state)
        if state == 4:
            self.sal.send_command("enterControl")
            retval = self.sal.waitForCompletion(self.sal.cmdId, int(self.socs_timeout))
            accepted = 1
            # accepted = self.sal.manager.acceptCommand_enterControl
        elif state == 0:
            if self.opts.config_version not in set(self.valid_settings):
                raise Exception("Selected settings \"{}\" not valid.".format(self.opts.config_version))
            self.sal.send_command("start", settingsToApply=self.opts.config_version)
            retval = self.sal.waitForCompletion(self.sal.cmdId, int(self.socs_timeout))
            accepted = 1
            # accepted = self.sal.manager.acceptCommand_enterControl
        elif state == 1:
            self.sal.send_command("enable")
            retval = self.sal.waitForCompletion(self.sal.cmdId, int(self.socs_timeout))
            accepted = 1
        else:
            self.log.error('Unrecognized state %i' % state)

        return accepted

    def listen_scheduler_state(self):

        lasttime = time.time()
        while self.wait_for_scheduler:
            rcode = self.sal.manager.getEvent_summaryState(self.scheduler_summary_state)
            if rcode == 0:
                break
            else:
                tf = time.time()
                if (tf - lasttime) > self.socs_timeout:
                    raise SchedulerTimeoutError("Could not listen to Scheduler state!")
        return rcode

    def listen_scheduler_settings(self):

        lasttime = time.time()
        while self.wait_for_scheduler:
            rcode = self.sal.manager.getEvent_validSettings(self.scheduler_valid_settings)
            if rcode == 0:
                break
            else:
                tf = time.time()
                if (tf - lasttime) > self.socs_timeout:
                    raise SchedulerTimeoutError("Could not listen to Scheduler state!")
        return rcode