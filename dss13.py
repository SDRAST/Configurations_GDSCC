import re
import logging
module_logger = logging.getLogger(__name__)

from MonitorControl import Beam, ComplexSignal, IF, Device, Observatory, Port
from MonitorControl import Switch, ClassInstance, Telescope
from MonitorControl import valid_property, link_ports
from MonitorControl.FrontEnds import FrontEnd
from MonitorControl.Receivers import Receiver
from MonitorControl.BackEnds import Backend

def make_IFMS_outputs():
  names = []
  for n in range(1,25):
    names.append('out%02d' % n)
  return names

class Ellipsoid(Switch):
  """
  """
  def __init__(self, name, inputs=None, output_names=[], state=0, active=True):
    """
    """
    mylogger = logging.getLogger(__name__+".Ellipsoid")
    #self.name = name
    stype = "1xN"
    if output_names == None:
      raise ObservatoryError("","Ellipsoid must have some outputs")
    #mylogger.debug("__init__: %s inputs: %s", str(self), str(inputs))
    #mylogger.debug("__init__: output names: %s", output_names)
    Switch.__init__(self, name, inputs=inputs, output_names=output_names,
                    stype = stype, state=state)
    self.logger = mylogger
    self.stype = stype
    self.pos = self.outkeys[self.state]
    self.outputs[self.pos].source = self.inputs[self.inputs.keys()[0]]
    self.set_state(0)
    
    
class DSS13feSX(FrontEnd):
  """
  Has manually operated polarizers
  """
  def __init__(self, name, inputs=None, band=None, pols_out=None,
               output_names=None, active=True):
    """
    This has one input, 'S' or 'X'.  Each has one output, either 'L' or 'R'
    depending on the position of the manually operated polarizer.  If the
    polarization is obtained from the port name, it will need to be changed
    in station_configuration() whenever the polarization is changed.
    """
    mylogger = logging.getLogger(module_logger.name+".DSS13feSX")
    band, output_names, pols_out = get_FE_band_and_pols(inputs,
                                                        band=band,
                                                        pols_out=pols_out,
                                                     output_names=output_names)
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.outputs = connect_FE_inputs_and_outputs(self.inputs,
                                                 band,
                                                 self.outputs,
                                                 pols_out)
    self.logger = mylogger
    #self.name = name
    self.logger.debug("__init__: outputs: %s", self.outputs)
      

class DSNfe(FrontEnd):
  """
  A generic DSN front end.

  This handles bands S, X and Ka.  A DSN front end has only one input but
  either one or two outputs for one or two polarizations.

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

    At present, a DSN FrontEnd object will have one input and two outputs
    but for a multi-feed front end, if each feed produces two pols, and the
    implicit polarization encoding is used, each output pair for a given feed
    is a list.  For pols_out it is a list of lists dicts and for
    output_names it is a list of list of str.

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
    #self.name = name
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
  
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".XXKa_fe")
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    #self.name = name
    self.logger.debug("__init__: outputs: %s", self.outputs)
                      
class XwideFE(FrontEnd):
  """
  """
  def __init__(self, name, inputs=None, band=None, pols_out=[],
               output_names=None, active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".XwideFE")
    band, output_names, pols_out = get_FE_band_and_pols(inputs,
                                                        band=band,
                                                        pols_out=pols_out,
                                                     output_names=output_names)
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    #self.name = name
    self.outputs = connect_FE_inputs_and_outputs(self.inputs,
                                                 band,
                                                 self.outputs,
                                                 pols_out)
    self.logger.debug("__init__: outputs: %s", self.outputs)

class DSN_K(FrontEnd):
  """
  """
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    
    """
    mylogger = logging.getLogger(module_logger.name+".DSN_K")
    #self.name = name
    FrontEnd.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    for key in self.inputs.keys():
      self.logger.debug("__init__: %s signal source is %s",
                        self.inputs[key], self.inputs[key].source)
      self.inputs[key].signal = self.inputs[key].source.signal
      self.logger.debug("__init__: %s input signal is %s", self,
                        self.inputs[key].signal)
      if self.inputs[key].signal == None:
        self.inputs[key].signal = Beam('none')
      self.inputs[key].signal.data['band'] = 'K'
    link_ports(self.inputs,self.outputs)
    for key in self.outputs.keys():
      self.outputs[key].signal = ComplexSignal(self.outputs[key].source.signal)
    self.logger.debug("__init__: outputs: %s", self.outputs)

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
    #self.name = name
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
    This receiver has two inuts and two outputs
    """
    mylogger = logging.getLogger(module_logger.name+".Kdc")
    Receiver.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
    self.logger = mylogger
    inkeys = self.inputs.keys()
    inkeys.sort()
    outkeys = self.outputs.keys()
    outkeys.sort()
    self.chan = {}
    for key in inkeys:
      index = inkeys.index(key)
      outname = outkeys[index]
      ch_inputs = {key: self.inputs[key]}
      self.chan[key] = Receiver.RFsection(self, key,
                                          inputs=ch_inputs,
                                          output_names=[outname])
      link_ports(ch_inputs, self.chan[key].outputs)
      for chkey in self.chan[key].outputs.keys():
        self.outputs[chkey] = self.chan[key].outputs[chkey]
    self.logger.debug("__init__: outputs: %s", self.outputs)

class HP_IFSwitch(Device):
  """
  """
  def __init__(self, name, inputs=None, output_names=[], active=True):
    """
    """
    mylogger = logging.getLogger(module_logger.name+".HP_IFSwitch")
    Device.__init__(self, name, inputs=inputs, output_names=output_names,
                    active=active)
    self.logger = mylogger
    self.channel = {}
    for key in output_names:
      self.channel[key] = self.Channel(self, key, inputs=inputs,
                                       output_names=[name])

  class Channel(Switch):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=[]):
      self.parent = parent
      self.stype = "Nx1"
      Switch.__init__(self, name, inputs=inputs, output_names=output_names,
                      stype = self.stype)
      for port in self.outputs.keys():
        self.parent.outputs[port] = self.outputs[port]

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
    for key in self.inputs.keys():
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
      for port in self.outputs.keys():
        self.parent.outputs[port] = self.outputs[port]

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

def get_FE_band_and_pols(inputs, band=None, pols_out=None, output_names=[]):
    # Make sure that the band is specified
    if band == None:
      bands = valid_property(inputs.keys(), 'band')
      if bands == False:
        raise ObservatoryError('band',' property key not found')
      band = bands[bands.keys()[0]]
      module_logger.debug('get_FE_band_and_pols: band is %s', band)
      if len(inputs) > 1:
        # check that all bands are the same
        if not (bands==band).all():
          raise ObservatoryError(str(band),'is not in every input name')
    input_keys = inputs.keys()
    input_keys.sort()
    module_logger.debug("get_FE_band_and_pols: inputs: %s", input_keys)
    # Having the band in the output name is helpful but not required.
    valid_property(output_names, 'band', abort=False)
    # Make sure that the output polarizations are specified
    if pols_out == None and output_names == None:
      raise ObservatoryError("No outputs specified")
    elif pols_out:
      output_names = pols_out.keys()
      output_names.sort()
    else:
      pols_out = valid_property(output_names, 'pol_type')
    module_logger.debug("get_FE_band_and_pols: output_names=%s", output_names)
    module_logger.debug("get_FE_band_and_pols: pols_out: %s",pols_out)
    return band, output_names, pols_out

def connect_FE_inputs_and_outputs(inputs, band, outputs, pols_out):
    # connect the inputs and outputs
    output_names = outputs.keys()
    output_names.sort()
    if len(inputs) == 1:
      link_ports(inputs, outputs)
    else:
      assert len(inputs) == len(outputs), \
        "number of output groups must equal the number of inputs"
      for item in pols_out:
        module_logger.debug("connect_FE_inputs_and_outputs: processing %s",
                            item)
        index = output_names.index(item)
        link_ports(inputs[input_keys[index]], item)
    # Specify the output signals
    for key in outputs.keys():
      if outputs[key].signal == None:
        outputs[key].signal = ComplexSignal(None,
                                                 name=key,
                                                 pol=pols_out[key])
      else:
        outputs[key].signal = ComplexSignal(
                                               outputs[key].source.signal,
                                               name=key,
                                               pol=pols_out[key])
      outputs[key].signal.data['band'] = band
      outputs[key].signal.data['pol'] = pols_out[key]
    return outputs

def get_receiver_IF_output_types(output_names):
    # Make sure that the output IF types are specified
    if output_names == None:
      raise ObservatoryError("No outputs specified")
    IF_out = valid_property(output_names, 'IF_type')
    module_logger.debug("__init__: IF_out: %s",IF_out)
    return IF_out

def connect_receiver_inputs_and_outputs(inputs, outputs, IF_out):
    output_names = outputs.keys()
    output_names.sort()
    # connect the inputs and outputs
    if len(inputs) == 1:
      link_ports(inputs, outputs)
    else:
      assert len(inputs) == len(outputs), \
        "number of output groups must equal the number of inputs"
      input_keys = inputs.keys()
      input_keys.sort()
      module_logger.debug(" input keys: %s", input_keys)
      for item in IF_out:
        module_logger.debug(
                          "connect_receiver_inputs_and_outputs: processing %s",
                          item)
        index = output_names.index(item)
        link_ports({input_keys[index]: inputs[input_keys[index]]},
                   {item: outputs[item]})
    # Specify the output signals
    for key in outputs.keys():
      if outputs[key].signal == None:
        outputs[key].signal = IF(None, IF_type=IF_out[key])
      else:
        outputs[key].signal = IF(outputs[key].source.signal,
                                      IF_type=IF_out[key])
    return outputs
    
def station_configuration(equipment, roach_loglevel=logging.WARNING):
  """
  DSS-13 configuration

  This requires classes Ellipsoid, DSNfe, DSS13feSX, DSNrx, DSNrxXKa,
  IFmatrixSwitch, WVSR

  DSS-13 is awkward because there are really two IF switches, one in the
  pedestal which selects 4 from many and another one in the control room
  which select many from four.
  """
  site = Observatory("Venus")
  tel = Telescope(site, dss=13)
  equipment['Telescope']
  equipment['FE_selector'] = ClassInstance(Switch, Ellipsoid, "ellipsoid",
                               inputs={'antenna': tel.outputs[tel.name]},
                               output_names=['pos1','pos2','pos3','pos4',
                                             'pos5','pos6'])
  FEs = {'X-X/Ka': ClassInstance(FrontEnd, DSNfe, 'X-X/Ka',
                   inputs={'X': equipment['FE_selector'].outputs['pos1']},
                   output_names=['XR', 'XL']),
         'Ka-X/Ka': ClassInstance(FrontEnd, DSNfe, 'Ka-X/Ka',
                  inputs={'Ka': equipment['FE_selector'].outputs['pos1']},
                  output_names=['KaR', 'KaL']),
         'S-S/X': ClassInstance(FrontEnd, DSS13feSX, 'S-S/X',
                     inputs={'S':  equipment['FE_selector'].outputs['pos2']},
                     output_names=['SR']),
         'X-S/X': ClassInstance(FrontEnd, DSS13feSX, 'X-S/X',
                     inputs={'X':  equipment['FE_selector'].outputs['pos2']},
                     output_names=['XR']),
         'XXKa': ClassInstance(FrontEnd, XXKa_fe, 'XXKa',
                 inputs={'X/Ka/XTx': equipment['FE_selector'].outputs['pos3']},
                 output_names=['XR', 'XL', 'KaR', 'KaL']),
         'Xwide': ClassInstance(FrontEnd, XwideFE, 'Xwide',
                        inputs={'X': equipment['FE_selector'].outputs['pos4']},
                        output_names=['XR', 'XL']),
         'K': ClassInstance(FrontEnd, DSN_K, 'K',
                        inputs={'K': equipment['FE_selector'].outputs['pos5']},
                        output_names=['KL','KR'])
        }
  equipment['FrontEnd'] = FEs
  # No RF switch(es)
  receivers = {'S-S/X': ClassInstance(Receiver, DSNrx, 'S-S/X',
                                    inputs={'SR': FEs['S-S/X'].outputs['SR']},
                                    output_names=['U-SR']),
               'X-S/X': ClassInstance(Receiver, DSNrx, 'X-S/X',
                                    inputs={'XR': FEs['X-S/X'].outputs['XR']},
                                    output_names=['U-XR']),
               'X-X/Ka': ClassInstance(Receiver, DSNrx, 'X-X/Ka',
                                  inputs={'XR':  FEs['X-X/Ka'].outputs['XR'],
                                          'XL':  FEs['X-X/Ka'].outputs['XL']},
                                   output_names=['U-XL','U-XR']),
               'Ka-X/Ka': ClassInstance(Receiver, DSNrx, 'Ka-X/Ka',
                                 inputs={'KaL': FEs['Ka-X/Ka'].outputs['KaL'],
                                         'KaR': FEs['Ka-X/Ka'].outputs['KaR']},
                                    output_names=['U-KaL','U-KaR']),
               'XXKa': None,
               'GSSR': ClassInstance(Receiver, GSSRdc, 'GSSR',
                                     inputs={'XL': FEs['Xwide'].outputs['XL'],
                                             'XR': FEs['Xwide'].outputs['XR']},
                                     output_names=['XLU', 'XRU']),
               'K': ClassInstance(Receiver, Kdc, 'K',
                                  inputs={'KL': FEs['K'].outputs['KL'],
                                          'KR': FEs['K'].outputs['KR']},
                                  output_names=['KLU', 'KRU'])}
  equipment['Receiver'] = receivers
  IFsw1 = ClassInstance(Device, HP_IFSwitch,
                        'Pedestal IF Switch',
                        inputs={'SX-S-RU': receivers['S-S/X'].outputs['U-SR'],
                              'SX-X-RU': receivers['X-S/X'].outputs['U-XR'],
                              'XKa-X-RU': receivers['X-X/Ka'].outputs['U-XR'],
                              'XKa-X-LU': receivers['X-X/Ka'].outputs['U-XL'],
                           'XKa-Ka-RU': receivers['Ka-X/Ka'].outputs['U-KaR'],
                           'XKa-Ka-LU': receivers['Ka-X/Ka'].outputs['U-KaL']},
                           output_names=['IF1','IF2','IF3','IF4'])
  IFsw2 = ClassInstance(Device, IFMatrixSwitch,
                                    'Station IF Switch',
                               inputs={'IF1': IFsw1.outputs['IF1'],
                                       'IF2': IFsw1.outputs['IF2'],
                                       'IF3': IFsw1.outputs['IF3'],
                                       'IF4': IFsw1.outputs['IF4']},
                               output_names=make_IFMS_outputs())
  equipment['IF_switch'] = {'pedestal': IFsw1, 'control room': IFsw2}
  backends = {'WVSR': ClassInstance(Backend, WVSR, 'VenusWVSR',
                               inputs={'WVSR1': IFsw2.outputs['out16']})}
  equipment['Backend'] = backends
  # No sampling clock (for now)
  return site, equipment
