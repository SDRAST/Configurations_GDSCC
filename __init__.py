"""
Configurations at the Goldstone Complex

Nested dict 'cfg' is keyed the DSN stations, then the DSN receivers and then
the polarizations which are available at the inputs of the VLBI DAT matrix
switch, which will also be the DTO matrix switch. This dict can edited easily
if more IFs become available, simply replacing the appropriate 0 with the input
number. If there is no key, that IF does not exist.
"""
import logging

module_logger = logging.getLogger(__name__)

cfg = {14: {'S' :{'R':0,'L':0},
            'X' :{'R':3,'L':2}},
       15: {'S' :{'R':0},
            'X' :{'R':1}},
       24: {'S' :{'R':0},
            'X' :{'R':7,'L':4},
            'Ka':{'R':9}},
       25: {'X' :{'R':5},
            'Ka':{'R':6}},
       26: {'X' :{'R':0,'L':0},
            'Ka':{'R':8}}}