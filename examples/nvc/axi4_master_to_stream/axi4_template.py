status_color  = {"NONE" : {"foreground": "#707070" , "background": "#202020" },
                 "XFER" : {"foreground": "#FFFFFF" , "background": "red" },
                 "VALID": {"foreground": "#FFFFFF" , "background": "blue" },
                 "READY": {"foreground": "#A0A0A0" , "background": "#303030" }}
class Template:
    def __init__(self, parent_group, name, signal_pattern, clock_pattern=None, option=None):
        self.name           = name
        self.signal_pattern = signal_pattern
        self.option         = option
        self.signal_map     = []
        self.root_group     = parent_group.add_group(self.name, option)
        if clock_pattern is not None:
            self.root_group.add_signal_clock(clock_pattern)

    def build_signal_map(self, signal_map, option):
        def build(contents, parent_option):
            new_list = []
            for item in contents:
                if "group" in item:
                    group_name     = item["name"]
                    group_option   = item.get("option")
                    child_contents = item["group"]
                    child_group    = build(child_contents, group_option)
                    new_list.append({"name": group_name, "option": group_option, "group": child_group})
                if "signal" in item:
                    signal_name    = item["name"]
                    signal_option  = item.get("option")
                    signal_pattern = item["signal"]
                    signal_pattern = self.signal_pattern + signal_pattern
                    new_list.append({"name": signal_name, "option": signal_option, "signal": signal_pattern})
            return new_list
        self.signal_map = build(signal_map, option)
                
    def build_group(self):
        def build(group, signal_map):
            for item in signal_map:
                if "group" in item:
                    group_name     = item["name"]
                    group_option   = item.get("option")
                    child_contents = item["group"]
                    child_group    = group.add_group(group_name, group_option)
                    build(child_group, child_contents)
                    continue
                if "signal" in item:
                    signal_name    = item["name"]
                    signal_option  = item.get("option")
                    signal_pattern = item["signal"]
                    group.add_signals(signal_pattern, signal_option)
                    continue
        build(self.root_group, self.signal_map)

    def add_virtual_module(self, vm_name):
        return self.root_group.model.add_virtual_module(vm_name)
    
    def add_input_signals_to_virtual_module(self, virtual_module):
        def add_input_singals(signal_map):
            for item in signal_map:
                if "group" in item:
                    child_contents = item["group"]
                    add_input_singals(child_contents)
                if "signal" in item:
                    signal_name    = item["name"]
                    signal_option  = item.get("option")
                    signal_pattern = item["signal"]
                    virtual_module.add_input_signal(signal_name, signal_pattern, signal_option)
        add_input_singals(self.signal_map)
                    
class AXI4_Read_Template(Template):
    SIGNAL_MAP = [
        {"name"  : "ar",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "arid"    , "signal": "arid*"    , "option": {"signal": {"required": False}}},
             {"name": "araddr"  , "signal": "araddr*"  , "option": {"signal": {"required": True }}},
             {"name": "arlen"   , "signal": "arlen*"   , "option": {"signal": {"required": False}}},
             {"name": "arsize"  , "signal": "arsize*"  , "option": {"signal": {"required": False}}},
             {"name": "arburst" , "signal": "arburst*" , "option": {"signal": {"required": False}}},
             {"name": "arlock"  , "signal": "arlock*"  , "option": {"signal": {"required": False}}},
             {"name": "arcache" , "signal": "arcache*" , "option": {"signal": {"required": False}}},
             {"name": "arprot"  , "signal": "arprot*"  , "option": {"signal": {"required": False}}},
             {"name": "arregion", "signal": "arregion*", "option": {"signal": {"required": False}}},
             {"name": "aruser"  , "signal": "aruser*"  , "option": {"signal": {"required": False}}},
             {"name": "arvalid" , "signal": "arvalid"  , "option": {"signal": {"required": True }}},
             {"name": "arready" , "signal": "arready"  , "option": {"signal": {"required": True }}},
         ],
        },
        {"name"  : "r",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "rid"     , "signal": "rid*"     , "option": {"signal": {"required": False}}},
             {"name": "ruser"   , "signal": "ruser*"   , "option": {"signal": {"required": False}}},
             {"name": "rdata"   , "signal": "rdata*"   , "option": {"signal": {"required": True }}},
             {"name": "rresp"   , "signal": "rresp*"   , "option": {"signal": {"required": True }}},
             {"name": "rlast"   , "signal": "rlast"    , "option": {"signal": {"required": True }}},
             {"name": "rvalid"  , "signal": "rvalid"   , "option": {"signal": {"required": True }}},
             {"name": "rready"  , "signal": "rready"   , "option": {"signal": {"required": True }}},
         ],
        },
    ]
    def __init__(self, parent_group, name, signal_pattern, clock_pattern, option=None):
        super().__init__(parent_group, name, signal_pattern, None, option)
        self.build_signal_map(self.SIGNAL_MAP, self.option)
        self.clock_pattern  = clock_pattern

    def build(self):
        self.build_group()
        self.vm_name        = self.name + "_vm"
        self.virtual_module = self.add_virtual_module(self.vm_name)
        self.add_input_signals_to_virtual_module(self.virtual_module)
        self.virtual_module.add_clock_signal( "aclk", self.clock_pattern)
        self.virtual_module.add_output_signal("status"        , "VHDL_STRING"  , None, "NONE")
        self.virtual_module.add_output_signal("pipeline_level", "VHDL_SIGNED"  , 32,   0)
        self.virtual_module.add_output_signal("ar_status"     , "VHDL_STRING"  , None, "NONE")
        self.virtual_module.add_output_signal("r_status"      , "VHDL_STRING"  , None, "NONE")
        self.axi_ar = self.root_group.get_group(["ar"])
        self.axi_r  = self.root_group.get_group(["r" ])
        def gen_status(aclk, arvalid, arready, rvalid, rready, rlast, pipeline_level, status):
            if aclk.rising_edge:
                curr_level = int(pipeline_level)
                if arvalid.is_high and arready.is_high:
                    curr_level = curr_level + 1
                if rvalid.is_high and rready.is_high and rlast.is_high:
                    curr_level = curr_level - 1
                pipeline_level <<= curr_level
            if int(pipeline_level) > 0:
                status <<= "XFER"
            elif arvalid.is_high and arready.is_high:
                status <<= "XFER"
            elif arvalid.is_high and arready.is_low:
                status <<= "VALIE"
            elif arvalid.is_low  and arready.is_high:
                status <<= "READY"
            else:
                status <<= "NONE"
        def gen_ar_status(arvalid, arready, ar_status):
            if   arvalid.is_high and arready.is_high:
                ar_status <<= "XFER"
            elif arvalid.is_high and arready.is_low:
                ar_status <<= "VALID"
            elif arvalid.is_low  and arready.is_high:
                ar_status <<= "READY"
            else:
                ar_status <<= "NONE"
        def gen_r_status(rvalid, rready, r_status):
            if   rvalid.is_high and rready.is_high:
                r_status <<= "XFER"
            elif rvalid.is_high and rready.is_low:
                r_status <<= "VALID"
            elif rvalid.is_low  and rready.is_high:
                r_status <<= "READY"
            else:
                r_status <<= "NONE"
        self.virtual_module.add_process(gen_status)
        self.virtual_module.add_process(gen_ar_status)
        self.virtual_module.add_process(gen_r_status)
        status_option = {"color": {"wave": {"text": status_color}}}
        self.root_group.add_display_signal(f"[{self.vm_name}]status", status_option)
        self.axi_ar.add_display_signal( f"[{self.vm_name}]ar_status", status_option)
        self.axi_r.add_display_signal(   f"[{self.vm_name}]r_status", status_option)
            
class AXI4_Write_Template(Template):
    SIGNAL_MAP = [
        {"name"  : "aw",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "awid"    , "signal": "awid*"    , "option": {"signal": {"required": False}}},
             {"name": "awaddr"  , "signal": "awaddr*"  , "option": {"signal": {"required": True }}},
             {"name": "awlen"   , "signal": "awlen*"   , "option": {"signal": {"required": False}}},
             {"name": "awsize"  , "signal": "awsize*"  , "option": {"signal": {"required": False}}},
             {"name": "awburst" , "signal": "awburst*" , "option": {"signal": {"required": False}}},
             {"name": "awlock"  , "signal": "awlock*"  , "option": {"signal": {"required": False}}},
             {"name": "awcache" , "signal": "awcache*" , "option": {"signal": {"required": False}}},
             {"name": "awprot"  , "signal": "awprot*"  , "option": {"signal": {"required": False}}},
             {"name": "awregion", "signal": "awregion*", "option": {"signal": {"required": False}}},
             {"name": "awuser"  , "signal": "awuser*"  , "option": {"signal": {"required": False}}},
             {"name": "awqos"   , "signal": "awqos*"   , "option": {"signal": {"required": False}}},
             {"name": "awvalid" , "signal": "awvalid"  , "option": {"signal": {"required": True }}},
             {"name": "awready" , "signal": "awready"  , "option": {"signal": {"required": True }}},
         ],
        },
        {"name"  : "w",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "wid"     , "signal": "wid*"     , "option": {"signal": {"required": False}}},
             {"name": "wuser"   , "signal": "wuser*"   , "option": {"signal": {"required": False}}},
             {"name": "wdata"   , "signal": "wdata*"   , "option": {"signal": {"required": True }}},
             {"name": "wstrb"   , "signal": "wstrb*"   , "option": {"signal": {"required": True }}},
             {"name": "wlast"   , "signal": "wlast"    , "option": {"signal": {"required": True }}},
             {"name": "wvalid"  , "signal": "wvalid"   , "option": {"signal": {"required": True }}},
             {"name": "wready"  , "signal": "wready"   , "option": {"signal": {"required": True }}},
         ],
        },
        {"name"  : "b",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "bid"     , "signal": "bid*"     , "option": {"signal": {"required": False}}},
             {"name": "buser"   , "signal": "buser*"   , "option": {"signal": {"required": False}}},
             {"name": "bresp"   , "signal": "bresp*"   , "option": {"signal": {"required": True }}},
             {"name": "bvalid"  , "signal": "bvalid"   , "option": {"signal": {"required": True }}},
             {"name": "bready"  , "signal": "bready"   , "option": {"signal": {"required": True }}},
         ],
        },
    ]
    def __init__(self, parent_group, name, signal_pattern, clock_pattern=None, option=None):
        super().__init__(parent_group, name, signal_pattern, None, option)
        self.build_signal_map(self.SIGNAL_MAP, self.option)
        self.clock_pattern = clock_pattern

    def build(self):
        self.build_group()
        self.vm_name        = self.name + "_vm"
        self.virtual_module = self.add_virtual_module(self.vm_name)
        self.add_input_signals_to_virtual_module(self.virtual_module)
        self.virtual_module.add_clock_signal( "aclk", self.clock_pattern)
        self.virtual_module.add_output_signal("status"        , "VHDL_STRING"  , None, "NONE")
        self.virtual_module.add_output_signal("pipeline_level", "VHDL_SIGNED"  , 32,   0)
        self.virtual_module.add_output_signal("aw_status"     , "VHDL_STRING"  , None, "NONE")
        self.virtual_module.add_output_signal("w_status"      , "VHDL_STRING"  , None, "NONE")
        self.virtual_module.add_output_signal("b_status"      , "VHDL_STRING"  , None, "NONE")
        self.axi_aw = self.root_group.get_group(["aw"])
        self.axi_w  = self.root_group.get_group(["w" ])
        self.axi_b  = self.root_group.get_group(["b" ])
        def gen_status(aclk, awvalid, awready, bvalid, bready, pipeline_level, status):
            if aclk.rising_edge:
                curr_level = int(pipeline_level)
                if awvalid.is_high and awready.is_high:
                    curr_level = curr_level + 1
                if bvalid.is_high and bready.is_high:
                    curr_level = curr_level - 1
                pipeline_level <<= curr_level
            if int(pipeline_level) > 0:
                status <<= "XFER"
            elif awvalid.is_high and awready.is_high:
                status <<= "XFER"
            elif awvalid.is_high and awready.is_low:
                status <<= "VALIE"
            elif awvalid.is_low  and awready.is_high:
                status <<= "READY"
            else:
                status <<= "NONE"
        def gen_aw_status(awvalid, awready, aw_status):
            if   awvalid.is_high and awready.is_high:
                aw_status <<= "XFER"
            elif awvalid.is_high and awready.is_low:
                aw_status <<= "VALID"
            elif awvalid.is_low  and awready.is_high:
                aw_status <<= "READY"
            else:
                aw_status <<= "NONE"
        def gen_w_status(wvalid, wready, w_status):
            if   wvalid.is_high and wready.is_high:
                w_status <<= "XFER"
            elif wvalid.is_high and wready.is_low:
                w_status <<= "VALID"
            elif wvalid.is_low  and wready.is_high:
                w_status <<= "READY"
            else:
                w_status <<= "NONE"
        def gen_b_status(bvalid, bready, b_status):
            if   bvalid.is_high and bready.is_high:
                b_status <<= "XFER"
            elif bvalid.is_high and bready.is_low:
                b_status <<= "VALID"
            elif bvalid.is_low  and bready.is_high:
                b_status <<= "READY"
            else:
                b_status <<= "NONE"
        self.virtual_module.add_process(gen_status)
        self.virtual_module.add_process(gen_aw_status)
        self.virtual_module.add_process(gen_w_status)
        self.virtual_module.add_process(gen_b_status)
        status_option = {"color": {"wave": {"text": status_color}}}
        self.root_group.add_display_signal(f"[{self.vm_name}]status", status_option)
        self.axi_aw.add_display_signal( f"[{self.vm_name}]aw_status", status_option)
        self.axi_w.add_display_signal(   f"[{self.vm_name}]w_status", status_option)
        self.axi_b.add_display_signal(   f"[{self.vm_name}]b_status", status_option)

class AXI4_Stream_Template(Template):
    SIGNAL_MAP = [
             {"name": "data"    , "signal": "data*"    , "option": {"signal": {"required": True }}},
             {"name": "strb"    , "signal": "strb*"    , "option": {"signal": {"required": True }}},
             {"name": "last"    , "signal": "last"     , "option": {"signal": {"required": True }}},
             {"name": "valid"   , "signal": "valid"    , "option": {"signal": {"required": True }}},
             {"name": "ready"   , "signal": "ready"    , "option": {"signal": {"required": True }}},
         ]
    def __init__(self, parent_group, name, signal_pattern, clock_pattern=None, option=None):
        super().__init__(parent_group, name, signal_pattern, None, option)
        self.build_signal_map(self.SIGNAL_MAP, self.option)
        self.clock_pattern = clock_pattern
        
    def build(self):
        self.build_group()
        self.vm_name        = self.name + "_vm"
        self.virtual_module = self.add_virtual_module(self.vm_name)
        self.add_input_signals_to_virtual_module(self.virtual_module)
        self.virtual_module.add_clock_signal( "aclk"  , self.clock_pattern)
        self.virtual_module.add_output_signal("status", "VHDL_STRING"  , None, "NONE")
        def gen_status(valid, ready, status):
            if   valid.is_high and ready.is_high:
                status <<= "XFER"
            elif valid.is_high and ready.is_low:
                status <<= "VALID"
            elif valid.is_low  and ready.is_high:
                status <<= "READY"
            else:
                status <<= "NONE"
        self.virtual_module.add_process(gen_status)
        status_option = {"color": {"wave": {"text": status_color}}}
        self.root_group.add_display_signal(f"[{self.vm_name}]status", status_option)

