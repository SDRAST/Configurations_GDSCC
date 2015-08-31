import logging
from support.logs import init_logging, get_loglevel, set_loglevel
logging.basicConfig(level=logging.INFO)
logpath = "/tmp/" # for now
mylogger = logging.getLogger()
init_logging(mylogger,
             loglevel = logging.INFO,
             consolevel = logging.DEBUG,
             logname = logpath+"DSS-13_server.log")
mylogger.debug(" Handlers: %s", mylogger.handlers)

from MonitorControl.Configurations import station_configuration
    
observatory, equipment = station_configuration('dss-13')
telescope = equipment['Telescope']
frontends = equipment['FrontEnd']
receivers = equipment['Receiver']

if __name__ == "__main__":
  from MonitorControl.config_test import show_signal_path
  show_signal_path([frontends['X-X/Ka'], receivers['X-X/Ka']])
  show_signal_path([frontends['Ka-X/Ka'], receivers['Ka-X/Ka']])
  show_signal_path([frontends['S-S/X'],  receivers['S-S/X']])
  show_signal_path([frontends['X-S/X'],  receivers['X-S/X']])
  show_signal_path([frontends['XXKa'], receivers['XXKa']])
  show_signal_path([frontends['Xwide'],receivers['GSSR']])
  show_signal_path([frontends['K'],    receivers['K']])
