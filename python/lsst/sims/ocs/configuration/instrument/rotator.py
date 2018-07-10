import lsst.pex.config as pexConfig

__all__ = ["Rotator"]

class Rotator(pexConfig.Config):
    """Configuration of the LSST Rotator.
    """

    # Parameters
    minpos = pexConfig.Field('Minimum position (units=degrees) of rotator.', float)
    maxpos = pexConfig.Field('Maximum position (units=degrees) of rotator.', float)
    filter_change_pos = pexConfig.Field('Position (units=degrees) of rotator to allow filter changes.', float)

    follow_sky = pexConfig.Field('Flag that if True enables the movement of the rotator during slews to put '
                                 'North-Up. If range is insufficient, then the alignment is North-Down. If '
                                 'the flag is False, then the rotator does not move during the slews, it is '
                                 'only tracking during the exposures.', bool)
    resume_angle = pexConfig.Field('Flag that if True enables the rotator to keep the image angle after a '
                                   'filter change, moving back the rotator to the previous angle after the '
                                   'rotator was placed in filter change position. If the flag is False, '
                                   'then the rotator is left in the filter change position.', bool)

    # Kinematatic parameters
    maxspeed = pexConfig.Field('Maximum speed (units=degrees/second) of rotator movement.', float)
    accel = pexConfig.Field('Maximum acceleration (units=degrees/second**2) of rotator movement.', float)
    decel = pexConfig.Field('Maximum deceleration (units=degrees/second**2) of rotator movement.', float)

    def setDefaults(self):
        """Set defaults for the LSST Rotator.
        """
        self.minpos = -90.0
        self.maxpos = 90.0
        self.filter_change_pos = 0.0
        self.follow_sky = True
        self.resume_angle = True
        self.maxspeed = 3.5
        self.accel = 1.0
        self.decel = 1.0
