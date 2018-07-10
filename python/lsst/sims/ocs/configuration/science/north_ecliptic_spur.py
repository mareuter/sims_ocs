import lsst.pex.config as pexConfig

from lsst.sims.ocs.configuration.proposal import General, GeneralBandFilter, Selection
from lsst.sims.ocs.configuration.proposal import general_prop_reg, SELECTION_LIMIT_TYPES

__all__ = ["NorthEclipticSpur"]

@pexConfig.registerConfig("NorthEclipticSpur", general_prop_reg, General)
class NorthEclipticSpur(General):
    """This class sets the parameters for specifying the North Ecliptic Spur proposal.
    """

    def setDefaults(self):
        """Setup all the proposal information.
        """
        self.name = "NorthEclipticSpur"

        # -------------------------
        # Sky Region specifications
        # -------------------------

        # Ecliptic Longitude Band
        eb_limit = Selection()
        eb_limit.limit_type = SELECTION_LIMIT_TYPES[5]
        eb_limit.minimum_limit = -30.0
        eb_limit.maximum_limit = 10.0

        # Dec Band
        dec_limit = Selection()
        dec_limit.limit_type = SELECTION_LIMIT_TYPES[1]
        dec_limit.minimum_limit = 2.8
        dec_limit.maximum_limit = 90.0

        self.sky_region.selections = {0: eb_limit, 1: dec_limit}
        self.sky_region.combiners = ('and',)

        # -----------------------------
        # Sky Exclusion specifications
        # -----------------------------

        self.sky_exclusion.dec_window = 90.0

        # ---------------------------------
        # Sky Nightly Bounds specifications
        # ---------------------------------

        self.sky_nightly_bounds.twilight_boundary = -12.0
        self.sky_nightly_bounds.delta_lst = 60.0

        # ------------------------------
        # Sky Constraints specifications
        # ------------------------------

        self.sky_constraints.max_airmass = 2.5
        self.sky_constraints.max_cloud = 0.7

        # ----------------------
        # Scheduling information
        # ----------------------

        self.scheduling.max_num_targets = 100
        self.scheduling.accept_serendipity = False
        self.scheduling.accept_consecutive_visits = False
        self.scheduling.airmass_bonus = 0.
        self.scheduling.hour_angle_bonus = 0.3
        self.scheduling.hour_angle_max = 3.0
        self.scheduling.time_interval = 30 * 60
        self.scheduling.time_window_start = 0.5
        self.scheduling.time_window_max = 1.0
        self.scheduling.time_window_end = 2.0
        self.scheduling.time_weight = 1.0

        # --------------------------
        # Band Filter specifications
        # --------------------------

        g_filter = GeneralBandFilter()
        g_filter.name = 'g'
        g_filter.num_visits = 40
        g_filter.num_grouped_visits = 2
        g_filter.bright_limit = 21.0
        g_filter.dark_limit = 30.0
        g_filter.max_seeing = 2.0
        g_filter.exposures = [15.0, 15.0]

        r_filter = GeneralBandFilter()
        r_filter.name = 'r'
        r_filter.num_visits = 92
        r_filter.num_grouped_visits = 2
        r_filter.bright_limit = 20.25
        r_filter.dark_limit = 30.0
        r_filter.max_seeing = 2.0
        r_filter.exposures = [15.0, 15.0]

        i_filter = GeneralBandFilter()
        i_filter.name = 'i'
        i_filter.num_visits = 92
        i_filter.num_grouped_visits = 2
        i_filter.bright_limit = 19.5
        i_filter.dark_limit = 30.0
        i_filter.max_seeing = 2.0
        i_filter.exposures = [15.0, 15.0]

        z_filter = GeneralBandFilter()
        z_filter.name = 'z'
        z_filter.num_visits = 80
        z_filter.num_grouped_visits = 2
        z_filter.bright_limit = 17.0
        z_filter.dark_limit = 21.0
        z_filter.max_seeing = 2.0
        z_filter.exposures = [15.0, 15.0]

        self.filters = {g_filter.name: g_filter,
                        r_filter.name: r_filter,
                        i_filter.name: i_filter,
                        z_filter.name: z_filter}
