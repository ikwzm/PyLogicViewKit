from axi4_template import AXI4_Read_Template
from axi4_template import AXI4_Write_Template
from axi4_template import AXI4_Stream_Template

default_color = {"name":  {"background": "blue", "foreground": "white"},
                 "value": {"background": "blue", "foreground": "white"}}
view_model   = View_Model('axi4_m2s_tb_32_32_256_sync.fst', {"display_rows": 50, "color": default_color})
view_model.add_signal_clock("*::tb::i_clk", {"display_wave": True})

c_axi   = view_model.add_group("c_axi")
c_axi_r = AXI4_Read_Template( c_axi, "r", "*::tb::dut::c_", "*::tb::i_clk")
c_axi_w = AXI4_Write_Template(c_axi, "w", "*::tb::dut::c_", "*::tb::i_clk")
c_axi_r.build()
c_axi_w.build()

i_axi   = AXI4_Read_Template(  view_model, "i_axi" , "*::tb::dut::i_", "*::tb::i_clk")
i_axi.build()

o_view_list = view_model.add_view_list("o", {"display_rows": 7})
o_view_list.add_signal_clock("*::tb::o_clk", {"display_wave": True})
o_axis  = AXI4_Stream_Template(o_view_list, "o_axis", "*::tb::dut::o_", "*::tb::o_clk")
o_axis.build()

report   = (view_model.add_group("report", {"signal":{"unique": True}})
              .add_signals("*::tb::n_report")
              .add_signals("*::tb::c_report")
              .add_signals("*::tb::i_report")
              .add_signals("*::tb::o_report"))
