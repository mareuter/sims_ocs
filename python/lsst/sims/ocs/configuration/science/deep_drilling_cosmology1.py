import lsst.pex.config as pexConfig

from lsst.sims.ocs.configuration.proposal import BandFilter, SubSequence, Sequence
from lsst.sims.ocs.configuration.proposal import sequence_prop_reg

__all__ = ["DeepDrillingCosmology1"]

@pexConfig.registerConfig("DeepDrillingCosmology1", sequence_prop_reg, Sequence)
class DeepDrillingCosmology1(Sequence):
    """This class sets the parameters for specifying the Deep Drilling Cosmology1 proposal.
    """

    def setDefaults(self):
        """Setup all the proposal information.
        """
        Sequence.setDefaults(self)

        self.name = "DeepDrillingCosmology1"

        # -------------------------
        # Sky Region specifications
        # -------------------------

        self.sky_user_regions = [290, 744, 1427, 2412, 2786]

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

        self.sky_constraints.max_airmass = 1.5
        self.sky_constraints.max_cloud = 0.7

        #---------------------------
        # Sub-sequence specification
        #---------------------------

        sseq0 = SubSequence()
        sseq0.name = "main"
        sseq0.filters = ['r', 'g', 'i', 'z', 'y']
        sseq0.visits_per_filter = [20, 10, 20, 26, 20]
        sseq0.num_events = 27
        sseq0.num_max_missed = 0
        sseq0.time_interval = 3 * 24 * 60 * 60
        sseq0.time_window_start = 0.8
        sseq0.time_window_max = 1.0
        sseq0.time_window_end = 1.4
        sseq0.time_weight = 1.0

        sseq1 = SubSequence()
        sseq1.name = "u-band"
        sseq1.filters = ['u']
        sseq1.visits_per_filter = [20]
        sseq1.num_events = 7
        sseq1.num_max_missed = 0
        sseq1.time_interval = 1 * 24 * 60 * 60
        sseq1.time_window_start = 0.8
        sseq1.time_window_max = 1.0
        sseq1.time_window_end = 1.4
        sseq1.time_weight = 1.0

        self.sub_sequences = {0: sseq0, 1: sseq1}

        # ----------------------
        # Scheduling information
        # ----------------------

        self.scheduling.max_num_targets = 100
        self.scheduling.accept_serendipity = False
        self.scheduling.accept_consecutive_visits = True
        self.scheduling.airmass_bonus = 0.
        self.scheduling.hour_angle_bonus = 0.3

        # --------------------------
        # Band Filter specifications
        # --------------------------

        u_filter = BandFilter()
        u_filter.name = 'u'
        u_filter.bright_limit = 21.3
        u_filter.dark_limit = 30.0
        u_filter.max_seeing = 1.5
        u_filter.exposures = [15.0, 15.0]

        g_filter = BandFilter()
        g_filter.name = 'g'
        g_filter.bright_limit = 19.5
        g_filter.dark_limit = 30.0
        g_filter.max_seeing = 1.5
        g_filter.exposures = [15.0, 15.0]

        r_filter = BandFilter()
        r_filter.name = 'r'
        r_filter.bright_limit = 19.5
        r_filter.dark_limit = 30.0
        r_filter.max_seeing = 1.5
        r_filter.exposures = [15.0, 15.0]

        i_filter = BandFilter()
        i_filter.name = 'i'
        i_filter.bright_limit = 19.5
        i_filter.dark_limit = 30.0
        i_filter.max_seeing = 1.5
        i_filter.exposures = [15.0, 15.0]

        z_filter = BandFilter()
        z_filter.name = 'z'
        z_filter.bright_limit = 17.5
        z_filter.dark_limit = 30.0
        z_filter.max_seeing = 1.5
        z_filter.exposures = [15.0, 15.0]

        y_filter = BandFilter()
        y_filter.name = 'y'
        y_filter.bright_limit = 17.5
        y_filter.dark_limit = 30.0
        y_filter.max_seeing = 1.5
        y_filter.exposures = [15.0, 15.0]

        self.filters = {u_filter.name: u_filter,
                        g_filter.name: g_filter,
                        r_filter.name: r_filter,
                        i_filter.name: i_filter,
                        z_filter.name: z_filter,
                        y_filter.name: y_filter}
