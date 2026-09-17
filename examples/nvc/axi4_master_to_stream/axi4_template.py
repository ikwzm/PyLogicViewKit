from logic_view_kit import View_Option

status_color  = {"NONE" : {"foreground": "#707070" , "background": "#202020" },
                 "XFER" : {"foreground": "#FFFFFF" , "background": "red" },
                 "VALID": {"foreground": "#FFFFFF" , "background": "blue" },
                 "READY": {"foreground": "#A0A0A0" , "background": "#303030" }}
class Template:
    def __init__(self, parent_group, name, option=None):
        self.name           = name
        self.parent_group   = parent_group
        self.option         = View_Option(option)
        self.template       = self.VIEW_TEMPLATE
        self.root_group     = parent_group.add_group(self.name, self.option)

    def add_virtual_module(self, vm_name):
        return self.root_group.model.add_virtual_module(vm_name)
    
class AXI4_Read_Template(Template):
    VIEW_TEMPLATE = [
        {"name"  : "aclk",
         "option": {"signal": {"unique": True}},
         "clock" : {"signal": "{clock}", "option": {"signal":{"required":True}}}
        },
        {"name"  : "ar",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "arid"    , "signal": "{prefix}arid*"    , "option":{"signal":{"required":False}}},
             {"name": "araddr"  , "signal": "{prefix}araddr*"  , "option":{"signal":{"required":True }}},
             {"name": "arlen"   , "signal": "{prefix}arlen*"   , "option":{"signal":{"required":False}}},
             {"name": "arsize"  , "signal": "{prefix}arsize*"  , "option":{"signal":{"required":False}}},
             {"name": "arburst" , "signal": "{prefix}arburst*" , "option":{"signal":{"required":False}}},
             {"name": "arlock"  , "signal": "{prefix}arlock*"  , "option":{"signal":{"required":False}}},
             {"name": "arcache" , "signal": "{prefix}arcache*" , "option":{"signal":{"required":False}}},
             {"name": "arprot"  , "signal": "{prefix}arprot*"  , "option":{"signal":{"required":False}}},
             {"name": "arregion", "signal": "{prefix}arregion*", "option":{"signal":{"required":False}}},
             {"name": "aruser"  , "signal": "{prefix}aruser*"  , "option":{"signal":{"required":False}}},
             {"name": "arvalid" , "signal": "{prefix}arvalid"  , "option":{"signal":{"required":True }}},
             {"name": "arready" , "signal": "{prefix}arready"  , "option":{"signal":{"required":True }}},
         ],
        },
        {"name"  : "r",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "rid"     , "signal": "{prefix}rid*"     , "option":{"signal":{"required":False}}},
             {"name": "ruser"   , "signal": "{prefix}ruser*"   , "option":{"signal":{"required":False}}},
             {"name": "rdata"   , "signal": "{prefix}rdata*"   , "option":{"signal":{"required":True }}},
             {"name": "rresp"   , "signal": "{prefix}rresp*"   , "option":{"signal":{"required":True }}},
             {"name": "rlast"   , "signal": "{prefix}rlast"    , "option":{"signal":{"required":True }}},
             {"name": "rvalid"  , "signal": "{prefix}rvalid"   , "option":{"signal":{"required":True }}},
             {"name": "rready"  , "signal": "{prefix}rready"   , "option":{"signal":{"required":True }}},
         ],
        },
    ]
    def __init__(self, parent_group, name, prefix, clock, option=None):
        new_option = View_Option({"signal": {"prefix": prefix, "clock": clock}}).merge(option)
        super().__init__(parent_group, name, new_option)

    def build(self):
        self.root_group.apply_view_template(self.VIEW_TEMPLATE)
        self.vm_name        = self.name + "_vm"
        self.vm_option      = self.root_group.child_option.merge(self.option)
        self.virtual_module = self.add_virtual_module(self.vm_name)
        self.virtual_module.apply_view_template(self.VIEW_TEMPLATE, self.vm_option)
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
    VIEW_TEMPLATE = [
        {"name"  : "aclk",
         "clock" : {"signal": "{clock}", "option": {"signal":{"unique": True, "required":True}}}
        },
        {"name"  : "aw",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "awid"    , "signal": "{prefix}awid*"    , "option":{"signal":{"required":False}}},
             {"name": "awaddr"  , "signal": "{prefix}awaddr*"  , "option":{"signal":{"required":True }}},
             {"name": "awlen"   , "signal": "{prefix}awlen*"   , "option":{"signal":{"required":False}}},
             {"name": "awsize"  , "signal": "{prefix}awsize*"  , "option":{"signal":{"required":False}}},
             {"name": "awburst" , "signal": "{prefix}awburst*" , "option":{"signal":{"required":False}}},
             {"name": "awlock"  , "signal": "{prefix}awlock*"  , "option":{"signal":{"required":False}}},
             {"name": "awcache" , "signal": "{prefix}awcache*" , "option":{"signal":{"required":False}}},
             {"name": "awprot"  , "signal": "{prefix}awprot*"  , "option":{"signal":{"required":False}}},
             {"name": "awregion", "signal": "{prefix}awregion*", "option":{"signal":{"required":False}}},
             {"name": "awuser"  , "signal": "{prefix}awuser*"  , "option":{"signal":{"required":False}}},
             {"name": "awqos"   , "signal": "{prefix}awqos*"   , "option":{"signal":{"required":False}}},
             {"name": "awvalid" , "signal": "{prefix}awvalid"  , "option":{"signal":{"required":True }}},
             {"name": "awready" , "signal": "{prefix}awready"  , "option":{"signal":{"required":True }}},
         ],
        },
        {"name"  : "w",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "wid"     , "signal": "{prefix}wid*"     , "option":{"signal":{"required":False}}},
             {"name": "wuser"   , "signal": "{prefix}wuser*"   , "option":{"signal":{"required":False}}},
             {"name": "wdata"   , "signal": "{prefix}wdata*"   , "option":{"signal":{"required":True }}},
             {"name": "wstrb"   , "signal": "{prefix}wstrb*"   , "option":{"signal":{"required":True }}},
             {"name": "wlast"   , "signal": "{prefix}wlast"    , "option":{"signal":{"required":True }}},
             {"name": "wvalid"  , "signal": "{prefix}wvalid"   , "option":{"signal":{"required":True }}},
             {"name": "wready"  , "signal": "{prefix}wready"   , "option":{"signal":{"required":True }}},
         ],
        },
        {"name"  : "b",
         "option": {"signal": {"unique": True}},
         "group" : [
             {"name": "bid"     , "signal": "{prefix}bid*"     , "option":{"signal":{"required":False}}},
             {"name": "buser"   , "signal": "{prefix}buser*"   , "option":{"signal":{"required":False}}},
             {"name": "bresp"   , "signal": "{prefix}bresp*"   , "option":{"signal":{"required":True }}},
             {"name": "bvalid"  , "signal": "{prefix}bvalid"   , "option":{"signal":{"required":True }}},
             {"name": "bready"  , "signal": "{prefix}bready"   , "option":{"signal":{"required":True }}},
         ],
        },
    ]
    def __init__(self, parent_group, name, prefix, clock, option=None):
        new_option = View_Option({"signal": {"prefix": prefix, "clock": clock}}).merge(option)
        super().__init__(parent_group, name, new_option)

    def build(self):
        self.root_group.apply_view_template(self.VIEW_TEMPLATE)
        self.vm_name        = self.name + "_vm"
        self.vm_option      = self.root_group.child_option.merge(self.option)
        self.virtual_module = self.add_virtual_module(self.vm_name)
        self.virtual_module.apply_view_template(self.VIEW_TEMPLATE, self.vm_option)
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
    VIEW_TEMPLATE = [
             {"name"  : "aclk", 
              "clock" : {"signal": "{clock}", "option": {"signal":{"unique": True, "required":True}}}},
             {"name": "data"    , "signal": "{prefix}data*"    , "option":{"signal":{"required":True }}},
             {"name": "strb"    , "signal": "{prefix}strb*"    , "option":{"signal":{"required":True }}},
             {"name": "last"    , "signal": "{prefix}last"     , "option":{"signal":{"required":True }}},
             {"name": "valid"   , "signal": "{prefix}valid"    , "option":{"signal":{"required":True }}},
             {"name": "ready"   , "signal": "{prefix}ready"    , "option":{"signal":{"required":True }}},
         ]
    def __init__(self, parent_group, name, prefix, clock, option=None):
        new_option = View_Option({"signal": {"prefix": prefix, "clock": clock}}).merge(option)
        super().__init__(parent_group, name, new_option)
        
    def build(self):
        self.root_group.apply_view_template(self.VIEW_TEMPLATE)
        self.vm_name        = self.name + "_vm"
        self.vm_option      = self.root_group.child_option.merge(self.option)
        self.virtual_module = self.add_virtual_module(self.vm_name)
        self.virtual_module.apply_view_template(self.VIEW_TEMPLATE, self.vm_option)
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

