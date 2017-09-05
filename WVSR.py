"""
For WVSR backend using standard DSN receivers
"""
import IPython
IPython.version_info = IPython.release.version.split('.')
IPython.version_info.append('')

import logging

from MonitorControl import ClassInstance
from MonitorControl.BackEnds import Backend
from MonitorControl.BackEnds.DSN import WVSRbackend
from MonitorControl.BackEnds.DSN.helpers import WVSRmetadataCollector
from MonitorControl.Configurations.DSN_standard import standard_equipment
from support.logs import init_logging, get_loglevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def station_configuration(equipment, project, dss, year, doy, band,
                          roach_loglevel=None):
  """
  describe a standard DSN Complex with WVSR recorders
  """
  rx_name = band+str(dss)
  rx = equipment['Receiver'][rx_name]
  collector = WVSRmetadataCollector(project, dss, year, doy)
  BE_inputs = {}
  output_names = []
  for wvsr in collector.wvsr_cfg.keys():
    for IF in collector.wvsr_cfg[wvsr]['channels']:
      BE_inputs["IF"+str(IF)] = rx.outputs[rx_name + \
                                 collector.wvsr_cfg[wvsr][IF]['pol'][0] + 'U']
    for subch in collector.wvsr_cfg[wvsr][1]['subchannels']:
        for Stokes in ['I', 'Q', 'U', 'V']:
          output_names.append(rx_name + "_"+subch+"_"+Stokes)
  logger.debug("station_configuration: BE inputs: %s", BE_inputs)
  logger.debug("station_configuration: BE outputs: %s", output_names)
  BE = ClassInstance(Backend,
                     WVSRbackend,
                     "WVSR spectrometer",
                     collector,
                     inputs = BE_inputs,
                     output_names = output_names)
  equipment['Backend'] = BE
  return equipment
  
if __name__ == "__main__":
  from MonitorControl.config_test import show_signal_path
  
  mylogger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  mylogger = init_logging(mylogger,
                        loglevel = logging.INFO,
                        consolevel = logging.DEBUG,
                        logname = "/var/tmp/WVSRbe.log")
  equipment = standard_equipment(14)
  equipment = station_configuration(equipment,'AUTO_EGG', 14, 2016, 237, 'X')
  
  show_signal_path([equipment['FrontEnd']['X14'],
                    equipment['Receiver']['X14'],
                    equipment['Backend']])

