from builtins import object
from builtins import range
import logging
import numpy

from lsst.sims.ocs.observatory import MainObservatory
from lsst.sims.ocs.setup import LoggingLevel
from lsst.ts.astrosky.model import AstronomicalSkyModel
from lsst.ts.dateloc import ObservatoryLocation

__all__ = ["Sequencer"]

class Sequencer(object):
    """Handle the observation of a target.

    This class is responsible for taking a target from the Scheduler and performing the necessary steps to
    make an astronomical observation. It is then responsible for handing that observation back.

    Attributes
    ----------
    targets_received : int
        Counter for the number of targets received by the sequencer.
    targets_missed : int
        Counter for the number of targets that were actually observed due to scheduler rejection.
    observations_made : int
        Counter for the number of observations made by the sequencer.
    observation : SALPY_scheduler.observationC
        DDS topic instance for the observation information.
    observatory_model : :class:`.MainObservatory`
        Instance of the SOCS observatory model.
    observatory_state : SALPY_scheduler.observatoryStateC
        DDS topic instance for the observatory state information.
    idle_delay : float
        Time (units=seconds) to wait when a missed target is received.
    log : logging.Logger
        The logging instance.
    """

    def __init__(self, obs_site_config, idle_delay, no_dds=False):
        """Initialize the class.

        Parameters
        ----------
        obs_site_config : :class:`.ObservingSite`
            The instance of the observing site configuration.
        idle_delay : float
            The delay time (seconds) to skip forward when no target is received.
        """
        self.targets_received = 0
        self.targets_missed = 0
        self.observation = None
        self.observatory_model = MainObservatory(obs_site_config)
        self.observatory_location = ObservatoryLocation(obs_site_config.latitude_rad,
                                                        obs_site_config.longitude_rad,
                                                        obs_site_config.height)
        self.observatory_state = None
        self.log = logging.getLogger("kernel.Sequencer")
        self.idle_delay = (idle_delay, "seconds")
        self.sky_model = AstronomicalSkyModel(self.observatory_location)
        self.no_dds = no_dds

    @property
    def observations_made(self):
        """Get the number of observations made.

        Returns
        -------
        int
        """
        return self.observatory_model.observations_made

    def end_night(self):
        """Perform end of night functions.
        """
        # Park the telescope for the day.
        self.observatory_model.park()

    def get_observatory_state(self, timestamp):
        """Return the observatory state in a DDS topic instance.

        Parameters
        ----------
        timestamp : float
            The current timestamp at the state retrieval request.

        Return
        ------
        SALPY_scheduler.observatoryStateC
        """
        self.observatory_model.update_state(timestamp)
        obs_current_state = self.observatory_model.current_state

        self.observatory_state.timestamp = timestamp
        self.observatory_state.pointingRa = obs_current_state.ra
        self.observatory_state.pointingDec = obs_current_state.dec
        self.observatory_state.pointingAngle = obs_current_state.ang
        self.observatory_state.pointingAltitude = obs_current_state.alt
        self.observatory_state.pointingAzimuth = obs_current_state.az
        self.observatory_state.pointingPa = obs_current_state.pa
        self.observatory_state.pointingRot = obs_current_state.rot
        self.observatory_state.tracking = obs_current_state.tracking
        self.observatory_state.telescopeAltitude = obs_current_state.telalt
        self.observatory_state.telescopeAzimuth = obs_current_state.telaz
        self.observatory_state.telescopeRotator = obs_current_state.telrot
        self.observatory_state.domeAltitude = obs_current_state.domalt
        self.observatory_state.domeAzimuth = obs_current_state.domaz
        self.observatory_state.filterPosition = obs_current_state.filter
        self.observatory_state.filterMounted = ",".join(obs_current_state.mountedfilters)
        self.observatory_state.filterUnmounted = ','.join(obs_current_state.unmountedfilters)

        return self.observatory_state

    def initialize(self, sal, obs_config):
        """Perform initialization steps.

        This function handles gathering the observation telemetry topic from the given SalManager instance.

        Parameters
        ----------
        sal : :class:`.SalManager`
            A SalManager instance.
        obs_config : :class:`.Observatory`
            The instance of the observatory configuration.
        """
        if self.no_dds:
            from SALPY_scheduler import scheduler_observationC
            from SALPY_scheduler import scheduler_observatoryStateC
            self.observation = scheduler_observationC()
            self.observatory_model.configure(obs_config)
            self.observatory_state = scheduler_observatoryStateC()
        else:
            self.observation = sal.set_publish_topic("observation")
            self.observatory_state = sal.set_publish_topic("observatoryState")
            self.observatory_model.configure(obs_config)


    def finalize(self):
        """Perform finalization steps.

        This function logs the number or targets received and observations made.
        """
        self.log.info("Number of targets received: {}".format(self.targets_received))
        self.log.info("Number of observations made: {}".format(self.observations_made))
        self.log.info("Number of targets missed: {}".format(self.targets_missed))

    def observe_target(self, target, th):
        """Observe the given target.

        This function performs the necessary steps to observe the given target. The current steps are:

          * Update the simulation time after "slewing"
          * Copy target information to observation
          * Update the simulation time after "visit"

        If the targetId is -1, this means a target was not offered by the Scheduler. Time is forwarded
        by the idle delay time and slew and exposure information are set to None. The observation takes the
        target's Id.

        Parameters
        ----------
        target : SALPY_scheduler.targetC
            A target telemetry topic containing the current target information.
        th : :class:`.TimeHandler`
            An instance of the simulation's TimeHandler.

        Returns
        -------
        SALPY_scheduler.observationC
            An observation telemetry topic containing the observed target parameters.
        dict(:class:`.SlewHistory`, :class:`.SlewState`, :class:`.SlewState`, list[:class:`.SlewActivity`])
            A dictionanry of all the slew information from the visit.
        dict(list[:class:`.TargetExposure`], list[:class:`.ObsExposure`])
            A dictionary of all the exposure information from the visit.
        """
        if target.targetId != -1:
            self.log.log(LoggingLevel.EXTENSIVE.value, "Received target {}".format(target.targetId))
            self.targets_received += 1

            self.sky_model.update(target.requestTime)
            target.requestMjd = self.sky_model.date_profile.mjd

            slew_info, exposure_info = self.observatory_model.observe(th, target, self.observation)
            self.sky_model.update(self.observation.observationStartTime)

            nra = numpy.radians(numpy.array([self.observation.ra]))
            ndec = numpy.radians(numpy.array([self.observation.decl]))

            sky_mags = self.sky_model.get_sky_brightness(nra, ndec, extrapolate=True,
                                                         override_exclude_planets=False)
            attrs = self.sky_model.get_target_information(nra, ndec)
            msi = self.sky_model.get_moon_sun_info(nra, ndec)

            self.observation.skyBrightness = sky_mags[self.observation.filter][0]
            self.observation.airmass = attrs["airmass"][0]
            self.observation.altitude = numpy.degrees(attrs["altitude"][0])
            self.observation.azimuth = numpy.degrees(attrs["azimuth"][0])
            self.observation.moonRa = numpy.degrees(msi["moonRA"])
            self.observation.moonDec = numpy.degrees(msi["moonDec"])
            self.observation.moonAlt = numpy.degrees(msi["moonAlt"][0])
            self.observation.moonAz = numpy.degrees(msi["moonAz"][0])
            self.observation.moonPhase = msi["moonPhase"]
            self.observation.moonDistance = numpy.degrees(msi["moonDist"][0])
            self.observation.sunAlt = numpy.degrees(msi["sunAlt"][0])
            self.observation.sunAz = numpy.degrees(msi["sunAz"][0])
            self.observation.sunRa = numpy.degrees(msi["sunRA"])
            self.observation.sunDec = numpy.degrees(msi["sunDec"])
            self.observation.solarElong = numpy.degrees(msi["solarElong"][0])
        else:
            self.log.log(LoggingLevel.EXTENSIVE.value, "No target received!")
            self.observation.observationId = target.targetId
            self.observation.targetId = target.targetId
            if target.filter == '':
                self.observation.filter = 'z'
            # if target.seeing == 0.0:
            self.observation.seeingFwhmEff = 0.1
            if sum(target.exposureTimes) == 0.0:
                for i in range(target.numExposures):
                    self.observation.exposureTimes[i] = 15
                self.observation.numExposures = 1
            # if target.airmass == 0.0:
            self.observation.airmass = 1.0
            # if target.sky_brightness == 0.0:
            self.observation.skyBrightness = 30.0
            slew_info = None
            exposure_info = None
            th.update_time(*self.idle_delay)
            self.targets_missed += 1

        return self.observation, slew_info, exposure_info

    def sky_brightness_config(self):
        """Get the configuration from the SkyModelPre files.

        Returns
        -------
        list[tuple(key, value)]
        """
        return self.sky_model.sky_brightness_config()

    def start_day(self, filter_swap):
        """Perform start of day functions.

        Parameters
        ----------
        filter_swap : scheduler_filterSwapC
            The instance of the filter swap information.
        """
        if filter_swap.needSwap:
            self.observatory_model.swap_filter(filter_swap.filterToUnmount)

    def start_night(self, night, duration):
        """Perform start of night functions.

        Parameters
        ----------
        night : int
            The current survey observing night.
        duration : int
            The survey duration in days.
        """
        self.observatory_model.start_night(night, duration)
