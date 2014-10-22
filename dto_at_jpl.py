# -*- coding: utf-8 -*-
"""
Hardware configuration for DTO in PSDG lab at JPL

This describes the signal flow from the front ends through switches and
receivers to the signal processors.  It also identifies the specific
hardware used to implement generic devices.

Examples of use::
 In [8]:  station_configuration(firmware =
   {'roach1':'kurt_spec','roach2':'kurt_spec'},
   roach_loglevel = Logging.logging.WARNING)
 Out[8]:
  (<Observatory.Observatory object at 0x30044d0>,
   DSS-21,
   {'noise': noise source, 'tone': synthesizer},
   {'RFI': noise with RFI, 'noise': pure noise, 'tone': pure tone},
   {'RFI': noise +RFI, 'noise': pure noise, 'tone': tone},
   {0: IF_sw 0, 1: IF_sw 1, 2: IF_sw 2, 3: IF_sw 3},
   {0: KurtSpec 0, 1: KurtSpec 1, 2: KurtSpec 2, 3: KurtSpec 3},
   {0: <Observatory.Instruments.synthesizers.Valon1 object at 0x3100650>,
    1: <Observatory.Instruments.synthesizers.Valon2 object at 0x31006d0>})
"""
from MonitorControl import Observatory, Telescope, Switch, ClassInstance, DataChl
from MonitorControl.FrontEnds import FrontEnd
from MonitorControl.Receivers import Receiver
from MonitorControl.BackEnds import Backend
from Electronics.Instruments import Synthesizer
from Electronics.Switches import JFW50MS287
from Observatory.BackEnds.ROACH.roach import Roach, Spec
from Observatory.BackEnds.ROACH.kurt_spec import KurtosisSpectrometer
from Electronics.Instruments.synthesizers import Valon1,Valon2
import logging

module_logger = logging.getLogger(__name__)

def trace_signals(FE_chl,DC):
  for key in FE_chl.keys():
    module_logger.debug(" FE_chl[%s] connects to DC[%s]",
                        key, str(FE_chl[key].destinations))
  for key in DC.keys():
    module_logger.debug(" DC[%s] signal source is %s",
                   key,str(DC[key].sources))
  
def station_configuration(roach_loglevel=logging.WARNING):
  """
  This is the test setup in the lab with simulated 'front ends' and
  'downconverters'::
   FE     FE_chl     DC
                                 +---+                   ROACH
   noise  +RFI    noise+RFI  --1 |   |                   +---+
                  none       --2 |   | 1--ADC0 input 0 --|   |
                  none       --3 | s |                   | 1 |
                  none       --4 | w | 2--ADC0 input 1 --|   |
   noise  pure    pure-noise --5 | i |                   +---+
                  none       --6 | t |                   +---+
                  none       --7 | c | 3--ADC0 input 0 --|   |
                  none       --8 | h |                   | 2 |
   tone   pure    tone       --9 |   | 4--ADC0 input 1 --|   |
                             ...                         +---+
                  none       -24 |   |
                                 +---+
  The superclasses, which are defined in module Observatory, are::
   - Observatory - site for the control room and signal processing equipment
   - Telescope   - which captures the radiation
   - FrontEnd    - which receives the radiation and splits it into its various
                   channels for further processing
   - FE_channel  - which processes on signal stream from the front end
   - Receiver    - which does the down-conversion for one channel
   - Backend     - which processes the down-converted signal from a channel
   - Switch      - which can change the routing of a signal
  When required, to specify monitor and control code, a superclass is
  subclassed with a device class.  Examples shown below are class
  KurtosisSpectrometer() for the BackEnd() superclass and JFW50MS287() for the
  Switch() superclass.
  
  @return: class instances for hardware
  """
  # specify the observing context
  lab = Observatory("PSDGlab")
  telescope = Telescope(lab,dss=21)
  # specify the front ends; no actual M&C of hardware since DTO doesn't have
  # that option so no implementation class needed
  FE = {}
  FE["noise"]   = FrontEnd(telescope,"noise source")
  FE["antenna"] = FrontEnd(telescope,"amplified paperclip")
  FE["tone"]    = FrontEnd(telescope,"synthesizer")
  # define the front end channels; again, no actual M&C hardware
  FE_chl = {}
  FE_chl['noise'] = FE_channel(FE["noise"],  "pure noise")
  FE_chl['RFI']   = FE_channel(FE["antenna"],"noise with RFI")
  FE_chl['tone']  = FE_channel(FE["tone"],   "pure tone")
  # specify the down-converters and their signal sources; also not under our
  # control so no implementation classes
  DC = {}
  DC['noise'] = Receiver(FE_chl['noise'],"pure noise")
  DC['RFI']   = Receiver(FE_chl['RFI'],  "noise +RFI")
  DC['tone']  = Receiver(FE_chl['tone'], "tone")
  # specify where the DC inputs come from. There's no way to automate this.
  # These are single item lists because they are one-to-one connections
  #FE_chl['noise'].destinations = [DC['noise']]
  #FE_chl['RFI'].destinations   = [DC['RFI']]
  #FE_chl['tone'].destinations  = [DC['tone']]
  #DC['noise'].sources = [FE_chl['noise']]
  #DC['RFI'].sources   = [FE_chl['RFI']]
  #DC['tone'].sources  = [FE_chl['tone']]
  # The spectrometers require sample clock generators.
  sample_clk = {}
  sample_clk[0] = ClassInstance(Synthesizer,Valon1,timeout=10)
  sample_clk[1] = ClassInstance(Synthesizer,Valon2,timeout=10)
  module_logger.debug(" roach1 sample clock is %f",
                 sample_clk[0].get_p("frequency"))
  module_logger.debug(" roach2 sample clock is %f",
                 sample_clk[1].get_p("frequency"))
  # describe the backend input selector switches; real hardware this time
  IFsw = {}
  for index in range(4):
    IFsw[index] = ClassInstance(Switch,
                                JFW50MS287,
                                lab,
                                index,
                                inputs=[DC['RFI'],  None,None,None,
                                        DC['noise'],None,None,None,
                                        DC['tone'], None,None,None,
                                        None,       None,None,None,
                                        None,       None,None,None,
                                        None,       None,None,None])
    state = IFsw[index].get_state()
    signal_source = IFsw[index].sources[0]
    module_logger.debug(" IFsw[%d] state is %d",index, state)
    module_logger.debug(" IFsw[%d] signal source is %s",
                                                   index, str(signal_source))
    signal_source.destinations.append((IFsw[index],state))
  # Specify the backends; we need these before we can specify the switch
  # The back-end IDs are keyed to the switch outputs, that is, the first
  # switch output feeds spectrometer[0], the last spectrometer[3].
  roach = {}
  roaches = ['roach1','roach2'] # firmware.keys()
  roaches.sort()
  spec = {}
  data_channel = {}
  for name in roaches:
    module_logger.debug(' Instantiating %s', name)
    roach_index = int(name[-1]) - 1
    roach[roach_index] = ClassInstance(Backend,
                                       Spec,
                                       lab,
                                       key = None,
                                       roach=name,
                                       LO = sample_clk[roach_index],
                                       loglevel = roach_loglevel)
    spec[roach_index] = find_BE_channels(roach[roach_index])
    data_channel[roach_index] = {0: DataChl(roach[roach_index],
                                            'gbe0',
                                            'gpu1',
                                            10000)}
    # This so far assumes that there is only one ADC in ZDOC 0.
    if spec.has_key(roach_num):
      if spec[roach_num].has_key(0):
        if spec[roach_num][0].has_key(RFnum):
          spec[roach_num][0][RFnum].sources = [IFsw[index]]
          IFsw[index].destinations = [spec[roach_num][0][RFnum]]
  # This set of loops only serves a diagnostic purposee.
  for roach_index in spec.keys():
    for ADC_index in spec[roach_index].keys():
      for RF in spec[roach_index][0].keys():
        module_logger.debug(" spec[%d][0][%d] signal source is %s",
                   roach_index, RF, str(spec[roach_index][0][RF].sources) )
  return lab, telescope, FE, FE_chl, DC, IFsw, roach, spec, sample_clk
 
def find_BE_channels(roach):
  """
  Find the BE_channel instances associated with a Backend instance

  This assumes that BE_channel instances were created when a Spec
  instance is created.
  
  @param roach : Roach object
  @type  roach : Backend instance

  @param spec : multi-level dictionary of BE_channel instances
  """
  myspec = {}
  module_logger.debug("find_BE_channels: finding spec[%d]",roach.number)
  ADC_keys = roach.ADC_inputs.keys()
  if roach.BE_channels:
    for ADC in ADC_keys:
      module_logger.debug("find_BE_channels: finding spec[%d][%d]",
                          roach.number,ADC)
      myspec[ADC] = {}
      for RF in roach.ADC_inputs[ADC]:
        module_logger.debug("find_BE_channels: finding spec[%d][%d][%d]",
                            roach.number,ADC,RF)
        myspec[ADC][RF] = roach.BE_channels[ADC][RF]
  module_logger.debug("find_BE_channels: Found instances: %s", str(myspec))
  return myspec
