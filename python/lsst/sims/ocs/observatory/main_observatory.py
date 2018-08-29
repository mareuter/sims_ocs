from builtins import object
from builtins import range
from builtins import str
import copy
import logging
import math

import palpy

from lsst.ts.dateloc import DateProfile, ObservatoryLocation
from lsst.ts.observatory.model import ObservatoryModel, Target

from lsst.sims.ocs.setup import LoggingLevel
from lsst.sims.ocs.observatory import ObsExposure, TargetExposure
from lsst.sims.ocs.observatory import SlewActivity, SlewHistory, SlewMaxSpeeds, SlewState
from lsst.sims.ocs.observatory import VariationalModel

__all__ = ["MainObservatory"]

class MainObservatory(object):
    """Class for the Main Observatory.

    This class is designed to look like the real observatory. In the default case, the observatory
    configuration is the main LSST obesrvatory. It uses the observatory model from the LSST Scheduler
    as its base information. There is an option to add variations onto the parameters and values that
    the model calculates to simulate real world behaviors.

    Attributes
    ----------
    log : logging.Logger
        The logging instance.
    model : lsst.ts.scheduler.observatory_model.ObservatoryModel
        The instance of the Observatory model from the LSST Scheduler.
    param_dict : dict
        The configuration parameters for the Observatory model.
    """

    def __init__(self, obs_site_config):
        """Initialize the class.

        Parameters
        ----------
        obs_site_config : :class:`.ObservingSite`
            The instance of the observing site configuration.
        """
        self.log = logging.getLogger("observatory.MainObservatory")
        observatory_location = ObservatoryLocation()
        observatory_location.configure({"obs_site": obs_site_config.toDict()})
        self.config = None
        self.model = ObservatoryModel(observatory_location, logging.DEBUG)
        self.date_profile = DateProfile(0, observatory_location)
        self.param_dict = {}
        self.slew_count = 0
        self.observations_made = 0
        self.exposures_made = 0
        self.target_exposure_list = None
        self.observation_exposure_list = None
        self.slew_history = None
        self.slew_final_state = None
        self.slew_initial_state = None
        self.slew_activities_list = None
        self.slew_activities_done = 0
        self.slew_maxspeeds = None
        self.variational_model = None

    def __getattr__(self, name):
        """Find attributes in lsst.ts.scheduler.observator_model.ObservatorModel as well as MainObservatory.
        """
        try:
            return getattr(self.model, name)
        except AttributeError:
            cclass_name = self.__class__.__name__
            aclass_name = self.model.__class__.__name__
            raise AttributeError("'{}' and '{}' objects have no attribute '{}'".format(cclass_name,
                                                                                       aclass_name,
                                                                                       name))

    def calculate_visit_time(self, target, th):
        """Calculate the visit time from the target and camera information.

        This function calculates the visit time from the current camera configuration parameters
        and the list of effective exposure times from the target. The visit time is calculated as:

        shutter_time = 2.0 * (0.5 * camera shutter time)
        visit_time = sum over number of exposures (shutter_time + effective exposure time)
        visit_time += (number of exposures - 1) * camera readout time

        Parameters
        ----------
        target : SALPY_scheduler.targetC
            The Scheduler topic instance holding the target information.

        Returns
        -------
        (float, str)
            The calculated visit time and a unit string (default it seconds).
        """
        self.target_exposure_list = []
        self.observation_exposure_list = []

        camera_config = self.config.camera
        shutter_time = 2.0 * (0.5 * camera_config.shutter_time)

        visit_time = 0.0
        for i in range(target.numExposures):
            self.exposures_made += 1
            effective_exposure_time = target.exposureTimes[i]
            self.target_exposure_list.append(TargetExposure(self.exposures_made, i + 1,
                                                            effective_exposure_time,
                                                            target.targetId))

            exposure_start_time = th.future_timestamp(visit_time, "seconds")
            visit_time += (shutter_time + effective_exposure_time)

            self.observation_exposure_list.append(ObsExposure(self.exposures_made, i + 1,
                                                              effective_exposure_time,
                                                              exposure_start_time, self.observations_made))

            if i < (target.numExposures - 1):
                visit_time += camera_config.readout_time

        return (visit_time, "seconds")

    def configure(self, obs_config):
        """Configure the ObservatoryModel parameters.

        Parameters
        ----------
        obs_config : :class:`.Observatory`
            The instance of the observatory configuration.
        """
        self.config = obs_config
        self.param_dict.update(self.config.toDict())
        self.model.configure(self.param_dict)
        self.variational_model = VariationalModel(obs_config)

    def get_slew_activities(self):
        """Get the slew activities for the given slew.

        This function retrieved the list of slew activities from the model after
        lsst.ts.scheduler.observatory_model.ObservatoryModel::slew is called. The
        activites are stored in an internal structure so parameters nor returns are
        necessary.
        """
        self.slew_activities_list = []
        critical_activities = self.model.lastslew_criticalpath
        for activity, delay in self.model.lastslew_delays_dict.items():
            self.slew_activities_done += 1
            self.slew_activities_list.append(SlewActivity(self.slew_activities_done, activity, delay,
                                                          str(activity in critical_activities),
                                                          self.slew_count))

    def get_slew_state(self, slew_state_info):
        """Get the slew state from the current state instance.

        This function takes a given slew state instance and copies the information to the namedtuple
        that will allow it to be transferred to the database.

        Parameters
        ----------
        slew_state_info : lsst.ts.scheduler.observatory_model.ObservatoryState
            The current slew state instance.

        Returns
        -------
        :class:`.SlewState`
            The copied slew state information.
        """
        slew_state = SlewState(self.slew_count, slew_state_info.time, slew_state_info.ra,
                               slew_state_info.dec, str(slew_state_info.tracking), slew_state_info.alt,
                               slew_state_info.az, slew_state_info.pa, slew_state_info.domalt,
                               slew_state_info.domaz, slew_state_info.telalt, slew_state_info.telaz,
                               slew_state_info.telrot, slew_state_info.ang, slew_state_info.filter,
                               self.slew_count)
        return slew_state

    def observe(self, time_handler, target, observation):
        """Perform the observation of the given target.

        Parameters
        ----------
        time_handler : :class:`.TimeHandler`
            An instance of the simulation's TimeHandler.
        target : SALPY_scheduler.targetC
            The Scheduler topic instance holding the target information.
        observation : SALPY_scheduler.observationC
            The Scheduler topic instance for recording the observation information.

        Returns
        -------
        dict(:class:`.SlewHistory`, :class:`.SlewState`, :class:`.SlewState`, list[:class:`.SlewActivity`])
            A dictionanry of all the slew information from the visit.
        dict(list[:class:`.TargetExposure`], list[:class:`.ObsExposure`])
            A dictionary of all the exposure information from the visit.
        """
        self.observations_made += 1

        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Starting observation {} for target {}.".format(self.observations_made,
                                                                     target.targetId))

        slew_time = self.slew(target)
        time_handler.update_time(*slew_time)

        observation.observationId = self.observations_made
        observation.observationStartTime = time_handler.current_timestamp
        start_mjd, start_lst = self.date_profile(observation.observationStartTime)
        observation.observationStartMjd = start_mjd
        observation.observationStartLst = math.degrees(start_lst)
        observation.targetId = target.targetId
        observation.numProposals = target.numProposals
        for i in range(observation.numProposals):
            observation.proposalIds[i] = target.proposalId[i]
        # observation.fieldId = target.fieldId
        # observation.groupId = target.groupId
        observation.filter = target.filter
        observation.ra = target.ra
        observation.decl = target.decl
        observation.angle = target.skyAngle
        observation.numExposures = target.numExposures
        observation.slewTime = slew_time[0]

        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Exposure Times for Target {}: {}".format(target.targetId, list(target.exposureTimes)))
        visit_time = self.calculate_visit_time(target, time_handler)
        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Visit Time for Target {}: {}".format(target.targetId, visit_time[0]))

        observation.visitTime = visit_time[0]
        for i, exposure in enumerate(self.observation_exposure_list):
            observation.exposureTimes[i] = int(exposure.exposureTime)

        time_handler.update_time(*visit_time)

        self.log.log(LoggingLevel.EXTENSIVE.value,
                     "Observation {} completed at {}.".format(self.observations_made,
                                                              time_handler.current_timestring))

        slew_info = {"slew_history": self.slew_history, "slew_initial_state": self.slew_initial_state,
                     "slew_final_state": self.slew_final_state, "slew_activities": self.slew_activities_list,
                     "slew_maxspeeds": self.slew_maxspeeds}

        exposure_info = {"target_exposures": self.target_exposure_list,
                         "observation_exposures": self.observation_exposure_list}

        return slew_info, exposure_info

    def slew(self, target):
        """Perform the slewing operation for the observatory to the given target.

        Parameters
        ----------
        target : SALPY_scheduler.targetC
            The Scheduler topic instance holding the target information.

        Returns
        -------
        float
            The time to slew the telescope from its current position to the target position.
        """
        self.slew_count += 1
        self.log.log(LoggingLevel.TRACE.value, "Slew count: {}".format(self.slew_count))
        initial_slew_state = copy.deepcopy(self.model.current_state)
        self.log.log(LoggingLevel.TRACE.value, "Initial slew state: {}".format(initial_slew_state))
        self.slew_initial_state = self.get_slew_state(initial_slew_state)

        sched_target = Target.from_topic(target)
        self.model.slew(sched_target)

        final_slew_state = copy.deepcopy(self.model.current_state)
        self.log.log(LoggingLevel.TRACE.value, "Final slew state: {}".format(final_slew_state))
        self.slew_final_state = self.get_slew_state(final_slew_state)

        slew_time = (final_slew_state.time - initial_slew_state.time, "seconds")

        slew_distance = palpy.dsep(final_slew_state.ra_rad, final_slew_state.dec_rad,
                                   initial_slew_state.ra_rad, initial_slew_state.dec_rad)

        self.slew_history = SlewHistory(self.slew_count, initial_slew_state.time, final_slew_state.time,
                                        slew_time[0], math.degrees(slew_distance), self.observations_made)

        self.get_slew_activities()

        self.slew_maxspeeds = SlewMaxSpeeds(self.slew_count, final_slew_state.domalt_peakspeed,
                                            final_slew_state.domaz_peakspeed,
                                            final_slew_state.telalt_peakspeed,
                                            final_slew_state.telaz_peakspeed,
                                            final_slew_state.telrot_peakspeed, self.slew_count)

        return slew_time

    def start_night(self, night, duration):
        """Perform start of night functions.

        Parameters
        ----------
        night : int
            The current survey observing night.
        duration : int
            The survey duration in days.
        """
        if self.variational_model.active:
            new_obs_config = self.variational_model.modify_parameters(night, duration)
            self.model.configure(new_obs_config)

    def swap_filter(self, filter_to_unmount):
        """Perform a filter swap.

        This function takes a requested filter to unmount and checks it against the list
        of removable filters. If it is not on the list, no filter swap is performed. If it
        is on the list, a filter swap is performed.

        Parameters
        ----------
        filter_to_unmount : str
            The filter requested for unmounting.
        """
        self.log.debug("Swap out {} filter.".format(filter_to_unmount))
        self.model.swap_filter(filter_to_unmount)
