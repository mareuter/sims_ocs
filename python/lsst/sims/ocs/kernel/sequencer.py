from builtins import object
from builtins import range
from array import array
import logging
import numpy
import sys

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

    def __init__(self, obs_site_config, idle_delay):
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
        self.observatory_state.pointing_ra = obs_current_state.ra
        self.observatory_state.pointing_dec = obs_current_state.dec
        self.observatory_state.pointing_angle = obs_current_state.ang
        self.observatory_state.pointing_altitude = obs_current_state.alt
        self.observatory_state.pointing_azimuth = obs_current_state.az
        self.observatory_state.pointing_pa = obs_current_state.pa
        self.observatory_state.pointing_rot = obs_current_state.rot
        self.observatory_state.tracking = obs_current_state.tracking
        self.observatory_state.telescope_altitude = obs_current_state.telalt
        self.observatory_state.telescope_azimuth = obs_current_state.telaz
        self.observatory_state.telescope_rotator = obs_current_state.telrot
        self.observatory_state.dome_altitude = obs_current_state.domalt
        self.observatory_state.dome_azimuth = obs_current_state.domaz
        self.observatory_state.filter_position = obs_current_state.filter
        self.observatory_state.filter_mounted = ",".join(obs_current_state.mountedfilters)
        self.observatory_state.filter_unmounted = ','.join(obs_current_state.unmountedfilters)

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

            self.sky_model.update(target.request_time)
            target.request_mjd = self.sky_model.date_profile.mjd

            slew_info, exposure_info = self.observatory_model.observe(th, target, self.observation)
            self.sky_model.update(self.observation.observation_start_time)

            nid = numpy.array([target.fieldId])
            nra = numpy.radians(numpy.array([self.observation.ra]))
            ndec = numpy.radians(numpy.array([self.observation.dec]))

            sky_mags = self.sky_model.get_sky_brightness(nid, extrapolate=True,
                                                         override_exclude_planets=False)
            attrs = self.sky_model.get_target_information(nid, nra, ndec)
            msi = self.sky_model.get_moon_sun_info(nra, ndec)

            self.observation.sky_brightness = sky_mags[self.observation.filter][0]
            self.observation.airmass = attrs["airmass"][0]
            self.observation.altitude = numpy.degrees(attrs["altitude"][0])
            self.observation.azimuth = numpy.degrees(attrs["azimuth"][0])
            self.observation.moon_ra = numpy.degrees(msi["moonRA"])
            self.observation.moon_dec = numpy.degrees(msi["moonDec"])
            self.observation.moon_alt = numpy.degrees(msi["moonAlt"][0])
            self.observation.moon_az = numpy.degrees(msi["moonAz"][0])
            self.observation.moon_phase = msi["moonPhase"]
            self.observation.moon_distance = numpy.degrees(msi["moonDist"][0])
            self.observation.sun_alt = numpy.degrees(msi["sunAlt"][0])
            self.observation.sun_az = numpy.degrees(msi["sunAz"][0])
            self.observation.sun_ra = numpy.degrees(msi["sunRA"])
            self.observation.sun_dec = numpy.degrees(msi["sunDec"])
            self.observation.solar_elong = numpy.degrees(msi["solarElong"][0])
        else:
            self.log.log(LoggingLevel.EXTENSIVE.value, "No target received!")
            self.observation.observationId = target.targetId
            self.observation.targetId = target.targetId
            if target.filter == '':
                self.observation.filter = 'z'
            if target.seeing == 0.0:
                self.observation.seeing_fwhm_eff = 0.1
            if sum(target.exposure_times) == 0.0:
                for i in range(target.num_exposures):
                    self.observation.exposure_times[i] = 15
                self.observation.num_exposures = 1
            if target.airmass == 0.0:
                self.observation.airmass = 1.0
            if target.sky_brightness == 0.0:
                self.observation.sky_brightness = 30.0
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
        if filter_swap.need_swap:
            self.observatory_model.swap_filter(filter_swap.filter_to_unmount)

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

    def set_topic(self, th, sky_brightness_filters):
        """Set the sky brightness information into the topic. We will be
        broadcasting the entire sky's sky brightness using the opsim fields. 
        In other words, 5292 floating point values for all 5 filters 
        [u,g,r,i,z,y].

        Parameters
        ----------
        th : :class:`TimeHandler`
            A time handling instance.
        sky_brightness_filters : A dictionary of filters as keys and 
            SALPY_scheduler.scheduler_skyBrightness topics as values. So that we
            can iterate through this dictionary and the skymap filters in the 
            same loop. 
        """
        fields = numpy.arange(1,5293)
        skymap = self.sky_model.get_sky_brightness(fields, extrapolate=True,
                                                         override_exclude_planets=False)

        for filter in skymap:

            tempByteArray = array("H")

            f_min = min(i for i in skymap[filter] if i > 0)
            f_max = numpy.max(skymap[filter])
            SCALE = round(255 / (f_min - f_max),2)
            ZERO = round(f_max,2)

            sky_brightness_filters[filter].timestamp = th.current_timestamp
            sky_brightness_filters[filter].scale = SCALE
            sky_brightness_filters[filter].zero = ZERO

            for val in range(len(skymap[filter])):

                if skymap[filter][val] < 0:
                    tempByteArray.append(0)
                    continue
                else:
                    originalFloat = skymap[filter][val]
                    uint = int((originalFloat-ZERO) * SCALE)
                    # print("SEQUENCER::SKYMAP::" + str(filter)+"::" + str(val) + " " + str(uint))
                    sky_brightness_filters[filter].sky_brightness[val] = uint