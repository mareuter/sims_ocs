from builtins import object
import logging

__all__ = ["ConfigurationCommunicator"]

class ConfigurationCommunicator(object):
    """Main class for configuration communication.

    This class handles setting up the configuration DDS topics and publishing them so they can be picked up
    by the Scheduler.

    Attributes
    ----------
    sal : :class:`.SalManager`
        The object responsible for SAL interaction.
    config: :class:`.SimulationConfig`
        The top-level simulation configuration object.
    log : logging.Logger
        The logging instance.
    """

    def __init__(self):
        """Initialize the class.
        """
        self.sal = None
        self.config = None
        self.log = logging.getLogger("configuration.ConfigurationCommunicator")

    def initialize(self, sal, config):
        """Perform initialization steps.

        Parameters
        ----------
        sal : :class:`.SalManager`
            The instance responsible for SAL interaction.
        config : :class:`.SimulationConfig`
            The top-level simulation configuration instance.
        """
        self.log.info("Initializing configuration communication")
        self.sal = sal
        self.config = config
        self.configure()

    def _configure_scheduler(self):
        """Configure and send the Scheduler configuration topic.
        """
        self.sched_conf = self.sal.set_publish_topic("schedulerConfig")
        self.sched_conf.survey_duration = self.config.survey.full_duration

    def _configure_scheduler_driver(self):
        """Configure and the Scheduler Driver configuration topic.
        """
        self.sched_driver_conf = self.sal.set_publish_topic("driverConfig")
        self.sched_driver_conf.coadd_values = self.config.sched_driver.coadd_values
        self.sched_driver_conf.time_balancing = self.config.sched_driver.time_balancing
        self.sched_driver_conf.timecost_time_max = self.config.sched_driver.timecost_time_max
        self.sched_driver_conf.timecost_time_ref = self.config.sched_driver.timecost_time_ref
        self.sched_driver_conf.timecost_cost_ref = self.config.sched_driver.timecost_cost_ref
        self.sched_driver_conf.timecost_weight = self.config.sched_driver.timecost_weight
        self.sched_driver_conf.filtercost_weight = self.config.sched_driver.filtercost_weight
        self.sched_driver_conf.propboost_weight = self.config.sched_driver.propboost_weight
        self.sched_driver_conf.night_boundary = self.config.sched_driver.night_boundary
        self.sched_driver_conf.new_moon_phase_threshold = self.config.sched_driver.new_moon_phase_threshold
        self.sched_driver_conf.ignore_sky_brightness = self.config.sched_driver.ignore_sky_brightness
        self.sched_driver_conf.ignore_airmass = self.config.sched_driver.ignore_airmass
        self.sched_driver_conf.ignore_clouds = self.config.sched_driver.ignore_clouds
        self.sched_driver_conf.ignore_seeing = self.config.sched_driver.ignore_seeing

    def _configure_observing_site(self):
        """Configure and send the Observing Site configuration topic.
        """
        self.obs_site_conf = self.sal.set_publish_topic("obsSiteConfig")

        self.obs_site_conf.name = self.config.observing_site.name
        self.obs_site_conf.latitude = self.config.observing_site.latitude
        self.obs_site_conf.longitude = self.config.observing_site.longitude
        self.obs_site_conf.height = self.config.observing_site.height
        self.obs_site_conf.pressure = self.config.observing_site.pressure
        self.obs_site_conf.temperature = self.config.observing_site.temperature
        self.obs_site_conf.relative_humidity = self.config.observing_site.relative_humidity

    def _configure_telescope(self):
        """Configure and send the Telescope configuration topic.
        """
        self.tel_conf = self.sal.set_publish_topic("telescopeConfig")

        self.tel_conf.altitude_minpos = self.config.observatory.telescope.altitude_minpos
        self.tel_conf.altitude_maxpos = self.config.observatory.telescope.altitude_maxpos
        self.tel_conf.altitude_maxspeed = self.config.observatory.telescope.altitude_maxspeed
        self.tel_conf.altitude_accel = self.config.observatory.telescope.altitude_accel
        self.tel_conf.altitude_decel = self.config.observatory.telescope.altitude_decel
        self.tel_conf.azimuth_minpos = self.config.observatory.telescope.azimuth_minpos
        self.tel_conf.azimuth_maxpos = self.config.observatory.telescope.azimuth_maxpos
        self.tel_conf.azimuth_maxspeed = self.config.observatory.telescope.azimuth_maxspeed
        self.tel_conf.azimuth_accel = self.config.observatory.telescope.azimuth_accel
        self.tel_conf.azimuth_decel = self.config.observatory.telescope.azimuth_decel
        self.tel_conf.settle_time = self.config.observatory.telescope.settle_time

    def _configure_dome(self):
        """Configure and send the dome configuration topic.
        """
        self.dome_conf = self.sal.set_publish_topic("domeConfig")

        self.dome_conf.altitude_maxspeed = self.config.observatory.dome.altitude_maxspeed
        self.dome_conf.altitude_accel = self.config.observatory.dome.altitude_accel
        self.dome_conf.altitude_decel = self.config.observatory.dome.altitude_decel
        self.dome_conf.azimuth_maxspeed = self.config.observatory.dome.azimuth_maxspeed
        self.dome_conf.azimuth_accel = self.config.observatory.dome.azimuth_accel
        self.dome_conf.azimuth_decel = self.config.observatory.dome.azimuth_decel
        self.dome_conf.settle_time = self.config.observatory.dome.settle_time

    def _configure_rotator(self):
        """Configure and send the rotator configuration topic.
        """
        self.rot_conf = self.sal.set_publish_topic("rotatorConfig")

        self.rot_conf.minpos = self.config.observatory.rotator.minpos
        self.rot_conf.maxpos = self.config.observatory.rotator.maxpos
        self.rot_conf.filter_change_pos = self.config.observatory.rotator.filter_change_pos
        self.rot_conf.maxspeed = self.config.observatory.rotator.maxspeed
        self.rot_conf.accel = self.config.observatory.rotator.accel
        self.rot_conf.decel = self.config.observatory.rotator.decel
        self.rot_conf.followsky = self.config.observatory.rotator.follow_sky
        self.rot_conf.resume_angle = self.config.observatory.rotator.resume_angle

    def _configure_camera(self):
        """Configure and send the camera configuration topic.
        """
        self.cam_conf = self.sal.set_publish_topic("cameraConfig")

        self.cam_conf.readout_time = self.config.observatory.camera.readout_time
        self.cam_conf.shutter_time = self.config.observatory.camera.shutter_time
        self.cam_conf.filter_mount_time = self.config.observatory.camera.filter_mount_time
        self.cam_conf.filter_change_time = self.config.observatory.camera.filter_change_time
        self.cam_conf.filter_max_changes_burst_num = \
            self.config.observatory.camera.filter_max_changes_burst_num
        self.cam_conf.filter_max_changes_burst_time = \
            self.config.observatory.camera.filter_max_changes_burst_time
        self.cam_conf.filter_max_changes_avg_num = self.config.observatory.camera.filter_max_changes_avg_num
        self.cam_conf.filter_max_changes_avg_time = self.config.observatory.camera.filter_max_changes_avg_time
        self.cam_conf.filter_mounted = self.config.observatory.camera.filter_mounted_str
        self.cam_conf.filter_pos = self.config.observatory.camera.filter_pos
        self.cam_conf.filter_removable = self.config.observatory.camera.filter_removable_str
        self.cam_conf.filter_unmounted = self.config.observatory.camera.filter_unmounted_str

    def _configure_slew(self):
        """Configure and send the slew configuration topic.
        """
        self.slew_conf = self.sal.set_publish_topic("slewConfig")

        self.slew_conf.prereq_domalt = self.config.observatory.slew.get_string_rep("prereq_domalt")
        self.slew_conf.prereq_domaz = self.config.observatory.slew.get_string_rep("prereq_domaz")
        self.slew_conf.prereq_telalt = self.config.observatory.slew.get_string_rep("prereq_telalt")
        self.slew_conf.prereq_telaz = self.config.observatory.slew.get_string_rep("prereq_telaz")
        self.slew_conf.prereq_telopticsopenloop = \
            self.config.observatory.slew.get_string_rep("prereq_telopticsopenloop")
        self.slew_conf.prereq_telopticsclosedloop = \
            self.config.observatory.slew.get_string_rep("prereq_telopticsclosedloop")
        self.slew_conf.prereq_telrot = self.config.observatory.slew.get_string_rep("prereq_telrot")
        self.slew_conf.prereq_filter = self.config.observatory.slew.get_string_rep("prereq_filter")
        self.slew_conf.prereq_adc = self.config.observatory.slew.get_string_rep("prereq_adc")
        self.slew_conf.prereq_ins_optics = self.config.observatory.slew.get_string_rep("prereq_ins_optics")
        self.slew_conf.prereq_guider_pos = self.config.observatory.slew.get_string_rep("prereq_guider_pos")
        self.slew_conf.prereq_guider_adq = self.config.observatory.slew.get_string_rep("prereq_guider_adq")
        self.slew_conf.prereq_telsettle = self.config.observatory.slew.get_string_rep("prereq_telsettle")
        self.slew_conf.prereq_domazsettle = self.config.observatory.slew.get_string_rep("prereq_domazsettle")
        self.slew_conf.prereq_exposures = self.config.observatory.slew.get_string_rep("prereq_exposures")
        self.slew_conf.prereq_readout = self.config.observatory.slew.get_string_rep("prereq_readout")

    def _configure_optics_loop_corr(self):
        """Configure and send the optics loop correction configuration topic.
        """
        self.olc_conf = self.sal.set_publish_topic("opticsLoopCorrConfig")

        self.olc_conf.tel_optics_ol_slope = self.config.observatory.optics_loop_corr.tel_optics_ol_slope
        self.config.observatory.optics_loop_corr.set_array(self.olc_conf, "tel_optics_cl_alt_limit")
        self.config.observatory.optics_loop_corr.set_array(self.olc_conf, "tel_optics_cl_delay")

    def _configure_park(self):
        """Configure and send the park position configuration.
        """
        self.park_conf = self.sal.set_publish_topic("parkConfig")

        self.park_conf.telescope_altitude = self.config.observatory.park.telescope_altitude
        self.park_conf.telescope_azimuth = self.config.observatory.park.telescope_azimuth
        self.park_conf.telescope_rotator = self.config.observatory.park.telescope_rotator
        self.park_conf.dome_altitude = self.config.observatory.park.dome_altitude
        self.park_conf.dome_azimuth = self.config.observatory.park.dome_azimuth
        self.park_conf.filter_position = self.config.observatory.park.filter_position

    def _configure_proposals(self):
        """Publish the general and sequence proposals.
        """
        self.sal.set_publish_topic("generalPropConfig")
        self.sal.set_publish_topic("sequencePropConfig")

    def configure(self):
        """Configure all publish topics for the configuration communicator.
        """
        self._configure_scheduler()
        self._configure_scheduler_driver()
        self._configure_observing_site()
        self._configure_telescope()
        self._configure_dome()
        self._configure_rotator()
        self._configure_camera()
        self._configure_slew()
        self._configure_optics_loop_corr()
        self._configure_park()
        self._configure_proposals()

    def run(self):
        """Send all of the configuration topics.
        """
        self.log.info("Running configuration communication")
        self.sal.put(self.sched_conf)
        self.sal.put(self.sched_driver_conf)
        self.sal.put(self.obs_site_conf)
        self.sal.put(self.tel_conf)
        self.sal.put(self.dome_conf)
        self.sal.put(self.rot_conf)
        self.sal.put(self.cam_conf)
        self.sal.put(self.slew_conf)
        self.sal.put(self.olc_conf)
        self.sal.put(self.park_conf)
        num_proposals = 1
        if self.config.science.general_props.active is not None:
            for general_config in self.config.science.general_props.active:
                general_topic = general_config.set_topic(self.sal.get_topic("generalPropConfig"))
                general_topic.prop_id = num_proposals
                self.sal.put(general_topic)
                num_proposals += 1
        else:
            general_topic = self.sal.get_topic("generalPropConfig")
            general_topic.prop_id = -1
            general_topic.name = "NULL"
            self.sal.put(general_topic)
        if self.config.science.sequence_props.active is not None:
            for sequence_config in self.config.science.sequence_props.active:
                sequence_topic = sequence_config.set_topic(self.sal.get_topic("sequencePropConfig"))
                sequence_topic.prop_id = num_proposals
                self.sal.put(sequence_topic)
                num_proposals += 1
        else:
            sequence_topic = self.sal.get_topic("sequencePropConfig")
            sequence_topic.prop_id = -1
            sequence_topic.name = "NULL"
            self.sal.put(sequence_topic)
        self.log.info("Sent configuration for {} proposals.".format(num_proposals - 1))
