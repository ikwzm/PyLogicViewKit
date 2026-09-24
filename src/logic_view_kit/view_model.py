#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from   .value_formatter   import Value_Formatter
from   .view_option       import View_Option
from   .virtual_module    import Virtual_Module
import re

class View_Model:

    class View_Item:
        def __init__(self, view_list, parent_group, option=None):
            self.view_list    = view_list
            self.model        = self.view_list.model
            self.parent_group = parent_group
            self.option       = View_Option(self.DEFAULT_OPTION)
            if parent_group is not None:
                self.option   = self.option.merge(parent_group.child_option)
                self.depth    = parent_group.depth + 1
            else:
                self.depth    = 0
            self.option       = self.option.merge(option)
            self.color_option = self.option["color"]
            self.shape_option = self.option["shape"]

            # Colors for SignalNameColumn
            self.signal_name_color             = self.get_color("name" , "foreground")
            self.signal_name_background_color  = self.get_color("name" , "background")

            # Colors for SignalValueColumn
            self.signal_value_color            = self.get_color("value", "foreground")
            self.signal_value_background_color = self.get_color("value", "background")

            # Colors for SignalWaveformColumn
            self.wave_group_color              = self.get_color("wave" , "group"     )
            self.wave_signal_color             = self.get_color("wave" , "signal"    )
            self.wave_value_color              = self.get_color("wave" , "value"     )
            self.wave_background_color         = self.get_color("wave" , "background")
            self.wave_text_color               = self.get_color("wave" , "text"      )
            # Shape for SignalWaveformColumn
            self.edge_slope_width              = self.shape_option.get("edge_slope_width"    , 0)
            self.margin_top_height             = self.shape_option.get("margin_top_height"   , 5)
            self.margin_bottom_height          = self.shape_option.get("margin_bottom_height", 5)
            self.draw_line_width               = self.shape_option.get("draw_line_width"     , 1)
            self.selected_line_width           = self.shape_option.get("selected_line_width" ,
                                                                        self.draw_line_width + 1)
            
        def get_color(self, key, prop):
            return self.color_option.get(key,{}).get(prop)

    class View_Signal(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None ,
            "value_format"    : None ,
        }
        def __init__(self, view_list, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
        
    class View_Actual_Signal(View_Signal):
        def __init__(self, view_list, path, node, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.path         = path
            self.node         = node
            self.name         = node["name"]
            self.handle       = node["handle"]
            self.width        = node["width"]
            self.registered   = False
            self.closed       = False
            self.display_name = self.option["display_name"] or self.name
            self.is_logic     = self.width == 1 and not self.name.endswith("]")
            self.value_type   = node["value_type"]
            self.value_formatter = Value_Formatter.get(self.value_type,
                                                       self.width,
                                                       self.is_logic,
                                                       self.option["value_format"])
        def close(self):
            if self.closed is True:
                return
            self.closed = True
            self.unregister_database()

        def register_database(self):
            if self.registered is False:
                self.model.database.register_handle(self.handle)
                self.registered = True

        def unregister_database(self):
            if self.registered is True:
                self.model.database.unregister_handle(self.handle)
                self.registered = False

        def get_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            self.register_database()
            return self.model.database.get(self.handle, start_time, end_time)

        def get_reversed_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            self.register_database()
            return self.model.database.reversed_get(self.handle, start_time, end_time)

        def format_value(self, value):
            return self.value_formatter.format_value(value)
            
    class View_Virtual_Signal(View_Signal):
        def __init__(self, view_list, signal, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.signal       = signal
            self.name         = self.signal.name
            self.value_type   = self.signal.value_type
            self.width        = self.value_type.width
            self.is_logic     = self.value_type.is_logic
            self.closed       = False
            self.display_name = self.option["display_name"] or self.name
            self.value_formatter = Value_Formatter.get(self.value_type,
                                                       self.width,
                                                       self.is_logic,
                                                       self.option["value_format"])
        def close(self):
            if self.closed is True:
                return
            self.closed = True

        def register_database(self):
            pass

        def unregister_database(self):
            pass

        def get_wave(self, start_time, end_time):
            return self.signal.get_wave(start_time, end_time)

        def get_reversed_wave(self, start_time, end_time):
            return self.signal.get_reversed_wave(start_time, end_time)

        def format_value(self, value):
            return self.value_formatter.format_value(value)

    class View_Clock(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None,
            "display_wave"    : False,
            "rising_edge"     : True
        }
        def __init__(self, view_list, name, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.name         = name
            self.closed       = False
            self.display_name = self.option["display_name"] or self.name
            self.display_wave = self.option["display_wave"]
            self.rising_edge  = self.option["rising_edge"]

        def close(self):
            if self.closed is True:
                return
            self.closed = True

        def register_database(self):
            pass

        def unregister_database(self):
            pass

    class View_Signal_Clock(View_Clock):
        DEFAULT_OPTION = {
            "display_name"    : None ,
            "display_wave"    : False,
            "rising_edge"     : True ,
        }
        def __init__(self, signal, option=None):
            super().__init__(signal.view_list, signal.name, signal.parent_group, option)
            self.signal   = signal
            self.option   = self.option.merge(self.signal.option)
            self.is_logic = signal.is_logic
            
        def register_database(self):
            self.signal.register_database()

        def unregister_database(self):
            self.signal.unregister_database()

        def get_edges(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            prev_level = None
            first      = True
            for curr_time, curr_value in self.get_wave(start_time, end_time):
                if curr_value in ("1", "h"):
                    curr_level = 1
                else:
                    curr_level = 0
                if first:
                    first = False
                    prev_level = curr_level
                    continue
                if ((self.rising_edge is True  and prev_level == 0 and curr_level == 1) or
                    (self.rising_edge is False and prev_level == 1 and curr_level == 0)):
                    yield curr_time
                prev_level = curr_level
                
        def get_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            return self.signal.get_wave(start_time, end_time)

        def get_reversed_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            return self.signal.get_reversed_wave(start_time, end_time)

        def is_same_wave(self, clock):
            if not isinstance(clock, self.model.View_Signal_Clock):
                return False
            if clock.signal.handle != self.signal.handle:
                return False
            return True

    class View_Virtual_Clock(View_Clock):
        DEFAULT_OPTION = {
            "display_name"    : None,
            "display_wave"    : False,
            "rising_edge"     : True
        }
        def __init__(self, view_list, name, cycle_time, offset_time, parent_group, option=None):
            super().__init__(view_list, name, parent_group, option)
            self.cycle_time  = cycle_time
            self.offset_time = self.view_list.model.start_time + offset_time
            self.is_logic    = True

        def get_next_edge_time(self, time):
            return (self.offset_time +
                    ((time - self.offset_time + self.cycle_time - 1) // self.cycle_time)
                     * self.cycle_time)
            
        def get_prev_edge_time(self, time):
            return (self.offset_time +
                    ((time - self.offset_time                      ) // self.cycle_time)
                     * self.cycle_time)
            
        def get_edges(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            first_time = self.get_prev_edge_time(start_time)
            last_time  = self.get_next_edge_time(end_time)
            for time in range(first_time, last_time, self.cycle_time):
                yield time

        def get_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            half_cycle_time = self.cycle_time // 2
            if self.rising_edge:
                first_half_level  = "1"
                second_half_level = "0"
            else:
                first_half_level  = "0"
                second_half_level = "1"
            for time in self.get_edges(start_time, end_time):
                yield (time                  , first_half_level )
                yield (time + half_cycle_time, second_half_level)

        def get_reversed_edges(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            first_time = self.get_prev_edge_time(end_time)
            last_time  = self.get_next_edge_time(start_time)
            for time in range(first_time, last_time, -self.cycle_time):
                yield time

        def get_reversed_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            half_cycle_time = self.cycle_time // 2
            if self.rising_edge:
                first_half_level  = "1"
                second_half_level = "0"
            else:
                first_half_level  = "0"
                second_half_level = "1"
            for time in self.get_reversed_edges(start_time, end_time):
                yield (time                  , first_half_level )
                yield (time - half_cycle_time, second_half_level)

        def is_same_wave(self, clock):
            if not isinstance(clock, self.model.View_Virtual_Clock):
                return False
            if clock.cycle_time  != self.cycle_time:
                return False
            if clock.offset_time != self.offset_time:
                return False
            return True

    class View_Group(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None,
            "expand"          : True,
            "signal"          : {"struct_as_group": True}
        }
        def __init__(self, view_list, name, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.name           = name
            self.item_list      = []
            self.group_map      = {}
            self.signal_map     = {}
            self.closed         = False
            self.child_option   = self.option.select(View_Model.INHERITABLE_OPTION)
            self.display_name   = self.option["display_name"] or self.name
            self.display_signal = None
            self.expanded       = self.option["expand"]

        def close(self):
            if self.closed is True:
                return
            self.closed = True
            self.unregister_database()
            if self.display_signal is not None:
                self.display_signal.close()
            for item in self.item_list:
                item.close()
            self.item_list.clear()
            self.group_map.clear()
            self.signal_map.clear()

        def new_option_for_actual_signal(self, option, force_flags=None):
            signal_option = View_Option(self.option["signal"])
            if isinstance(option, dict) and "signal" in option:
                signal_option = signal_option.merge(option["signal"])
            option = View_Option(option)
            if isinstance(force_flags, dict):
                option = option.merge({"signal": force_flags})
            return option.merge({"signal": signal_option})

        def get_actual_signal_list(self, pattern, tree, option):
            signal_option      = option["signal"]
            struct_as_group    = signal_option["struct_as_group"]
            signal_is_unique   = signal_option.get("unique"  , False)
            signal_is_required = signal_option.get("required", False)
            signal_pattern     = pattern.format_map(signal_option)

            signal_list = self.model.database.find_signals(signal_pattern, tree, struct_as_group)

            if signal_is_required is True and len(signal_list) == 0:
                raise RuntimeError(f'No signal matched the specified pattern: "{signal_pattern}"')
            if signal_is_unique   is True and len(signal_list) >= 2:
                raise RuntimeError(f'Multiple signals matched the specified pattern: "{signal_pattern}"')
            return signal_list

        def add_actual_signals(self, pattern, tree, option):
            signal_option   = self.new_option_for_actual_signal(option)
            struct_as_group = signal_option["signal"]["struct_as_group"]
            signal_list     = self.get_actual_signal_list(pattern, tree, signal_option)
            for path_name_list, node in signal_list:
                path = "::".join(path_name_list)
                if "handle" in node:
                    signal = self.model.View_Actual_Signal(self.view_list, path, node, self, signal_option)
                    self.item_list.append(signal)
                    self.signal_map[signal.name] = signal
                elif struct_as_group is True:
                    group_option = View_Option({"expand": False}).merge(option)
                    group = self.add_group(node["name"], group_option)
                    for child in node.get("contents", []):
                       group.add_actual_signals(pattern="**", tree=child, option=option)
                else:
                    raise RuntimeError(f'The specified pattern does not match a signal: "{pattern}"')
            return self

        def get_virtual_signal(self, vm_name, signal_name, option=None):
            vm_signal = self.model.get_output_signal_from_virtual_module(vm_name, signal_name)
            if vm_signal is None:
                raise RuntimeError(f"Not Found Virtual Signal({vm_name},{signal_name}")
            return self.model.View_Virtual_Signal(self.view_list, vm_signal, self, option)
            
        def add_virtual_signal(self, vm_name, signal_name, option=None):
            signal = self.get_virtual_signal(vm_name, signal_name, option)
            self.item_list.append(signal)
            self.signal_map[signal.name] = signal
            return self

        VIRTUAL_SIGNAL_NAME_RE=re.compile(r"^\[\s*([a-zA-Z_-]+)\s*\]\s*([a-zA-Z_-]+)")
        def add_signals(self, pattern, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            match = self.VIRTUAL_SIGNAL_NAME_RE.fullmatch(pattern)
            if match:
                vm_name   = match.group(1)
                vm_signal = match.group(2)
                return self.add_virtual_signal(vm_name, vm_signal, option)
            else:
                root_tree = self.model.database.get_root_tree()
                return self.add_actual_signals(pattern, tree=root_tree, option=option)

        def get_actual_signal(self, pattern, option=None):
            signal_option = self.new_option_for_actual_signal(option, {"required": True, "unique": True})
            signal_list   = self.get_actual_signal_list(pattern, tree=None, option=signal_option)
            path = "::".join(signal_list[0][0])
            node = signal_list[0][1]
            if "handle" not in node:
                raise RuntimeError(f'The specified pattern does not match a signal: "{pattern}"')
            return self.model.View_Actual_Signal(self.view_list, path, node, self, signal_option)

        def add_display_signal(self, pattern, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            match = self.VIRTUAL_SIGNAL_NAME_RE.fullmatch(pattern)
            if match:
                vm_name   = match.group(1)
                vm_signal = match.group(2)
                self.display_signal = self.get_virtual_signal(vm_name, vm_signal, option)
            else:
                root_tree = self.model.database.get_root_tree()
                self.display_signal = self.get_actual_signal(pattern, option)
            return self
        
        def add_signal_clock(self, pattern, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            signal = self.get_actual_signal(pattern, option)
            clock  = self.model.View_Signal_Clock(signal, option)
            self.item_list.append(clock)
            self.signal_map[clock.name] = clock
            if self.view_list.clock is None:
                self.view_list.clock = clock
            elif not self.view_list.clock.is_same_wave(clock):
                raise RuntimeError("View_List already contains a clock")
            return self
            
        def add_virtual_clock(self, name, cycle_time, offset_time, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            cycle  = self.model.parse_time(cycle_time)
            offset = self.model.parse_time(offset_time)
            clock  = self.model.View_Virtual_Clock(self.view_list, name, cycle, offset, self, option)
            self.item_list.append(clock)
            self.signal_map[clock.name] = clock
            if self.view_list.clock is None:
                self.view_list.clock = clock
            elif not self.view_list.clock.is_same_wave(clock):
                raise RuntimeError("View_List already contains a clock")
            return self
            
        def add_group(self, name, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            if isinstance(option, dict) and "template" in option:
                view_template = option.pop("template")
            else:
                view_template = None
            group = self.model.View_Group(self.view_list, name, self, option)
            if view_template is not None:
                group.applay_view_template(view_template)
            self.item_list.append(group)
            self.group_map[group.name] = group
            return group

        def apply_view_template(self, view_template):
            def apply_group(group, group_template):
                for item in group_template:
                    if "group" in item:
                        group_name     = item["name"]
                        group_option   = View_Option(item.get("option"))
                        child_template = item["group"]
                        child_group    = group.add_group(group_name, group_option)
                        apply_group(child_group, child_template)
                        continue
                    if "signal" in item:
                        signal_name    = item["name"]
                        signal_option  = View_Option(item.get("option"))
                        signal_pattern = item["signal"]
                        group.add_signals(signal_pattern, signal_option)
                        continue
                    if "clock" in item:
                        clock_name     = item["name"]
                        clock_option   = View_Option(item.get("option"))
                        clock_contents = item["clock"]
                        if "signal" in clock_contents:
                            clock_pattern = clock_contents["signal"]
                            clock_option  = clock_option.merge(clock_contents.get("option"))
                            group.add_signal_clock(clock_pattern, clock_option)
                            continue
                        if "virtual" in clock_contents:
                            clock_pattern = clock_contents["virtual"]
                            cycle_time    = clock_pattern["cycle_time"]
                            offset_time   = clock_pattern.get("offset_time", "0 ns")
                            clock_option  = clock_option.merge(clock_contents.get("option"))
                            group.add_virtual_clock(clock_name, cycle_time, offset_time, clock_option)
                            continue
                    raise RuntimeError(f"Invalid view_template item: {item}")
            apply_group(self, view_template)

        def get_group(self, path):
            if not path:
                return self
            name = path.pop(0)
            if name in self.group_map:
                return self.group_map[name].get_group(path)
            return None

        def get_signal(self, path):
            if not path:
                return None
            name = path.pop(0)
            if not path:
                if name in self.signal_map:
                    return self.signal_map[name]
            else:
                if name in self.group_map:
                    return self.group_map[name].get_signal(path)
            return None
            
            
        def register_database(self):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            for item in self.item_list:
                item.register_database()
            if self.display_signal is not None:
                self.display_signal.register_database()
                
        def unregister_database(self):
            for item in self.item_list:
                item.unregister_database()
            if self.display_signal is not None:
                self.display_signal.unregister_database()
                
        def items(self):
            return self.item_list

    class View_List:
        DEFAULT_OPTION = {
            "display_rows"      : 24 ,
        }
        def __init__(self, model, name, option=None):
            self.model          = model
            self.name           = name
            self.start_time     = self.model.start_time
            self.end_time       = self.model.end_time
            self.current_time   = self.start_time
            self.option         = View_Option(self.DEFAULT_OPTION).merge(option)
            self.group_option   = self.option.select(View_Model.INHERITABLE_OPTION)
            self.root_group     = self.model.View_Group(self, "", None, self.group_option)
            self.clock          = None
            self.view_item_list = []
            self.item_row_map   = {}
            
            self.background_color = self.get_color("wave", "background", "black")

        def close(self):
            if self.root_group is None:
                return
            self.root_group.close()
            self.root_group = None
            self.clock      = None
            self.view_item_list.clear()
            self.item_row_map.clear()
                
        def register_database(self):
            if self.root_group is not None:
                self.root_group.register_database()
                
        def unregister_database(self):
            if self.root_group is not None:
                self.root_group.unregister_database()

        def add_group(self, name, option=None):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            if isinstance(option, dict) and "template" in option:
                view_template = option.pop("template")
            else:
                view_template = None
            group_option = self.group_option.merge(option)
            group = self.root_group.add_group(name, group_option)
            if view_template is not None:
                group.apply_view_template(view_template)
            return group

        def apply_view_template(self, view_template):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            self.root_group.apply_view_template(view_template)

        def add_signal_clock(self, pattern, option=None):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            clock_option = self.group_option.merge(option)
            return self.root_group.add_signal_clock(pattern, clock_option)

        def add_virtual_clock(self, name, cycle_time, offset_time, option=None):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            clock_option = self.group_option.merge(option)
            return self.root_group.add_virtual_clock(name, cycle_time, offset_time, clock_option)
        
        def rebuild(self):
            self.view_item_list.clear()
            self.item_row_map.clear()
            self._append_group_to_view_item_list(self.root_group)
            for row, item in enumerate(self.view_item_list):
                self.item_row_map[id(item)] = row

        def _append_group_to_view_item_list(self, group):
            for item in group.items():
                if self.item_is_signal(item):
                    self.view_item_list.append(item)
                    continue
                if self.item_is_group(item):
                    self.view_item_list.append(item)
                    if item.expanded:
                        self._append_group_to_view_item_list(item)
                    continue
                if self.item_is_clock(item):
                    if item.display_wave:
                        self.view_item_list.append(item)
                    continue

        def set_group_expand(self, group, expand):
            if group.view_list is not self:
                raise RuntimeError("group does not belong to this View_List")
            if not self.item_is_group(group):
                return
            group.expanded = bool(expand)
            self.rebuild()

        def expand_group(self, group):
            self.set_group_expand(group, True )

        def collapse_group(self, group):
            self.set_group_expand(group, False)
        
        def toggle_group(self, group):
            self.set_group_expand(group, not group.expanded)

        def format_time_scale(self, time_scale):
            return self.model.format_time_scale(time_scale)

        def format_timestamp(self, timestamp, time_scale=None):
            return self.model.format_timestamp(timestamp, time_scale)

        def parse_timestamp(self, value, unit=None, time_scale=None):
            return self.model.parse_timestamp(value, unit, time_scale)

        def view_items(self):
            return self.view_item_list

        def row_count(self):
            return len(self.view_item_list)
        
        def row_to_item(self, row):
            if row < 0 or row >= self.row_count():
                return None
            return self.view_item_list[row]

        def item_to_signal(self, item):
            if item is None:
                return None
            if self.item_is_signal(item):
                return item
            if self.item_is_clock(item):
                return item
            if self.item_is_group(item):
                return item.display_signal
            return None

        def get_signal_value(self, signal, time):
            if signal is None:
                return None
            wave = signal.get_wave(time, time)
            try:
                return next(wave)[1]
            except StopIteration:
                return None

        def get_signal_next_edge_time(self, signal, curr_time, end_time):
            if signal is None:
                return None
            curr_value = self.get_signal_value(signal, curr_time)
            for next_time, next_value in signal.get_wave(curr_time, end_time):
                if next_time > curr_time and next_value != curr_value:
                    return next_time
            return end_time

        def get_signal_prev_edge_time(self, signal, curr_time, start_time):
            if signal is None:
                return None
            curr_value = self.get_signal_value(signal, curr_time)
            prev_time  = curr_time
            for time, prev_value in signal.get_reversed_wave(start_time, curr_time):
                if prev_time < curr_time and prev_value != curr_value:
                    return prev_time
                prev_time = time
            return start_time
        
        def item_to_row(self, item):
            return self.item_row_map.get(id(item))

        def item_is_contains(self, item):
            return id(item) in self.item_row_map

        def item_is_group(self, item):
            return isinstance(item, self.model.View_Group)

        def item_is_signal(self, item):
            return isinstance(item, self.model.View_Signal)
        
        def item_is_clock(self, item):
            return isinstance(item, self.model.View_Clock)
        
        def row_is_group(self, row):
            item = self.row_to_item(row)
            return item is not None and self.item_is_group(item)
        
        def row_is_signal(self, row):
            item = self.row_to_item(row)
            return item is not None and self.item_is_signal(item)
        
        def row_to_parent_group(self, row):
            item = self.row_to_item(row)
            if item is None:
                return None
            return item.parent_group

        def get_option(self, key, default_value=None):
            return self.option.get(key, default_value)
        
        def get_color(self, key, prop=None, default_value=None):
            color = self.get_option("color", {})
            return color.get(key,{}).get(prop, default_value)

    DEFAULT_OPTION = {
        "header_height"      : 24    ,
        "footer_height"      : 24    ,
        "signal_height"      : 24    ,
        "signal_name_width"  : 200   ,
        "signal_value_width" : 200   ,
        "display_rows"       : 24    ,
        "start_time"         : None  ,
        "end_time"           : None  ,
        "time_quantum"       : "1 ns",
        "shape"              : {
            "draw_line_width"      : 1 ,
            "edge_slope_width"     : 3 ,
            "margin_top_height"    : 5 ,
            "margin_bottom_height" : 5 ,
        },
        "color"              : {
            "cursor"    : "yellow",
            "marker"    : "red"   ,
            "header"    : {"background": "black", "foreground"   : "white"},
            "time_ruler": {"background": "black",
                           "line"      : "gray" ,
                           "text"      : "white"},
            "name"      : {"background": "black", "foreground"   : "white"},
            "value"     : {"background": "black", "foreground"   : "white"},
            "wave"      : {"background": "black",
                           "signal"    : "#00ff00",
                           "value"     : "white"  ,
                           "group"     : None     ,
                           "text"      : None     },
        },
        "signal"             : {
            "struct_as_group"  : True ,
            "required"         : False,
            "unique"           : False,
        },
    }
    INHERITABLE_OPTION = {"color"       : {"name": True, "value": True, "wave": True},
                          "shape"       : True,
                          "signal"      : True
                         }
    VIEW_LIST_OPTION   = {"color"       : {"name": True, "value": True, "wave": True},
                          "shape"       : True,
                          "signal"      : True,
                          "display_rows": True,
                         }
    def __init__(self, database, option=None):
        self.database       = database
        self.option         = View_Option(self.DEFAULT_OPTION).merge(option)
        self.view_option    = self.option.select(View_Model.VIEW_LIST_OPTION)
        self.database.build_tree()
        self.start_time     = self.parse_time(self.option["start_time"  ])
        self.end_time       = self.parse_time(self.option["end_time"    ])
        self.time_quantum   = self.parse_time(self.option["time_quantum"])
        if self.start_time is None or self.start_time < self.database.total_start_time:
            self.start_time = self.database.total_start_time
        if self.end_time   is None or self.end_time   > self.database.total_end_time  :
            self.end_time   = self.database.total_end_time
        self.current_time   = self.start_time
        self.view_list_list = []
        self.curr_view_list = self.add_view_list("top")
        self.virtual_models = {}
        self.closed         = False

    def set_start_time(self, start_time):
        self.start_time = start_time
        if self.start_time is None or self.start_time < self.database.total_start_time:
            self.start_time = self.database.total_start_time
        
    def set_end_time(self, end_time):
        self.end_time = end_time
        if self.end_time   is None or self.end_time   > self.database.total_end_time  :
            self.end_time   = self.database.total_end_time
        
    def parse_time(self, text):
        if text is None:
            return None
        text = text.strip()
        # 数値 + 単位
        m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Zµ]+)", text)
        if m:
            value = float(m.group(1))
            unit  = m.group(2)
            return self.database.parse_timestamp(value, unit)
        # 数値のみ
        m = re.fullmatch(r"[0-9]+", text)
        if m:
            return self.database.parse_timestamp(int(text))

        raise ValueError(f"Invalid time format: {text}")

    def add_view_list(self, name, option=None):
        new_option  = self.view_option.merge(option)
        view_list   = self.View_List(self, name, new_option)
        self.view_list_list.append(view_list)
        return view_list

    def view_lists(self):
        return self.view_list_list

    def add_virtual_module(self, vm_name):
        virtual_module = Virtual_Module(vm_name, self.database)
        self.virtual_models[vm_name] = virtual_module
        return virtual_module

    def get_output_signal_from_virtual_module(self, vm_name, signal_name):
        if vm_name in self.virtual_models:
            virtual_module = self.virtual_models[vm_name]
            for output_signal  in virtual_module.output_signal_list:
                if output_signal.name == signal_name:
                    return output_signal
        return None

    def refresh(self):
        self.rebuild()
        
    def rebuild(self):
        for view_list in self.view_list_list:
            view_list.rebuild()

    def close(self):
        for virtual_model in self.virtual_models.values():
            virtual_model.close()
        for view_list in self.view_list_list:
            view_list.close()
        self.database.close()
        self.view_list_list.clear()
        self.curr_view_list = None
        self.closed         = True

    def load_wave(self, start_time=None, end_time=None):
        if start_time is None:
            start_time = self.start_time

        if end_time is None:
            end_time   = self.end_time

        for view_list in self.view_list_list:
            view_list.register_database()
        
        for virtual_model in self.virtual_models.values():
            virtual_model.register_database()

        self.database.load_wave_signals(start_time, end_time)

        for virtual_model in self.virtual_models.values():
            virtual_model.generate_wave(start_time, end_time)

    def format_time_scale(self, time_scale):
        return self.database.format_time_scale(time_scale)

    def format_timestamp(self, timestamp, time_scale=None):
        return self.database.format_timestamp(timestamp, time_scale)

    def parse_timestamp(self, value, unit=None, time_scale=None):
        return self.database.parse_timestamp(value, unit, time_scale)

    def add_group(self, name, option=None):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.add_group(name, option)

    def apply_view_template(self, view_template):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.apply_view_template(view_template)

    def add_signal_clock(self, pattern, option=None):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.add_signal_clock(pattern, option)

    def add_virtual_clock(self, name, cycle_time, offset_time, option=None):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.add_virtual_clock(name, cycle_time, offset_time, option)

    def set_group_expand(self, group, expand):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.set_group_expand(group, expand)

    def expand_group(self, group):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.expand_group(group)

    def collapse_group(self, group):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.collapse_group(group)
        
    def toggle_group(self, group):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.toggle_group(group)

    def view_items(self):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.view_items()

    def row_count(self):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.row_count()
        
    def row_to_item(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.row_to_item(row)

    def item_to_row(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_to_row(item)

    def item_is_contains(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_is_contains(item)

    def item_is_group(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_is_group(item)

    def item_is_signal(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_is_signal(item)
        
    def row_is_group(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        item = self.row_to_item(row)
        return item is not None and self.item_is_group(item)
        
    def row_is_signal(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        item = self.row_to_item(row)
        return item is not None and self.item_is_signal(item)
        
    def row_to_parent_group(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        item = self.row_to_item(row)
        if item is None:
            return None
        return item.parent_group

    def get_option(self, key, default_value=None):
        return self.option.get(key, default_value)

    def get_color(self, key, prop=None, default_value=None):
        color = self.get_option("color", {})
        if prop is None:
            return color.get(key, default_value)
        return color.get(key,{}).get(prop, default_value)
