import lsst.pex.config as pexConfig

from lsst.sims.ocs.configuration.proposal import General, GeneralBandFilter, Selection
from lsst.sims.ocs.configuration.proposal import general_prop_reg, SELECTION_LIMIT_TYPES

__all__ = ["WideFastDeep"]

@pexConfig.registerConfig("WideFastDeep", general_prop_reg, General)
class WideFastDeep(General):
    """This class sets the parameters for specifying the Wide, Fast, Deep proposal.
    """

    def setDefaults(self):
        """Setup all the proposal information.
        """
        self.name = "WideFastDeep"

        # -------------------------
        # Sky Region specifications
        # -------------------------

        # Dec Band
        dec_limit = Selection()
        dec_limit.limit_type = SELECTION_LIMIT_TYPES[1]
        dec_limit.minimum_limit = -62.5
        dec_limit.maximum_limit = 2.8

        self.sky_region.selections = {0: dec_limit}

        # -----------------------------
        # Sky Exclusion specifications
        # -----------------------------

        self.sky_exclusion.dec_window = 90.0

        # Galactic Plane
        gal_plane = Selection()
        gal_plane.limit_type = SELECTION_LIMIT_TYPES[6]
        gal_plane.minimum_limit = 0.0
        gal_plane.maximum_limit = 10.0
        gal_plane.bounds_limit = 90.0

        self.sky_exclusion.selections = {0: gal_plane}

        # ---------------------------------
        # Sky Nightly Bounds specifications
        # ---------------------------------

        self.sky_nightly_bounds.twilight_boundary = -12.0
        self.sky_nightly_bounds.delta_lst = 60.0

        # ------------------------------
        # Sky Constraints specifications
        # ------------------------------

        self.sky_constraints.max_airmass = 1.5
        self.sky_constraints.max_cloud = 0.7

        # ----------------------
        # Scheduling information
        # ----------------------

        self.scheduling.max_num_targets = 500
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

        u_filter = GeneralBandFilter()
        u_filter.name = 'u'
        u_filter.num_visits = 75
        u_filter.bright_limit = 21.3
        u_filter.dark_limit = 30.0
        u_filter.max_seeing = 1.5
        u_filter.exposures = [15.0, 15.0]

        g_filter = GeneralBandFilter()
        g_filter.name = 'g'
        g_filter.num_visits = 105
        g_filter.num_grouped_visits = 2
        g_filter.bright_limit = 21.0
        g_filter.dark_limit = 30.0
        g_filter.max_seeing = 1.5
        g_filter.exposures = [15.0, 15.0]

        r_filter = GeneralBandFilter()
        r_filter.name = 'r'
        r_filter.num_visits = 240
        r_filter.num_grouped_visits = 2
        r_filter.bright_limit = 20.25
        r_filter.dark_limit = 30.0
        r_filter.max_seeing = 1.5
        r_filter.exposures = [15.0, 15.0]

        i_filter = GeneralBandFilter()
        i_filter.name = 'i'
        i_filter.num_visits = 240
        i_filter.num_grouped_visits = 2
        i_filter.bright_limit = 19.5
        i_filter.dark_limit = 30.0
        i_filter.max_seeing = 1.5
        i_filter.exposures = [15.0, 15.0]

        z_filter = GeneralBandFilter()
        z_filter.name = 'z'
        z_filter.num_visits = 210
        z_filter.num_grouped_visits = 2
        z_filter.bright_limit = 17.0
        z_filter.dark_limit = 21.0
        z_filter.max_seeing = 1.5
        z_filter.exposures = [15.0, 15.0]

        y_filter = GeneralBandFilter()
        y_filter.name = 'y'
        y_filter.num_visits = 210
        y_filter.bright_limit = 16.5
        y_filter.dark_limit = 21.0
        y_filter.max_seeing = 1.5
        y_filter.exposures = [15.0, 15.0]

        self.filters = {u_filter.name: u_filter,
                        g_filter.name: g_filter,
                        r_filter.name: r_filter,
                        i_filter.name: i_filter,
                        z_filter.name: z_filter,
                        y_filter.name: y_filter}
