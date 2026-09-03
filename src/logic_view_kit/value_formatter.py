#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import re

class Value_Formatter:
    
    class Vector:
        VALUE_FORMAT_RE = re.compile(
            r"^(?P<alternate>\#?)"
            r"(?P<zero>0?)"
            r"(?P<width>\d*)"
            r"(?P<type>[bBoOxXd])"
            r"(?P<suffix>.*)$"
        )
        def __init__(self, value_type, width=1, value_format=None):
            self.value_type = value_type
            if value_format is not None:
                self.value_format = value_format
            elif width >= 8 and width % 4 == 0:
                self.value_format = f"#0{width // 4 + 2}x"
            else:
                self.value_format = f"0{width}b"
            match = self.VALUE_FORMAT_RE.fullmatch(self.value_format)
            if match is None:
                raise ValueError(f"Invalid format: {self.value_format!r}")
            format_alternate   = bool(match.group("alternate"))
            self.format_zero   = bool(match.group("zero"))
            self.format_width  = int(match.group("width")) if match.group("width") else None
            self.format_type   = match.group("type")
            self.format_suffix = match.group("suffix")
            if not format_alternate:
                self.value_format_prefix = ""
            elif self.format_type in ("b", "B"):
                self.value_format_prefix = "0b"
            elif self.format_type in ("o", "O"):
                self.value_format_prefix = "0o"
            elif self.format_type == "x":
                self.value_format_prefix = "0x"
            elif self.format_type == "X":
                self.value_format_prefix = "0X"
            else:
                self.value_format_prefix = ""

        def format_value(self, value):
            if all(c in "01" for c in value):
                return format(int(value,2), self.value_format)

            def _format_4state_bits(value, bit_width):
                result  = []
                padding = (-len(value)) % bit_width
                value   = "0" * padding + value
                for pos in range(0, len(value), bit_width):
                    bits = value[pos:pos + bit_width]
                    if all(c in "01" for c in bits):
                        number = int(bits, 2)
                        result.append(format(number, self.format_type))
                    elif any(c in "xXuU" for c in bits):
                        result.append("U")
                    elif any(c in "zZ"   for c in bits):
                        result.append("Z")
                    else:
                        result.append("?")
                return "".join(result)
            
            if   self.format_type in ("x", "X"):
                result = _format_4state_bits(value, 4)
            elif self.format_type in ("o", "O"):
                result = _format_4state_bits(value, 3)
            else:
                result = value

            if self.format_width is not None:
                content_width = self.format_width - len(self.value_format_prefix)
                if len(result) < content_width:
                    padding = content_width - len(result)
                    if self.format_zero:
                        result = "0" * padding + result
                    else:
                        result = " " * padding + result
            return self.value_format_prefix + result + self.format_suffix

    class Logic:
        def __init__(self, value_type, width=1, value_format=None):
            self.value_type   = value_type
            self.width        = width
            if value_format is None:
                self.value_format = ""
            else:
                self.value_format = value_format
        def format_value(self, value):
            return format(value, self.value_format)
        
    class Other:
        def __init__(self, value_type, width, value_format=None):
            self.value_type   = value_type
            self.width        = width
            if value_format is None:
                self.value_format = ""
            else:
                self.value_format = value_format
        def format_value(self, value):
            return format(value, self.value_format)

    @classmethod
    def get(cls, value_type, width, is_logic=False, value_format=None):
        if is_logic is True:
            return cls.Logic(value_type, width, value_format)
        if value_type.is_logic:
            return cls.Logic(value_type, width, value_format)
        if value_type.is_vector:
            return cls.Vector(value_type, width, value_format)
        return cls.Other(value_type, width, value_format)
