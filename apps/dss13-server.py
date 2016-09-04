"""
Server for receivers and instruments at DSS-13
"""
import logging

from support.logs import init_logging, get_loglevel, set_loglevel
from MonitorControl.Configurations import station_configuration
from MonitorControl.config_test import show_signal_path

logging.basicConfig(level=logging.INFO)

logpath = "/tmp/" # for now

if __name__ == "__main__":

  mylogger = logging.getLogger()
  init_logging(mylogger,
               loglevel = logging.INFO,
               consolevel = logging.INFO,
               logname = logpath+"DSS-13_server.log")
  mylogger.debug(" Handlers: %s", mylogger.handlers)
    
  observatory, equipment = station_configuration('dss-13')
  telescope = equipment['Telescope']
  frontends = equipment['FrontEnd']
  receivers = equipment['Receiver']

  show_signal_path([frontends['X-X/Ka'], receivers['X-X/Ka']])
  show_signal_path([frontends['Ka-X/Ka'], receivers['Ka-X/Ka']])
  show_signal_path([frontends['S-S/X'],  receivers['S-S/X']])
  show_signal_path([frontends['X-S/X'],  receivers['X-S/X']])
  show_signal_path([frontends['XXKa'], receivers['XXKa']])
  show_signal_path([frontends['Xwide'],receivers['GSSR']])
  show_signal_path([frontends['K'],    receivers['K']])
  show_signal_path([equipment['IF_switch']['pedestal']])
