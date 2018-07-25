"""
Configurations at the Goldstone Complex

Nested dict 'cfg' is keyed the DSN stations, then the DSN receivers and then
the polarizations which are available at the inputs of the VLBI DAT matrix
switch, which will also be the DTO matrix switch. This dict can edited easily
if more IFs become available, simply replacing the appropriate 0 with the input
number. If there is no key, that IF does not exist.

References
==========
http://deepspace.jpl.nasa.gov/dsndocs/810-005/302/302C.pdf

The following are from cable tracing and table from Larry (DVP-DTO.jpg)::
   24SR  -> J1A  ->  2
   14SR  -> J2A  ->  4
         -> J3A  ->
         -> J4A  ->  8
         -> J5A  -> 10
         -> J6A  ->  6
   26XR  -> J7A  -> 18
   26KaR -> J8A  -> 20
         -> J9A  ->
         -> J10A ->
         -> J11A ->
         -> J12A -> 24
"""
import logging

logger = logging.getLogger(__name__)

#     0 means not connected
cfg = {14: {'S' :{'R': 4,     # J2A  14S
                  'L': 0},    #     
            'X' :{'R': 6,     # J10A 14X
                  'L': 0}},   #     
       15: {'S' :{'R': 0},    #      
            'X' :{'R': 0}},   #      
       24: {'S' :{'R': 2},    # J1A  24S
            'X' :{'R': 0,     #
                  'L': 0},    #
            'Ka':{'R': 0}},   #      
       25: {'X' :{'R': 0},    #      
            'Ka':{'R': 0}},   #      
       26: {'S' :{'R': 0},    # 
            'X' :{'R':18,     # J7A  26X
                  'L': 0},    #
            'Ka':{'R':20}}}   # J8A  26K

feeds = {}

mech = {14:{'diam': 70,
            'type': 'cas'},
        15:{'diam': 34,
            'type': 'HEF'},
        13:{'diam': 34,
            'type': 'BWG'},
        24:{'diam': 34,
            'type': 'BWG'},
        25:{'diam': 34,
            'type': 'BWG'},
        26:{'diam': 34,
            'type': 'BWG'}}

wrap = {14: {'stow_az': 180,
             'wrap':    {'center':  45}},
        15: {'stow_az': 0,
             'wrap':    {'center': 135}},
        24: {'stow_az': 0,
             'wrap':    {'center': 135}},
        25: {'stow_az': 0,
             'wrap':    {'center': 135}},
        26: {'stow_az': 0,
             'wrap':    {'center': 135}}}

def make_switch_inputs(rx):
  """
  Identifies the signals going into the IF switch
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

