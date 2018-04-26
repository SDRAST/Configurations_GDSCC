"""
DSN Transient Observatory deployed at Goldstone

Front end names are of the form band+dss, where band is S, X or Ka and dss is
the station number. The available receivers and polarizations for each antenna
are described in dict 'cfg', which follows the convention established in the
MonitorControl module.

The output channels must have unique names because each has its own
independent data stream.
"""
import logging
import Pyro

from Electronics.Instruments import Synthesizer
from Electronics.Instruments.JFW50MS import MS287client
from Electronics.Instruments.Valon import Valon1, Valon2
from MonitorControl import ClassInstance, Device, Observatory
from MonitorControl import ObservatoryError, Switch
from MonitorControl.Antenna import Telescope
from MonitorControl.BackEnds import Backend
from MonitorControl.BackEnds.ROACH1 import SAOspec
from MonitorControl.BackEnds.ROACH1.SAOfwif import SAObackend
from MonitorControl.Configurations.GDSCC import cfg
from MonitorControl.FrontEnds import FrontEnd
from MonitorControl.FrontEnds.DSN import DSN_fe
from MonitorControl.Receivers import Receiver
from MonitorControl.Receivers.DSN import DSN_rx
from support.network import LAN_hosts_status

logger = logging.getLogger(__name__)

                             
def make_switch_inputs(rx):
  """
  """
  inputs = {}
  for index in range(1,25):
    inputs["In%02d" % index] = None
  for dss in cfg.keys():
    logger.debug("make_switch_inputs: doing DSS %d", dss)
    for band in cfg[dss].keys():
      logger.debug("make_switch_inputs: doing band %s", band)
      logger.debug("make_switch_inputs: details: %s", cfg[dss][band])
      for pol in cfg[dss][band].keys():
        swin = "In%02d" % cfg[dss][band][pol]
        rxout = band+str(dss)+pol+"U"
        inputs[swin] = rx[band+str(dss)].outputs[rxout]
        logger.debug("DSS-%2d %s %s goes to %s from %s",
                     dss, band, pol, swin, rxout)
  inputs.pop("In00") # all the receivers not connected to switch inputs
  print "make_switch_inputs: %s" % inputs
  return inputs

def station_configuration(equipment,
                          roach_loglevel=logging.WARNING,
                          hardware=None):
  """
  Describe a DSN Complex

  Implicit here is the naming convention explained above for DSN front ends and
  receivers.  The telescope output name is expected to be the same as the
  telescope name.

  The front end names are constructed from the dict `cfg'.  The initialization
  of 'DSN_fe' depends on this to know the band name.
  
  @param equipment : equipment in addition to what is defined here
  @type  equipment : dict of Device subclass objects
  
  @param roachlist : ROACHs to be used with this configuration; default: all
  @type  roachlist : list of str
  
  @param roach_loglevel : log level for the ROACH loggers
  @type  roach_loglevel : str
  
  @param hardware : hardware which is available or to be tested
  @type  hardware : dict of boolean
  """
  if hardware is None:
      hardware = {
        "Antenna":     False,
        "FrontEnd":    True,  # currently we have no control over the front ends
        "Receiver":    True,  # currently we have no control over the receivers
        "IF_switch":   {"DTO": True},    # allow multiple switches
        "Synthesizer": False,
        "Backend":     False
      }
  if equipment is None:
      equipment = {}
    
  # Define the site
  obs = Observatory("GDSCC")
  tel = {}
  fe = {}
  rx = {}
  # For each station at the site, get a Telescope object, FrontEnd objects,
  # Receiver objects, Switch objects
  for dss in cfg.keys():                                 # 14,...,26
    logger.debug("station_configuration: processing DSS-%d", dss)
    # define the telescope
    tel[dss] = Telescope(obs, dss=dss, active=hardware["Antenna"])
    # for each band available on the telescope
    for band in cfg[dss].keys():                         # S, X, Ka
      logger.debug("station_configuration: processing band %s", dss)
      fename = band+str(dss)
      outnames = []
      # for each polarization processed by the receiver
      for pol in cfg[dss][band].keys():                  # L, R
        logger.debug("station_configuration: processing pol %s", pol)
        outnames.append(fename+pol)   #   cfg[dss][band][pol])
      logger.debug("station_configuration: FE output names: %s", outnames)
      fe[fename] = ClassInstance(FrontEnd, 
                                 DSN_fe, 
                                 fename,
                                 inputs = {fename:
                                           tel[dss].outputs[tel[dss].name]},
                                 output_names = outnames)
      rx_inputs = {}
      rx_outnames = []
      for outname in outnames:
        rx_inputs[outname] = fe[fename].outputs[outname]
        rx_outnames.append(outname+'U')                 # all DSN IFs are USB
      rx[fename] = ClassInstance(Receiver, 
                                 DSN_rx, 
                                 fename,
                                 inputs = rx_inputs,
                                 output_names = rx_outnames)
  equipment['Telescope'] = tel
  equipment['FrontEnd'] = fe
  equipment['Receiver'] = rx
  #This part has to be done by hand to show the physical cabling
  #print make_switch_inputs(rx)
  try:
    IFswitch = ClassInstance(Device,
                           MS287client,
                           "Matrix Switch",
                           inputs=make_switch_inputs(rx),
                           output_names=['IF1', 'IF2', 'IF3', 'IF4'])
    equipment['IF_switch'] = {"DTO": IFswitch}
  except Pyro.errors.NamingError, details:
    logger.error("Is the MS287 IF switch server running?")
    raise Pyro.errors.NamingError("Is the MS287 IF switch server running?")
  sample_clk = {}
  sample_clk[0] = ClassInstance(Synthesizer,Valon1,timeout=10)
  sample_clk[1] = ClassInstance(Synthesizer,Valon2,timeout=10)
  logger.debug(" roach1 sample clock is %f",
                 sample_clk[0].get_p("frequency"))
  logger.debug(" roach2 sample clock is %f",
                 sample_clk[1].get_p("frequency"))
  equipment['Synthesizer'] = sample_clk
  BE = ClassInstance(Backend,
                     SAOspec,
                     "32K Spectrometer",
                     inputs = {"Ro1In1": IFswitch.outputs['IF1'],
                               "Ro2In1": IFswitch.outputs['IF3']},
                     output_names = [["IF1pwr"],
                                     ["IF2pwr"]])
  equipment['Backend'] = BE                         
  return obs, equipment

if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  mylogger = logging.getLogger()
  mylogger.setLevel(logging.DEBUG)
  
  from MonitorControl.Configurations import station_configuration

  obs, equipment = station_configuration('DTO-32K')
  print "obs =", obs
  tel = equipment['Telescope']
  fe = equipment['FrontEnd']
  rx = equipment['Receiver']
  print "tel =", tel
  print "fe =", fe
  print "rx =", rx
  IFswitch = equipment['IF_switch']
  print "IFswitch =", IFswitch
  BE = equipment['Backend']
  print "BE =", BE
