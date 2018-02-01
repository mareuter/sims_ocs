import lsst.pex.config as pexConfig

__all__ = ["SchedulerDriver"]

class SchedulerDriver(pexConfig.Config):
    """Configuration of the LSST Scheduler's Driver.
    """

    coadd_values = pexConfig.Field('Flag to determine if two identical field/filter targets have their '
                                   'ranks added and then considered as one target.', bool)
    time_balancing = pexConfig.Field('Flag to detemine if cross-proposal time-balancing is used.', bool)
    timecost_time_max = pexConfig.Field('The slew time (units=seconds) where the time cost value equals '
                                        'one.', float)
    timecost_time_ref = pexConfig.Field('The reference slew time (units=seconds) that sets the steepness of '
                                        'the cost function.', float)
    timecost_cost_ref = pexConfig.Field('The cost value associated with the time cost reference slew time.',
                                        float)
    timecost_weight = pexConfig.Field('The weighting value to apply to the slew time cost function result.',
                                      float)
    filtercost_weight = pexConfig.Field('The weighting value to apply to the filter change cost function '
                                        'result.', float)
    propboost_weight = pexConfig.Field('The weighting value to apply to the time balancing equations. This '
                                       'parameter should be greater than or equal to zero.', float)
    night_boundary = pexConfig.Field('Solar altitude (degrees) when it is considered night.', float)
    new_moon_phase_threshold = pexConfig.Field('New moon phase threshold for swapping to dark time filter.',
                                               float)
    ignore_sky_brightness = pexConfig.Field('Flag to ignore sky brightness limits when rejecting targets.',
                                            bool)
    ignore_airmass = pexConfig.Field('Flag to ignore airmass limits when rejecting targets.', bool)
    ignore_clouds = pexConfig.Field('Flag to ignore cloud limits when rejecting targets.', bool)
    ignore_seeing = pexConfig.Field('Flag to ignore seeing limits when rejecting targets.', bool)
    lookahead_window_size = pexConfig.Field('Distance into the future the lookahead "looks", 1 unit = 5 minute', int)
    lookahead_bonus_weight = pexConfig.Field('Adjusts the weight of the lookahead bonus. Higher values '
                                             'add to fields with limited future visibility', float)

    def setDefaults(self):
        """Set defaults for the LSST Scheduler's Driver.
        """
        self.coadd_values = True
        self.time_balancing = True
        self.timecost_time_max = 150.0
        self.timecost_time_ref = 5.0
        self.timecost_cost_ref = 0.3
        self.timecost_weight = 1.0
        self.filtercost_weight = 1.0
        self.propboost_weight = 1.0
        self.night_boundary = -12.0
        self.new_moon_phase_threshold = 20.0
        self.ignore_sky_brightness = False
        self.ignore_airmass = False
        self.ignore_clouds = False
        self.ignore_seeing = False
        self.lookahead_window_size = 8000
        self.lookahead_bonus_weight = 1.0

    def validate(self):
        """Validate configuration parameters.
        """
        pexConfig.Config.validate(self)
        if self.propboost_weight < 0:
            raise ValueError("Proposal boost weight must be greater than or equal to zero.")
