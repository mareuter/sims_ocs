import lsst.pex.config as pexConfig

import re

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
        print(param)

        array = getattr(conf, param)

        print(param)

        local_param = getattr(self, param)
        
        for i, v in enumerate(local_param):
            array[i] = v

    def camelcase_to_snakecase(self, name):
        """This method is a result of legacy code. Originally snake case
        was used as the DDS topics. set_array() expects the topic and the
        class attribute to be identical, because of this it was easier to
        convert the topic back into snake case than to change the legacy
        code. Perhaps we can polish and remove this method at a future time."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
