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

Attachment to e-mail from Alina Bedrossian on 03/21/2017 at 09:16 AM gives 
this assignment::
  Antenna Type	Switch	CDSCC	  GDSCC	  MDSCC
      BWG1	      1	    34_S1	  24_S1	  54_S1
	                2	    34_X1	  26_S1	  54_X1
	                3	    34_Ka1	15_X1	  54_Ka1
      BWG2	      4	    35_X1	  25_X1	  55_X1
	                5	    35_Ka1	25_Ka1	55_Ka1
      BWG3	      6	    36_S1	  15_S1	  65_S1
	                7	    36_X1	  26_X1	  65_X1
	                8	    36_Ka1	26_Ka1	63_X2
      70-m	      9	    43_S1	  14_S1	  63_S1
	               10	    43_X1	  14_X1	  63_X1
      AUX	       11	    AUX1	  AUX1	  AUX1
	               12	    AUX2	  AUX2	  AUX2

"""
import logging

logger = logging.getLogger(__name__)

cfg = {14: {'S' :{'R':9,     # S14RU
                  'L':0},
            'X' :{'R':10,    # X14RU
                  'L':0}},
       15: {'S' :{'R':6},    # S15RU
            'X' :{'R':3}},   # X15RU
       24: {'S' :{'R':1},    # S24RU
            'X' :{'R':0,
                  'L':0},
            'Ka':{'R':0}},
       25: {'X' :{'R':4},    # X25RU
            'Ka':{'R':5}},   # Ka25RU
       26: {'S' :{'R':2},    # S26RU
            'X' :{'R':7,     # X26RU
                  'L':0},
            'Ka':{'R':8}}}   # Ka26RU

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


