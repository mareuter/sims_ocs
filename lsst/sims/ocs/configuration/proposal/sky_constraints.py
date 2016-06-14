import lsst.pex.config as pexConfig

__all__ = ["SkyConstraints"]

class SkyConstraints(pexConfig.Config):
    """Configuration for a proposal's sky constraints.
    """

    max_airmass = pexConfig.Field('The maximum airmass allowed for any field.', float)

    def setDefaults(self):
        """Default specification for sky constarints.
        """
        self.max_airmass = 2.5
