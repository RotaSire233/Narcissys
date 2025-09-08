from typing import Dict, Final, ClassVar
from dataclasses import dataclass
from enum import Enum
from loguru import logger as _logger

class DtypeList:
    int_8 = "int_8"
    int_16 = "int_16"
    int_32 = "int_32"

    float_16 = "float_16"
    float_32 = "float_32"
    float_64 = "float_64"

    string = "str"
    string_flow = "str_flow"

    image = "img"
    audio = "aud"

    
