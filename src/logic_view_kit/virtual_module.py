#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from .value_type import Value_Type
from bisect      import bisect_right
from collections import deque
import heapq
import re
import inspect

class Register:
    class Base:
        def __init__(self, name, value_type, value=None):
            self.name       = name
            self.value_type = value_type
            self.curr_value = value

        def __str__(self):
            return self.curr_value
                
    class Logic(Base):
        VALID_VALUES = frozenset("01lLhHwWzZuUxX-")
        HIGH_VALUES  = frozenset("1hH")
        LOW_VALUES   = frozenset("0lL")
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type)
            self.curr_value = Register.Logic.parse_value(value, self.value_type)

        def set_curr_value(self, value):
            self.curr_value = Register.Logic.parse_value(value, self.value_type)

        @staticmethod
        def parse_value(value, value_type):
            if   isinstance(value, Register.Logic):
                return value.curr_value
            elif isinstance(value, int) and value in (0, 1):
                return str(value)
            elif isinstance(value, str) and len(value) == 1:
                if value in Register.Logic.VALID_VALUES:
                    return value
            return "X"

        @staticmethod
        def value_is_high(value):
            return value in Register.Logic.HIGH_VALUES

        @staticmethod
        def value_is_low(value):
            return value in Register.Logic.LOW_VALUES

        @staticmethod
        def value_is_01(value):
            return (Register.Logic.value_is_high(value) or
                    Register.Logic.value_is_low(value ))

        @staticmethod
        def value_to_01(value, default="0"):
            if Register.Logic.value_is_high(value):
                return "1"
            if Register.Logic.value_is_low(value):
                return "0"
            return default

        @property
        def is_high(self):
            return Register.Logic.value_is_high(self.curr_value)

        @property
        def is_low(self):
            return Register.Logic.value_is_low(self.curr_value)

        def __int__(self):
            if self.is_high:
                return 1
            else:
                return 0

        AND_TABLE = {
            "U": {"U":"U", "X":"U", "0":"0", "1":"U", "Z":"U", "W":"U", "L":"0", "H":"U", "-":"U"},
            "X": {"U":"U", "X":"X", "0":"0", "1":"X", "Z":"X", "W":"X", "L":"0", "H":"X", "-":"X"},
            "0": {"U":"0", "X":"0", "0":"0", "1":"0", "Z":"0", "W":"0", "L":"0", "H":"0", "-":"0"},
            "1": {"U":"U", "X":"X", "0":"0", "1":"1", "Z":"X", "W":"X", "L":"0", "H":"1", "-":"X"},
            "Z": {"U":"U", "X":"X", "0":"0", "1":"X", "Z":"X", "W":"X", "L":"0", "H":"X", "-":"X"},
            "W": {"U":"U", "X":"X", "0":"0", "1":"X", "Z":"X", "W":"X", "L":"0", "H":"X", "-":"X"},
            "L": {"U":"0", "X":"0", "0":"0", "1":"0", "Z":"0", "W":"0", "L":"0", "H":"0", "-":"0"},
            "H": {"U":"U", "X":"X", "0":"0", "1":"1", "Z":"X", "W":"X", "L":"0", "H":"1", "-":"X"},
            "-": {"U":"U", "X":"X", "0":"0", "1":"X", "Z":"X", "W":"X", "L":"0", "H":"X", "-":"X"},
        }
        @staticmethod
        def value_and_value(value1, value2):
            return Register.Logic.AND_TABLE[value1.to_upper()][value2.to_upper()]
            
        def __and__(self, other):
            value  = Register.Logic.parse_value(other, self.value_type)
            result = Register.Logic.value_and_value(self.curr_value, value)
            return   Constant.Logic(None, self.value_type, result)
                
        OR_TABLE = {
            "U": {"U":"U", "X":"U", "0":"U", "1":"U", "Z":"U", "W":"U", "L":"U", "H":"U", "-":"U"},
            "X": {"U":"U", "X":"X", "0":"X", "1":"X", "Z":"X", "W":"X", "L":"X", "H":"X", "-":"X"},
            "0": {"U":"U", "X":"X", "0":"0", "1":"1", "Z":"X", "W":"X", "L":"0", "H":"1", "-":"X"},
            "1": {"U":"U", "X":"X", "0":"1", "1":"1", "Z":"1", "W":"1", "L":"1", "H":"1", "-":"1"},
            "Z": {"U":"U", "X":"X", "0":"X", "1":"1", "Z":"X", "W":"X", "L":"X", "H":"1", "-":"X"},
            "W": {"U":"U", "X":"X", "0":"X", "1":"1", "Z":"X", "W":"X", "L":"X", "H":"1", "-":"X"},
            "L": {"U":"U", "X":"X", "0":"0", "1":"1", "Z":"X", "W":"X", "L":"0", "H":"1", "-":"X"},
            "H": {"U":"U", "X":"X", "0":"1", "1":"1", "Z":"1", "W":"1", "L":"1", "H":"1", "-":"1"},
            "-": {"U":"U", "X":"X", "0":"X", "1":"1", "Z":"X", "W":"X", "L":"X", "H":"1", "-":"X"},
        }
        @staticmethod
        def value_or_value(value1, value2):
            return Register.Logic.OR_TABLE[value1.to_upper()][value2.to_upper()]
            
        def __or__(self, other):
            value  = Register.parse_value(other, self.value_type)
            result = Register.Logic.value_or_value(self.curr_value, value)
            return   Constant.Logic(None, self.value_type, result)

        XOR_TABLE = {
            "U": {"U":"U", "X":"U", "0":"U", "1":"U", "Z":"U", "W":"U", "L":"U", "H":"U", "-":"U"},
            "X": {"U":"U", "X":"X", "0":"X", "1":"X", "Z":"X", "W":"X", "L":"X", "H":"X", "-":"X"},
            "0": {"U":"U", "X":"X", "0":"0", "1":"1", "Z":"X", "W":"X", "L":"0", "H":"1", "-":"X"},
            "1": {"U":"U", "X":"X", "0":"1", "1":"0", "Z":"X", "W":"X", "L":"1", "H":"0", "-":"X"},
            "Z": {"U":"U", "X":"X", "0":"X", "1":"X", "Z":"X", "W":"X", "L":"X", "H":"X", "-":"X"},
            "W": {"U":"U", "X":"X", "0":"X", "1":"X", "Z":"X", "W":"X", "L":"X", "H":"X", "-":"X"},
            "L": {"U":"U", "X":"X", "0":"0", "1":"1", "Z":"X", "W":"X", "L":"0", "H":"1", "-":"X"},
            "H": {"U":"U", "X":"X", "0":"1", "1":"0", "Z":"X", "W":"X", "L":"1", "H":"0", "-":"X"},
            "-": {"U":"U", "X":"X", "0":"X", "1":"X", "Z":"X", "W":"X", "L":"X", "H":"X", "-":"X"},
        }
        @staticmethod
        def value_xor_value(value1, value2):
            return Register.Logic.XOR_TABLE[value1.to_upper()][value2.to_upper()]

        def __xor__(self, other):
            value  = Register.Logic.parse_value(other, self.value_type)
            result = Register.Logic.value_xor_value(self.curr_value, value)
            return   Constant.Logic(None, self.value_type, result)
                
        NOT_TABLE = {
            "U":"U", "X":"X", "0":"1", "1":"0", "Z":"X", "W":"X", "L":"1", "H":"0", "-":"X"
        }
        @staticmethod
        def not_value(value):
            return Register.Logic.NOT_TABLE[value.to_upper()]

        def __invert__(self):
            result = Register.Logic.not_value(self.curr_value)
            return   Constant.Logic(None, self.value_type, result)
                
    class Logic_Vector(Base):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type)
            self.curr_value = Register.Logic_Vector.parse_value(value, self.value_type)

        def set_curr_value(self, value):
            self.curr_value = Register.Logic_Vector.parse_value(value, self.value_type)

        @staticmethod
        def parse_value(value, value_type):
            if   isinstance(value, Register.Logic_Vector):
                return Register.Logic_Vector.resize_value(value.curr_value, value_type)
            elif isinstance(value, int):
                return Register.Logic_Vector.integer_to_value(value, value_type)
            elif isinstance(value, str) and all(ch in Register.Logic.VALID_VALUES for ch in value):
                return Register.Logic_Vector.resize_value(value, value_type)
            else:
                return None

        @staticmethod
        def resize_value(value, value_type):
            width  = value_type.width
            signed = value_type.signed
            if len(value) > width:
                return value[-width:]
            if len(value) < width:
                msb       = value[0]
                msb_is_01 = Register.Logic.value_is_01(msb)
                if signed is False and msb_is_01 is True:
                    extension = "0"
                else:
                    extension = msb
                return (extension * (width - len(value))) + value
            return value

        @staticmethod
        def integer_to_value(value, value_type):
            width  = value_type.width
            signed = value_type.signed
            if signed:
                value &= ((1 << width) - 1)
            elif value < 0:
                raise ValueError("negative value for unsigned type")
            return format(value, f"0{width}b")
        
        @staticmethod
        def value_to_01(value, default="0"):
            return ''.join(Register.Logic.value_to_01(ch,default) for ch in value)

        @staticmethod
        def value_to_integer(value, value_type):
            width  = value_type.width
            signed = value_type.signed
            number = int(Register.Logic_Vector.value_to_01(value), 2)
            if signed and number & (1 << width - 1):
                number -= (1 << width)
            return number
        
        def __int__(self):
            result = Register.Logic_Vector.value_to_integer(self.curr_value, self.value_type)
            return result

        @staticmethod
        def value_and_value(value1, value2):
            return ''.join(Register.Logic.value_and_value(c1,c2) for c1,c2 in zip(value1, value2))
            
        def __and__(self, other):
            value  = Register.Logic_Vector.parse_value(other, self.value_type)
            result = Register.Logic_Vector.value_and_value(self.curr_value, value)
            return   Constant.Logic_Vector(None, self.value_type, result)
        
        @staticmethod
        def value_or_value(value1, value2):
            return ''.join(Register.Logic.value_or_value(c1,c2) for c1,c2 in zip(value1, value2))
            
        def __or__(self, other):
            value  = Register.Logic_Vector.parse_value(other, self.value_type)
            result = Register.Logic_Vector.value_or_value(self.curr_value, value)
            return   Constant.Logic_Vector(None, self.value_type, result)
        
        @staticmethod
        def value_xor_value(value1, value2):
            return ''.join(Register.Logic.value_xor_value(c1,c2) for c1,c2 in zip(value1, value2))
            
        def __xor__(self, other):
            value  = Register.Logic_Vector.parse_value(other, self.value_type)
            result = Register.Logic_Vector.value_xor_value(self.curr_value, value)
            return   Constant.Logic_Vector(None, self.value_type, result)

        @staticmethod
        def not_value(value):
            return ''.join(Register.Logic.not_value(c) for c in value)

        def __invert__(self):
            result = Register.Logic_Vector.not_value(self.curr_value)
            return   Constant.Logic_Vector(None, self.value_type, result)
        
    class Other(Base):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type)
            self.curr_value = Register.Other.parse_value(value, self.value_type)

        def set_curr_value(self, value):
            self.curr_value = Register.Other.parse_value(value, self.value_type)

        @staticmethod
        def parse_value(value, value_type):
            if   isinstance(value, Register.Other):
                return value.curr_value
            elif isinstance(value, str):
                return value
            elif isinstance(value, int):
                return str(int)
            else:
                return None

    class Readable_Logic(Logic):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            self.prev_value = self.curr_value

        def set_curr_value(self, value):
            self.prev_value = self.curr_value
            super().set_curr_value(value)

        @property
        def rising_edge(self):
            return (Register.Logic.value_is_high(self.curr_value) and
                    Register.Logic.value_is_low(self.prev_value))

        @property
        def falling_edge(self):
            return (Register.Logic.value_is_low(self.curr_value) and
                    Register.Logic.value_is_high(self.prev_value))

    class Readonly_Logic(Readable_Logic):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
        
        def __ilshift__(self, value):
            raise RuntimeError(f'{self.name} can not override value')
                
    class Writeable_Logic(Readable_Logic):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            self.next_value = self.curr_value
            self.changed    = False

        def __ilshift__(self, value):
            next_value = type(self).parse_value(value, self.value_type)
            if next_value is not None:
                self.next_value = next_value
            return self

        def write_init(self):
            self.next_value = self.curr_value
            self.changed    = False
        
        def write_back(self):
            if self.curr_value != self.next_value:
                self.curr_value = self.next_value
                self.changed    = True

    class Readable_Logic_Vector(Logic_Vector):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            self.prev_value = self.curr_value

        def set_curr_value(self, value):
            self.prev_value = self.curr_value
            super().set_curr_value(value)

    class Readonly_Logic_Vector(Readable_Logic_Vector):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            
        def __ilshift__(self, value):
            raise RuntimeError(f'{self.name} can not override value')
                
    class Writeable_Logic_Vector(Readable_Logic_Vector):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            self.next_value = self.curr_value
            self.changed    = False

        def __ilshift__(self, value):
            next_value = type(self).parse_value(value, self.value_type)
            if next_value is not None:
                self.next_value = next_value
            return self
            
        def write_init(self):
            self.next_value = self.curr_value
            self.changed    = False
            
        def write_back(self):
            if self.curr_value != self.next_value:
                self.curr_value = self.next_value
                self.changed    = True

    class Readable_Other(Other):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            self.prev_value = self.curr_value

        def set_curr_value(self, value):
            self.prev_value = self.curr_value
            super().set_curr_value(value)
            
    class Readonly_Other(Readable_Other):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            
        def __ilshift__(self, value):
            raise RuntimeError(f'{self.name} can not override value')
                
    class Writeable_Other(Readable_Other):
        def __init__(self, name, value_type, value=None):
            super().__init__(name, value_type, value)
            
        def __ilshift__(self, value):
            next_value = type(self).parse_value(value, self.value_type)
            if next_value is not None:
                self.next_value = next_value
            return self

        def write_init(self):
            self.next_value = self.curr_value
            self.changed    = False
            
        def write_back(self):
            if self.curr_value != self.next_value:
                self.curr_value = self.next_value
                self.changed    = True

    @classmethod
    def new(cls, name, value_type, writeable=False, value=None):
        if writeable is True:
            if value_type.is_vector:
                return cls.Writeable_Logic_Vector(name, value_type, value)
            if value_type.is_logic:
                return cls.Writeable_Logic(name, value_type, value)
            return cls.Writeable_Other(name, value_type)
        else:
            if value_type.is_vector:
                return cls.Readonly_Logic_Vector(name, value_type, value)
            if value_type.is_logic:
                return cls.Readonly_Logic(name, value_type, value)
            return cls.Readonly_Other(name, value_type)

class Constant:
    class Logic(Register.Logic):
        def __init__(self, name, value_type, value):
            super().__init__(name, value_type, value)
              
    class Logic_Vector(Register.Logic_Vector):
        def __init__(self, name, value_type, value):
            super().__init__(name, value_type, value)
                
    class Other(Register.Other):
        def __init__(self, name, value_type, value):
            super().__init__(name, value_type, value)
                
    @classmethod
    def new(cls, name, value_type, value_width, value):
        _value_type = Value_Type(name, value_type, value_width)
        if   _value_type.is_vector:
            return cls.Logic_Vector(name, _value_type, value)
        elif _value_type.is_logic:
            return cls.Logic(name, _value_type, value)
        else:
            return cls.Other(name, value_type, value)
            
class Virtual_Module:

    class Signal:
        def __init__(self, module, name, value_type):
            self.module     = module
            self.name       = name
            self.value_type = value_type

    class Readonly_Signal(Signal):
        def __init__(self, module, name, value_type, value=None):
            super().__init__(module, name, value_type)
            self.register = Register.new(name, value_type, writeable=False, value=value)
        
    class Writeable_Signal(Signal):
        def __init__(self, module, name, value_type, value=None):
            super().__init__(module, name, value_type)
            self.register = Register.new(name, value_type, writeable=True , value=value)
            
    class Input_Signal(Readonly_Signal):
        def __init__(self, module, name, node, path, option=None):
            super().__init__(module, name, node["value_type"])
            self.node       = node
            self.path       = path
            self.handle     = node["handle"]
            self.registered = False
            self.closed     = False

        def set_curr_value(self, value):
            self.register.set_curr_value(value)
            
        def close(self):
            if self.closed is True:
                return
            self.closed = True
            self.unregister_database()

        def register_database(self):
            if self.registered is False:
                self.module.database.register_handle(self.handle)
                self.registered = True

        def unregister_database(self):
            if self.registered is True:
                self.module.database.unregister_handle(self.handle)
                self.registered = False

        def get_wave(self, start_time, end_time):
            self.register_database()
            return self.module.database.get(self.handle, start_time, end_time)
        
    class Output_Signal(Writeable_Signal):
        def __init__(self, module, name, value_type, value_width, init_value):
            _value_type = Value_Type(name, value_type, value_width)
            super().__init__(module, name, _value_type, init_value)
            self.start_time = None
            self.end_time   = None
            self.curr_time  = None
            self.closed     = False
            self.time_list  = []
            self.value_list = []
            
        def pre_process(self, time):
            self.curr_time  = time
            self.register.write_init()

        def post_process(self):
            self.register.write_back()
            if self.register.changed:
                if isinstance(self.register.curr_value, int):
                    curr_value = format(self.register.curr_value,"b")
                else:
                    curr_value = self.register.curr_value
                self.append(self.curr_time, curr_value)
                
        def append(self, time, value):
            self.time_list.append(time)
            self.value_list.append(value)
            if self.start_time is None:
                self.start_time = time
            self.end_time = time

        def is_generated(self, start_time, end_time):
            if self.start_time is None:
                return False
            return ((start_time >= self.start_time) and (end_time <= self.end_time))

        def update_generated_time(self, start_time, end_time):
            if self.start_time is None or self.start_time > start_time:
                self.start_time = start_time
            if self.end_time   is None or self.end_time   < end_time:
                self.end_time = end_time

        def clear(self):
            self.start_time = None
            self.end_time   = None
            self.time_list.clear()
            self.value_list.clear()

        def close(self):
            if self.closed is True:
                return
            self.closed = True
            self.clear()

        def get_wave(self, start_time, end_time):
            if not self.time_list:
                return iter(())
            # lo_pos  : start_time 以下の最後の変化位置
            lo_pos = bisect_right(self.time_list, start_time)
            if lo_pos > 0:
                lo_pos = lo_pos -1
            else:
                lo_pos = 0
            # hi_pos : end_time より大きい最初の位置
            hi_pos = bisect_right(self.time_list, end_time  ) 
            # start_time 〜 end_time の変化を示すイタレータを返す
            return (
                (self.time_list[i], self.value_list[i])
                for i in range(lo_pos, hi_pos)
            )

    class Process:
        def __init__(self, model, process, user_argument=None):
            self.model         = model
            self.process       = process
            self.name          = self.get_process_name(process)
            self.user_argument = user_argument if isinstance(user_argument, dict) else {}
            self.parameters    = inspect.signature(process).parameters
            self.argument_list = []

        @staticmethod
        def get_process_name(process):
            return getattr(process, "__name__", type(process).__name__)

        def prepare(self):
            self.argument_list.clear() 

            for param_name in self.parameters:
                if param_name in self.model.signal_map:
                    self.argument_list.append(self.model.signal_map[param_name].register)
                    continue
                if param_name in self.user_argument:
                    self.argument_list.append(self.user_argument[param_name])
                    continue
                raise RuntimeError(f'Not found argument "{param_name}" in process "{self.name}"')

        def run(self):
            self.process(*self.argument_list)

    def __init__(self, name, database):
        self.name               = name
        self.database           = database
        self.clock_signal_pos   = -1
        self.input_signal_list  = []
        self.output_signal_list = []
        self.signal_map         = {}
        self.process_list       = []
        self.start_time         = None
        self.end_time           = None
        if self.start_time is None or self.start_time < self.database.total_start_time:
            self.start_time = self.database.total_start_time
        if self.end_time   is None or self.end_time   > self.database.total_end_time  :
            self.end_time   = self.database.total_end_time
        self.current_time   = self.start_time

    def close(self):
        for input_signal  in self.input_signal_list:
            input_signal.close()
        for output_signal in self.output_signal_list:
            output_signal.close()

    def find_input_signal(self, pattern):
        signal_list = self.database.find_signals(pattern, tree=None, struct_as_var=False)
        if len(signal_list) == 0:
            raise RuntimeError(f'No signal matched the specified pattern: "{pattern}"')
        if len(signal_list) >= 2:
            raise RuntimeError(f'Multiple signals matched the specified signal pattern: "{pattern}"')
        path = "::".join(signal_list[0][0])
        node = signal_list[0][1]
        if "handle" not in node:
            raise RuntimeError(f'The specified pattern does not match a signal: "{pattern}"')
        return node, path

    def new_clock_signal(self, name, pattern, option=None):
        if self.clock_signal_pos >= 0:
            raise RuntimeError(f'Multiple clock signals')
        node, path = self.find_input_signal(pattern)
        signal     = self.Input_Signal(self, name, node, path, option)
        self.clock_signal_pos = len(self.input_signal_list)
        self.input_signal_list.append(signal)
        self.signal_map[signal.name] = signal
        return signal

    def add_clock_signal(self, name, pattern, option=None):
        signal = self.new_clock_signal(name, pattern, option=None)
        return self
    
    def new_input_signal(self, name, pattern, option=None):
        node, path = self.find_input_signal(pattern)
        signal     = self.Input_Signal(self, name, node, path, option)
        self.input_signal_list.append(signal)
        self.signal_map[signal.name] = signal
        return signal

    def add_input_signal(self, name, pattern, option=None):
        signal = self.new_input_signal(name, pattern, option=None)
        return self

    def new_output_signal(self, name, value_type, value_width, init_value=None):
        signal = self.Output_Signal(self, name, value_type, value_width, init_value)
        self.output_signal_list.append(signal)
        self.signal_map[signal.name] = signal
        return signal

    def add_output_signal(self, name, value_type, value_width, init_value=None):
        signal = self.new_output_signal(name, value_type, value_width, init_value)
        return self

    def new_process(self, process, user_argument=None):
        return self.Process(self, process, user_argument)
        
    def add_process(self, process, user_argument=None):
        process = self.new_process(process, user_argument)
        self.process_list.append(process)
        return self

    def register_database(self):
        for input_signal in self.input_signal_list:
            input_signal.register_database()
                
    def unregister_database(self):
        for input_signal in self.input_signal_list:
            input_signal.unregister_database()

    def generate_wave(self, start_time, end_time):
        input_signal_iterator_list = []
        input_signal_wave_queue    = []
        pending_signal_wave_queue  = deque()

        # process の準備
        for process in self.process_list:
            process.prepare()

        # 出力信号の波形情報をクリア
        for output_signal in self.output_signal_list:
            output_signal.clear()
        
        # 入力信号の変化した時刻と値を input_signal_wave_queue に保持
        for pos, signal in enumerate(self.input_signal_list):
            iterator = signal.get_wave(start_time, end_time)
            input_signal_iterator_list.append(iterator)
            try:
                time, value = next(iterator)
            except StopIteration:
                continue
            heapq.heappush(input_signal_wave_queue, (time, pos, value))

        # input_signal_wave_queue と pending_signal_wave_queue が両方とも空になるまでループ
        while input_signal_wave_queue or pending_signal_wave_queue:
            clock_signal_event        = False
            clock_signal_event_value  = None
            input_signal_changed_list = []
            # ペンディングされた入力信号がある場合
            if pending_signal_wave_queue:
                # ペンディングされた入力信号の値が変化する時刻
                time = pending_signal_wave_queue[0][0]
            # ペンディングされた入力信号がない場合
            else:
                # 入力信号の値が変化する時刻のうち最も早い時刻
                time = input_signal_wave_queue[0][0]

                # 同じ時刻に変化する入力信号を取り出す
                # その際、クロック信号とそれ以外の信号とを分別する
                # クロック以外の信号は一旦 pending_signal_wave_queue に格納する
                while input_signal_wave_queue and input_signal_wave_queue[0][0] == time:
                    _, pos, value = heapq.heappop(input_signal_wave_queue)
                    if pos == self.clock_signal_pos:
                        clock_signal_event       = True
                        clock_signal_event_value = value
                    else:
                        pending_signal_wave_queue.append((time, pos, value))
                        
            # 同じ時刻に変化する信号のうち、クロック信号がある場合は
            # 先にクロック信号の変化のみで process を実行する
            # この場合は pending_signal_wave_queue の内容を保持して次のループで実行する
            if clock_signal_event:
                # クロック信号に値をセットして input_signal_changed_list に追加
                clock_signal = self.input_signal_list[self.clock_signal_pos]
                clock_signal.set_curr_value(clock_signal_event_value)
                input_signal_changed_list.append(self.clock_signal_pos)
            # 同じ時刻に変化する信号のうち、クロック信号がない場合
            # pending_signal_wave_queue の中身をすべて取り出して
            # 信号に値をセットして input_signal_changed_list に追加する
            else:
                while pending_signal_wave_queue:
                    _, pos, value = pending_signal_wave_queue.popleft()
                    input_signal = self.input_signal_list[pos]
                    input_signal.set_curr_value(value)
                    input_signal_changed_list.append(pos)

            # Output_Signal に時刻をセット
            for output_signal in self.output_signal_list:
                output_signal.pre_process(time)
            
            # process を実行
            for process in self.process_list:
                process.run()

            # Output_Signal の変化を取得
            for output_signal in self.output_signal_list:
                output_signal.post_process()

            # 変化した入力信号の次の値を取得して input_signal_wave_queue に追加
            for pos in input_signal_changed_list:
                try:
                    next_time, next_value = next(input_signal_iterator_list[pos])
                    heapq.heappush(input_signal_wave_queue, (next_time, pos, next_value))
                except StopIteration:
                    pass                

            # Clock_Signal に値を再度セットして rising_edge / falling_edge を False にする
            if clock_signal_event:
                clock_signal = self.input_signal_list[self.clock_signal_pos]
                clock_signal.set_curr_value(clock_signal_event_value)

        # 出力信号の格納時刻を更新
        for output_signal in self.output_signal_list:
            output_signal.update_generated_time(start_time, end_time)
