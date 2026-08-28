default_color = {"name":  {"background": "blue", "foreground": "white"},
                 "value": {"background": "blue", "foreground": "white"}}
view_model   = View_Model('axi4_m2s_tb_32_32_256_sync.fst', {"color": default_color})
view_model.add_signal_clock("*::tb::i_clk", {"display_wave": True})
# view_model.add_virtual_clock("v_clk", "10 ns", "5 ns", {"display_wave": True})
c_axi    = view_model.add_group("c_axi")
c_axi_ar = c_axi.add_group("ar").add_signals("*::tb::dut::c_ar*")
c_axi_r  = c_axi.add_group("r" ).add_signals("*::tb::dut::c_r*" )
c_axi_aw = c_axi.add_group("aw").add_signals("*::tb::dut::c_aw*")
c_axi_w  = c_axi.add_group("w" ).add_signals("*::tb::dut::c_w*" )
c_axi_b  = c_axi.add_group("b" ).add_signals("*::tb::dut::c_b*" )

i_axi    = view_model.add_group("i_axi")
i_axi_ar = i_axi.add_group("ar").add_signals("*::tb::dut::i_ar*")
i_axi_r  = (i_axi.add_group("r" )
              .add_signals("*::tb::dut::i_rid*"   )
              .add_signals("*::tb::dut::i_rdata*" )
              .add_signals("*::tb::dut::i_rresp*" )
              .add_signals("*::tb::dut::i_rlast*" )
              .add_signals("*::tb::dut::i_rvalid" )
              .add_signals("*::tb::dut::i_rready" ))

o_axis   = (view_model.add_group("o_axis")
              .add_signals("*::tb::dut::o_data*")
              .add_signals("*::tb::dut::o_strb*")
              .add_signals("*::tb::dut::o_last*")
              .add_signals("*::tb::dut::o_valid")
              .add_signals("*::tb::dut::o_ready"))
            
