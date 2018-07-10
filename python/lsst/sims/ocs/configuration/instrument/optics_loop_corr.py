import lsst.pex.config as pexConfig

__all__ = ["OpticsLoopCorr"]

class OpticsLoopCorr(pexConfig.Config):
    """Configuration of the LSST Optics Loop Corrections.
    """

    tel_optics_ol_slope = pexConfig.Field('Delay factor for Open Loop optics correction '
                                          '(units=seconds/degrees in ALT slew)', float)

    # Table of delay factors for Closed Loop optics correction according to the ALT slew range.
    tel_optics_cl_alt_limit = pexConfig.ListField('Altitude (units=degrees) limits for the delay ranges.',
                                                  float)

    tel_optics_cl_delay = pexConfig.ListField('Time delay (units=seconds) for the corresponding ALT slew '
                                              'range in the Closed Loop optics correction.', float)

    def setDefaults(self):
        """Set defaults for the LSST Optics Loop Corrections.
        """
        self.tel_optics_ol_slope = 1.0 / 3.5
        self.tel_optics_cl_alt_limit = [0.0, 9.0, 90.0]
        self.tel_optics_cl_delay = [0.0, 36.0]

    def set_array(self, conf, param):
        """Set a DDS topic array parameter.

        Parameters
        ----------
        conf : SALPY_scheduler.scheduler_opticsLoopCorrConfigC
            The optics loop corrections configuration instance.
        param : str
            The name of the topic parameter to fill.
        """
        array = getattr(conf, param)
        local_param = getattr(self, param)
        for i, v in enumerate(local_param):
            array[i] = v
