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

from MonitorControl import ClassInstance, Device, Observatory
try:
  from . import cfg
except:
  pass
from MonitorControl import ClassInstance, Device, Observatory
from MonitorControl.Antenna import Telescope
from MonitorControl import MonitorControlError, Switch
from MonitorControl.Antenna import Telescope
from MonitorControl.Configurations.GDSCC import cfg, make_switch_inputs
from MonitorControl.FrontEnds import FrontEnd
from MonitorControl.FrontEnds.DSN import DSN_fe
from MonitorControl.Receivers import Receiver
from MonitorControl.Receivers.DSN import DSN_rx
from support.network import LAN_hosts_status

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

up, down, IP, MAC, ROACHlist = LAN_hosts_status()
n_roaches = len(ROACHlist)
if n_roaches < 2:
  logger.warning("Only %d ROACHes available", n_roaches)
if n_roaches < 1:
  raise ObservatoryError("", "Cannot proceed without ROACHes")
roaches = ROACHlist[:2]

def station_configuration(equipment,
                          roach_loglevel=logging.WARNING,
                          hardware={"sampling_clock": False,
                                    "IF_switch":      False,
                                    "Backend":        False}):
  """
  Describe a DSN Complex

  Implicit here is the naming convention explained above for DSN front ends and
  receivers.  The telescope output name is expected to be the same as the
  telescope name.

  The front end names are constructed from the dict `cfg'.  The initialization
  of 'DSN_fe' depends on this to know the band name.
  """
  print("DTO:", hardware)
  # Define the site
  obs = Observatory("GDSCC")
  tel = {}
  fe = {}
  rx = {}
  # For each station at the site
  for dss in list(cfg.keys()):
    # define the telescope
    tel[dss] = Telescope(obs, dss=dss)
    # for each band available on the telescope
    for band in list(cfg[dss].keys()):                         # S, X, Ka
      logger.debug("station_configuration: processing band %s", dss)
      fename = band+str(dss)
      outnames = []
      # for each polarization processed by the receiver
      for polindex in range(len(list(cfg[dss][band].keys()))):
        outnames.append(fename+list(cfg[dss][band].keys())[polindex])
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
        rx_outnames.append(outname+'U')
      rx[fename] = ClassInstance(Receiver, 
                                 DSN_rx, 
                                 fename,
                                 inputs = rx_inputs,
                                 output_names = rx_outnames)
  equipment['Telescope'] = tel
  equipment['FrontEnd'] = fe
  equipment['Receiver'] = rx
  #This part has to be done by hand to show the physical cabling
  if hardware['IF_switch']:
    from Electronics.Instruments.JFW50MS import MS287client
    IFswitch = ClassInstance(Device,
                           MS287client,
                           "Matrix Switch",
                           inputs=make_switch_inputs(rx),
                           output_names=['IF1', 'IF2', 'IF3', 'IF4'])
    equipment['IF_switch'] = {"DTO": IFswitch}
  else:
    IFswitch = Device("JWF MS 287",
                      inputs=make_switch_inputs(rx),
                      output_names=['IF1', 'IF2', 'IF3', 'IF4'])
    equipment['IF_switch'] = IFswitch
  if hardware['sampling_clock']:
    from Electronics.Instruments import Synthesizer
    from Electronics.Instruments.Valon import Valon1, Valon2 
    sample_clk = {}
    sample_clk[0] = ClassInstance(Synthesizer,Valon1,timeout=10)
    sample_clk[1] = ClassInstance(Synthesizer,Valon2,timeout=10)
    logger.debug(" roach1 sample clock is %f",
                 sample_clk[0].get_p("frequency"))
    logger.debug(" roach2 sample clock is %f",
                 sample_clk[1].get_p("frequency"))
    equipment['sampling_clock'] = sample_clk
  else:
    equipment['sampling_clock'] = None
    
  if hardware["Backend"]:
    from MonitorControl.BackEnds import Backend
    from MonitorControl.BackEnds.ROACH1 import KurtSpec_client
    BE = ClassInstance(Backend,
                     KurtSpec_client,
                     "Kurtosis Spectrometer",
                     inputs = {"Ro1In1": IFswitch.outputs['IF1'],
                               "Ro1In2": IFswitch.outputs['IF2'],
                               "Ro2In1": IFswitch.outputs['IF3'],
                               "Ro2In2": IFswitch.outputs['IF4']},
                     output_names = [["IF1kurt", "IF1pwr"],
                                     ["IF2kurt", "IF2pwr"],
                                     ["IF3kurt", "IF3pwr"],
                                     ["IF4kurt", "IF4pwr"]])
    equipment['Backend'] = BE 
  else:
    # if there is no backend, make up a dummy
    equipment['Backend'] = Device("Kurtosis Spectrometer",
                     inputs = {"Ro1In1": IFswitch.outputs['IF1'],
                               "Ro1In2": IFswitch.outputs['IF2'],
                               "Ro2In1": IFswitch.outputs['IF3'],
                               "Ro2In2": IFswitch.outputs['IF4']},
                     output_names = [["IF1kurt", "IF1pwr"],
                                     ["IF2kurt", "IF2pwr"],
                                     ["IF3kurt", "IF3pwr"],
                                     ["IF4kurt", "IF4pwr"]])
  return obs, equipment

if __name__ == "__main__":

  from MonitorControl.Configurations.GDSCC.DTO import station_configuration
  obs, tel, fe, rx, IFswitch, sample_clk, BE = station_configuration()
  print("obs =",obs)
  print("tel =",tel)
  print("fe =",fe)
  print("rx =",rx)
  print("IFswitch =",IFswitch)
  print("Sample clock =", sample_clk)
  print("Backend =", BE)
