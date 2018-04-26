"""
Test of SAO spectrometer firmware

In the DTO configuration equipment there is no 'FE_selector' or 'Rx_selector'.
The 'sampling_clock' is not relevant and can be removed.  We do not control it.

The only devices we can control are the DTO IF switch and the ROACHes.
"""
import logging
import sys

from MonitorControl.Configurations import station_configuration
from support.logs import get_loglevel, initiate_option_parser, init_logging
from support.logs import set_module_loggers
from support.pyro import PyroServerLauncher, PyroServer

logger = logging.getLogger(__name__)

class DTO_Manager(PyroServer):
  """
  Class for operation of the kurtosis spectrometer server and other servers
  
  This manages all the systems in an integrated way. Specific devices which are
  controlled are::
    sample_clk   - controlled indirectly via the spectrometer
    spectrometer - two ROACHes configured with kurtosis spectrometer firmware
    switch       - the JFW50MS287 24x4 IF switch
  For this server (DTO_mgr-dtoServer) to run, the other servers MS287server and
  kurtosis_spectrometerServer must already be running.
  
  Attributes::
    DSPnames     - names of the DSP (ROACH) objects (list)
    gain         - gain of RF sections  (dict of dicts)
    RFids        - RF inputs for each DSP (dict) 
    spectrometer - Backend object
    switch       - IF switch object
    sw_states    - input port associated with each output of switch
  
  Methods::
    adjust_ADC_inputs         - Adjusts the RF section gains to be optimized
    check_ADC_inputs          - Gets the input levels to the ADC RF ports
    check_ADC_temps           - Get ADC temperatures
    check_firmware            - Firmware running
    check_ROACH_fans          -
    get_active_channels       - Return a list of switch inputs connected to IFs
    get_sampler_clocks_status -
    help_methods              -
    survey_ADC_inputs         -
    survey_input_spectra      -
    update_gains              -
  """
  def __init__(self, name, configuration='DTO'):
    """
    """
    PyroServer.__init__(self) #  This screws up logging in this class
    self.logger = logging.getLogger(logger.name+".DTO_Manager")
    self.logger.debug("__init__: getting configuration")
    obs, equip = station_configuration('DTO-32K')
    self.switch = equip['IF_switch']['DTO']
    self.spectrometer = equip['Backend']
    self.sample_clk = equip['sampling_clock']
    self.logger.debug("__init__: getting status")
    self.sw_states = self.switch.get_states()
    self.DSPnames = self.spectrometer.roach.keys()
    self.RFchannel = {}
    self.gain = {}
    self.enabled = {}
    self.firmware = {}
    for name in self.DSPnames:
      RFids = self.spectrometer.roach[name].RFchannel.keys()
      self.RFchannel[name] = {} 
      self.gain[name] = {}
      self.enabled[name] = {}
      self.firmware[name] = self.spectrometer.roach[name].firmware()
      for RF in RFids:
        self.RFchannel[name][RF] = self.spectrometer.roach[name].RFchannel[RF]
        self.gain[name][RF] = self.RFchannel[name][RF].RF_gain_get()
        self.enabled[name][RF] = self.RFchannel[name][RF].RF_enabled()
    self.logger.debug("__init__: done")
    
  def adjust_ADC_inputs(self):
    """
    Adjusts the RF section gains to be optimized
    
    NOT FINISHED
    """
    self.ADC_input = {}
    for name in self.DSPnames:
      self.ADC_input[name] = {}
      for RF in self.RFchannel[name].keys():
        self.ADC_input[name][RF] = self.RFchannel[name][RF].get_ADC_input()
    return self.ADC_input
        
  def check_ADC_inputs(self):
    """
    Gets the input levels to the ADC RF ports
    
    Example::
      In [6]: dto.check_ADC_inputs()
      Out[6]: {'roach1': {'Ro1In1': {'Vrms ADC': 0.077036732881698239,
                                     'W ADC': 0.00011869316426172253,
                                     'dBm ADC': -9.2557429207235806,
                                     'sample mean': -0.9522705078125,
                                     'sample std': 19.602222107302349},
                          'Ro1In2': {'Vrms ADC': 0.3967253365333282,
                                     'W ADC': 0.0031478198529496502,
                                     'dBm ADC': 4.9800987009472388,
                                     'sample mean': 0.75634765625,
                                     'sample std': 100.94792278201734}},
               'roach2': {'Ro2In1': {'Vrms ADC': 0.058285365018334714,
                                     'W ADC': 6.7943675506410312e-05,
                                     'dBm ADC': -11.678509630742379,
                                     'sample mean': -0.6939697265625,
                                     'sample std': 14.830881684054635},
                          'Ro2In2': {'Vrms ADC': 0.058425994756105,
                                     'W ADC': 6.8271937264808175e-05,
                                     'dBm ADC': -11.657577735584706,
                                     'sample mean': -0.47607421875,
                                     'sample std': 14.866665332342238}}}
    """
    self.ADC_input = {}
    for name in self.DSPnames:
      self.ADC_input[name] = {}
      self.logger.debug("check_ADC_inputs: for %s", self.RFchannel[name])
      for RF in self.RFchannel[name].keys():
        self.logger.debug("check_ADC_inputs: called for %s channel %s", name, RF)
        self.ADC_input[name][RF] = self.RFchannel[name][RF].get_ADC_input()
    return self.ADC_input
            
  def check_ADC_temps(self):
    """
    Get ADC temperatures
    
    Example::
      In [3]: dto.check_ADC_temps()
      Out[3]: {'roach1': {0: {'IC': 72.875,   'ambient': 36.25}},
               'roach2': {0: {'IC': 107.1875, 'ambient': 40.9375}}}

    """
    self.ADC_temps = {}
    for name in self.DSPnames:
      # m.roaches keys are integers
      if self.spectrometer.roach[name]:
        # 'None' is allowed but ignored
        if self.spectrometer.roach[name].firmware:
          try:
            self.logger.info("check_ADC_temps: for %s", name)
            self.ADC_temps[name] = self.spectrometer.roach[name].get_temperatures()
          except RuntimeError:
            self.logger.error(" Could not get "+name+" temperatures", exc_info=True)
            self.ADC_temps[name] = None
        else:
          self.logger.warning(
                       " Cannot get roach %s temps because it has no firmware",name)
          self.ADC_temps[name] = None
      else:
        self.logger.warning(" 'None' was ignored for roach %s", ID)
        self.ADC_temps[name] = None
    return self.ADC_temps
  
  def check_firmware(self):
    """
    Firmware running
    
    NOT FINISHED
    """
    self.logger.info(" Boffiles: %s",self.spectrometer.boffiles)
    self.logger.info(" Alive: %s",self.spectrometer.alive)
    self.logger.info(" Firmware: %s",self.spectrometer.firmware)
    return {"Bofs": self.spectrometer.boffiles,
            "Alive": self.spectrometer.alive,
            "firmware": self.spectrometer.firmware}

  def check_ROACH_fans(self):
    """
    """
    fan_state = {}
    for name in self.DSPnames:
      fan_state[name] = self.spectrometer.roach[name].check_fans()
    return fan_state

  def get_active_channels(self):
    """
    Returns a list of switch inputs connected to IF channels
    """
    sources = {}
    for inp in self.IFswitch.inputs.keys():
      if self.IFswitch.inputs[inp].source:
        sources[self.IFswitch.inputs[inp].name] = self.IFswitch.inputs[inp].source
    return sources
    
  def get_sampler_clocks_status(self):
    """
     Get states of sampler clocks
    """
    for clk in self.sample_clk.keys():
      self.sample_clk[clk].update_synth_status()
      self.sample_clk[clk].status = self.sample_clk[clk].hw.status[clk+1]
      self.sample_clk[clk].freq   = self.sample_clk[clk].status["frequency"]
      self.sample_clk[clk].pwr    = self.sample_clk[clk].status["rf_level"]
      self.logger.info(
                 "get_sampler_clocks_status:\nsampler clock %d status is %s",
                 clk, self.sample_clk[clk].status)
      return self.sample_clk[clk]          

  def survey_ADC_inputs(self, dtype='sample std'):
    """
    Gets the ADC input levels of all 24 IF switch inputs
    
    The way this is done depends on the firmware.  The kurtosis firmware can
    handle two IFs per ROACH.  The spectrometer firmware only one.  Also, the
    IF names differ.
    
    Example::
      In [8]: dto.survey_ADC_inputs()
      Out[8]: { 0: 15.817079517489939,   1: 115.07169265166732,
                2:  7.9240825810617839,  3: 118.03780773433128,
               ...
               20: 19.866611599872531,  21: 100.37293565384729,
               22: 14.672623631996771,  23:  15.126908283893673}
    """
    ADCin = {}
    if self.firmware['roach1'] != self.firmware['roach2']:
      self.logger.error(
                    "survey_ADC_inputs: roaches do not have the same firmware")
    elif self.firmware['roach1'] == 'sao_spec':
      for SWin in range(0,24,2):
        for SWout in range(2):
          self.switch.set_state(str(SWout+1), SWin+SWout+1)
        ADC_levels = self.check_ADC_inputs()
        ADCin[SWin]   = ADC_levels['roach1']['IF1pwr'][dtype]
        ADCin[SWin+1] = ADC_levels['roach2']['IF2pwr'][dtype]
    else:
      # assume 'kurt_spec' with two IFs per ROACH
      for SWin in range(0,24,4):
        for SWout in range(0,4):
          self.switch.set_state(str(SWout+1), SWin+SWout+1)
        ADC_levels = self.check_ADC_inputs()
        ADCin[SWin]   = ADC_levels['roach1']['Ro1In1'][dtype]
        ADCin[SWin+1] = ADC_levels['roach1']['Ro1In2'][dtype]
        ADCin[SWin+2] = ADC_levels['roach2']['Ro2In1'][dtype]
        ADCin[SWin+3] = ADC_levels['roach2']['Ro2In2'][dtype]
    self.logger.info("survey_ADC_inputs: %s", ADCin)
    return ADCin

  def survey_input_spectra(self, moment=2):
    """
    Gets spectra from all 24 IF switch inputs
    
    Example::
      In [6]: power = dto.survey_input_spectra()
      In [7]: power
      Out[7]: 
      {0: array([ 16832073.,    653468.,    ...,     80056.,     36481.]),
       1: array([    25911.,      3965.,    ...,      1308.,       762.]),
       2: array([  1921445.,   1184770.,    ...,   1436680.,  24885598.]),
       ...
      22: array([  2605225.,    826109.,    ...,    542307.,    692218.]),
      23: array([    37307.,      2800.,    ...,      1693.,       522.])}
    """
    data = {}
    for SWin in range(0,24,4):
      for SWout in range(0,4):
        self.switch.set_state(str(SWout+1), SWin+SWout+1)
        index = SWin+SWout
        roachID = 1 + SWout % 2
        RFid = 1 + SWout // 2
        roach = "roach"+str(roachID)
        rf = "Ro"+str(roachID)+"In"+str(RFid)
        data[index] = self.RFchannel[roach][rf].get_accums()[moment]
    return data
  
  def update_gains(self):
    """
    Gets the current gain settings of the RF sections
    
    Example::
      In [20]: dto.update_gains()
      Out[20]: {'roach1': {'Ro1In1': 20.0, 'Ro1In2': 20.0},
                'roach2': {'Ro2In1': 20.0, 'Ro2In2': 20.0}}
    """
    for name in self.DSPnames:
      for RF in self.RFchannel[name].keys():
        self.gain[name][RF] = self.RFchannel[name][RF].RF_gain_get()
        self.enabled[name][RF] = self.RFchannel[name][RF].RF_enabled()
    return self.gain
  
  def RF_enabled(self):
    """
    """
    return self.enabled
  
  def help_methods(self):
    """
    Returns help for DTO_Manager methods
    
    Example::
      In [4]: methods = dto.help_methods()
      In [5]: for key in methods.keys():
         ...:     print key
         ...:     print methods[key]
         ...: 
         
      get_sampler_clocks_status
          Get states of sampler clocks
    
      survey_input_spectra
          Gets spectra from all 24 IF switch inputs
    
          Example::
            In [6]: power = dto.survey_input_spectra()
            In [7]: power
            Out[7]: 
            {0: array([ 16832073.,    653468.,    ...,     80056.,     36481.]),
             1: array([    25911.,      3965.,    ...,      1308.,       762.]),
             2: array([  1921445.,   1184770.,    ...,   1436680.,  24885598.]),
             ...
            22: array([  2605225.,    826109.,    ...,    542307.,    692218.]),
            23: array([    37307.,      2800.,    ...,      1693.,       522.])}
      ...    
    
      get_active_channels
          Returns a list of switch inputs connected to IF channels
    """
    mkeys = DTO_Manager.__dict__.keys()
    report = {}
    for key in mkeys:
      if key[:2] == "__":
        continue
      else:
        report[key] = DTO_Manager.__dict__[key].__doc__
    return report
    
if __name__ == "__main__":
  from socket import gethostname
  __name__ = 'DTO_manager'

  loggers = set_module_loggers(
    {'MonitorControl':                                'debug',
     'support':                                       'warning',
     'Electronics.Instruments.JFW50MS':               'warning',
     'MonitorControl.BackEnds.ROACH1.firmware_server':'warning'})
       
  from optparse import OptionParser
  p = initiate_option_parser("Pyro server for SAObackend.","")
  p.usage = 'manager.py [options]'
  p.description = __doc__
  args = p.parse_args(sys.argv[1:])

  logger.setLevel(logging.DEBUG) # why this?
  # This cannot be delegated to another module or class
  mylogger = init_logging(logging.getLogger(),
                          loglevel   = get_loglevel(args.file_loglevel),
                          consolevel = get_loglevel(args.console_loglevel),
                          logname    = args.logpath+__name__+".log")
  mylogger.debug(" Handlers: %s", mylogger.handlers)
  loggers = set_module_loggers(eval(args.modloglevels))

  # Set the module logger levels no lower than my level.
  for lgr in loggers.keys():
    if loggers[lgr].level < mylogger.level:
      loggers[lgr].setLevel(mylogger.level)
    mylogger.info("%s logger level is %s", lgr, loggers[lgr].level)

  psl = PyroServerLauncher(__name__+"Server") # the name by which the Pyro task is known
  m = DTO_Manager(__name__)
  mylogger.info(" Starting server...")
  psl.start(m)
  # clean up after the server stops
  mylogger.debug(" Server done.")
  psl.finish()

