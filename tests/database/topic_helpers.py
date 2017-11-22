#import collections

import SALPY_scheduler
import lsst.sims.ocs.kernel
import lsst.sims.ocs.observatory

target = SALPY_scheduler.scheduler_targetC()
target.targetId = 10
target.fieldId = 300
target.groupId = 2
target.filter = "z"
target.ra = 1.000
target.decl = -3.00
target.angle = 0.5
target.num_exposures = 2
target.exposure_times[0] = 15
target.exposure_times[1] = 15
target.request_time = 1640995200.0
target.request_mjd = 59280.0
target.airmass = 1.4
target.sky_brightness = 20.4
target.cloud = 0.0
target.seeing = 0.5
target.slew_time = 4.75
target.cost = 0.1
target.rank = 0.013
target.prop_boost = 0.005
target.num_proposals = 2
target.moon_ra = 65.0
target.moon_dec = -10.0
target.moon_alt = -30.0
target.moon_az = 250.0
target.moon_phase = 0.5
target.moon_distance = 60.0

field_topic = SALPY_scheduler.scheduler_fieldC()
field_topic.ID = 1
field_topic.fov = 0.5
field_topic.ra = 30.0
field_topic.decl = -30.0
field_topic.gl = -45.0
field_topic.gb = 45.0
field_topic.el = 60.0
field_topic.eb = -60.0

field_tuple = (1, 0.5, 30.0, -30.0, -45.0, 45.0, 60.0, -60.0)

observation_topic = SALPY_scheduler.scheduler_observationC()
observation_topic.observationId = 5
observation_topic.targetId = 10
observation_topic.night = 1
observation_topic.observation_start_time = 1640995200.0
observation_topic.observation_start_mjd = 59580.0
observation_topic.observation_start_lst = 29.87546023333333
observation_topic.fieldId = 300
observation_topic.groupId = 2
observation_topic.filter = "r"
observation_topic.ra = 1.000
observation_topic.decl = -3.00
observation_topic.angle = 0.5
observation_topic.altitude = 60.0
observation_topic.azimuth = 240.0
observation_topic.num_exposures = 2
observation_topic.exposure_times[0] = 15
observation_topic.exposure_times[1] = 15
observation_topic.visit_time = 34.0
observation_topic.airmass = 1.4
observation_topic.sky_brightness = 20.4
observation_topic.cloud = 0.2
observation_topic.seeing_fwhm_500 = 0.7
observation_topic.seeing_fwhm_geom = 0.75
observation_topic.seeing_fwhm_eff = 1.04
observation_topic.five_sigma_depth = 21.3
observation_topic.moon_ra = 65.0
observation_topic.moon_dec = -10.0
observation_topic.moon_alt = -30.0
observation_topic.moon_az = 250.0
observation_topic.moon_phase = 0.5
observation_topic.moon_distance = 60.0
observation_topic.sun_ra = 245.0
observation_topic.sun_dec = 0.0
observation_topic.sun_alt = -10.0
observation_topic.sun_az = 250.0
observation_topic.solar_elong = 250.0

slew_history_coll = lsst.sims.ocs.observatory.SlewHistory(slewCount=1, startDate=2922, endDate=2925,
                                                          slewTime=6.0, slewDistance=1.0,
                                                          ObsHistory_observationId=1)

slew_state_coll = lsst.sims.ocs.observatory.SlewState(slewStateId=1, slewStateDate=1640995200.0,
                                                      targetRA=1.000, targetDec=-3.000, tracking="False",
                                                      altitude=34.1, azimuth=155.4, paraAngle=0.5,
                                                      domeAlt=35.2, domeAz=156.3, telAlt=34.6, telAz=155.6,
                                                      rotTelPos=1.0, rotSkyPos=-0.5, filter="r",
                                                      SlewHistory_slewCount=1)

slew_activity_coll = lsst.sims.ocs.observatory.SlewActivity(slewActivityId=1, activity="Readout",
                                                            activityDelay=2.0, inCriticalPath="False",
                                                            SlewHistory_slewCount=1)

slew_maxspeed_coll = lsst.sims.ocs.observatory.SlewMaxSpeeds(slewMaxSpeedId=1, domeAltSpeed=1.0,
                                                             domeAzSpeed=2.3, telAltSpeed=0.5, telAzSpeed=1.1,
                                                             rotatorSpeed=0.1, SlewHistory_slewCount=1)

exposure_coll1 = lsst.sims.ocs.observatory.TargetExposure(exposureId=1, exposureNum=1, exposureTime=15.0,
                                                          TargetHistory_targetId=3)

exposure_coll2 = lsst.sims.ocs.observatory.TargetExposure(exposureId=2, exposureNum=2, exposureTime=15.0,
                                                          TargetHistory_targetId=3)

exposure_coll3 = lsst.sims.ocs.observatory.ObsExposure(exposureId=1, exposureNum=1, exposureTime=15.0,
                                                       exposureStartTime=2922.0, ObsHistory_observationId=3)

exposure_coll4 = lsst.sims.ocs.observatory.ObsExposure(exposureId=1, exposureNum=2, exposureTime=15.0,
                                                       exposureStartTime=2922.2, ObsHistory_observationId=3)

prop_info = lsst.sims.ocs.kernel.ProposalInfo(propId=1, propName="TestProposal", propType="General")

obs_prop_hist = lsst.sims.ocs.kernel.ObsProposalHistory(propHistId=1, Proposal_propId=2, proposalValue=1.32,
                                                        proposalNeed=0.5, proposalBonus=0.82,
                                                        proposalBoost=0.2, ObsHistory_observationId=10)

target_prop_hist = lsst.sims.ocs.kernel.TargetProposalHistory(propHistId=1, Proposal_propId=2,
                                                              proposalValue=1.32, proposalNeed=0.5,
                                                              proposalBonus=0.82, proposalBoost=0.2,
                                                              TargetHistory_targetId=10)

prop_field_info = lsst.sims.ocs.kernel.ProposalFieldInfo(propFieldId=1, Proposal_propId=4,
                                                         Field_fieldId=1545)

config_tuple = (10, "config/test/a", "1.0")
