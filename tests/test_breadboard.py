"""python3 -m unittest discover tests"""
import copy, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "wiring-guide"
SCRIPT = SKILL / "breadboard.py"
sys.path.insert(0, str(SKILL))
sys.dont_write_bytecode = True
import breadboard as bb  # noqa: E402

BOARD = {"rows": 30, "row1": "left", "near": "a", "rails": "both", "outer": "-"}
UNO = {"id": "uno", "kind": "offboard", "model": "uno-r3", "label": "Uno", "side": "far", "usb": "left", "headers": [
    {"name": "lower", "at": 2, "pins": ["", "IOREF", "RESET", "3.3V", "5V", "GND", "GND", "VIN"]},
    {"name": "upper", "at": 1, "pins": ["SCL", "SDA", "AREF", "GND", "D13", "D12", "D11", "D10", "D9", "D8", None, "D7", "D6", "D5", "D4", "D3", "D2", "D1", "D0"]}]}
PICO = {"id": "pico", "model": "pico", "label": "Pico", "usb": "left", "span": [1, 20], "pins": {
    "c": ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6", "GP7", "GP8", "GP9", "GND", "GP10", "GP11", "GP12", "GP13", "GND", "GP14", "GP15"],
    "h": ["VBUS", "VSYS", "GND", "3V3_EN", "3V3", "ADC_VREF", "GP28", "AGND", "GP27", "GP26", "RUN", "GP22", "GND", "GP21", "GP20", "GP19", "GP18", "GND", "GP17", "GP16"]}}
R = {"id": "R1", "kind": "resistor", "value": "220"}
LED = {"id": "LED1", "kind": "led", "color": "red"}
SW = {"id": "SW1", "kind": "switch"}
SONAR = {"id": "M1", "kind": "module", "names": ["VCC", "TRIG", "ECHO", "GND"], "vcc": [4.5, 5.5]}
OLED = {"id": "M1", "kind": "module", "names": ["GND", "VCC", "SCL", "SDA"], "vcc": [3.0, 3.6]}


def spec(boards=(UNO,), parts=(), connect=(), **kw):
    return copy.deepcopy({"title": "t", "board": BOARD, "boards": list(boards), "parts": list(parts), "connect": list(connect), **kw})


def led_circuit(value="220", pin="uno.D13", board=UNO):
    return spec([board], [{**R, "value": value}, LED], [["-", f"{board['id']}.GND", "LED1.-"], [pin, "R1.1"], ["R1.2", "LED1.+"]])


class Cli(unittest.TestCase):
    def run_spec(self, s):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "s.json"), Path(d, "o.html")
            src.write_text(json.dumps(s))
            r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(src), str(out)], capture_output=True, text=True)
            self.assertNotIn("Traceback", r.stderr)
            return r.returncode, r.stdout, out.read_text() if out.exists() else None

    def assertStops(self, s, pattern):
        code, text, page = self.run_spec(s)
        self.assertEqual(code, 1, text)
        self.assertIsNone(page, "a page was written")
        self.assertRegex(text, "ERROR: .*" + pattern)

    def assertWarnsOnly(self, s, pattern):
        code, text, page = self.run_spec(s)
        self.assertEqual(code, 0, text)
        self.assertIsNotNone(page)
        self.assertRegex(text, "warning: .*" + pattern)


class Normal(Cli):
    def test_led_circuit_makes_a_page_with_its_current(self):
        code, text, page = self.run_spec(led_circuit())
        self.assertEqual(code, 0, text)
        self.assertIn("LED1: about 14.5 mA", text)
        self.assertIn("limit 30 mA assumed", text)
        self.assertNotIn("warning:", text)
        self.assertIn("prefers-color-scheme: dark", page)
        self.assertIn('data-step="1"', page)

    def test_every_run_states_what_was_not_checked(self):
        self.assertIn("not checked by this script:", self.run_spec(led_circuit())[1])

    def test_example_spec_is_clean(self):
        code, text, _ = self.run_spec(json.loads((SKILL / "spec.example.json").read_text()))
        self.assertEqual(code, 0, text)
        self.assertNotIn("warning:", text)


class Led(Cli):
    def test_no_resistor_stops(self):
        s = spec([UNO], [LED], [["-", "uno.GND", "LED1.-"], ["uno.D13", "LED1.+"]])
        self.assertStops(s, "LED1 has no resistor")

    def test_no_resistor_on_a_supply_stops(self):
        s = spec([UNO], [LED], [["-", "uno.GND", "LED1.-"], ["+", "uno.5V", "LED1.+"]])
        self.assertStops(s, "LED1 has no resistor")

    def test_no_resistor_with_only_a_button_stops(self):
        s = spec([UNO], [LED, SW], [["-", "uno.GND", "LED1.-"], ["uno.5V", "SW1.1"], ["SW1.2", "LED1.+"]])
        self.assertStops(s, "LED1 has no resistor")

    def test_resistor_on_the_cathode_side_counts(self):
        s = spec([UNO], [R, LED], [["-", "uno.GND", "R1.2"], ["R1.1", "LED1.-"], ["uno.D13", "LED1.+"]])
        code, text, _ = self.run_spec(s)
        self.assertEqual(code, 0, text)
        self.assertIn("LED1: about 14.5 mA", text)

    def test_too_small_a_resistor_stops(self):
        self.assertStops(led_circuit("47"), "LED1: about 68 mA")

    def test_over_the_working_level_only_warns(self):
        self.assertWarnsOnly(led_circuit("120"), "uno.D13: 26.7 mA")

    def test_pico_pin_limit_is_lower(self):
        self.assertWarnsOnly(led_circuit("330", "pico.GP15", PICO), "pico.GP15: 4.5 mA .* 4 mA")
        self.assertStops(led_circuit("100", "pico.GP15", PICO), "pico.GP15: 15.0 mA .* 12 mA")

    def test_two_leds_add_up_on_one_pin(self):
        s = spec([UNO], [{**R, "value": "150"}, {**R, "id": "R2", "value": "150"}, LED, {**LED, "id": "LED2"}],
                 [["-", "uno.GND", "LED1.-", "LED2.-"], ["uno.D13", "R1.1", "R2.1"], ["R1.2", "LED1.+"], ["R2.2", "LED2.+"]])
        self.assertStops(s, r"uno.D13: 42.7 mA")

    def test_backwards_stops(self):
        s = spec([UNO], [R, LED], [["-", "uno.GND", "LED1.+"], ["uno.D13", "R1.1"], ["R1.2", "LED1.-"]])
        self.assertStops(s, "LED1 is backwards")


class Voltage(Cli):
    def test_5v_module_output_on_a_3v3_pin_stops(self):
        s = spec([PICO], [{**SONAR, "out_v": {"ECHO": 5}}],
                 [["pico.VBUS", "M1.VCC"], ["pico.GND", "M1.GND"], ["pico.GP2", "M1.TRIG"], ["pico.GP3", "M1.ECHO"]])
        self.assertStops(s, "M1.ECHO outputs 5 V into pico.GP3")

    def test_module_output_level_unknown_warns(self):
        s = spec([PICO], [SONAR], [["pico.VBUS", "M1.VCC"], ["pico.GND", "M1.GND"], ["pico.GP2", "M1.TRIG"], ["pico.GP3", "M1.ECHO"]])
        self.assertWarnsOnly(s, "M1.ECHO is powered at 5 V .* pico.GP3")

    def test_divider_is_not_called_an_overvoltage(self):
        parts = [{**SONAR, "out_v": {"ECHO": 5}}, {**R, "value": "1k"}, {**R, "id": "R2", "value": "2k"}]
        s = spec([PICO], parts, [["pico.VBUS", "M1.VCC"], ["-", "pico.GND", "M1.GND", "R2.2"], ["pico.GP2", "M1.TRIG"],
                                 ["M1.ECHO", "R1.1"], ["R1.2", "R2.1", "pico.GP3"]])
        code, text, page = self.run_spec(s)
        self.assertEqual(code, 0, text)
        self.assertIsNotNone(page)

    def test_5v_supply_straight_on_a_3v3_pin_stops(self):
        self.assertStops(spec([PICO], [], [["pico.VBUS", "pico.GP2"]]), "pico.GP2 is a 3.3 V pin")

    def test_button_to_5v_on_a_3v3_pin_stops(self):
        s = spec([PICO], [SW], [["pico.VBUS", "SW1.1"], ["pico.GP2", "SW1.2"]])
        self.assertStops(s, "SW1: pressing it puts 5 V on pico.GP2")

    def test_two_boards_at_different_levels_stop(self):
        s = spec([UNO, {**PICO, "span": [8, 27]}], [], [["uno.D13", "pico.GP2"]])
        self.assertStops(s, "pico.GP2 is a 3.3 V pin")

    def test_5v_pin_into_a_3v3_module_stops(self):
        s = spec([UNO], [OLED], [["uno.3.3V", "M1.VCC"], ["uno.GND", "M1.GND"], ["uno.SCL", "M1.SCL"], ["uno.SDA", "M1.SDA"]])
        self.assertStops(s, "uno.SCL drives M1.SCL at 5 V")

    def test_module_on_too_high_a_supply_stops(self):
        s = spec([UNO], [OLED], [["uno.5V", "M1.VCC"], ["uno.GND", "M1.GND"]])
        self.assertStops(s, "M1.VCC gets 5 V, over its 3.6 V maximum")

    def test_module_powered_backwards_stops(self):
        s = spec([UNO], [SONAR], [["uno.GND", "M1.VCC"], ["uno.5V", "M1.GND"]])
        self.assertStops(s, "powered backwards")

    def test_module_without_a_supply_range_stops(self):
        m = {k: v for k, v in SONAR.items() if k != "vcc"}
        self.assertStops(spec([UNO], [m], [["uno.5V", "M1.VCC"], ["uno.GND", "M1.GND"]]), "supply range is not given")

    def test_pull_up_above_a_pin_level_warns(self):
        s = spec([PICO], [{**R, "value": "4.7k"}], [["pico.VBUS", "R1.1"], ["R1.2", "pico.GP2"]])
        self.assertWarnsOnly(s, "R1 pulls pico.GP2.* up to 5 V")

    def test_flash_pin_stops_and_strapping_pin_warns(self):
        esp = {"id": "esp", "kind": "offboard", "model": "esp32-devkitc", "label": "ESP32", "side": "far", "usb": "left",
               "headers": [{"name": "J3", "at": 1, "pins": ["CLK", "D0", "D1", "IO15", "IO2", "IO0", "IO4", "IO16", "IO17", "IO5", "IO18", "IO19", "GND"]}]}
        self.assertStops(led_circuit("330", "esp.D0", esp), "esp.D0: do not use it")
        self.assertWarnsOnly(led_circuit("330", "esp.IO2", esp), "esp.IO2: strapping pin")


class GapsFoundInReview(Cli):
    def wired(self, legs, **kw):
        return {"title": "t", "board": BOARD, "boards": [UNO], "parts": [{"id": "LED1", "kind": "led", "legs": legs, **kw}],
                "wires": [{"n": 1, "from": "uno.D13", "to": "14g"}, {"n": 2, "from": "uno.GND", "to": "N-3"}]}

    def test_named_legs_get_the_led_checks(self):
        self.assertStops(self.wired([["+", "14f"], ["-", "N-14"]]), "LED1 has no resistor")

    def test_named_legs_in_the_other_order_are_still_read_by_name(self):
        self.assertStops(self.wired([["-", "N-14"], ["+", "14f"]]), "LED1 has no resistor")

    def test_named_legs_backwards_stop(self):
        self.assertStops(self.wired([["-", "14f"], ["+", "N-14"]]), "LED1 is backwards")

    def test_other_supply_names_need_a_range(self):
        for name in ("V", "VS", "VBAT", "AVCC", "+5V", "3.3V"):
            m = {"id": "M1", "kind": "module", "names": [name, "GND", "S"]}
            self.assertStops(spec([UNO], [m], [["uno.5V", f"M1.{name}"], ["uno.GND", "M1.GND"]]), "supply range is not given")

    def test_unknown_supply_name_stops_a_module_until_it_is_named(self):
        m = {"id": "M1", "kind": "module", "names": ["PW", "GND"]}
        c = [["uno.5V", "M1.PW"], ["uno.GND", "M1.GND"]]
        self.assertStops(spec([UNO], [m], c), "no leg is recognised as its supply")
        self.assertStops(spec([UNO], [{**m, "supply": ["PW"], "vcc": [3, 3.6]}], c), "M1.PW gets 5 V")

    def test_chip_ground_named_vss_on_a_supply_stops(self):
        chip = {"id": "U1", "kind": "dip", "pins": 4, "names": ["VDD", "A", "B", "VSS"], "vcc": [3, 5.5]}
        self.assertStops(spec([UNO], [chip], [["uno.GND", "U1.VDD"], ["uno.5V", "U1.VSS"]]), "powered backwards")

    def test_board_ground_and_supply_under_other_labels(self):
        b = {**{k: v for k, v in UNO.items() if k != "model"}, "logic_v": 5, "power": {"VCC": 5},
             "headers": [{"name": "h", "at": 1, "pins": ["VCC", "G", "V5", "D2"]}]}
        self.assertStops(spec([b], [], [["uno.VCC", "uno.G"]]), "shorted together")
        self.assertStops(spec([{**b, "power": {}}], [], [["uno.VCC", "uno.D2"]]), "looks like a supply pin")

    def test_switches_in_series_across_the_supply_stop(self):
        s = spec([UNO], [SW, {**SW, "id": "SW2"}], [["uno.5V", "SW1.1"], ["SW1.2", "SW2.1"], ["SW2.2", "uno.GND"]])
        self.assertStops(s, "SW1, SW2: pressing them all joins 0 V and 5 V")

    def test_three_switches_chained_from_either_end_stop(self):
        s = spec([PICO], [SW, {**SW, "id": "SW2"}, {**SW, "id": "SW3"}],
                 [["pico.VBUS", "SW1.1"], ["SW2.2", "SW3.1"], ["SW1.2", "SW2.1"], ["SW3.2", "pico.GP2"]])
        self.assertStops(s, "pressing them all puts 5 V on pico.GP2")

    def test_two_separate_buttons_are_not_a_short(self):
        s = spec([UNO], [SW, {**SW, "id": "SW2"}], [["uno.D2", "SW1.1"], ["SW1.2", "uno.GND"], ["uno.D3", "SW2.1"], ["SW2.2", "uno.GND#2"]])
        self.assertEqual(self.run_spec(s)[0], 0)

    def test_5v_through_an_led_into_a_3v3_pin_stops(self):
        s = spec([PICO], [{**R, "value": "1k"}, LED], [["pico.VBUS", "R1.1"], ["R1.2", "LED1.+"], ["LED1.-", "pico.GP2"]])
        self.assertStops(s, "LED1 joins 5 V to pico.GP2")

    def test_active_low_led_on_its_own_level_is_fine(self):
        s = spec([PICO], [{**R, "value": "1k"}, LED], [["pico.3V3", "R1.1"], ["R1.2", "LED1.+"], ["LED1.-", "pico.GP2"]])
        self.assertEqual(self.run_spec(s)[0], 0)


class BoardAndFixes(Cli):
    def test_bad_board_values_stop(self):
        for key, value in (("near", "A"), ("row1", "top"), ("rails", "yes"), ("outer", "x")):
            s = led_circuit()
            s["board"][key] = value
            self.assertStops(s, f'board: {key} "{value}"')

    def built(self, wires, **kw):
        return {"title": "t", "as_built": True, "board": BOARD, "boards": [UNO], "parts": [], "wires": wires, **kw}

    def test_dashed_fix_is_not_counted_as_connected(self):
        code, text, page = self.run_spec(self.built([
            {"n": 1, "from": "uno.5V", "to": "F+3"}, {"n": 2, "from": "uno.GND", "to": "F+9", "dashed": True}]))
        self.assertEqual(code, 0, text)
        self.assertNotIn("Do not power this up", page)

    def test_real_fault_is_still_found_beside_a_dashed_fix(self):
        code, text, page = self.run_spec(self.built([
            {"n": 1, "from": "uno.5V", "to": "F+3"}, {"n": 2, "from": "uno.GND", "to": "F+9"}, {"n": 3, "from": "uno.GND#2", "to": "F-9", "dashed": True}]))
        self.assertEqual(code, 1)
        self.assertRegex(text, "ERROR: .*shorted together")
        self.assertIn("Do not power this up", page)

    def test_dashed_wire_needs_as_built(self):
        s = self.built([{"n": 1, "from": "uno.5V", "to": "F+3", "dashed": True}])
        del s["as_built"]
        self.assertStops(s, "a dashed fix belongs")

    def test_other_error_does_not_hide_a_shorted_part(self):
        s = {"title": "t", "board": BOARD, "boards": [UNO], "parts": [{**R, "legs": ["14f", "20g"]}],
             "wires": [{"n": 1, "from": "14h", "to": "20h"}]}
        code, text, _ = self.run_spec(s)
        self.assertRegex(text, "ERROR: R1: legs 14f and 20g are on a slant")
        self.assertRegex(text, "ERROR: R1: both legs are on one net")


class Shorts(Cli):
    def test_supply_to_gnd_stops(self):
        self.assertStops(spec([UNO], [], [["uno.5V", "uno.GND"]]), "shorted together")

    def test_same_short_through_the_rails_stops(self):
        self.assertStops(spec([UNO], [], [["+", "uno.5V", "uno.GND"]]), "shorted together")

    def test_mixed_supplies_stop(self):
        self.assertStops(spec([UNO], [], [["+", "uno.5V", "uno.3.3V"]]), "3.3 V and 5 V shorted together")

    def test_supply_on_the_minus_rail_stops(self):
        self.assertStops(spec([UNO], [], [["-", "uno.5V"]]), "the − rail has 5 V")

    def test_button_across_the_supply_stops(self):
        self.assertStops(spec([UNO], [SW], [["uno.5V", "SW1.1"], ["uno.GND", "SW1.2"]]), "SW1: pressing it joins 0 V and 5 V")

    def test_pot_wiper_on_a_supply_stops(self):
        pot = {"id": "P1", "kind": "pot"}
        self.assertStops(spec([UNO], [pot], [["uno.5V", "P1.W"], ["uno.GND", "P1.1"], ["uno.D9", "P1.2"]]), "wiper")

    def test_backwards_electrolytic_stops(self):
        s = spec([UNO], [{"id": "C1", "kind": "cap", "polar": True}], [["uno.GND", "C1.+"], ["uno.5V", "C1.-"]])
        self.assertStops(s, "C1 is backwards")

    def test_pin_tied_to_a_supply_warns(self):
        self.assertWarnsOnly(spec([UNO], [], [["uno.D9", "uno.GND"]]), "uno.D9 is tied straight to 0 V")


class Placement(Cli):
    hand = {"title": "t", "board": BOARD, "boards": [UNO],
            "parts": [{**R, "legs": ["14f", "14g"]}, {**LED, "legs": ["20f", "N-20"]}],
            "wires": [{"n": 1, "from": "uno.D13", "to": "14h", "color": "green"},
                      {"n": 2, "from": "uno.GND", "to": "N-3", "color": "black"},
                      {"n": 3, "from": "14i", "to": "20g", "color": "blue"}]}

    def test_both_legs_in_one_strip_stops(self):
        self.assertStops(copy.deepcopy(self.hand), "R1: both legs are in the same strip")

    def test_as_built_keeps_the_page_and_says_not_to_power_it(self):
        code, text, page = self.run_spec({**copy.deepcopy(self.hand), "as_built": True})
        self.assertEqual(code, 1)
        self.assertRegex(text, "ERROR: R1: both legs")
        self.assertIn("Do not power this up", page)

    def test_clean_as_built_has_no_banner(self):
        s = copy.deepcopy(self.hand)
        s["as_built"] = True
        s["parts"] = [{**R, "legs": ["14h", "20h"]}, {**LED, "legs": ["25f", "N-25"]}]
        s["wires"][0]["to"] = "14i"
        s["wires"][2].update({"from": "20j", "to": "25g"})
        code, text, page = self.run_spec(s)
        self.assertEqual(code, 0, text)
        self.assertNotIn("Do not power this up", page)

    def test_both_legs_on_one_net_stop(self):
        self.assertStops(spec([UNO], [R], [["uno.D13", "R1.1", "R1.2"]]), "R1: both legs are on one net")

    def test_hole_off_the_board_stops_even_as_built(self):
        s = copy.deepcopy(self.hand)
        s["as_built"] = True
        s["parts"][0]["legs"] = ["14f", "99f"]
        self.assertStops(s, "hole 99f does not exist")


class BadRefs(Cli):
    def test_missing_pin_stops(self):
        self.assertStops(led_circuit(pin="uno.D99"), "uno.D99: uno has no such pin")

    def test_missing_pin_on_a_plugged_in_board_is_not_dropped(self):
        self.assertStops(led_circuit("330", "pico.GP99", PICO), "pico.GP99: pico has no such pin")

    def test_missing_nth_pin_stops(self):
        self.assertStops(spec([UNO], [R], [["uno.GND#9", "R1.1"]]), "uno.GND#9")

    def test_missing_leg_is_not_dropped(self):
        self.assertStops(spec([UNO], [R], [["uno.D13", "R1.7"]]), "R1.7: R1 has legs 1, 2")

    def test_unknown_id_stops(self):
        self.assertStops(spec([UNO], [R], [["nano.D13", "R1.1"]]), "nothing has the id nano")

    def test_unreadable_resistor_value_stops(self):
        self.assertStops(led_circuit("4k7"), "cannot read resistor value")

    def test_malformed_spec_stops_without_a_traceback(self):
        self.assertStops({"title": "t"}, "give rows")
        self.assertStops({"board": BOARD, "parts": [{"id": "R1", "kind": "resistor", "legs": ["1a"]}]}, "malformed")


class Boards(Cli):
    def test_unknown_model_stops(self):
        self.assertStops(led_circuit(board={**UNO, "model": "teensy41"}), 'model "teensy41" is not supported')

    def test_no_model_stops(self):
        b = {k: v for k, v in UNO.items() if k != "model"}
        self.assertStops(led_circuit(board=b), 'model "None" is not supported')

    def test_unknown_kind_stops(self):
        self.assertStops(led_circuit(board={**UNO, "kind": "shield"}), 'kind "shield" is not supported')

    def test_unknown_part_kind_stops(self):
        self.assertStops(spec([UNO], [{"id": "Q1", "kind": "transistor"}], []), 'kind "transistor" is not supported')

    def test_other_board_works_once_its_facts_are_given(self):
        b = {k: v for k, v in UNO.items() if k != "model"}
        b.update(model="teensy41", logic_v=3.3, power={"5V": 5, "3.3V": 3.3})
        code, text, _ = self.run_spec(led_circuit("470", board=b))
        self.assertEqual(code, 0, text)
        self.assertRegex(text, "warning: uno.D13: its current limit is not given")
        self.assertStops({**led_circuit("470", board=b), "connect": [["uno.5V", "uno.D13"]]}, "uno.D13 is a 3.3 V pin")


def build(s):
    for lst in (bb.errors, bb.warnings, bb.fatal, bb.checks):
        lst.clear()
    bb.validate(s)
    page = bb.Page(bb.plan(s))
    out, _ = page.render((SKILL / "template.html").read_text())
    assert not bb.errors, bb.errors
    return page, out


class Drawn(unittest.TestCase):
    """Read the holes back out of the SVG, then rebuild the nets from a breadboard's own wiring rules."""

    def drawn_nets(self, page, html):
        b = page.b
        where = {}
        for n in range(1, b.rows + 1):
            for letter, y in b.ly.items():
                where[(b.x(n), y)] = ("strip", n, "far" if letter in "fghij" and b.near == "a" else "near")
            for (side, pos), y in b.ry.items():
                where[(b.x(n), y)] = ("rail", side, b.sign[pos])
        for d in page.boards.values():
            if d.get("kind") == "offboard":
                for sk in d["sockets"]:
                    where[tuple(d["xy"](sk))] = ("pin", d["id"], sk[0])
        for d in page.boards.values():
            if d.get("kind") != "offboard":
                for letter, names in d["pins"].items():
                    for i, nm in enumerate(names):
                        hole = (b.x(d["span"][0] + i), b.ly[letter])
                        self.pin_holes[(d["id"], nm)] = self.pin_holes.get((d["id"], nm), []) + [where[hole]]

        parent = {}

        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                a = parent[a]
            return a

        def at(x, y):
            return where[(float(x), float(y))]

        ends = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="4.2"', html)
        self.assertEqual(len(ends) % 2, 0)
        for (x1, y1), (x2, y2) in zip(ends[::2], ends[1::2]):
            parent[find(at(x1, y1))] = find(at(x2, y2))
        return find, at

    def check(self, s):
        self.pin_holes = {}
        wanted = copy.deepcopy(s["connect"])
        page, html = build(s)
        find, at = self.drawn_nets(page, html)
        lines = iter(re.findall(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)" stroke="#9aa1a8" stroke-width="2.2"/>', html))
        dots = iter(re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="3.5" fill="var\(--chip\)"/>', html))
        legs = {}
        for p in s["parts"]:
            names = bb.leg_names(p)
            if p["kind"] in bb.TWO_LEG:
                x1, y1, x2, y2 = next(lines)
                legs[f'{p["id"]}.{names[0]}'], legs[f'{p["id"]}.{names[1]}'] = at(x1, y1), at(x2, y2)
            elif p["kind"] == "switch":
                pts = [next(dots) for _ in range(4)]
                legs[f'{p["id"]}.1'], legs[f'{p["id"]}.2'] = at(*pts[0]), at(*pts[2])
                self.assertEqual(at(*pts[0]), at(*pts[1]), "the joined pair is in one strip")
                self.assertEqual(at(*pts[2]), at(*pts[3]))
            else:
                for nm in names:
                    legs[f'{p["id"]}.{nm}'] = at(*next(dots))

        def node(e):
            if e in ("+", "-", "GND"):
                return None
            if e in legs:
                return legs[e]
            bid, pin = e.split(".", 1)
            want, _, nth = pin.partition("#")
            if (bid, want) in self.pin_holes:
                return self.pin_holes[(bid, want)][int(nth or 1) - 1]
            return ("pin", bid, want)

        groups = []
        for g in wanted:
            roots = {find(node(e)) for e in g if node(e) is not None}
            self.assertEqual(len(roots), 1, f"{g} is not one net in the drawing: {roots}")
            groups.append(roots.pop())
        self.assertEqual(len(set(groups)), len(groups), f"two separate groups are joined in the drawing: {wanted}")
        return html

    def test_uno_led_and_button(self):
        self.check(json.loads((SKILL / "spec.example.json").read_text()))

    def test_pico_in_the_breadboard_with_a_second_gnd(self):
        self.check(spec([PICO], [{**R, "value": "1k"}, LED, SW],
                        [["-", "pico.GND#2", "LED1.-", "SW1.2"], ["pico.GP15", "R1.1"], ["R1.2", "LED1.+"], ["pico.GP16", "SW1.1"]],
                        board={**BOARD, "rows": 30}))

    def test_module_and_several_leds(self):
        self.check(spec([UNO], [SONAR, R, {**R, "id": "R2"}, LED, {**LED, "id": "LED2", "color": "green"}],
                        [["-", "uno.GND", "M1.GND", "LED1.-", "LED2.-"], ["+", "uno.5V", "M1.VCC"], ["uno.D9", "M1.TRIG"], ["uno.D8", "M1.ECHO"],
                         ["uno.D13", "R1.1"], ["R1.2", "LED1.+"], ["uno.D12", "R2.1"], ["R2.2", "LED2.+"]]))

    def test_this_check_notices_a_wire_drawn_one_hole_off(self):
        s = json.loads((SKILL / "spec.example.json").read_text())
        self.pin_holes = {}
        real = bb.Page.add_wire

        def shifted(page, d):                                   # the page draws what the spec does not say
            if "uno.D13" in (d["from"], d["to"]):
                end = "from" if d["to"] == "uno.D13" else "to"
                d = {**d, end: re.sub(r"\d+", lambda m: str(int(m[0]) + 1), d[end], count=1)}
            real(page, d)
        bb.Page.add_wire = shifted
        try:
            with self.assertRaises((AssertionError, KeyError, StopIteration)):
                self.check(s)
        finally:
            bb.Page.add_wire = real


class Readable(unittest.TestCase):
    """The parts of 'easy to read' a script can measure. Layout still needs a person or a judge: see evals/."""

    specs = [json.loads((SKILL / "spec.example.json").read_text()), spec([PICO], [{**R, "value": "1k"}, LED, SW],
             [["-", "pico.GND", "LED1.-", "SW1.2"], ["pico.GP15", "R1.1"], ["R1.2", "LED1.+"], ["pico.GP16", "SW1.1"]])]

    def test_no_text_under_12px(self):
        for s in self.specs:
            sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", build(copy.deepcopy(s))[1].split('<div class="wrap">')[1])]
            self.assertTrue(all(x >= 12 for x in sizes), sizes)

    def test_wire_badges_do_not_overlap(self):
        for s in self.specs:
            html = build(copy.deepcopy(s))[1]
            boxes = [(float(x), float(y)) for x, y in re.findall(r'<rect x="([\d.-]+)" y="([\d.-]+)" width="20" height="16" rx="8"', html)]
            self.assertGreater(len(boxes), 0)
            for i, a in enumerate(boxes):
                for c in boxes[i + 1:]:
                    self.assertFalse(abs(a[0] - c[0]) < 20 and abs(a[1] - c[1]) < 16, (a, c))

    def test_each_step_has_its_list_item_drawing_and_table_row(self):
        for s in self.specs:
            html = build(copy.deepcopy(s))[1]
            body = html.split('<div class="wrap">')[1]
            steps = {int(n) for n in re.findall(r'<li data-step="(\d+)"', body)}
            self.assertEqual(steps, set(range(1, len(steps) + 1)))
            self.assertEqual({int(n) for n in re.findall(r'<g data-step="(\d+)"', body)} - steps, set())
            self.assertEqual({int(n) for n in re.findall(r'<tr data-step="(\d+)"', body)}, steps)

    def test_both_themes_and_the_stepper_are_kept(self):
        html = build(copy.deepcopy(self.specs[0]))[1]
        for token in ("prefers-color-scheme: dark", "--w-blk", "const UI ="):
            self.assertIn(token, html)


class Index(unittest.TestCase):
    def test_progress_example_renders(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d, "i.html")
            r = subprocess.run([sys.executable, "-B", str(SKILL / "render_index.py"), str(SKILL / "progress.example.md"), str(out), "Example"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Example", out.read_text())


if __name__ == "__main__":
    unittest.main()
