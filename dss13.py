"""
Configuration information for DSS-13

Documentation
=============
Documents::
  1 DSS13-report-on-configuration-performance-8-1-14.pdf       dated 2014-08-01
  2 Load and Diode Control-DSS13.pdf                           dated 
  3 4X16 Switch-1.pdf                                          dated 2011-08-24
"""
import re
import logging
module_logger = logging.getLogger(__name__)

from MonitorControl import Beam, ComplexSignal, IF, Device, Observatory, Port
from MonitorControl import Switch, ClassInstance, Telescope
from MonitorControl import valid_property, link_ports
from MonitorControl.FrontEnds import FrontEnd
from MonitorControl.Receivers import Receiver
from MonitorControl.BackEnds import Backend
from MonitorControl.Switches.Ellipsoid13.client import Ellipsoid

def make_IFMS_outputs():
  names = []
  for n in range(1,25):
    names.append('out%02d' % n)
  return names
    
# ================================== Front Ends ===============================
    
class DSNfe(FrontEnd):
  """
  A generic DSN front end.

  This handles bands S, X and Ka.  A DSN front end has only one input but
  either one or two outputs for one or two polarizations.
    
  The standard DSN receivers are dual S/X and dual X/Ka, separately fed using
  a dichroic reflector to divert the longer wavelength beam.  It may have two
  simultaneous polarizations, RCP and LCP, and so two IFs, or one manually
  selectable polarization.  The normal position of the polarizer is then RCP.

  If the band is not specified with the keyword argument 'band' then this
  superclass requires a naming convention for the band in which the actual
  band code appears first in the name, for example, X-X/Ka and Ka-X/Ka.
  The first occurrence of a valid band code in the name is used as the
  band.

  The polarization of each output is specified with a dict in the keyword
  argument 'pols_out'.  The output port names are the keys of the dict.
  If the dict is not specified then the keyword argument 'output_names'
  must be specified with one polarization code appearing in the name.
  """
  def __init__(self, name, inputs=None, band=None, pols_out=None,
               output_names=None, active=True):
    """
    Creates a DSN FrontEnd object.

    A DSN FrontEnd object has one input and two outputs.  If each feed produces
    two pols and the implicit polarization encoding is used, each output pair 
    for a given feed is a list.  For pols_out it is a list of lists dicts and 
    for output_names it is a list of list of str.

    @param name : unique name to identify this instance
    @type  name : str

    @param inputs : upstream Port objects providing the signals
    @type  inputs : dict of Port instances

    @param band : optional waveguide band in which the front end operates.
    @type  band : str

    @param pols_out : optional polarization spec for the outputs (see docstr)
    @type  pols_out : dict of str

    @param output_names : optional names to be assigned to output ports
    @type  output_names : list of str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool
    """
    mylogger = logging.getLogger(module_logger.name+".DSNfe")
    mylogger.debug(" initializing FrontEnd %s", self)
    band, output_names, pols_out = get_FE_band_and_pols(inputs,
                                                        band=band,
                                                        pols_out=pols_out,
                                                     output_names=output_names)
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    self.outputs = connect_FE_inputs_and_outputs(self.inputs,
                                                 band,
                                                 self.outputs,
                                                 pols_out)
    self.logger.debug(" initialized  for %s",self)
         
class XXKa_fe(FrontEnd):
  """
  This has a coaxial feed pair and five outputs::
    # X-RCP
    # X-LCP
    # Ka-RCP
    # Ka-LCP
    # Ka-RCP-error
  It also has an 80-kW Ka transmitter.
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".XXKa_fe")
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    self.logger.debug("__init__: outputs: %s", self.outputs)
    self.logger.debug(" initialized  for %s",self)
                      
class XwideFE(FrontEnd):
  """
  This is an X-band receiver with the cryogenic passband filter removed.
  """
  def __init__(self, name, inputs=None, band=None, pols_out=[],
               output_names=None, active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".XwideFE")
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    self.logger.debug("__init__: outputs: %s", self.outputs)

class DSN_K(FrontEnd):
  """
  This is a 26-GHz receiver used primarily for lunar mission support.
  
  This has a manually selectable polarization.
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    
    """
    mylogger = logging.getLogger(module_logger.name+".DSN_K")
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    # It's not clear to me why I don't use DSN_fe.
    for key in list(self.inputs.keys()):
      self.logger.debug("__init__: %s signal source is %s",
                        self.inputs[key], self.inputs[key].source)
      self.inputs[key].signal = self.inputs[key].source.signal
      self.logger.debug("__init__: %s input signal is %s", self,
                        self.inputs[key].signal)
      if self.inputs[key].signal == None:
        self.inputs[key].signal = Beam('none')
      self.inputs[key].signal.data['band'] = 'K'
    link_ports(self.inputs,self.outputs)
    for key in list(self.outputs.keys()):
      self.outputs[key].signal = ComplexSignal(self.outputs[key].source.signal)
    self.logger.debug("__init__: outputs: %s", self.outputs)

# ---------------------------------- Receivers --------------------------------

class DSNrx(Receiver):
  """
  Generic DSN receiver class.

  These typically have fixed local oscillators.  It may handle one or
  two polarizations.

  This superclass requires a naming convention for the band in which the
  actual band code appears first in the name, for example, X-X/Ka and Ka-X/Ka.
  The first occurrence of a valid band code in the name is used as the
  band.

  Likewise, for the output ports, the IF type must appear first.
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    Initialize a DSN receiver instance.
    
    

    @param name : unique identifier
    @type  name : str

    @param inputs : signal channels
    @type  inputs : Port instances

    @param output_names : names of the output channels/ports
    @type  output_names : list of str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool
    """
    mylogger = logging.getLogger(module_logger.name+".DSNrx")
    IF_out = get_receiver_IF_output_types(output_names)
    Receiver.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    
    # Having the band and pol in the output name is helpful but not required.
    valid_property(output_names, 'band', abort=False)
    valid_property(output_names, 'pol', abort=False)
    
    self.outputs = connect_receiver_inputs_and_outputs(self.inputs,
                                                       self.outputs,
                                                       IF_out)
    self.logger.debug("__init__: outputs: %s", self.outputs)

class GSSRdc(Receiver):
  """
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".GSSRdc")
    Receiver.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    #self.name = name
    self.logger.debug("__init__: outputs: %s", self.outputs)

class Kdc(Receiver):
  """
  I don't know anything about this, really.
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    This receiver has two inputs and two outputs
    """
    mylogger = logging.getLogger(module_logger.name+".Kdc")
    Receiver.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    inkeys = list(self.inputs.keys())
    inkeys.sort()
    outkeys = list(self.outputs.keys())
    outkeys.sort()
    self.chan = {}
    for key in inkeys:
      index = inkeys.index(key)
      outname = outkeys[index]
      ch_inputs = {key: self.inputs[key]}
      self.chan[key] = Receiver.RFsection(self, key, inputs=ch_inputs,
                                                        output_names=[outname])
      link_ports(ch_inputs, self.chan[key].outputs)
      for chkey in list(self.chan[key].outputs.keys()):
        self.outputs[chkey] = self.chan[key].outputs[chkey]
    self.logger.debug("__init__: outputs: %s", self.outputs)

class MMS(Receiver):
  """
  """
  def __init__(self, name, inputs=None,
                      output_names=[], active=False):
    mylogger = logging.getLogger(module_logger.name+".Kdc")
    Receiver.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    if inputs:
      self.DC = Receiver.RFsection(self, name, inputs=inputs,
                                   output_names=output_names)

class XXKa(Receiver):
  """
  This receiver has two X-band pols and two Ka-band pols.
  """
  def __init__(self, name, inputs=None,
                      output_names=[], active=False):
    """
    Create an XXKa receiver object
    
    @param name : name assigned to the receivers
    @type  name : str

    @param inputs : signal channels
    @type  inputs : Port instances

    @param output_names : names of the output channels/ports
    @type  output_names : list of str
    
    @param active : receiver is available AND WORKING IF True
    """
    mylogger = logging.getLogger(module_logger.name+".XXKa")
    Receiver.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    
    if inputs == []:
      raise 
      inkeys = list(self.inputs.keys())
      inkeys.sort()
      outkeys = list(self.outputs.keys())
      outkeys.sort()
      self.chan = {}
      for key in inkeys:
        index = inkeys.index(key)
        outname = outkeys[index]
        ch_inputs = {key: self.inputs[key]}
        self.logger.debug("__init__: %s inputs: %s", key, ch_inputs)
        self.logger.debug("__init__: %s output: %s", key, outname)
        self.chan[key] = Receiver.RFsection(self, key, inputs=ch_inputs,
                                                        output_names=[outname])
      link_ports(ch_inputs, self.chan[key].outputs)
      for chkey in list(self.chan[key].outputs.keys()):
        self.outputs[chkey] = self.chan[key].outputs[chkey]
    self.logger.debug("__init__: outputs: %s", self.outputs)
        

# ===================================== Switches ==============================
    
class HP_IFSwitch(Device):
  """
  The IF paths through the switch are:
  J100 o--                    --o 215 ---- 300 - 
  J101 o  \                  /  o 214 ---- 304  \
  J102 o   \                /   o 213 ---- 308   \
  J103 o------o- channel 0 -----o 212 ---- 312    \
                                                   |
  J104 o--                    --o 211 ---- 301 --- o -- IF0
  J105 o  \                  /  o 210 ---- 305    /|
  J106 o   \                /   o 209 ---- 309   / |
  J107 o------o- channel 1 -----o 208 ---- 313  /  |
                                                |  |
  J108 o--                    --o 207 ---- 302 -   |
  J109 o  \                  /  o 206 ---- 306    /
  J110 o   \                /   o 205 ---- 310   /
  J111 o------o- channel 2 -----o 204 ---- 314  /
                                               /
  J112 o--                    --o 203 ---- 303- 
  J113 o  \                  /  o 202 ---- 307
  J114 o   \                /   o 201 ---- 311
  J115 o------o- channel 3 -----o 200 ---- 315
  
  Likewise, (304,305,306,307) select IF2,
            (308,309,310,311) select IF3,
            (312,313,314,315) select IF4
  
  The user must select an input port, 100-115 and then an output port,
  IF0-IF3. For example, 
  """
  def __init__(self, name, inputs=None, output_names=[], active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".HP_IFSwitch")
    mylogger.debug("__init__: inputs: %s", inputs)
    Device.__init__(self, name, inputs=inputs, output_names=output_names,
                    active=active)
    self.logger = mylogger
    self.logger.debug("__init__: superclass Device initialized")
    input_names = list(inputs.keys())
    input_names.sort()
    self.channel = {}
    self.states = {}
    for key in output_names:
      index = output_names.index(key)
      start = index*4
      end = start+3
      ch_inputs = {}
      for inp in range(4):
        ch_inputs[inp] = inputs[input_names[index+inp]]
      self.logger.debug("__init__: channel inputs: %s", ch_inputs)
      self.channel[key] = self.Channel(self, key, inputs=ch_inputs,
                                       output_names=[key])
      self.states[key] = self.channel[key].state

  class Channel(Switch):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=[]):
      self.parent = parent
      self.stype = "Nx1"
      mylogger = logging.getLogger(parent.logger.name+".Channel")
      mylogger.debug("__init__: inputs: %s", inputs)
      Switch.__init__(self, name, inputs=inputs, output_names=output_names,
                      stype = self.stype)
      self.logger = mylogger
      for port in list(self.outputs.keys()):
        self.parent.outputs[port] = self.outputs[port]
      self.get_state()


class IFMatrixSwitch(Device):
  """
  """
  def __init__(self, name, inputs=None, output_names=[], active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".IFMatrixSwitch")
    Device.__init__(self, name, inputs=inputs, output_names=output_names,
                    active=active)
    self.logger = mylogger
    self.channel = {}
    for key in list(self.inputs.keys()):
      self.channel[key] = self.Channel(self, key,
                                       inputs={key: self.inputs[key]},
                                       output_names=output_names)

  class Channel(Switch):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=[],
                 active=True):
      """
      """
      self.parent = parent
      #self.name = name
      self.stype = "1xN"
      Switch.__init__(self, name, inputs=inputs, output_names=output_names,
                      stype = self.stype)
      for port in list(self.outputs.keys()):
        self.parent.outputs[port] = self.outputs[port]

# =================================== Back Ends ===============================

class WVSR(Backend):
  """
  """
  def __init__(self, name, inputs=None, output_names=[], active=True):
    """
    """
    #self.name = name
    mylogger = logging.getLogger(module_logger.name+".WVSR")
    Backend.__init__(self, name, inputs=inputs, output_names=output_names)
    self.logger = mylogger

# =================================== functions ===============================

def get_FE_band_and_pols(inputs, band=None, pols_out=None, output_names=[]):
  """
  This extracts band and polarization information from the input and output
  port names.
  
  The input names are checked for a valid band name as defined in the top-level
  MonitorControl module. The valid bands are accumulated in a list.  If the
  'band' argument is not specified, the first in the list is taken as the 
  receiver's band. All the inputs must have the same band code.
  
  If the polarizations of the output ports are not specified, then that
  information is extracted from the output names.  Optionally, the polarization
  of each port may be specified, in which case these are used for the output
  port names
  
  @param inputs : same as the kwarg (keyword argument) for the Device class
  @type  inputs : list of Port instances
  
  @param band : optional valid MonitorControl band code
  @type  band : str
  
  @param pols_out : optional valid MonitorControl polarization codes
  @type  pols_out : list of str
  
  @param output_names : optional names for the outputs. Use 'pols_out' if None
  @type  output_names : list of str
  
  @return: (band, output names, output polarization)
  """
  # Make sure that the band is specified
  input_keys = list(inputs.keys())
  input_keys.sort()
  module_logger.debug("get_FE_band_and_pols: inputs: %s", input_keys)
  if band == None:
    bands = valid_property(input_keys, 'band')
    if bands == False:
      raise ObservatoryError('band',' property key not found')
    band = bands[list(bands.keys())[0]]
    module_logger.debug('get_FE_band_and_pols: band is %s', band)
    if len(inputs) > 1:
      # check that all bands are the same
      if not (bands==band).all():
        raise ObservatoryError(str(band),'is not in every input name')
  # Having the band in the output name is helpful but not required.
  #valid_property(output_names, 'band', abort=False)
  # Make sure that the output polarizations are specified
  if pols_out == None and output_names == None:
    raise ObservatoryError("No outputs specified")
  elif pols_out:
    output_names = list(pols_out.keys())
    output_names.sort()
  else:
     pols_out = valid_property(output_names, 'pol_type')
  module_logger.debug("get_FE_band_and_pols: output_names=%s", output_names)
  module_logger.debug("get_FE_band_and_pols: pols_out: %s",pols_out)
  return band, output_names, pols_out

def connect_FE_inputs_and_outputs(inputs, band, outputs, pols_out):
  """
  Invokes MonitorControl function 'link_ports' to connect inputs to outputs.
  
  It sets the 'destinations' attribute for the inputs and the 'source'
  attribute for the outputs.  It also propagates the input signals to the
  outputs, or creates 'Complex Signal' objects if the input signals are not
  specified
  
  @param inputs : same as the kwarg (keyword argument) for the Device class
  @type  inputs : list of Port instances
  
  @param band : optional valid MonitorControl band code
  @type  band : str

  @param outputs : as defined in the Device initialization
  @type  outputs : list of Port instances

  @param pols_out : required valid MonitorControl polarization codes
  @type  pols_out : list of str
  
  @return: modified outputs
  """
  # connect the inputs and outputs
  output_names = list(outputs.keys())
  output_names.sort()
  if len(inputs) == 1:
    link_ports(inputs, outputs)
  else:
    assert len(inputs) == len(outputs), \
                      "number of output groups must equal the number of inputs"
    for item in pols_out:
      module_logger.debug("connect_FE_inputs_and_outputs: processing %s", item)
      index = output_names.index(item)
      link_ports(inputs[input_keys[index]], item)
  # Specify the output signals
  for key in list(outputs.keys()):
    if outputs[key].signal == None:
      outputs[key].signal = ComplexSignal(None, name=key, pol=pols_out[key])
    else:
      outputs[key].signal = ComplexSignal(outputs[key].source.signal, name=key,
                                          pol=pols_out[key])
    outputs[key].signal.data['band'] = band
    outputs[key].signal.data['pol'] = pols_out[key]
  return outputs

def get_receiver_IF_output_types(output_names):
  """
  Extracts the IF type information from the receiver output port names
  
  The valid IF codes are defined in the MonitorControl module
  
  @param output_names : optional names for the outputs. Use 'pols_out' if None
  @type  output_names : list of str
  
  @return: list of str
  """
  # Make sure that the output IF types are specified
  if output_names == None:
    raise ObservatoryError("No outputs specified")
  IF_out = valid_property(output_names, 'IF_type')
  module_logger.debug("__init__: IF_out: %s",IF_out)
  return IF_out

def connect_receiver_inputs_and_outputs(inputs, outputs, IF_out):
  """
  Invokes MonitorControl function 'link_ports' to connect inputs to outputs.
  
  It sets the 'destinations' attribute for the inputs and the 'source'
  attribute for the outputs.  It also propagates the input signals to the
  outputs, or creates 'IF' Signal objects if the input signals are not
  specified
  
  @param inputs : same as the kwarg (keyword argument) for the Device class
  @type  inputs : list of Port instances

  @param outputs : as defined in the Device initialization
  @type  outputs : list of Port instances

  @param IF_out : required valid MonitorControl IF codes
  @type  IF_out : list of str
  
  @return: modified outputs
  """
  output_names = list(outputs.keys())
  output_names.sort()
  # connect the inputs and outputs
  if len(inputs) == 1:
    link_ports(inputs, outputs)
  else:
    assert len(inputs) == len(outputs), \
                      "number of output groups must equal the number of inputs"
    input_keys = list(inputs.keys())
    input_keys.sort()
    module_logger.debug(" input keys: %s", input_keys)
    for item in IF_out:
      module_logger.debug("connect_receiver_inputs_and_outputs: processing %s",
                          item)
      index = output_names.index(item)
      link_ports({input_keys[index]: inputs[input_keys[index]]},
                 {item: outputs[item]})
  # Specify the output signals
  for key in list(outputs.keys()):
    if outputs[key].signal == None:
      outputs[key].signal = IF(None, IF_type=IF_out[key])
    else:
      outputs[key].signal = IF(outputs[key].source.signal, IF_type=IF_out[key])
  return outputs
    
def station_configuration(equipment, roach_loglevel=logging.WARNING):
  """
  DSS-13 configuration

  This requires classes Ellipsoid, DSNfe, DSNrx, DSNrxXKa,
  IFmatrixSwitch, WVSR

  DSS-13 is awkward because there are really two IF switches, one in the
  pedestal which selects 4 from many and another one in the control room
  which select many from four.
  """
  site = Observatory("Venus")
  tel = Telescope(site, dss=13)
  equipment['Telescope'] = tel
  equipment['FE_selector'] = ClassInstance(Switch, Ellipsoid, "ellipsoid",
                               inputs={'antenna': tel.outputs[tel.name]},
                               output_names=['pos1','pos2','pos3','pos4',
                                             'pos5','pos6'])
  # The following information comes from document 1 (see Documentation).
  # Generally, the implicit band and polarization specification (i.e. in the
  # name) since most receivers are named conveniently.
  FEs = {'X-X/Ka': ClassInstance(FrontEnd, DSNfe, 'X-X/Ka',
                   inputs={'X': equipment['FE_selector'].outputs['pos1']},
                   output_names=['XR', 'XL']),
         'Ka-X/Ka': ClassInstance(FrontEnd, DSNfe, 'Ka-X/Ka',
                  inputs={'Ka': equipment['FE_selector'].outputs['pos1']},
                  output_names=['KaR', 'KaL']),
         'S-S/X': ClassInstance(FrontEnd, DSNfe, 'S-S/X',
                       inputs={'S':  equipment['FE_selector'].outputs['pos2']},
                       output_names=['SR']),
         'X-S/X': ClassInstance(FrontEnd, DSNfe, 'X-S/X',
                       inputs={'X':  equipment['FE_selector'].outputs['pos2']},
                       output_names=['XR']),
         'XXKa': ClassInstance(FrontEnd, XXKa_fe, 'XXKa',
                 inputs={'X':  equipment['FE_selector'].outputs['pos3'],
                         'Ka': equipment['FE_selector'].outputs['pos3']},
                 output_names=['XR', 'XL', 'KaR', 'KaL']),
         'Xwide': ClassInstance(FrontEnd, DSNfe, 'Xwide',
                        inputs={'X': equipment['FE_selector'].outputs['pos4']},
                        output_names=['XR', 'XL']),
         'K': ClassInstance(FrontEnd, DSN_K, 'K',
                        inputs={'K': equipment['FE_selector'].outputs['pos5']},
                        output_names=['out'])
        }
  equipment['FrontEnd'] = FEs
  # No RF switch(es)
  receivers = {'S-S/X': ClassInstance(Receiver, DSNrx, 'S-S/X',
                                    inputs={'SR': FEs['S-S/X'].outputs['SR']},
                                    output_names=['SRU']),
               'X-S/X': ClassInstance(Receiver, DSNrx, 'X-S/X',
                                    inputs={'XR': FEs['X-S/X'].outputs['XR']},
                                    output_names=['XRU']),
               'X-X/Ka': ClassInstance(Receiver, DSNrx, 'X-X/Ka',
                                  inputs={'XR':  FEs['X-X/Ka'].outputs['XR'],
                                          'XL':  FEs['X-X/Ka'].outputs['XL']},
                                   output_names=['XLU','XRU']),
               'Ka-X/Ka': ClassInstance(Receiver, DSNrx, 'Ka-X/Ka',
                                 inputs={'KaL': FEs['Ka-X/Ka'].outputs['KaL'],
                                         'KaR': FEs['Ka-X/Ka'].outputs['KaR']},
                                    output_names=['KaLU','KaRU']),
               'XXKa': ClassInstance(Receiver, DSNrx, 'XXKa',
                                    inputs={'XR':  FEs['XXKa'].outputs['XR'],
                                            'XL':  FEs['XXKa'].outputs['XL'],
                                            'KaR': FEs['XXKa'].outputs['KaR'],
                                            'KaL': FEs['XXKa'].outputs['KaL']},
                                    output_names=['XRU','XLU','KaRU','KaLU']),
               'GSSR': ClassInstance(Receiver, GSSRdc, 'GSSR',
                                     inputs={'XL': FEs['Xwide'].outputs['XL'],
                                             'XR': FEs['Xwide'].outputs['XR']},
                                     output_names=['XLU', 'XRU']),
               'K': ClassInstance(Receiver, Kdc, 'K',
                                  inputs={'in': FEs['K'].outputs['out']},
                                  output_names=['U']),
               'MMS-1': ClassInstance(Receiver, MMS, 'MMS-1',
                                      inputs=None, output_names=['U'])}
  equipment['Receiver'] = receivers
  IFsw1 = ClassInstance(Device, HP_IFSwitch,
                        'Pedestal IF Switch',
                           inputs={100: None,
                                   101: receivers['XXKa'].outputs['XRU'],
                                   102: receivers['X-X/Ka'].outputs['XLU'],
                                   103: receivers['GSSR'].outputs['XRU'],
                                   104: receivers['X-X/Ka'].outputs['XRU'],
                                   105: receivers['X-S/X'].outputs['XRU'],
                                   106: None,
                                   107: receivers['GSSR'].outputs['XLU'],
                                   108: receivers['Ka-X/Ka'].outputs['KaLU'],
                                   109: receivers['XXKa'].outputs['XLU'],
                                   110: None,
                                   111: receivers['MMS-1'].outputs['U'],
                                   112: receivers['Ka-X/Ka'].outputs['KaRU'],
                                   113: receivers['S-S/X'].outputs['SRU'],
                                   114: receivers['K'].outputs['U'],
                                   115: None},
                           output_names=['IF0','IF1','IF2','IF3'])
  IFsw2 = ClassInstance(Device, IFMatrixSwitch,
                                    'Station IF Switch',
                               inputs={'IF0': IFsw1.outputs['IF0'],
                                       'IF1': IFsw1.outputs['IF1'],
                                       'IF2': IFsw1.outputs['IF2'],
                                       'IF3': IFsw1.outputs['IF3']},
                               output_names=make_IFMS_outputs())
  equipment['IF_switch'] = {'pedestal': IFsw1, 'control room': IFsw2}
  backends = {'WVSR': ClassInstance(Backend, WVSR, 'VenusWVSR',
                               inputs={'WVSR1': IFsw2.outputs['out16']})}
  equipment['Backend'] = backends
  # No sampling clock (for now)
  return site, equipment
