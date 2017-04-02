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

from . import cfg

from MonitorControl import ClassInstance, Device, Observatory, Telescope
from MonitorControl import ObservatoryError, Switch
from MonitorControl.FrontEnds import FrontEnd
from MonitorControl.FrontEnds.DSN import DSN_fe
from MonitorControl.Receivers import Receiver
from MonitorControl.Receivers.DSN import DSN_rx
from MonitorControl.BackEnds import Backend
from MonitorControl.BackEnds.ROACH1.KurtSpec import KurtosisSpectrometer
from Electronics.Instruments import Synthesizer
from Electronics.Instruments.JFW50MS import MS287client
from Electronics.Instruments.Valon import Valon1, Valon2
from support.network import LAN_hosts_status

logging.basicConfig(level=logging.DEBUG)
module_logger = logging.getLogger(__name__)

up, down, IP, MAC, ROACHlist = LAN_hosts_status()
n_roaches = len(ROACHlist)
if n_roaches < 2:
  module_logger.warning("Only %d ROACHes available", n_roaches)
if n_roaches < 1:
  raise ObservatoryError("", "Cannot proceed without ROACHes")
roaches = ROACHlist[:2]

cfg = {14: {'S':['R','L'], 'X':['R','L']},
       15: {'S':['R'], 'X':['R']},
       24: {'S':['R'], 'X':['R'], 'Ka':['R']},
       25: {'X':['R','L'], 'Ka':['R']},
       26: {'X':['R','L'], 'Ka':['R']}}

def station_configuration(equipment, roach_loglevel=logging.WARNING):
  """
  Describe a DSN Complex

  Implicit here is the naming convention explained above for DSN front ends and
  receivers.  The telescope output name is expected to be the same as the
  telescope name.

  The front end names are constructed from the dict `cfg'.  The initialization
  of 'DSN_fe' depends on this to know the band name.
  """
  # Define the site
  obs = Observatory("GDSCC")
  tel = {}
  fe = {}
  rx = {}
  # For each station at the site
  for dss in cfg.keys():
    # define the telescope
    tel[dss] = Telescope(obs, dss=dss)
    # for each band available on the telescope
    for band in cfg[dss].keys():
      fename = band+str(dss)
      outnames = []
      # for each polarization processed by the receiver
      for polindex in range(len(cfg[dss][band])):
        outnames.append(fename+cfg[dss][band][polindex])
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
  IFswitch = ClassInstance(Device,
                           MS287client,
                           "Matrix Switch",
                           inputs={'In01': rx['S14'].outputs['S14RU'],
                                   'In02': rx['S14'].outputs['S14LU'],
                                   'In03': rx['X14'].outputs['X14RU'],
                                   'In04': rx['X14'].outputs['X14LU'],
                                   'In05': rx['S15'].outputs['S15RU'],
                                   'In06': rx['X15'].outputs['X15RU'],
                                   'In07': rx['S24'].outputs['S24RU'],
                                   'In08': rx['X24'].outputs['X24RU'],
                                   'In09': rx['Ka24'].outputs['Ka24RU'],
                                   'In10': rx['X25'].outputs['X25RU'],
                                   'In11': rx['X25'].outputs['X25LU'],
                                   'In12': rx['Ka25'].outputs['Ka25RU'],
                                   'In13': rx['X26'].outputs['X26RU'],
                                   'In14': rx['X26'].outputs['X26LU'],
                                   'In15': rx['Ka26'].outputs['Ka26RU'],
                                   'In16': None,
                                   'In17': None,
                                   'In18': None,
                                   'In19': None,
                                   'In20': None,
                                   'In21': None,
                                   'In22': None,
                                   'In23': None,
                                   'In24': None},
                           output_names=['IF1', 'IF2', 'IF3', 'IF4'])
  equipment['IF_switch'] = {"DTO": IFswitch}
  sample_clk = {}
  sample_clk[0] = ClassInstance(Synthesizer,Valon1,timeout=10)
  sample_clk[1] = ClassInstance(Synthesizer,Valon2,timeout=10)
  module_logger.debug(" roach1 sample clock is %f",
                 sample_clk[0].get_p("frequency"))
  module_logger.debug(" roach2 sample clock is %f",
                 sample_clk[1].get_p("frequency"))
  equipment['sampling_clock'] = sample_clk
  BE = ClassInstance(Backend,
                     KurtosisSpectrometer,
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
  return obs, equipment

if __name__ == "__main__":

  from MonitorControl.Configurations.configGDSCC.DTO import station_configuration
  obs, tel, fe, rx, IFswitch, sample_clk, BE = station_configuration()
  print "obs =",obs
  print "tel =",tel
  print "fe =",fe
  print "rx =",rx
  print "IFswitch =",IFswitch
  print "Sample clock =", sample_clk
  print "Backend =", BE
