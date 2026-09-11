#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import re

class Value_Type:
    class Vector_Range:
        def __init__(self, left, right):
            self.left  = left
            self.right = right
            self.high  = max(left, right)
            self.low   = min(left, right)
            self.width = self.high - self.low + 1
            
    VERILOG_VECTOR_RE       = re.compile(r"^(.*?)\s*\[\s*(.*?)\s*\]$")
    VERILOG_VECTOR_RANGE_RE = re.compile(r"^(\d+)\s*:\s*(\d+)$")
    VERILOG_VECTOR_WIDTH_RE = re.compile(r"^(\d+)$")
    VHDL_VECTOR_RE          = re.compile(r"^(.*?)\s*\(\s*(.*?)\s*\)$")
    VHDL_VECTOR_RANGE_TO_RE = re.compile(r"^(\d+)\s*[tT][oO]\s*(\d+)$")
    VHDL_VECTOR_RANGE_DN_RE = re.compile(r"^(\d+)\s*[dD][oO][wW][nN][tT][oO]\s*(\d+)$")
    VERILOG_VECTOR_TYPES    = ("SV_INTEGER" , "SV_UNSIGNED_INTEGER" ,
                               "SV_INT"     , "SV_UNSIGNED_INT"     ,
                               "SV_SHORTINT", "SV_UNSIGNED_SHORTINT",
                               "SV_LONGINT" , "SV_UNSIGNED_LONGINT" ,
                               "SV_BYTE"    , "SV_UNSIGNED_BYTE"    ,
                               "SV_BIT"     , "SV_UNSIGNED_BIT"     ,
                               "SV_LOGIC"   , "SV_UNSIGNED_LOGIC"   )
    VHDL_VECTOR_TYPES       = ("VHDL_BIT_VECTOR",
                               "VHDL_STD_ULOGIC_VECTOR",
                               "VHDL_STD_LOGIC_VECTOR" ,
                               "VHDL_UNSIGNED"         ,
                               "VHDL_SIGNED"           )
    def __init__(self, name, value_type, width=0):
        vector_range_by_name = None
        vector_range_by_type = None
        signed = False
        if name is not None:
            if vector_range_by_name is None:
                match = Value_Type.VERILOG_VECTOR_RE.fullmatch(name)
                if match:
                    name       = match.group(1).strip()
                    range_spec = match.group(2)
                    if vector_range_by_name is None:
                        range_match = Value_Type.VERILOG_VECTOR_RANGE_RE.fullmatch(range_spec)
                        if range_match:
                            left  = int(range_match.group(1))
                            right = int(range_match.group(2))
                            vector_range_by_name = Value_Type.Vector_Range(left, right)
                    if vector_range_by_name is None:
                        width_match = Value_Type.VERILOG_VECTOR_WIDTH_RE.fullmatch(range_spec)
                        if width_match:
                            left  = int(width_match.group(1)) - 1
                            right = 0
                            vector_range_by_name = Value_Type.Vector_Range(left, right)
                    if vector_range_by_name is None:
                        raise ValueError(f"Invalid range specification {name}[{range_spec}]")
        if value_type is not None:
            if vector_range_by_type is None:
                match = Value_Type.VERILOG_VECTOR_RE.fullmatch(value_type)
                if match:
                    value_type = match.group(1).strip()
                    range_spec = match.group(2)
                    type_match = (value_type in Value_Type.VERILOG_VECTOR_TYPES)
                    if vector_range_by_type is None and type_match:
                        range_match = Value_Type.VERILOG_VECTOR_RANGE_RE.fullmatch(range_spec)
                        if range_match and type_match:
                            left  = int(range_match.group(1))
                            right = int(range_match.group(2))
                            vector_range_by_type = Value_Type.Vector_Range(left, right)
                    if vector_range_by_type is None and type_match:
                        width_match = Value_Type.VERILOG_VECTOR_WIDTH_RE.fullmatch(range_spec)
                        if width_match and type_match:
                            left  = int(width_match.group(1)) - 1
                            right = 0
                            vector_range_by_type = Value_Type.Vector_Range(left, right)
                    if vector_range_by_type is None:
                        raise ValueError(f"Invalid vector specification {value_type}[{range_spec}]")
            if vector_range_by_type is None:
                match = Value_Type.VHDL_VECTOR_RE.fullmatch(value_type)
                if match:
                    value_type = match.group(1).strip()
                    range_spec = match.group(2)
                    type_match = (value_type in Value_Type.VHDL_VECTOR_TYPES)
                    if vector_range_by_type is None and type_match:
                        range_match = Value_Type.VHDL_VECTOR_RANGE_TO_RE.fullmatch(range_spec)
                        if range_match:
                            left  = int(range_match.group(1))
                            right = int(range_match.group(2))
                            vector_range_by_type = Value_Type.Vector_Range(left, right)
                    if vector_range_by_type is None and type_match:
                        range_match = Value_Type.VHDL_VECTOR_RANGE_DN_RE.fullmatch(range_spec)
                        if range_match:
                            left  = int(range_match.group(1))
                            right = int(range_match.group(2))
                            vector_range_by_type = Value_Type.Vector_Range(left, right)
                    if vector_range_by_type is None:
                        raise ValueError(f"Invalid vector specification {value_type}({range_spec})")
            if vector_range_by_type is None:
                width_by_type = None
                if   value_type in Value_Type.VHDL_VECTOR_TYPES:
                    width_by_type = None if width == 0 else width
                elif value_type in ("SV_INTEGER" , "SV_UNSIGNED_INTEGER" ,
                                    "SV_INT"     , "SV_UNSIGNED_INT"     ):
                    width_by_type = 32   if width == 0 else width
                elif value_type in ("SV_SHORTINT", "SV_UNSIGNED_SHORTINT"):
                    width_by_type = 16   if width == 0 else width
                elif value_type in ("SV_LONGINT" , "SV_UNSIGNED_LONGINT" ):
                    width_by_type = 64   if width == 0 else width
                elif value_type in ("SV_BYTE"    , "SV_UNSIGNED_BYTE"    ):
                    width_by_type =  8   if width == 0 else width
                elif value_type in ("SV_BIT"     , "SV_UNSIGNED_BIT"     ,
                                    "SV_LOGIC"   , "SV_UNSIGNED_LOGIC"   ):
                    logic_width   =  1   if width == 0 else width
                    width_by_type = None if logic_width < 2 else logic_width
                if width_by_type is not None:
                    vector_range_by_type = self.Vector_Range(width_by_type-1, 0)
            signed = (value_type in ("SV_INTEGER", "SV_INT", "SV_SHORTINT", "SV_LONGINT", "VHDL_SIGNED"))
        if   vector_range_by_name is not None:
            self.vector_range = vector_range_by_name
            self.width        = self.vector_range.width
            self.is_vector    = True
            self.is_logic     = False
            self.signed       = signed
        elif vector_range_by_type is not None:
            self.vector_range = vector_range_by_type
            self.width        = self.vector_range.width
            self.is_vector    = True
            self.is_logic     = False
            self.signed       = signed
        elif value_type in ("SV_BIT"  , "SV_UNSIGNED_BIT"  ,
                            "SV_LOGIC", "SV_UNSIGNED_LOGIC",
                            "VHDL_BIT", "VHDL_STD_LOGIC"   ,"VHDL_STD_ULOGIC"):
            self.vector_range = None
            self.width        = 1
            self.is_vector    = False
            self.is_logic     = True
            self.signed       = False
        elif value_type in ("GEN_STRING", "VHDL_STRING", "VHDL_BOOLEAN"):
            self.vector_range = None
            self.width        = 1
            self.is_vector    = False
            self.is_logic     = False
            self.signed       = False
        elif width >  1:
            self.vector_range = self.Vector_Range(int(width)-1, 0)
            self.width        = self.vector_range.width
            self.is_vector    = True
            self.is_logic     = False
            self.signed       = signed
        elif width == 1:
            self.vector_range = None
            self.width        = 1
            self.is_vector    = False
            self.is_logic     = True
            self.signed       = False
        else:
            self.vector_range = None
            self.width        = 1
            self.is_vector    = False
            self.is_logic     = False
            self.signed       = False
        self.name       = name
        self.value_type = value_type

