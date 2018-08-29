from lsst.sims.cloudModel import CloudModel

__all__ = ["CloudInterface"]

class CloudInterface(object):
    """Interface between SOCS and the CloudModel. (to be changed to CloudSim 
    once the model is seperated using MVC like design)

    This class deals with interaction to the CloudModel as well as topic handling
    for it.
    """

    def __init__(self, time_handler):
        """Initialize the class.

        Parameters
        ----------
        time_handler : :class:`.TimeHandler`
            The instance of the simulation time handler.
        """
        self.cloud_model = CloudModel(time_handler)

    def get_cloud(self, delta_time):
        """Get the cloud for the specified time.

        Parameters
        ----------
        delta_time : int
            The time (seconds) from the start of the simulation.

        Returns
        -------
        float
            The cloud (fraction of sky in 8ths) closest to the specified time.
        """
        return self.cloud_model.get_cloud(delta_time)

    def initialize(self, cloud_file=None):
        """Configure the cloud information.

        This function gets the appropriate database file and creates the cloud information
        from it. The default behavior is to use the module stored database. However, an
        alternate database file can be provided. The alternate database file needs to have a
        table called *Cloud* with the following columns:

        cloudId
            int : A unique index for each cloud entry.
        c_date
            int : The time (units=seconds) since the start of the simulation for the cloud observation.
        cloud
            float : The cloud coverage in 8ths of the sky.

        Parameters
        ----------
        cloud_file : str, optional
            The full path to an alternate cloud database.
        """
        if cloud_file == "":
            cloud_file = None

        self.cloud_model.read_data(cloud_file)

    def set_topic(self, th, topic):
        """Set the cloud information into the topic.

        Parameters
        ----------
        th : :class:`TimeHandler`
            A time handling instance.
        topic: SALPY_scheduler.scheduler_cloudC
            An instance of the cloudg topic.
        """
        topic.timestamp = th.current_timestamp
        topic.bulkCloud = self.get_cloud(th.time_since_start)
