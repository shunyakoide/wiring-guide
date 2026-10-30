#!/usr/bin/env python3
"""Build a breadboard wiring page from a short JSON spec.

    python3 breadboard.py spec.json out.html

Draws the board, parts and wires, writes the steps, the table and a close-up of each
resistor value into a copy of template.html, then prints every net, what it checked, and
any mistakes it finds (a hole that does not exist, both legs in one strip, a supply
shorted to GND, 5 V on a 3.3 V pin, an LED without a resistor, ...).

warning: the page is written; tell the user or confirm it against the datasheet.
ERROR:   no page is written and it exits 1. With "as_built": true the spec records wiring
         the user already built, so a fault is the finding: the page is written with a
         do-not-power banner, still exit 1. A spec that cannot be drawn never gets a page.
See spec.example.json for the format. Python 3 standard library only.
"""
import html, json, math, re, sys
from pathlib import Path

P = 18                       # hole pitch in the drawing
X0 = 70                      # x of the leftmost number
OFF_H = 96                   # height of a board beside the breadboard: name, note, pin labels
HS = 44                      # between two headers of that board, room for rotated pin labels
RTL = ("ar", "fa", "he", "ur")

WORDS = {
    "en": {
        "where": "Where it goes", "table": "Wires and parts", "colors": "Reading the resistor bands",
        "th": ["Wire / part", "From", "To", "Jumper / value"],
        "howto": "Holes are named number + letter ({ex} = number {n}, letter {l}). Number 1 is at the {end1}, letter {near} is nearest you.",
        "left": "left", "right": "right",
        "rail": "{side} {sign} rail ({pos}) at {n}", "far": "far", "near": "near", "outer": "outer", "inner": "inner",
        "pin": "{board} {pin} ({header}{k} from the {end} end)", "usb": "USB", "lend": "left",
        "jumpers": "Jumpers: {list}.", "read": "read this way (the band set apart goes right)",
        "digit": "digit", "mult": "multiplier", "tol": "tolerance",
        "led": ["+ (long leg)", "− (short leg)"], "polar": ["+", "− (stripe)"], "diode": ["anode", "cathode (band)"],
        "names": ["black", "brown", "red", "orange", "yellow", "green", "blue", "violet", "grey", "white"], "gold": "gold", "silver": "silver",
        "ui": {"all": "All", "prev": "Previous step", "next": "Next step", "fit": "Fit", "zoomIn": "Zoom in", "zoomOut": "Zoom out"},
        "short": "short", "mid": "medium", "long": "long", "longleg": "long leg", "before": "Unplug USB before you start.",
        "t_part2": "{id} ({value}) in {a} and {b}.", "t_led": "{id}: long leg (+) in {a}, short leg in {b}.",
        "t_polar": "{id}: + leg in {a}, − leg in {b}.", "t_switch": "{id} in {holes}: the two legs farther apart go on one number.",
        "t_multi": "{id}: {legs}.", "t_dip": "{id} across the gap, notch to the left, pin 1 in {pin1}.", "t_wire": "Wire {n}: {a} → {b}.",
        "unsafe": "Do not power this up. The drawing shows the wiring as it is now, and it has a fault.",
    },
    "ja": {
        "where": "どこに挿すか", "table": "線と部品", "colors": "抵抗の色の読み方",
        "th": ["線・部品", "ここから", "ここへ", "ジャンパー・値"],
        "howto": "穴は「番号＋文字」で呼びます（{ex} ＝ 番号 {n}、文字 {l}）。番号 1 が{end1}端、文字 {near} があなたに近い側です。",
        "left": "左", "right": "右",
        "rail": "{side}の {sign} レール（{pos}）の {n}", "far": "奥", "near": "手前", "outer": "外側", "inner": "内側",
        "pin": "{board} の {pin}（{header}{end}側から {k} 番目）", "usb": "USB ", "lend": "左",
        "jumpers": "ジャンパー: {list}。", "read": "読む向き（離れた帯が右）",
        "digit": "数字", "mult": "かける数", "tol": "誤差",
        "led": ["＋（長い足）", "−（短い足）"], "polar": ["＋", "−（帯の側）"], "diode": ["アノード", "カソード（帯の側）"],
        "names": ["黒", "茶", "赤", "橙", "黄", "緑", "青", "紫", "灰", "白"], "gold": "金", "silver": "銀",
        "ui": {"all": "全部", "prev": "前の手順", "next": "次の手順", "fit": "全体", "zoomIn": "拡大", "zoomOut": "縮小"},
        "short": "短", "mid": "中", "long": "長", "longleg": "長い足", "before": "始める前に USB を抜きます。",
        "t_part2": "{id}（{value}）を {a} と {b} に。", "t_led": "{id}：長い足（＋）を {a}、短い足を {b} に。",
        "t_polar": "{id}：＋の足を {a}、−の足を {b} に。", "t_switch": "{id} を {holes} に。足の間が広い 2 本を同じ番号に。",
        "t_multi": "{id} の足を {legs} に。", "t_dip": "{id} を溝をまたいで、切り欠きを左、1 番ピンを {pin1} に。", "t_wire": "線 {n}：{a} → {b}。",
        "unsafe": "電源を入れないでください。この図は今の配線で、不具合があります。",
    },
}
WIRE = {"red": "var(--red)", "black": "var(--w-blk)", "green": "var(--w-grn)", "yellow": "var(--w-yel)",
        "orange": "var(--w-org)", "blue": "var(--w-blu)", "white": "#f4f4f4", "grey": "var(--w-edge)"}
LED = {"red": "#e5484d", "yellow": "#f5c518", "green": "#30a46c", "blue": "#3e7bfa", "white": "#f2f4f6", "orange": "#f08c00"}
TWO_LEG = ("resistor", "led", "cap", "buzzer", "diode")

# What the safety checks know about a board. Sources are in boards/*.md; a spec may override any key.
# logic_v: GPIO level. power: supply pins in volts, None for an input with no fixed voltage.
# pin_ma: [warn above, stop above]. forbid / avoid: pins and why.
BOARD_FACTS = {
    "uno-r3": {"logic_v": 5, "power": {"5V": 5, "3.3V": 3.3, "IOREF": 5, "VIN": None}, "pin_ma": [20, 40],
               "avoid": {"D0": "USB serial, can block uploads", "D1": "USB serial, can block uploads"}},
    "nano": {"logic_v": 5, "power": {"5V": 5, "3V3": 3.3, "VIN": None}, "pin_ma": [20, 40],
             "avoid": {"RX0": "USB serial, can block uploads", "TX1": "USB serial, can block uploads"}},
    "mega2560": {"logic_v": 5, "power": {"5V": 5, "3.3V": 3.3, "IOREF": 5, "VIN": None}, "pin_ma": [20, 40],
                 "avoid": {"D0": "USB serial, can block uploads", "D1": "USB serial, can block uploads"}},
    "pico": {"logic_v": 3.3, "power": {"3V3": 3.3, "3V3(OUT)": 3.3, "VBUS": 5, "VSYS": 5}, "pin_ma": [4, 12]},
    "esp32-devkitc": {"logic_v": 3.3, "power": {"3V3": 3.3, "5V": 5}, "pin_ma": [20, 28],
                      "forbid": {p: "wired to the module's flash" for p in ("CLK", "CMD", "D0", "D1", "D2", "D3")},
                      "avoid": {"IO0": "strapping pin", "IO2": "strapping pin", "IO5": "strapping pin", "IO12": "strapping pin", "IO15": "strapping pin",
                                "RX": "USB serial", "TX": "USB serial"}},
}
BOARD_KINDS = (None, "offboard")
PART_KINDS = TWO_LEG + ("switch", "dip", "pot", "rgb", "module", "part")
GND_PIN = re.compile(r"^([ADP]?GND\d*|GROUND|G|VSS|0V|-)$", re.I)
SUPPLY_LEG = re.compile(r"^(A?VCC\d*|DVCC|A?VDD\d*|VIN|VS|VM|V|VBAT|VBUS|VSYS|V\+|\+|PWR|POWER|\+?\d+(\.\d+)?V|\d+V\d+)$", re.I)
CATHODE_LEG = ("-", "K", "C", "cathode")
ANODE_LEG = ("+", "A", "anode")
RGB_COMMON = re.compile(r"^(K|A|C|COM|COMMON|GND|VCC|\+|-)$", re.I)
# Defaults of this skill, not from a datasheet, and printed as assumed: a part's vf and max_ma replace them.
LED_WARN_MA, LED_STOP_MA = 20, 30
VF_LOW = {"red": 1.8, "orange": 1.8, "yellow": 1.8, "green": 1.8, "blue": 2.8, "white": 2.8}   # low end, so the current is not understated
NOT_CHECKED = ("pin orders copied from a datasheet, breadboard rails that are split, supply capacity and total current, "
               "flyback diodes, motors, relays and servos, parts without declared limits, whether a dashed fix is safe, what firmware does with the pins")

errors, warnings, fatal, checks = [], [], [], []
esc = html.escape


def err(msg): errors.append(msg)


def stop(msg):
    """A spec that cannot be drawn: no page, even for as_built."""
    errors.append(msg)
    fatal.append(msg)


def pin_list(d):
    if d.get("kind") == "offboard":
        return [nm for h in d["headers"] for nm in h["pins"] if nm]
    return [nm for names in d["pins"].values() for nm in names]


def facts_of(d):
    return {**BOARD_FACTS.get(d.get("model"), {}), **d}


def validate(spec):
    """Stop at the boundary: everything the planner would otherwise drop or crash on."""
    b = spec.get("board", {})
    if not isinstance(b.get("rows"), int) or b["rows"] < 1:
        return stop("board: give rows (30 half, 63 full, 17 mini)")
    for key, allowed in (("near", "aj"), ("row1", ("left", "right")), ("rails", ("both", "far", "near", "none")), ("outer", "-+")):
        if key in b and b[key] not in allowed:
            stop(f'board: {key} "{b[key]}" is not one of {", ".join(allowed)}')
    for w in spec.get("wires", []):
        if w.get("dashed") and not spec.get("as_built"):
            stop(f'wire {w.get("n")}: a dashed fix belongs on an "as_built" page')
    boards, parts = {}, {}
    for d in spec.get("boards", []):
        who = d.get("id", "?")
        if d.get("kind") not in BOARD_KINDS:
            stop(f'{who}: board kind "{d["kind"]}" is not supported (leave it out for a board in the breadboard, or use "offboard")')
        elif not all(k in d for k in (("headers",) if d.get("kind") == "offboard" else ("span", "pins"))):
            stop(f"{who}: its pins are missing (see The spec in SKILL.md)")
        elif "logic_v" not in facts_of(d) or "power" not in facts_of(d):
            stop(f'{who}: model "{d.get("model")}" is not supported: choose one of {", ".join(BOARD_FACTS)}, '
                 'or give logic_v and power from its datasheet; ask the user if you cannot find them')
        else:
            boards[who] = d
    for p in spec.get("parts", []):
        who = p.get("id", "?")
        if p.get("kind") not in PART_KINDS:
            stop(f'{who}: part kind "{p.get("kind")}" is not supported ({", ".join(PART_KINDS)})')
        elif who in parts:
            stop(f"{who}: two parts have this id")
        else:
            parts[who] = p
    for group in spec.get("connect", []):
        for e in group:
            if e in ("+", "-", "GND"):
                continue
            who, _, leg = e.partition(".")
            if who in boards:
                want, _, nth = leg.partition("#")
                if pin_list(boards[who]).count(want) < int(nth or 1):
                    stop(f"connect: {e}: {who} has no such pin")
            elif who in parts:
                if "names" not in parts[who] and parts[who]["kind"] in ("rgb", "module", "part"):
                    stop(f"{who}: give the names of its legs")
                elif leg not in leg_names(parts[who]):
                    stop(f"connect: {e}: {who} has legs {', '.join(leg_names(parts[who]))}")
            else:
                stop(f"connect: {e}: nothing has the id {who}")


# ---------- geometry ----------

class Board:
    def __init__(self, b):
        self.rows = b["rows"]
        self.left1 = b.get("row1", "left") == "left"
        self.near = b.get("near", "a")
        self.rails = {s: b.get("rails", "both") in ("both", s) for s in ("far", "near")}
        outer = b.get("outer", "-")
        self.sign = {"outer": outer, "inner": "+" if outer == "-" else "-"}
        lets = "jihgfedcba" if self.near == "a" else "abcdefghij"
        self.top5, self.bot5 = lets[:5], lets[5:]

    def ly_order(self, letter):
        return (self.top5 + self.bot5).index(letter)

    def x(self, n):
        return X0 + P * ((n - 1) if self.left1 else (self.rows - n))

    def layout(self, top):
        y = top + 16
        self.ry = {}
        if self.rails["far"]:
            self.ry[("far", "outer")], self.ry[("far", "inner")] = y, y + P
            y += 2 * P
        self.num_top = y + 6
        y += 24
        self.ly = {}
        for i, l in enumerate(self.top5):
            self.ly[l] = y + i * P
        gy = self.ly[self.top5[-1]] + 4 * P   # wider than real, so chip pin names fit
        for i, l in enumerate(self.bot5):
            self.ly[l] = gy + i * P
        self.num_mid = (self.ly[self.top5[-1]] + gy) / 2 + 4
        y = self.ly[self.bot5[-1]] + 18
        self.num_bot = y + 6
        y += 22
        if self.rails["near"]:
            self.ry[("near", "inner")], self.ry[("near", "outer")] = y, y + P
            y += 2 * P
        self.top, self.bottom = top, y
        self.right = self.x(self.rows if self.left1 else 1)

    def side_of(self, letter):
        return "far" if letter in self.top5 else "near"


RAIL = re.compile(r"^([FN])([+-])(\d+)$")
HOLE = re.compile(r"^(\d+)([a-j])$")


class Page:
    def __init__(self, spec):
        self.s = spec
        self.lang = spec.get("lang", "en")
        w = dict(WORDS["en"])
        w.update(WORDS.get(self.lang, {}))
        w.update(spec.get("words", {}))
        if self.lang not in WORDS and "words" not in spec:
            warnings.append(f'lang "{self.lang}" has no built-in words: add a "words" object (see WORDS in breadboard.py)')
        self.w = w
        self.b = Board(spec["board"])
        self.used = {}           # hole key -> who uses it
        self.parent = {}         # union-find over nodes
        self.members = {}        # node -> list of names
        self.boards = {}         # id -> board/offboard spec with resolved pins
        self.items = {}          # id -> svg string
        self.rows = {}           # id -> table row cells
        self.covered = {}        # hole key -> module id
        self.reported = set()    # parts add_part already called shorted, so the net check does not repeat it
        self.must = set()        # part legs that should connect to something
        self.boxes = []          # label boxes placed so far (x, y, w, h)

    # --- nodes and nets ---
    def node(self, key):
        """The electrical node a hole or pin belongs to: a 5-hole strip, a rail, or a pin."""
        if key[0] == "h":
            n, l = key[1], key[2]
            return ("strip", n, self.b.side_of(l))
        if key[0] == "r":
            return ("rail", key[1], key[2])   # rails are not split, as asked in step 1
        return key

    def find(self, a):
        self.parent.setdefault(a, a)
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def join(self, a, b):
        self.parent[self.find(a)] = self.find(b)

    def member(self, key, name):
        self.members.setdefault(self.node(key), []).append(name)

    # --- endpoints ---
    def parse(self, ref, who):
        """Return (key, (x, y)) for a hole '12e', a rail 'F-12' / 'N+3', or a pin 'uno.5V'."""
        m = HOLE.match(ref)
        if m:
            n, l = int(m[1]), m[2]
            if not 1 <= n <= self.b.rows:
                stop(f"{who}: hole {ref} does not exist (the board has numbers 1–{self.b.rows})")
            return ("h", n, l), (self.b.x(n), self.b.ly[l])
        m = RAIL.match(ref)
        if m:
            side = "far" if m[1] == "F" else "near"
            sign, n = m[2], int(m[3])
            if not self.b.rails[side]:
                stop(f"{who}: {ref}: this board has no {side} rail")
                return ("r", side, sign, n), (self.b.x(n), self.b.top)
            pos = "outer" if self.b.sign["outer"] == sign else "inner"
            if not 1 <= n <= self.b.rows:
                stop(f"{who}: rail hole {ref} does not exist")
            return ("r", side, sign, n), (self.b.x(n), self.b.ry[(side, pos)])
        if "." in ref:
            bid, pin = ref.split(".", 1)
            ob = self.boards.get(bid)
            if not ob:
                stop(f"{who}: {ref}: no board with id {bid}")
                return ("p", bid, pin), (0, 0)
            hit = ob["find"](pin)
            if hit is None:
                stop(f"{who}: {ref}: {bid} has no pin {pin}")
                return ("p", bid, pin), (0, 0)
            return hit
        stop(f"{who}: cannot read '{ref}' (use 12e, F-12, N+3 or board.pin)")
        return ("x", ref), (0, 0)

    def take(self, key, who):
        if key[0] in ("h", "r", "p"):
            k = key
            if k in self.used:
                err(f"{who}: hole {self.name(key)} is already used by {self.used[k]}")
            elif k in self.covered and not who.startswith(self.covered[k]):
                err(f"{who}: hole {self.name(key)} is under {self.covered[k]}")
            self.used[k] = who

    def name(self, key):
        w = self.w
        if key[0] == "h":
            return f"{key[1]}{key[2]}"
        if key[0] == "r":
            side, sign, n = key[1], key[2], key[3]
            pos = "outer" if self.b.sign["outer"] == sign else "inner"
            return w["rail"].format(side=w[side], sign="＋" if sign == "+" else "−", pos=w[pos], n=n)
        if key[0] == "p":
            ob = self.boards[key[1]]
            return ob["label_pin"](key)
        return str(key)

    def shown(self, key):
        """Endpoint text for the table: a hole next to a board pin also names the pin."""
        t = self.name(key)
        if key[0] == "h":
            pin = self.pin_at.get(self.node(key))
            if pin:
                t += f" ({pin})"
        return t

    # ---------- boards that carry pins ----------
    def add_straddler(self, d):
        """A board plugged into the breadboard (Pico, Nano): its pins are holes."""
        bid, (lo, hi) = d["id"], d["span"]
        pins = {}
        for letter, names in d["pins"].items():
            if len(names) != hi - lo + 1:
                err(f"{bid}: letter {letter} lists {len(names)} pins for numbers {lo}–{hi}")
            for i, nm in enumerate(names):
                pins.setdefault(nm, []).append(("h", lo + i, letter))
        d["holes"] = [k for v in pins.values() for k in v]

        def find(pin):
            want, nth = (pin.split("#") + ["1"])[:2]            # GND#2: the second pin named GND
            hit = pins.get(want)
            if not hit or len(hit) < int(nth):
                return None
            k = hit[int(nth) - 1]
            return k, (self.b.x(k[1]), self.b.ly[k[2]])
        d["find"] = find
        self.boards[bid] = d

    def add_offboard(self, d):
        """A board beside the breadboard (Uno, ESP32 DevKit): its headers line up with the numbers."""
        bid = d["id"]
        sockets = []          # (pin name, header index, k from the counted end, number it lines up with)
        for hi, h in enumerate(d["headers"]):
            names = h["pins"]
            nums, n = [], h["at"]
            for nm in names:
                nums.append(n)
                n += 1
            count_from_right = d.get("usb", "left") == "right"
            real = [i for i, nm in enumerate(names) if nm is not None]
            order = list(reversed(real)) if count_from_right else real
            for k, i in enumerate(order, 1):
                sockets.append((names[i], hi, k, nums[i]))
        d["sockets"] = sockets

        def find(pin):
            want, nth = (pin.split("#") + ["1"])[:2]
            hits = [s for s in sockets if s[0] == want]
            if not hits:
                return None
            if len(hits) < int(nth):
                return None
            s = hits[int(nth) - 1]
            return ("p", bid, s), d["xy"](s)

        def label_pin(key):
            s = key[2]
            h = d["headers"][s[1]]
            end = self.w["usb"] if d.get("usb") else self.w["lend"]
            sep = "、" if self.lang == "ja" else ", "
            return self.w["pin"].format(board=d.get("short", d["label"]), pin=s[0],
                                         header=h["name"] + sep if h.get("name") else "", k=s[2], end=end)
        d["find"], d["label_pin"] = find, label_pin
        self.boards[bid] = d

    # ---------- drawing ----------
    def build(self):
        s, b = self.s, self.b
        offs = [d for d in s.get("boards", []) if d.get("kind") == "offboard"]
        strad = [d for d in s.get("boards", []) if d.get("kind") != "offboard"]
        n_off_wires = {"far": 0, "near": 0}
        for wd in s.get("wires", []):
            for ref in (wd["from"], wd["to"]):
                if "." in ref:
                    bid = ref.split(".")[0]
                    side = next((d.get("side", "far") for d in offs if d["id"] == bid), None)
                    if side:
                        n_off_wires[side] += 1
                        break
        far_off = [d for d in offs if d.get("side", "far") == "far"]
        near_off = [d for d in offs if d.get("side", "far") == "near"]
        top = 20
        if far_off:
            hh = max(len(d["headers"]) for d in far_off)
            box_h = OFF_H + HS * (hh - 1)
            self.lane_far = [top + box_h + 22 + 7 * i for i in range(n_off_wires["far"])]
            top += box_h + 30 + 7 * n_off_wires["far"]
        b.layout(top)
        bottom = b.bottom
        self.lane_near = []
        if near_off:
            self.lane_near = [bottom + 14 + 7 * i for i in range(n_off_wires["near"])]
            bottom += 22 + 7 * n_off_wires["near"]
        self.off_top = bottom
        if near_off:
            hh = max(len(d["headers"]) for d in near_off)
            bottom += OFF_H + HS * (hh - 1) + 10
        self.width = b.right + X0
        self.height = bottom + 20

        for d in offs:
            self.place_offboard(d, far=d.get("side", "far") == "far")
        for d in strad:
            self.add_straddler(d)
        self.pin_at = {}
        for d in strad:
            self.cover_gap([(self.b.x(n), 0) for n in d["span"]])
            ys = sorted(self.b.ly[l] for l in d["pins"])
            for n in range(d["span"][0], d["span"][1] + 1):      # the holes under its board
                for l, y in self.b.ly.items():
                    if ys[0] < y < ys[-1]:
                        self.covered.setdefault(("h", n, l), d["id"])
            for nm, keys in self.pin_names(d):
                for k in keys:
                    self.pin_at.setdefault(self.node(k), nm)
                    self.take(k, d["id"])
                    self.member(k, f'{d["id"]}.{nm}')
        for d in offs:
            for sk in d["sockets"]:
                if sk[0]:
                    self.member(("p", d["id"], sk), f'{d["id"]}.{sk[0]}')

        for pd in s.get("parts", []):
            c = pd.get("cover")
            for n in range(c["from"], c["to"] + 1) if c else ():
                for l in c.get("letters", ""):
                    self.covered.setdefault(("h", n, l), pd["id"])
        for pd in s.get("parts", []):
            self.add_part(pd)
        self.lane_i = {"far": 0, "near": 0}
        self.runs = []
        for wd in s.get("wires", []):
            self.add_wire(wd)

    def pin_names(self, d):
        out = {}
        for letter, names in d["pins"].items():
            for i, nm in enumerate(names):
                out.setdefault(nm, []).append(("h", d["span"][0] + i, letter))
        return out.items()

    def place_offboard(self, d, far):
        xs = []
        for h in d["headers"]:
            n = h["at"]
            for nm in h["pins"]:
                xs.append(self.b.x(n))
                n += 1
        x0, x1 = min(xs) - 30, max(xs) + 30
        if far:
            y0 = 20
            hy = [y0 + OFF_H + HS * (len(d["headers"]) - 1) - 14 - HS * i for i in range(len(d["headers"]))]
        else:
            y0 = self.off_top
            hy = [y0 + 14 + HS * i for i in range(len(d["headers"]))]
        h_box = OFF_H + HS * (len(d["headers"]) - 1)

        def xy(sk):
            return (self.b.x(sk[3]), hy[sk[1]])
        d["xy"] = xy
        d["box"] = (x0, y0, x1 - x0, h_box)
        d["hy"] = hy
        self.add_offboard(d)

    def svg_boards_off(self):
        out = []
        for d in self.s.get("boards", []):
            if d.get("kind") != "offboard":
                continue
            x, y, w, h = d["box"]
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="var(--surface)" stroke="var(--chip)" stroke-width="1.5"/>')
            if d.get("usb"):
                edge = x if d["usb"] == "left" else x + w
                out.append(usb_port(edge, y + h / 2 - (14 if d.get("jack") else 0), d["usb"], 34, 30))
                if d.get("jack"):                               # the round power jack beside the USB port, as on an Uno
                    jx = edge - 22 if d["usb"] == "left" else edge - 4
                    out.append(f'<rect x="{jx}" y="{y + h / 2 + 8}" width="26" height="22" rx="4" fill="#1f2328" stroke="#8b939b"/>'
                               f'<circle cx="{jx + (8 if d["usb"] == "left" else 18)}" cy="{y + h / 2 + 19}" r="5" fill="#3a4048" stroke="#8b939b"/>')
            far = d.get("side", "far") == "far"
            ty = y + 20 if far else y + h - 12
            out.append(f'<text x="{x + 14}" y="{ty}" font-weight="700">{esc(d["label"])}</text>')
            if d.get("note"):
                out.append(f'<text x="{x + 14}" y="{ty + 16 if far else ty - 16}" class="m">{esc(d["note"])}</text>')
            used = {k[2] for k in self.used_pins if k[0] == "p" and k[1] == d["id"]}
            for sk in d["sockets"]:
                sx, sy = d["xy"](sk)
                fill = "var(--chip)" if sk in used else "var(--board)"
                out.append(f'<rect x="{sx - 5}" y="{sy - 5}" width="10" height="10" rx="1.5" fill="{fill}" stroke="var(--chip)"/>')
        return "".join(out)

    def svg_pin_labels(self):
        """Labels for the off-board pins in use, in the step that first uses each pin."""
        out = []
        for key, step in self.pin_steps.items():
            d = self.boards[key[1]]
            sx, sy = d["xy"](key[2])
            far = d.get("side", "far") == "far"
            ly = sy - 9 if far else sy + 9
            label = f'<text transform="translate({sx + 4} {ly}) rotate(-90)" text-anchor="{"start" if far else "end"}" class="m">{esc(key[2][0])}</text>'
            out.append(self.grp(step, label))
        return "".join(out)

    def svg_board(self):
        b, out = self.b, []
        out.append(f'<rect x="{X0 - 40}" y="{b.top}" width="{b.right - X0 + 80}" height="{b.bottom - b.top}" rx="10" fill="var(--board)" stroke="var(--line)"/>')
        dots = []
        for (side, pos), y in b.ry.items():
            sign = b.sign[pos]
            col = "var(--red)" if sign == "+" else "var(--w-blu)"
            off = -9 if (side == "far" and pos == "outer") or (side == "near" and pos == "inner") else 9
            out.append(f'<line x1="{X0 - 6}" x2="{b.right + 6}" y1="{y + off}" y2="{y + off}" stroke="{col}" stroke-width="1.5" opacity=".8"/>')
            out.append(f'<text x="{X0 - 26}" y="{y + 4}" class="m" text-anchor="middle">{"＋" if sign == "+" else "−"}</text>')
            for n in range(1, b.rows + 1):
                dots.append(f'<circle cx="{b.x(n)}" cy="{y}" r="2.6"/>')
        for l, y in b.ly.items():
            out.append(f'<text x="{X0 - 26}" y="{y + 4}" class="m" text-anchor="middle">{l}</text>')
            out.append(f'<text x="{b.right + 26}" y="{y + 4}" class="m" text-anchor="middle">{l}</text>')
            for n in range(1, b.rows + 1):
                dots.append(f'<circle cx="{b.x(n)}" cy="{y}" r="2.6"/>')
        out.append(f'<g fill="var(--hole)">{"".join(dots)}</g>')
        return "".join(out)

    def svg_numbers(self):
        b, nums = self.b, []
        for n in range(1, b.rows + 1):
            x = b.x(n)
            nums.append(f'<text x="{x}" y="{b.num_top}">{n}</text><text x="{x}" y="{b.num_bot}">{n}</text>')
            if n not in self.straddled:
                nums.append(f'<text x="{x}" y="{b.num_mid}">{n}</text>')
        # above the wires, with a rim of board colour, so a wire passing a number does not hide it
        return f'<g class="m" text-anchor="middle" stroke="var(--board)" stroke-width="4" paint-order="stroke">{"".join(nums)}</g>'


    def svg_straddlers(self):
        out = []
        for d in self.s.get("boards", []):
            if d.get("kind") == "offboard":
                continue
            lo, hi = d["span"]
            letters = list(d["pins"])
            ys = [self.b.ly[l] for l in letters]
            x0, x1 = min(self.b.x(lo), self.b.x(hi)) - 11, max(self.b.x(lo), self.b.x(hi)) + 11
            y0, y1 = min(ys) - 11, max(ys) + 11
            out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6" fill="var(--chip)" opacity=".22" stroke="var(--chip)"/>')
            if d.get("usb"):
                out.append(usb_port(x0 if d["usb"] == "left" else x1, (y0 + y1) / 2, d["usb"], 26, 16))
            out.append(f'<text x="{(x0 + x1) / 2}" y="{(y0 + y1) / 2 - 2}" text-anchor="middle" font-weight="700">{esc(d["label"])}</text>')
            if d.get("note"):
                out.append(f'<text x="{(x0 + x1) / 2}" y="{(y0 + y1) / 2 + 15}" text-anchor="middle" class="m">{esc(d["note"])}</text>')
            for nm, keys in self.pin_names(d):
                for k in keys:
                    out.append(f'<rect x="{self.b.x(k[1]) - 4}" y="{self.b.ly[k[2]] - 4}" width="8" height="8" fill="var(--chip)"/>')
        return "".join(out)

    def svg_straddler_labels(self):
        out = []
        for d in self.s.get("boards", []):
            if d.get("kind") == "offboard":
                continue
            letters = list(d["pins"])
            mid = sum(self.b.ly[l] for l in letters) / len(letters)
            for nm, keys in self.pin_names(d):
                for k in keys:
                    if self.node(k) not in self.live_nodes:
                        continue
                    x, y = self.b.x(k[1]), self.b.ly[k[2]]
                    inward = 1 if y < mid else -1
                    anchor = "end" if inward == 1 else "start"
                    out.append(f'<text transform="translate({x + 4} {y + inward * 9}) rotate(-90)" text-anchor="{anchor}" class="m">{esc(nm)}</text>')
        return "".join(out)

    # ---------- parts ----------
    def add_part(self, d):
        pid, kind = d["id"], d["kind"]
        if not any(k in d for k in ("legs", "pairs", "pin1")):
            return                                              # the planner found no room; it said so
        legs = d.get("legs", [])
        if kind == "switch":
            pairs = d["pairs"]
            keys = [[self.parse(r, pid) for r in pair] for pair in pairs]
            for pair in keys:
                for k, _ in pair:
                    self.take(k, pid)
                self.join(self.node(pair[0][0]), self.node(pair[1][0]))
            for i, pair in enumerate(keys):
                for k, _ in pair:
                    self.member(k, f"{pid}.{i + 1}")
            if self.find(self.node(keys[0][0][0])) == self.find(self.node(keys[1][0][0])):
                err(f"{pid}: its two sides are in the same strip, so it is always closed (turn it 90° or put the connected pair across the gap)")
            pts = [xy for pair in keys for _, xy in pair]
            self.items[pid] = self.draw_switch(pid, pts)
            self.rows[pid] = [pid, " · ".join(self.name(k) for pair in keys for k, _ in pair), "", d.get("value", "")]
            self.cover_gap(pts)
            return
        if kind == "dip":
            m = HOLE.match(d["pin1"])
            n0, l1 = int(m[1]), m[2]
            half = d["pins"] // 2
            l2 = {"e": "f", "f": "e"}.get(l1)
            if not l2:
                err(f"{pid}: pin 1 must be in letter e or f, across the gap")
                return
            names = d.get("names", [str(i + 1) for i in range(d["pins"])])
            keys = []
            for i in range(d["pins"]):
                n, l = (n0 + i, l1) if i < half else (n0 + d["pins"] - 1 - i, l2)
                k, xy = self.parse(f"{n}{l}", pid)
                self.take(k, pid)
                self.member(k, f"{pid}.{i + 1} {names[i]}")
                keys.append((k, xy))
            self.items[pid] = self.draw_dip(pid, d, keys, names)
            self.rows[pid] = [pid, f'{d.get("label", "")} · pin 1 = {d["pin1"]}', "", d.get("value", "")]
            self.cover_gap([xy for _, xy in keys])
            return
        named = [(l[0], l[1]) if isinstance(l, list) else (None, l) for l in legs]
        keys = []
        for nm, ref in named:
            k, xy = self.parse(ref, pid)
            self.take(k, pid)
            keys.append((nm, k, xy))
        for i, (nm, k, _) in enumerate(keys):
            self.member(k, f"{pid}.{nm or i + 1}")
            self.must.add(f"{pid}.{nm or i + 1}")
        if kind in TWO_LEG and len(keys) == 2:
            if self.node(keys[0][1]) == self.node(keys[1][1]):
                self.reported.add(pid)
                err(f"{pid}: both legs are in the same strip ({self.name(keys[0][1])}, {self.name(keys[1][1])}), so it is shorted out")
            (x1, y1), (x2, y2) = keys[0][2], keys[1][2]
            if x1 != x2 and y1 != y2:
                err(f"{pid}: legs {self.name(keys[0][1])} and {self.name(keys[1][1])} are on a slant; put both legs on one number or one letter")
            if kind == "resistor":
                if keys[0][1][0] == "h" and keys[1][1][0] == "h" and self.b.side_of(keys[0][1][2]) == self.b.side_of(keys[1][1][2]) and math.dist((x1, y1), (x2, y2)) < 4 * P:
                    err(f"{pid}: legs only {round(math.dist((x1, y1), (x2, y2)) / P)} holes apart; leave at least 3 holes between them")
        if kind == "pot" and len(keys) == 3 and keys[1][1][0] == "r":
            self.reported.add(pid)
            err(f"{pid}: the middle leg (wiper) is on a rail")
        pts = [xy for _, _, xy in keys]
        if len({self.b.side_of(k[2]) for _, k, _ in keys if k[0] == "h"}) > 1:
            self.cover_gap(pts)
        self.items[pid] = self.draw_part(pid, d, keys)
        val = d.get("value", "")
        if kind in TWO_LEG and len(keys) == 2:
            names = {"led": self.w["led"], "cap": self.w["polar"] if d.get("polar") else None,
                     "buzzer": self.w["polar"] if d.get("polar", True) else None, "diode": self.w["diode"]}.get(kind)
            a, c = (self.name(keys[0][1]), self.name(keys[1][1]))
            if names:
                a, c = f"{names[0]} {a}", f"{names[1]} {c}"
            label = pid + (f" {esc(d['label'])}" if d.get("label") else "")
            if kind == "resistor":
                label = self.mini_bands(val) + " " + label
                val = fmt_ohm(val)
            self.rows[pid] = [label, a, c, esc(val)]
        else:
            legs_t = " · ".join(f"{esc(nm)} {self.name(k)}" if nm else self.name(k) for nm, k, _ in keys)
            self.rows[pid] = [pid + (f" {esc(d['label'])}" if d.get("label") else ""), legs_t, "", esc(val)]

    def clear_of_numbers(self, y):
        """Move a label's baseline off the rows of numbers."""
        for ny in (self.b.num_top, self.b.num_mid, self.b.num_bot):
            if abs(y - ny) < 12:
                return ny + 14 if y >= ny else ny - 14
        return y

    def cover_gap(self, pts):
        xs = [x for x, _ in pts]
        for n in range(1, self.b.rows + 1):
            if min(xs) - 4 <= self.b.x(n) <= max(xs) + 4:
                self.straddled.add(n)

    def draw_switch(self, pid, pts):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, x1, y0, y1 = min(xs) - 8, max(xs) + 8, min(ys) - 8, max(ys) + 8
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        legs = "".join(f'<circle cx="{x}" cy="{y}" r="3.5" fill="var(--chip)"/>' for x, y in pts)
        return (f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="4" fill="var(--surface)" stroke="var(--chip)" stroke-width="1.5" opacity=".95"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{min(x1 - x0, y1 - y0) / 3.2}" fill="var(--chip)" opacity=".55"/>{legs}'
                + self.label(x1 + 4, y0 + 10, pid))

    def draw_dip(self, pid, d, keys, names):
        xs, ys = [xy[0] for _, xy in keys], [xy[1] for _, xy in keys]
        x0, x1, y0, y1 = min(xs) - 9, max(xs) + 9, min(ys) + 7, max(ys) - 7
        out = [f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="3" fill="#2b3036" stroke="var(--chip)"/>']
        p1x = keys[0][1][0]
        nx = x0 if abs(p1x - x0) < abs(p1x - x1) else x1
        out.append(f'<path d="M{nx} {(y0 + y1) / 2 - 6} a6 6 0 0 {1 if nx == x0 else 0} 0 12" fill="var(--board)"/>')
        mid = (y0 + y1) / 2
        for (k, (x, y)), nm in zip(keys, names):
            out.append(f'<rect x="{x - 3}" y="{y - 4}" width="6" height="8" fill="#c9ced4"/>')
            inward = 1 if y < mid else -1
            anchor = "end" if inward == 1 else "start"
            out.append(f'<text transform="translate({x + 4} {y + inward * 9}) rotate(-90)" text-anchor="{anchor}" style="fill:#e8ebee;font-size:12px" class="m">{esc(nm)}</text>')
        label = d.get("label", pid)
        out.append(f'<text x="{x1 + 6}" y="{mid + 4}" font-weight="700">{esc(label)}</text>')
        self.cover_gap([(x1, 0), (x1 + 8 + 9 * len(label), 0)])
        return "".join(out)

    def draw_part(self, pid, d, keys):
        kind = d["kind"]
        pts = [xy for _, _, xy in keys]
        out = []
        legcol = "#9aa1a8"
        if kind in TWO_LEG and len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            L = math.dist(pts[0], pts[1])
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{legcol}" stroke-width="2.2"/>')
            g = f'<g transform="translate({mx:.1f} {my:.1f}) rotate({ang:.1f})">'
            if kind == "resistor":
                bl = min(L - 10, 36)
                g += f'<rect x="{-bl / 2}" y="-5.5" width="{bl}" height="11" rx="4" fill="var(--res)" stroke="#b49a68"/>'
                for i, c in enumerate(band_colors(d.get("value", ""))):
                    bx = -bl / 2 + bl * (0.18, 0.34, 0.5, 0.8)[i]
                    g += f'<rect x="{bx - 2:.1f}" y="-5.5" width="4" height="11" fill="{c}"/>'
            elif kind == "led":
                col = LED.get(d.get("color", "red"), d.get("color", "red"))
                g += f'<circle r="8" fill="{col}" stroke="#00000055"/><line x1="5" y1="-7" x2="5" y2="7" stroke="#00000066" stroke-width="1.5"/>'
            elif kind == "cap":
                if d.get("polar"):
                    g += '<rect x="-9" y="-7" width="18" height="14" rx="3" fill="#2f4f7a"/><rect x="4" y="-7" width="4" height="14" fill="#cfd6de"/>'
                else:
                    g += '<ellipse rx="7" ry="5.5" fill="#d99a3a" stroke="#00000044"/>'
            elif kind == "buzzer":
                g += '<circle r="11" fill="#2b3036" stroke="var(--chip)"/><circle r="2.5" fill="#6b747d"/>'
            elif kind == "diode":
                g += '<rect x="-8" y="-4" width="16" height="8" rx="2" fill="#2b3036"/><rect x="4" y="-4" width="2.5" height="8" fill="#cfd6de"/>'
            out.append(g + "</g>")
            if kind in ("led", "buzzer") or (kind == "cap" and d.get("polar")):
                out.append(f'<text x="{x1 - 11}" y="{y1 + 4}" class="m" text-anchor="middle">+</text>')
            nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
            off = 17 if kind in ("buzzer",) else 13
            lx, ly = mx + nx * off, self.clear_of_numbers(my + ny * off + 4)
            if abs(nx) > 0.5:
                lx += 6 if nx > 0 else -6
            anchor = "middle" if abs(nx) < 0.5 else ("start" if nx > 0 else "end")
            out.append(self.label(lx, ly, pid, anchor))
        else:
            cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            for nm, k, (x, y) in keys:
                out.append(f'<line x1="{x}" y1="{y}" x2="{cx}" y2="{cy}" stroke="{legcol}" stroke-width="2"/>')
            if kind == "module":
                c = d.get("cover")
                if c:
                    xs = [self.b.x(c["from"]), self.b.x(c["to"])]
                    ys = [self.b.ly[l] for l in c["letters"]] if c.get("letters") else [cy]
                    x0, x1 = min(xs) - 10, max(xs) + 10
                    y0, y1 = min(ys + [cy]) - 10, max(ys + [cy]) + 10
                    out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6" fill="var(--chip)" opacity=".18" stroke="var(--chip)" stroke-dasharray="4 3"/>')
                    out.append(f'<text x="{x0 + 8}" y="{y1 - 8}" font-weight="700">{esc(pid)} {esc(d.get("label", ""))}</text>')
                out = [o for o in out if not o.startswith("<line")]
            elif kind == "pot":
                out.append(f'<rect x="{cx - 20}" y="{cy - 26}" width="40" height="22" rx="4" fill="#3d6fb4" opacity=".9"/><circle cx="{cx}" cy="{cy - 15}" r="7" fill="#e8ebee"/><line x1="{cx}" y1="{cy - 21}" x2="{cx}" y2="{cy - 15}" stroke="#2b3036" stroke-width="2"/>')
                out.append(f'<text x="{cx + 24}" y="{cy - 12}" font-weight="700">{esc(pid)}</text>')
            elif kind == "rgb":
                out.append(f'<circle cx="{cx}" cy="{cy - 14}" r="11" fill="#f2f4f6" stroke="var(--chip)"/>')
                out.append(f'<text x="{cx + 15}" y="{cy - 18}" font-weight="700">{esc(pid)}</text>')
            else:
                out.append(f'<rect x="{cx - 14}" y="{cy - 10}" width="28" height="20" rx="4" fill="#2b3036"/>')
                out.append(f'<text x="{cx + 18}" y="{cy - 12}" font-weight="700">{esc(pid)}</text>')
            for nm, k, (x, y) in keys:
                out.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="var(--chip)"/>')
                if nm and kind in ("module", "rgb", "pot", "part"):
                    if kind == "module":
                        c = d.get("cover")
                        down = bool(c) and any(self.b.ly[l] > y for l in c.get("letters", ""))
                        out.append(f'<text transform="translate({x + 4} {y + (9 if down else -9)}) rotate(-90)" text-anchor="{"end" if down else "start"}" class="m">{esc(nm)}</text>')
                    else:
                        out.append(f'<text x="{x}" y="{y + 16}" class="m" text-anchor="middle">{esc(nm)}</text>')
        return "".join(out)

    # ---------- wires ----------
    def add_wire(self, d):
        n = d["n"]
        wid = f"W{n}"
        a, pa = self.parse(d["from"], wid)
        c, pc = self.parse(d["to"], wid)
        for k in (a, c):
            self.take(k, f"wire {n}")
            self.member(k, f"wire {n}")
        if not d.get("dashed"):                                 # a fix not made yet: the checks look at the wiring as it is now
            self.join(self.node(a), self.node(c))
        if self.node(a) == self.node(c):
            err(f"wire {n}: both ends are in the same strip or rail, so it does nothing")
        col = WIRE.get(d.get("color", "blue"), d.get("color", "blue"))
        off = a if a[0] == "p" else c if c[0] == "p" else None
        if off:
            on, pon, poff = (c, pc, pa) if off is a else (a, pa, pc)
            ob = self.boards[off[1]]
            side = ob.get("side", "far")
            lanes = self.lane_far if side == "far" else self.lane_near
            lane = lanes[self.lane_i[side]] if lanes else (pon[1] + poff[1]) / 2
            self.lane_i[side] += 1
            path = f"M{pon[0]} {pon[1]} V{lane} H{poff[0]} V{poff[1]}"
            mid = ((pon[0] + poff[0]) / 2, lane)
        elif pa[0] == pc[0] or pa[1] == pc[1] and abs(pa[0] - pc[0]) <= P:
            path = f"M{pa[0]} {pa[1]} L{pc[0]} {pc[1]}"
            mid = ((pa[0] + pc[0]) / 2, (pa[1] + pc[1]) / 2)
        else:                                                   # up, across, down: each wire on its own lane, so none lie on top of each other
            x0, x1 = sorted((pa[0], pc[0]))
            far = pa[1] < self.b.ly[self.b.bot5[0]]
            rows = [self.b.ly[l] for l in (self.b.top5 if far else self.b.bot5)]
            lanes = sorted((rows[0] + 6 * i for i in range(int((rows[-1] - rows[0]) / 6) + 1)), key=lambda y: abs(y - pc[1]))
            lane = next((y for y in lanes if not any(abs(y - uy) < 6 and u0 < x1 + 6 and x0 < u1 + 6 for uy, u0, u1 in self.runs)), lanes[0])
            self.runs.append((lane, x0, x1))
            path = f"M{pa[0]} {pa[1]} V{lane} H{pc[0]} V{pc[1]}"
            if far != (pc[1] < self.b.ly[self.b.bot5[0]]):     # across the gap: go down between two strips, clear of the parts there
                xv = pc[0] - P / 2 if pc[0] > pa[0] else pc[0] + P / 2
                path = f"M{pa[0]} {pa[1]} V{lane} H{xv} V{pc[1]} H{pc[0]}"
            mid = ((pa[0] + pc[0]) / 2, lane)
        dash = ' stroke-dasharray="7 5"' if d.get("dashed") else ""
        edge = f'<path d="{path}" fill="none" stroke="var(--w-edge)" stroke-width="6" stroke-linecap="round"{dash}/>' if d.get("color") == "black" else ""
        g = (f'{edge}<path d="{path}" fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
             + "".join(f'<circle cx="{x}" cy="{y}" r="4.2" fill="{col}" stroke="var(--surface)" stroke-width="1.5"/>' for x, y in (pa, pc)))
        self.items[wid] = (g, mid, n)
        label = f'<span class="step">{n}</span>{esc(d.get("label", ""))}'
        self.rows[wid] = [label, self.shown(a), self.shown(c), esc(self.jumper(d))]
        self.wire_ends[wid] = (a, c)

    # ---------- page ----------
    def mini_bands(self, v):
        bands = band_colors(v)
        r = "".join(f'<rect x="{x}" y="1" width="3" height="10" fill="{c}"/>' for x, c in zip((11, 16, 21, 31), bands))
        return (f'<svg width="44" height="12" viewBox="0 0 44 12" style="vertical-align:-1px" aria-hidden="true">'
                f'<line x1="0" y1="6" x2="44" y2="6" stroke="#9aa1a8" stroke-width="1.5"/>'
                f'<rect x="7" y="1" width="30" height="10" rx="3" fill="var(--res)"/>{r}</svg>')

    def closeup(self, v, ox):
        """One resistor drawn large at x offset ox: each band led out to its value, color and meaning."""
        w, (d1, d2, ex) = self.w, bands_of(v)
        cols = band_colors(v)
        names = w["names"] + [w["gold"], w["silver"]]
        idx = [d1, d2, ex if ex >= 0 else (10 if ex == -1 else 11), 10]
        mult = f"{10 ** ex:g}" if ex >= 0 else ("0.1" if ex == -1 else "0.01")
        out = [f'<line x1="{ox + 10}" y1="52" x2="{ox + 350}" y2="52" stroke="#9aa1a8" stroke-width="3"/>',
               f'<rect x="{ox + 50}" y="36" width="250" height="32" rx="12" fill="var(--res)" stroke="#b49a68"/>']
        bx = [ox + 90, ox + 145, ox + 200, ox + 275]
        meaning = [w["digit"], w["digit"], w["mult"], w["tol"]]
        val = [str(d1), str(d2), "×" + mult, "±5%"]
        for i, (x, c) in enumerate(zip(bx, cols)):
            out.append(f'<rect x="{x - 6}" y="36" width="12" height="32" fill="{c}"/>')
            out.append(f'<line x1="{x}" y1="70" x2="{x}" y2="86" stroke="var(--muted)"/>')
            out.append(f'<text x="{x}" y="102" text-anchor="middle" font-weight="700">{esc(val[i])}</text>')
            out.append(f'<text x="{x}" y="118" text-anchor="middle" class="m">{esc(names[idx[i]])}</text>')
            out.append(f'<text x="{x}" y="134" text-anchor="middle" class="m">{esc(meaning[i])}</text>')
        out.append(f'<text x="{ox + 50}" y="22" class="m">→ {esc(w["read"])}</text>')
        out.append(f'<text x="{ox + 175}" y="162" text-anchor="middle" font-weight="700">{d1} {d2} × {mult} = {esc(fmt_ohm(v))}</text>')
        return "".join(out)

    def grp(self, step, body, extra=""):
        a = f' data-step="{step}"' if step else ""
        return f"<g{a}{extra}>{body}</g>"

    def render(self, template):
        s, w, b = self.s, self.w, self.b
        self.straddled, self.wire_ends = set(), {}
        self.build()
        steps = s.get("steps", [])
        step_of = {}
        for i, st in enumerate(steps, 1):
            for it in st["do"]:
                if it in step_of:
                    err(f"{it} is placed in two steps ({step_of[it]} and {i})")
                step_of[it] = i
        for it in self.items:
            if steps and it not in step_of:
                err(f"{it} is in no step")
        for it in step_of:
            if it not in self.items:
                err(f'step {step_of[it]} places {it}, which is not a part id or wire "W<n>"')

        # pins in use, and the step that first uses each
        self.used_pins, self.pin_steps, self.live_nodes = set(), {}, set()
        for wid, (a, c) in self.wire_ends.items():
            for k in (a, c):
                if k[0] == "p":
                    self.used_pins.add(k)
                    st = step_of.get(wid, 0)
                    if k not in self.pin_steps or (st and st < self.pin_steps[k]):
                        self.pin_steps[k] = st
                else:
                    self.live_nodes.add(self.node(k))
        for key, names in self.members.items():
            if len(names) > 1:
                self.live_nodes.add(key)

        # nets
        nets = {}
        for key, names in self.members.items():
            nets.setdefault(self.find(key), []).extend(names)
        for names in nets.values():
            if len(names) == 1 and names[0] in self.must:
                warnings.append(f"{names[0]} connects to nothing")
        Safety(self, nets).run()

        # svg
        body = [self.svg_board(), self.svg_boards_off(), self.svg_straddlers()]
        placed = []
        wires = [kv for kv in self.items.items() if isinstance(kv[1], tuple)]
        for it, svg in wires + [(None, None)] + [kv for kv in self.items.items() if kv not in wires]:   # wires, numbers, then parts on top
            if it is None:
                body.append(self.svg_numbers())
                continue
            if isinstance(svg, tuple):
                g, mid, n = svg
                bx, by = self.badge_spot(mid, placed)
                svg = g + (f'<rect x="{bx - 10}" y="{by - 9}" width="20" height="16" rx="8" fill="var(--surface)" stroke="var(--muted)"/>'
                           f'<text x="{bx}" y="{by + 3}" text-anchor="middle" class="m" style="fill:var(--fg)">{n}</text>')
            faint = ' opacity=".4"' if self.find_spec(it).get("faint") else ""
            body.append(self.grp(step_of.get(it), svg, faint))
        body.append(self.svg_pin_labels())
        body.append(self.svg_straddler_labels())
        for r in s.get("rings", []):
            st = r.get("step") or step_of.get(r.get("on"))
            ring = []
            pts = []
            for ref in r["at"]:
                k, (x, y) = self.parse(ref, "ring")
                pts.append((x, y))
                ring.append(f'<circle cx="{x}" cy="{y}" r="8" fill="none" stroke="var(--hl)" stroke-width="2.5"/>')
            if r.get("text"):
                x, y = max(pts, key=lambda p: p[0])
                ring.append(self.label(x + 12, y - 10, w["longleg"] if r["text"] == "_long" else r["text"], cls="hl"))
            body.append(self.grp(st, "".join(ring)))
        aria = esc(s.get("aria", s.get("title", "")))
        svg = f'<svg viewBox="0 0 {self.width} {self.height}" role="img" aria-label="{aria}">{"".join(body)}</svg>'

        # steps, table, close-ups
        lis = "".join(f'<li data-step="{i}">{st.get("text") or self.step_text(st)}</li>' for i, st in enumerate(steps, 1))
        if any("_auto" in st for st in steps) and "before" not in s:
            s["before"] = w["before"]
        trs = []
        order = [it for st in steps for it in st["do"]] or list(self.rows)
        for it in order:
            if it in self.rows:
                cells = self.rows[it]
                trs.append(f'<tr data-step="{step_of.get(it, "")}"><td>{cells[0]}</td><td class="v">{cells[1]}</td><td class="v">{cells[2]}</td><td class="v">{cells[3]}</td></tr>'.replace(' data-step=""', ""))
        jump = {}
        for wd in s.get("wires", []):
            if wd.get("jumper"):
                j = self.jumper(wd)
                jump[j] = jump.get(j, 0) + 1
        jtxt = f'<p>{w["jumpers"].format(list=("、" if self.lang == "ja" else ", ").join(f"{esc(k)} × {v}" for k, v in jump.items()))}</p>' if jump else ""
        ex_n = b.rows // 2
        howto = s.get("howto") or w["howto"].format(ex=f"{ex_n}c", n=ex_n, l="c", end1=w["left"] if b.left1 else w["right"], near=b.near)
        values = []
        for pd in s.get("parts", []):
            if pd["kind"] == "resistor" and pd.get("value") and pd["value"] not in values:
                values.append(pd["value"])
        notes = "".join(f'<p class="note">{n}</p>' for n in s.get("notes", []))
        th = "".join(f"<th>{esc(t)}</th>" for t in w["th"])
        sec = [f'<header><div class="eyebrow">{esc(s.get("eyebrow", ""))}</div><h1>{esc(s["title"])}</h1>'
               f'<p class="lead">{s.get("lead", "")}</p></header>'
               + (f'<p class="note">{esc(w["unsafe"])}</p>' if s.get("as_built") and errors else ""),
               f'<section><h2>{esc(w["where"])}</h2><p>{howto}</p><div class="figure">{svg}</div>'
               + (f'<p>{s["before"]}</p>' if s.get("before") else "") + (f"<ol>{lis}</ol>" if lis else "") + "</section>",
               f'<section><h2>{esc(w["table"])}</h2><div class="tw"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>{jtxt}{notes}</section>']
        if values:
            cw = 370 * len(values)
            body = "".join(self.closeup(v, 370 * i) for i, v in enumerate(values))
            aria = esc(", ".join(fmt_ohm(v) for v in values))
            sec.append(f'<section><h2>{esc(w["colors"])}</h2><div class="figure"><svg viewBox="0 0 {cw} 176" role="img" aria-label="{aria}">{body}</svg></div></section>')
        if s.get("after"):
            sec.append(s["after"])

        page = re.sub(r'<div class="wrap">.*?\n</div>\n<script>', lambda _: '<div class="wrap">\n' + "\n".join(sec) + "\n</div>\n<script>", template, count=1, flags=re.S)
        attrs = f'lang="{esc(self.lang)}"' + (' dir="rtl"' if self.lang.split("-")[0] in RTL else "")
        page = page.replace('<html lang="en">', f"<html {attrs}>", 1)
        page = re.sub(r"<title>.*?</title>", f'<title>{esc(s.get("page_title", s["title"]))}</title>', page, count=1)
        ui = dict(w["ui"])
        page = re.sub(r"const UI = \{.*?\};", lambda _: "const UI = " + json.dumps(ui, ensure_ascii=False) + ";", page, count=1)
        return page, nets

    def jumper(self, d):
        j = d.get("jumper", "")
        return self.w[j[1:]] if j.startswith("_") else j

    def step_text(self, st):
        """Words for a step the planner made: a part with its holes, or a wire with both ends."""
        w = self.w
        kind, it = st["_auto"]
        if kind == "wire":
            r = self.rows[f"W{it}"]
            return w["t_wire"].format(n=it, a=f"<b>{r[1]}</b>", b=f"<b>{r[2]}</b>")
        d = self.find_spec(it)
        k = d["kind"]
        if k == "dip":
            return w["t_dip"].format(id=it, pin1=f'<b>{d["pin1"]}</b>')
        if k == "switch":
            return w["t_switch"].format(id=it, holes="<b>" + "・".join(h for pair in d["pairs"] for h in pair) + "</b>")
        legs = d.get("legs", [])
        if k in TWO_LEG and len(legs) == 2:
            a, b = (f"<b>{self.name(self.parse(h, it)[0])}</b>" for h in legs)
            if k == "led":
                return w["t_led"].format(id=it, a=a, b=b)
            if k in ("buzzer", "diode") or d.get("polar"):
                return w["t_polar"].format(id=it, a=a, b=b)
            t = w["t_part2"].format(id=it, value=fmt_ohm(d.get("value", "")) if k == "resistor" else d.get("value", ""), a=a, b=b)
            return t.replace("（）", "").replace(" ()", "")
        return w["t_multi"].format(id=it, legs="、".join(f"{esc(nm)} <b>{h}</b>" for nm, h in legs) if self.lang == "ja" else ", ".join(f"{esc(nm)} <b>{h}</b>" for nm, h in legs))

    def find_spec(self, it):
        for pd in self.s.get("parts", []):
            if pd["id"] == it:
                return pd
        for wd in self.s.get("wires", []):
            if f'W{wd["n"]}' == it:
                return wd
        return {}

    def label(self, x, y, text, anchor="start", cls=None):
        """A text label moved to the nearest spot clear of other labels, badges and number rows."""
        w = sum(13 if ord(c) > 0x2000 else 7.5 for c in str(text))
        left = {"start": 0, "middle": -w / 2, "end": -w}[anchor]
        for dy in (0, -14, 14, -28, 28, -42):
            for dx in (0, 10, -10, 24, -24):
                bx, by = x + dx + left, y + dy - 11
                if any(abs(y + dy - 4 - ny) < 11 for ny in (self.b.num_top, self.b.num_mid, self.b.num_bot)):
                    continue
                if all(bx + w < ox or ox + ow < bx or by + 14 < oy or oy + oh < by for ox, oy, ow, oh in self.boxes):
                    self.boxes.append((bx, by, w, 14))
                    attr = f' class="{cls}"' if cls else ' font-weight="700"'
                    return f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}"{attr}>{esc(str(text))}</text>'
        return ""                                               # no clear spot: the table and the step text name it

    def badge_spot(self, mid, placed):
        x, y = mid
        b = self.b
        avoid_y = [b.num_top - 4, b.num_bot - 4, b.num_mid - 4]
        for dy in (0, -14, 14, -28, 28, -42, 42):
            for dx in (0, 16, -16, 32, -32):
                cx, cy = x + dx, y + dy
                if any(abs(cy - ay) < 12 for ay in avoid_y):
                    continue
                if all(abs(cx - px) > 22 or abs(cy - py) > 18 for px, py in placed) and \
                        all(cx + 10 < ox or ox + ow < cx - 10 or cy + 7 < oy or oy + oh < cy - 9 for ox, oy, ow, oh in self.boxes):
                    placed.append((cx, cy))
                    return cx, cy
        placed.append((x, y))
        return x, y


# ---------- electrical checks ----------
# Worked out from the nets the page really draws. Only rules that need no datasheet beyond the spec's facts.

def fmt_volts(vs):
    return " and ".join(f"{v:g} V" for v in sorted(vs))


def label(pin):
    return f"{pin[0]}.{pin[1]}"


class Safety:
    def __init__(self, page, nets):
        self.page, self.nets = page, nets
        self.parts = {p["id"]: p for p in page.s.get("parts", [])}
        self.leg, self.pins = {}, {}                            # "R1.1" -> net; net -> [(board, pin)]
        self.edges, self.load = {}, {}                          # net -> [(net, ohms)]; pin -> [(mA, part)]
        for key, names in page.members.items():
            for nm in names:
                who, _, rest = nm.partition(".")
                if who in page.boards:
                    self.pins.setdefault(page.find(key), []).append((who, rest))
                elif who in self.parts:
                    self.leg[f"{who}.{rest.split()[-1]}"] = page.find(key)
        for pid, p in self.parts.items():                       # two-leg parts placed with named legs: 1 is the anode side, as drawn
            if p["kind"] in TWO_LEG:
                for i, l in enumerate(p.get("legs", [])):
                    if isinstance(l, list):
                        order = 2 if l[0] in CATHODE_LEG else 1 if l[0] in ANODE_LEG else i + 1
                        self.leg[f"{pid}.{order}"] = self.leg[f"{pid}.{l[0]}"]

    def facts(self, pin):
        return facts_of(self.page.boards[pin[0]])

    def volts(self, net):
        """{pin: volts} for the supply and GND pins on a net."""
        out = {}
        for pin in self.pins.get(net, []):
            power = self.facts(pin)["power"]
            if GND_PIN.match(pin[1]):
                out[pin] = 0
            elif pin[1] in power:
                out[pin] = power[pin[1]]
        return out

    def known(self, net):
        return {v for v in self.volts(net).values() if v is not None}

    def signals(self, net):
        return [p for p in self.pins.get(net, []) if not GND_PIN.match(p[1]) and p[1] not in self.facts(p)["power"]]

    def logic(self, pin):
        return self.facts(pin)["logic_v"]

    def size(self, net):
        return sum(len(names) for key, names in self.page.members.items() if self.page.find(key) == net)

    def two_legs(self, pid):
        return self.leg.get(f"{pid}.1"), self.leg.get(f"{pid}.2")

    def run(self):
        self.check_nets()
        self.check_rails()
        self.check_switches()
        self.build_edges()
        for pid, p in self.parts.items():
            a, c = self.two_legs(pid)
            if p["kind"] in TWO_LEG + ("switch",) and a is not None and a == c and pid not in self.page.reported:
                err(f"{pid}: both legs are on one net ({', '.join(dict.fromkeys(self.nets[a]))}), so it is shorted out")
            if p["kind"] == "led" and a is not None and c is not None and a != c:
                self.check_led(pid, p, a, c)
            if p["kind"] == "rgb":
                self.check_rgb(pid, p)
            if p["kind"] == "pot":
                self.check_pot(pid, p)
            if p["kind"] in ("cap", "diode") and a is not None and c is not None:
                self.check_polarity(pid, p, a, c)
            self.check_draw(pid, p)
            if p["kind"] in ("module", "dip", "part"):
                self.check_powered(pid, p)
        self.check_pin_loads()

    def check_nets(self):
        for net in {self.page.find(k) for k in self.page.members}:
            v, known, used = self.volts(net), self.known(net), self.size(net) > 1
            names = ", ".join(label(p) for p in v)
            if len(known) > 1:
                err(f"{names} are joined: {fmt_volts(known)} shorted together")
            if None in v.values() and used:
                warnings.append(f"{names}: a power input with no fixed voltage; confirm the supply against the board's datasheet")
            if len({p[0] for p, x in v.items() if x}) > 1:
                warnings.append(f"{names}: two boards' supplies are tied together; one can back-feed the other")
            for pin in self.pins.get(net, []) if used else ():
                f = self.facts(pin)
                if SUPPLY_LEG.match(pin[1]) and pin[1] not in f["power"]:
                    err(f"{label(pin)} looks like a supply pin, but power does not give its voltage: take it from the board's datasheet")
                if pin[1] in f.get("forbid", {}):
                    err(f"{label(pin)}: do not use it: {f['forbid'][pin[1]]}")
                if pin[1] in f.get("avoid", {}):
                    warnings.append(f"{label(pin)}: {f['avoid'][pin[1]]}; pick another pin if you can")
            for p in self.signals(net):
                hi = max(known | {self.logic(q) for q in self.signals(net)})
                if hi > self.logic(p):
                    err(f"{label(p)} is a {self.logic(p):g} V pin, and this net has {hi:g} V on it: it can damage the pin (use a level shifter or a divider)")
                elif known:
                    warnings.append(f"{label(p)} is tied straight to {fmt_volts(known)}: driving it as an output the other way is a short")

    def check_rails(self):
        for node in list(self.page.parent):
            if node[0] == "rail":
                vs = self.known(self.page.find(node))
                if node[2] == "-" and any(vs):
                    err(f"the − rail has {fmt_volts(vs)} on it")
                if node[2] == "+" and 0 in vs:
                    err("the + rail is joined to GND")

    def check_switches(self):
        """Join the nets of every switch, as if all were pressed at once."""
        groups = []
        for pid, p in self.parts.items():
            a, c = self.two_legs(pid)
            if p["kind"] == "switch" and a is not None and c is not None and a != c:
                touching = [g for g in groups if g["nets"] & {a, c}]
                groups = [g for g in groups if g not in touching]
                groups.append({"nets": {a, c}.union(*(g["nets"] for g in touching)), "ids": sum((g["ids"] for g in touching), []) + [pid]})
        for g in groups:
            ids = ", ".join(g["ids"])
            verb = "pressing it" if len(g["ids"]) == 1 else "pressing them all"
            both = set().union(*(self.known(n) for n in g["nets"]))
            if len(both) > 1:
                err(f"{ids}: {verb} joins {fmt_volts(both)}: a short")
            for q in (q for n in g["nets"] for q in self.signals(n)):
                if both and max(both) > self.logic(q):
                    err(f"{ids}: {verb} puts {max(both):g} V on {label(q)}, a {self.logic(q):g} V pin")

    def build_edges(self):
        for pid, p in self.parts.items():
            a, c = self.two_legs(pid)
            if a is None or c is None or a == c:
                continue
            ohm = ohms(p.get("value", "")) if p["kind"] == "resistor" else 0 if p["kind"] == "switch" else None
            if ohm is None:
                continue
            self.edges.setdefault(a, []).append((c, ohm))
            self.edges.setdefault(c, []).append((a, ohm))
            for x, y in ((a, c), (c, a)) if p["kind"] == "resistor" else ():
                for q in self.signals(x):
                    if self.known(y) and max(self.known(y)) > self.logic(q):
                        warnings.append(f"{pid} pulls {label(q)}, a {self.logic(q):g} V pin, up to {max(self.known(y)):g} V: fine only as part of a divider that you have worked out")

    def reach(self, start, cut):
        """net -> lowest series ohms, not crossing the part itself."""
        dist, todo = {start: 0}, [start]
        while todo:
            n = todo.pop()
            for m, r in self.edges.get(n, []):
                if m != cut and dist[n] + r < dist.get(m, math.inf):
                    dist[m] = dist[n] + r
                    todo.append(m)
        return dist

    def check_led(self, pid, p, anode, cathode):
        up, down = self.reach(anode, cathode), self.reach(cathode, anode)
        src = [(r, q) for n, r in up.items() for q in ([(x, v) for x, v in self.volts(n).items() if v] + [(s, self.logic(s)) for s in self.signals(n)])]
        snk = [(r, q) for n, r in down.items() for q in ([x for x, v in self.volts(n).items() if v == 0] + self.signals(n))]
        if not src or not snk:
            if any(0 in self.known(n) for n in up) and not src:
                err(f"{pid} is backwards: its + leg goes to GND")
            elif any(any(self.known(n)) for n in down) and not snk:
                err(f"{pid} is backwards: its − leg goes to a supply")
            else:
                warnings.append(f"{pid}: no complete path from a supply or pin to GND or a pin, so its current was not checked")
            return
        low = {q for n in down for q in self.signals(n)}
        for hi, q in {(v, q) for _, (_, v) in src for q in low if v > self.logic(q)}:
            err(f"{pid} joins {hi:g} V to {label(q)}, a {self.logic(q):g} V pin: when the pin is not driven low it can be pushed above its limit")
        vf = p.get("vf", VF_LOW.get(p.get("color", "red"), 1.8))
        (ra, (who, v)), (rc, sink) = max(((s, t) for s in src for t in snk), key=lambda st: (st[0][1][1] - vf) / max(st[0][0] + st[1][0], 1e-9))
        if ra + rc == 0:
            err(f"{pid} has no resistor between {label(who)} ({v:g} V) and {label(sink)}: the current is limited by nothing")
            return
        ma = (v - vf) / (ra + rc) * 1000
        limit = p.get("max_ma", LED_STOP_MA)
        checks.append(f"{pid}: about {ma:.1f} mA ({fmt_ohm(ra + rc)}, {v:g} V from {label(who)}, Vf {vf:g} V{'' if 'vf' in p else ' assumed'}, limit {limit:g} mA{'' if 'max_ma' in p else ' assumed'})")
        if ma <= 0:
            warnings.append(f"{pid}: {v:g} V is not above its Vf of {vf:g} V, so it may not light")
        if ma > limit:
            err(f"{pid}: about {ma:.0f} mA, over {limit:g} mA: use a bigger resistor")
        elif ma > LED_WARN_MA and "max_ma" not in p:
            warnings.append(f"{pid}: about {ma:.0f} mA, over the usual {LED_WARN_MA} mA; check the LED's datasheet")
        for q in (who, sink):
            if q in low or q in {s for _, (s, _) in src if s[1] not in self.facts(s)["power"]}:
                self.load.setdefault(q, []).append((max(ma, 0), pid))

    def check_rgb(self, pid, p):
        for l in p.get("legs", []):
            n = self.leg.get(f"{pid}.{l[0]}") if isinstance(l, list) else None
            if n is not None and not RGB_COMMON.match(l[0]) and (self.signals(n) or any(self.known(n))):
                err(f"{pid}.{l[0]} has no resistor: give each colour its own")

    def check_pot(self, pid, p):
        ends = [l[0] if isinstance(l, list) else str(i + 1) for i, l in enumerate(p.get("legs", []))]
        if len(ends) == 3 and pid not in self.page.reported:
            w = self.known(self.leg.get(f"{pid}.{ends[1]}"))
            if w and any(self.known(self.leg.get(f"{pid}.{e}")) - w for e in (ends[0], ends[2])):
                err(f"{pid}: the middle leg (wiper) is on a supply: at one end of its travel it shorts the supply")

    def check_polarity(self, pid, p, plus, minus):
        a, c = self.known(plus), self.known(minus)
        if a and c and p["kind"] == "cap" and p.get("polar") and max(a) < min(c):
            err(f"{pid} is backwards: its + leg is at {fmt_volts(a)}, its − leg at {fmt_volts(c)}")
        if a and c and p["kind"] == "diode" and min(a) > max(c):
            err(f"{pid} conducts straight across the supply: anode {fmt_volts(a)}, cathode {fmt_volts(c)}")

    def check_draw(self, pid, p):
        on_pins = [q for k, n in self.leg.items() if k.startswith(pid + ".") for q in self.signals(n)]
        if p.get("draw_ma") is not None:
            for q in on_pins:
                self.load.setdefault(q, []).append((p["draw_ma"], pid))
        elif p["kind"] == "buzzer" and on_pins:
            warnings.append(f"{pid}: a coil buzzer (tens of ohms) can overload a pin; read its datasheet and give draw_ma")

    def check_pin_loads(self):
        for q, items in self.load.items():
            limits = self.facts(q).get("pin_ma")
            total = sum(m for m, _ in items)
            who = ", ".join(i for _, i in items)
            if not limits:
                warnings.append(f"{label(q)}: its current limit is not given, so {total:.1f} mA for {who} was not checked")
            elif total > limits[1]:
                err(f"{label(q)}: {total:.1f} mA for {who} is over the pin's {limits[1]} mA limit")
            elif total > limits[0]:
                warnings.append(f"{label(q)}: {total:.1f} mA for {who} is over the pin's {limits[0]} mA working level")

    def check_powered(self, pid, p):
        """A module, chip or other part: its supply range, its polarity, and the levels on its signal pins."""
        mine = {k.split(".", 1)[1]: n for k, n in self.leg.items() if k.startswith(pid + ".")}
        supply = p.get("supply", [m for m in mine if SUPPLY_LEG.match(m)])
        vcc = p.get("vcc")
        if supply and not vcc:
            err(f"{pid}: its supply range is not given: read its datasheet and set vcc [min, max], or ask the user")
        if not supply and "supply" not in p:
            msg = f"{pid}: no leg is recognised as its supply, so its voltages were not checked: name it in supply, or set supply [] if it has none"
            err(msg) if p["kind"] in ("module", "dip") else warnings.append(msg)
        fed = max((v for m in supply for v in self.known(mine[m])), default=None)
        for m in supply:
            for v in self.known(mine[m]):
                if v == 0:
                    err(f"{pid}.{m} is on GND: the part is powered backwards")
                elif vcc and v > vcc[1]:
                    err(f"{pid}.{m} gets {v:g} V, over its {vcc[1]:g} V maximum")
                elif vcc and v < vcc[0]:
                    warnings.append(f"{pid}.{m} gets {v:g} V, under its {vcc[0]:g} V minimum, so it may not work")
        io_max = p.get("io_max", vcc[1] if vcc else None)
        for m, n in mine.items():
            if m in supply:
                continue
            if GND_PIN.match(m):
                if any(self.known(n)):
                    err(f"{pid}.{m} is on {max(self.known(n)):g} V: the part is powered backwards")
                continue
            for q in self.signals(n):
                out = p.get("out_v", {}).get(m)
                if io_max is not None and self.logic(q) > io_max:
                    err(f"{label(q)} drives {pid}.{m} at {self.logic(q):g} V, over its {io_max:g} V maximum (use a level shifter)")
                if out is not None and out > self.logic(q):
                    err(f"{pid}.{m} outputs {out:g} V into {label(q)}, a {self.logic(q):g} V pin (use a level shifter or a divider)")
                if out is None and fed is not None and fed > self.logic(q):
                    warnings.append(f"{pid}.{m} is powered at {fed:g} V and wired straight to {label(q)}, a {self.logic(q):g} V pin: confirm its output level and set out_v")
            if io_max is not None and self.known(n) and max(self.known(n)) > io_max:
                err(f"{pid}.{m} has {max(self.known(n)):g} V on it, over its {io_max:g} V maximum")


def usb_port(edge, cy, side, h, depth):
    """A metal USB socket sticking out of a board's edge, labelled, so the user can match the board's direction."""
    sx = edge - depth + 6 if side == "left" else edge - 6
    tx = edge + 8 if side == "left" else edge - 8              # the word sits inside the board, never cut off by the figure's edge
    return (f'<rect x="{sx}" y="{cy - h / 2}" width="{depth}" height="{h}" rx="3" fill="#c3c9cf" stroke="#6b747d" stroke-width="1.2"/>'
            f'<rect x="{sx + 4}" y="{cy - h / 2 + 5}" width="{depth - 8}" height="{h - 10}" rx="2" fill="#4a5058"/>'
            f'<text x="{tx}" y="{cy + 4}" class="m" text-anchor="{"start" if side == "left" else "end"}" style="font-weight:700;fill:var(--fg)">USB</text>')


# ---------- resistor values ----------

def ohms(v):
    m = re.fullmatch(r"\s*(\d+\.?\d*)\s*([kKmM]?)\s*(Ω|ohms?|R)?\s*", str(v))
    if not m:                                                   # "4k7" must not read as 4 kΩ
        return None
    return float(m[1]) * {"": 1, "k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6}[m[2]]


def bands_of(v):
    o = ohms(v)
    if not o:
        err(f"cannot read resistor value '{v}' (write 220, 4.7k, 1M)")
        return 0, 0, 0
    ex = math.floor(math.log10(o)) - 1
    two = round(o / 10 ** ex)
    if two >= 100:
        ex, two = ex + 1, round(o / 10 ** (ex + 1))
    return two // 10, two % 10, ex


def band_colors(v):
    d1, d2, ex = bands_of(v)
    m = f"var(--b{ex})" if ex >= 0 else ("var(--b-gold)" if ex == -1 else "var(--b-silver)")
    return [f"var(--b{d1})", f"var(--b{d2})", m, "var(--b-gold)"]


def fmt_ohm(v):
    o = ohms(v)
    if o is None:
        return str(v)
    for div, suf in ((1e6, "M"), (1e3, "k"), (1, "")):
        if o >= div:
            return f"{o / div:g}{suf}Ω"
    return f"{o:g}Ω"


# ---------- automatic placement ----------
# A spec may list only the parts and what connects to what ("connect"); plan() then picks
# every hole, adds the wires and the steps. Parts that already have holes are kept as they are.

AXIAL = ("resistor", "diode")
SPAN = {"led": 1, "cap": 1, "buzzer": 3}


def leg_names(p):
    k = p["kind"]
    if k in ("led", "buzzer", "diode") or (k == "cap" and p.get("polar")):
        return ["+", "-"]
    if k == "dip" and "names" not in p:
        return [str(i + 1) for i in range(p["pins"])]
    if k in ("resistor", "cap", "switch"):
        return ["1", "2"]
    if k == "pot":
        return p.get("names", ["1", "W", "2"])
    return p["names"]


def plan(spec):
    """Fill in holes, wires and steps. Try with an empty number between parts first, then packed."""
    if not spec.get("connect"):
        return spec
    import copy
    for gap in (1, 0):
        mark = len(errors)
        out = _plan(copy.deepcopy(spec), gap)
        room = [e for e in errors[mark:] if "no room" in e]
        if not room or gap == 0:
            return out
        del errors[mark:]
    return out


def _plan(spec, gap):
    parts = spec.get("parts", [])
    b = Board(spec["board"])
    far_l, near_l = list(b.top5), list(reversed(b.bot5))       # edge first, gap last
    rows = b.rows
    parent = {}

    def f(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            x = parent[x]
        return x
    for group in spec["connect"]:
        for e in group[1:]:
            parent[f(e)] = f(group[0])
    nets = {}
    for e in list(parent):
        nets.setdefault(f(e), []).append(e)
    rail_of = {}                                                # net root -> "+" / "-"
    for root, eps in nets.items():
        for e in eps:
            if e in ("+", "-", "GND"):
                rail_of[root] = "-" if e in ("-", "GND") else "+"

    def net(ep):
        return f(ep) if ep in parent else None

    used, busy, strip = set(), {}, {}                          # holes; number -> halves with parts; (n, half) -> net
    for d in spec.get("boards", []):
        if d.get("kind") == "offboard":
            continue
        lo, hi = d["span"]
        for n in range(lo, hi + 1):
            busy[n] = {"near", "far"}
        for letter, names in d["pins"].items():
            half = b.side_of(letter)
            for i, nm in enumerate(names):
                used.add(f"{lo + i}{letter}")
                root = net(f'{d["id"]}.{nm}')
                if root is not None and (lo + i, half) not in strip:
                    strip[(lo + i, half)] = root
        ys = sorted(b.ly_order(l) for l in d["pins"])
        for n in range(lo, hi + 1):
            for l in b.top5 + b.bot5:
                if ys[0] < b.ly_order(l) < ys[-1]:
                    used.add(f"{n}{l}")
    # straddler pins named more than once (GND): any one of them serves
    for d in spec.get("boards", []):
        if d.get("kind") == "offboard":
            continue
        for root, eps in nets.items():
            for e in eps:
                if e.split(".")[0] == d["id"] and e.split(".", 1)[1] in ("GND",):
                    pass

    def free_run(k, halves):
        for n in range(1 + gap, rows - k + 2):
            if all(not (busy.get(m, set()) & halves) for m in range(n - gap, n + k + gap) if 1 <= m <= rows):
                for m in range(n, n + k):
                    busy.setdefault(m, set()).update(halves)
                return n
        err(f"no room left on the board for {pid}; say so in chat and suggest a bigger board")
        return None

    placed = []                                                 # part ids in order
    pin_half = {}                                               # net -> the half its board pin is on
    for d in spec.get("boards", []):
        if d.get("kind") == "offboard":
            for h in d["headers"]:
                for nm in h["pins"]:
                    r = net(f'{d["id"]}.{nm}') if nm else None
                    if r is not None:
                        pin_half.setdefault(r, d.get("side", "far"))
        else:
            for letter, names in d["pins"].items():
                for nm in names:
                    r = net(f'{d["id"]}.{nm}')
                    if r is not None:
                        pin_half.setdefault(r, b.side_of(letter))
    flip = {"near": "far", "far": "near"}

    def pref(p):
        """The half that keeps this part's wires short: its board pins' side (through a resistor, the other side)."""
        votes = []
        for nm in leg_names(p):
            r = net(f'{p["id"]}.{nm}')
            if r is None or r in rail_of:
                continue
            if r in pin_half:
                votes.append(pin_half[r])
            for q in parts:
                if q["kind"] in AXIAL and q is not p:
                    qn = [net(f'{q["id"]}.{x}') for x in leg_names(q)]
                    if r in qn and qn[1 - qn.index(r)] in pin_half:
                        votes.append(flip[pin_half[qn[1 - qn.index(r)]]])
        return "near" if votes.count("near") > votes.count("far") else "far"
    order = sorted([p for p in parts if not any(k in p for k in ("legs", "pairs", "pin1"))],
                   key=lambda p: {"dip": 0, "module": 1, "rgb": 1, "pot": 1, "part": 1, "switch": 2}.get(p["kind"], 3 if p["kind"] in AXIAL else 4))
    queue = list(order)
    while queue:
        p = queue.pop(0)
        pid, kind, names = p["id"], p["kind"], leg_names(p)
        roots = [net(f"{pid}.{nm}") for nm in names]
        if kind == "dip":
            half_n = p["pins"] // 2
            n = free_run(half_n, {"near", "far"})
            if n is None:
                continue
            p["pin1"] = f"{n}{near_l[4]}"
            for i, nm in enumerate(names):
                m, half = (n + i, "near") if i < half_n else (n + p["pins"] - 1 - i, "far")
                used.add(f"{m}{(near_l if half == 'near' else far_l)[4]}")
                if roots[i] is not None:
                    strip[(m, half)] = roots[i]
        elif kind == "switch":                                  # in one half, legs b–e (or f–i): the joined pair in one strip
            best = None
            for half in (pref(p), flip[pref(p)]):
                for n in range(1 + gap, rows - 1):
                    if all(half not in busy.get(m, set()) for m in range(n - gap, n + 3 + gap) if 1 <= m <= rows):
                        if best is None:
                            best = (n, half)
                        break
            if best is None:
                err(f"no room left on the board for {pid}; say so in chat and suggest a bigger board")
                continue
            n, half = best
            ls = near_l if half == "near" else far_l
            for m in range(n, n + 3):
                busy.setdefault(m, set()).add(half)
            p["pairs"] = [[f"{n}{ls[1]}", f"{n}{ls[4]}"], [f"{n + 2}{ls[1]}", f"{n + 2}{ls[4]}"]]
            for m, root in ((n, roots[0]), (n + 2, roots[1])):
                used.update({f"{m}{ls[1]}", f"{m}{ls[4]}"})
                strip[(m, half)] = root
        elif kind in AXIAL:
            spot = None
            for i, root in enumerate(roots):
                for (m, half), r in strip.items():
                    other = "near" if half == "far" else "far"
                    if r == root and root is not None and other not in busy.get(m, set()) and (m, other) not in strip:
                        spot = (m, half, i)
                        break
                if spot:
                    break
            if spot:
                m, half, i = spot
                other = "near" if half == "far" else "far"
                busy.setdefault(m, set()).add(other)
            else:
                m = free_run(1, {"near", "far"})
                if m is None:
                    continue
                i = next((j for j, r in enumerate(roots) if r in pin_half), 0)   # the leg on a board pin goes to that pin's side
                half = pin_half.get(roots[i], "near")
                other = flip[half]
            lt = {"near": near_l[3], "far": far_l[3]}
            holes = [None, None]
            holes[i] = f"{m}{lt[half]}"
            holes[1 - i] = f"{m}{lt[other]}"
            p["legs"] = holes
            used.update(holes)
            strip[(m, half)] = roots[i]
            strip[(m, other)] = roots[1 - i]
        elif kind in SPAN:
            span = SPAN[kind]
            a_root, c_root = roots
            rail = rail_of.get(c_root)
            n, h = None, pref(p)
            for (m, half), r in strip.items():
                ls = near_l if half == "near" else far_l
                if r == a_root and a_root is not None and f"{m}{ls[0]}" not in used and rail:
                    n, h = m, half
                    break
            ls, side = (near_l, "N") if h == "near" else (far_l, "F")
            if n is None:
                n = free_run(1 if rail else span + 1, {h})
                if n is None:
                    continue
                strip[(n, h)] = a_root
            busy.setdefault(n, set()).add(h)
            if rail:                                            # the − (or +) leg goes straight into the rail
                p["legs"] = [f"{n}{ls[0]}", f"{side}{rail}{n}"]
                used.update(p["legs"])
            else:
                p["legs"] = [f"{n}{ls[1]}", f"{n + span}{ls[1]}"]
                used.update(p["legs"])
                for m in range(n, n + span + 1):
                    busy.setdefault(m, set()).add(h)
                strip[(n + span, h)] = c_root
        else:                                                   # rgb, pot, module, part: a row of legs
            h = pref(p)
            ls = near_l if h == "near" else far_l
            n = free_run(len(names), {h})
            if n is None:
                continue
            letter = ls[4] if kind == "module" else ls[1]
            p["legs"] = [[nm, f"{n + i}{letter}"] for i, nm in enumerate(names)]
            for i, nm in enumerate(names):
                used.add(f"{n + i}{letter}")
                strip[(n + i, h)] = roots[i]
        placed.append(pid)
        p["_auto"] = True
        # resistors on this part's legs go next, so they can share its strips
        mine = {r for r in roots if r is not None and r not in rail_of}
        partners = [q for q in queue if q["kind"] in AXIAL and any(net(f'{q["id"]}.{nm}') in mine for nm in leg_names(q))]
        queue = partners + [q for q in queue if q not in partners]

    # where each part leg ended up
    leg_hole = {}
    for p in parts:
        if p.get("pairs"):
            leg_hole[f'{p["id"]}.1'], leg_hole[f'{p["id"]}.2'] = p["pairs"][0][0], p["pairs"][1][0]
        if p.get("pin1"):
            m = HOLE.match(p["pin1"])
            n0, l1 = int(m[1]), m[2]
            l2 = {"e": "f", "f": "e"}.get(l1, l1)
            for i, nm in enumerate(p.get("names", [])):
                half = p["pins"] // 2
                leg_hole[f'{p["id"]}.{nm}'] = f"{n0 + i}{l1}" if i < half else f'{n0 + p["pins"] - 1 - i}{l2}'
        nm = leg_names(p) if p["kind"] not in ("dip",) else None
        if p.get("legs"):
            for i, l in enumerate(p["legs"]):
                name, hole = (l if isinstance(l, list) else (nm[i] if nm else str(i + 1), l))
                leg_hole[f'{p["id"]}.{name}'] = hole

    def strip_of(hole):
        m = HOLE.match(hole)
        return (int(m[1]), b.side_of(m[2])) if m else None

    def free_hole(n, half, prefer=None, gap_first=False):
        ls = near_l if half == "near" else far_l
        ls = ls[::-1] if gap_first else ls
        for l in ([prefer] if prefer in ls else []) + ls:
            h = f"{n}{l}"
            if h not in used:
                used.add(h)
                return h
        err(f"strip {n} ({half}) has no free hole left for a wire")
        return f"{n}{(near_l if half == 'near' else far_l)[0]}"

    def rail_hole(half, sign, n):
        side = "F" if half == "far" else "N"
        for d in range(0, rows):
            for m in (n + d, n - d):
                h = f"{side}{sign}{m}"
                if 1 <= m <= rows and h not in used:
                    used.add(h)
                    return h
        return f"{side}{sign}{n}"

    off = {d["id"]: d for d in spec.get("boards", []) if d.get("kind") == "offboard"}
    strad = {d["id"]: d for d in spec.get("boards", []) if d.get("kind") != "offboard"}

    def pin_number(ep):
        bid, pin = ep.split(".", 1)
        d = off[bid]
        want, nth = (pin.split("#") + ["1"])[:2]
        k = 0
        for h in d["headers"]:
            n = h["at"]
            for nm in h["pins"]:
                if nm == want:
                    k += 1
                    if k == int(nth):
                        return n
                n += 1
        return 1

    wires, signal_i = [], 0
    colors = ["green", "yellow", "orange", "blue"]
    for root, eps in nets.items():
        terms, label = [], ""
        rail = rail_of.get(root)
        rail_halves = set()
        for e in eps:
            if e in ("+", "-", "GND"):
                continue
            bid = e.split(".")[0]
            if bid in off:
                terms.append(("pin", e, pin_number(e)))
                label = label or e.split(".", 1)[1].split("#")[0]
            elif bid in strad:
                d = strad[bid]
                pin = e.split(".", 1)[1]
                want, _, nth = pin.partition("#")
                spots = [(d["span"][0] + i, b.side_of(l)) for l, names in d["pins"].items() for i, nm in enumerate(names) if nm == want]
                terms.append(("strip", spots[int(nth or 1) - 1]))
                label = label or want
            elif e in leg_hole:
                h = leg_hole[e]
                st = strip_of(h)
                if st:
                    if ("strip", st) not in terms:
                        terms.append(("strip", st))
                else:
                    rail_halves.add("far" if h[0] == "F" else "near")
        if rail:
            col = "black" if rail == "-" else "red"
            for t in terms:
                if t[0] == "strip":
                    n, half = t[1]
                    wires.append({"from": free_hole(n, half), "to": rail_hole(half, rail, n), "color": col, "label": "GND" if rail == "-" else "+", "_net": root})
                    rail_halves.add(half)
                else:
                    wires.append({"from": t[1], "to": rail_hole("far" if off[t[1].split(".")[0]].get("side", "far") == "far" else "near", rail, t[2]), "color": col, "label": t[1].split(".", 1)[1].split("#")[0], "_net": root})
                    rail_halves.add("far" if off[t[1].split(".")[0]].get("side", "far") == "far" else "near")
            if rail_halves == {"far", "near"}:
                k = rows
                while k > 1 and (f"F{rail}{k}" in used or f"N{rail}{k}" in used):
                    k -= 1
                wires.append({"from": rail_hole("near", rail, k), "to": rail_hole("far", rail, k), "color": col, "label": "GND" if rail == "-" else "+", "_net": root})
            continue
        terms.sort(key=lambda t: t[2] if t[0] == "pin" else t[1][0])
        col = colors[signal_i % len(colors)]
        signal_i += 1
        ends = [t[1] if t[0] == "pin" else None for t in terms]
        for a, c in zip(terms, terms[1:]):
            # from the gap side to the edge side, so wires that run side by side step down without crossing
            fa = a[1] if a[0] == "pin" else free_hole(*a[1], gap_first=True)
            fc = c[1] if c[0] == "pin" else free_hole(*c[1], gap_first=a[0] == "strip" and a[1][1] != c[1][1])
            wires.append({"from": fa, "to": fc, "color": col, "label": label, "_net": root})
    start = max([w["n"] for w in spec.get("wires", [])], default=0)
    for i, w in enumerate(wires, start + 1):
        w["n"] = i
        dx = abs(_num(w["from"], pin_number) - _num(w["to"], pin_number))
        w["jumper"] = "_long" if "." in w["from"] + w["to"] or dx > 15 else ("_short" if dx <= 5 else "_mid")
    spec.setdefault("wires", []).extend(wires)

    # steps: wires that only feed the rails first, then each part followed by the wires it needs
    if not spec.get("steps"):
        part_of = {}
        for pid in placed:
            for e, h in leg_hole.items():
                if e.split(".")[0] == pid:
                    part_of.setdefault(h, pid)
        rank = {pid: i for i, pid in enumerate(placed)}
        later = {}
        first = []
        for w in wires:
            ids = []
            for end in (w["from"], w["to"]):
                st = strip_of(end) if HOLE.match(end) else None
                for h, pid in part_of.items():
                    if st and strip_of(h) == st or h == end:
                        ids.append(pid)
            if ids:
                later.setdefault(max(ids, key=rank.get), []).append(w["n"])
            else:
                first.append(w["n"])
        steps = [{"do": [f"W{n}"], "_auto": ("wire", n)} for n in first]
        for pid in placed:
            steps.append({"do": [pid], "_auto": ("part", pid)})
            steps += [{"do": [f"W{n}"], "_auto": ("wire", n)} for n in later.get(pid, [])]
        spec["steps"] = steps
    spec.setdefault("rings", [])
    first = True
    for p in parts:
        if p.get("_auto") and p["kind"] == "led":                # every long leg ringed, the words once
            spec["rings"].append({"at": [p["legs"][0]], "text": "_long" if first else "", "on": p["id"]})
            first = False
    return spec


def _num(end, pin_number):
    m = HOLE.match(end) or RAIL.match(end)
    if m:
        return int(m[1] if HOLE.match(end) else m[3])
    return pin_number(end)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    nets, out, as_built = {}, None, False
    try:
        spec = json.loads(Path(sys.argv[1]).read_text())
        as_built = bool(spec.get("as_built"))
        validate(spec)
        if not fatal:
            template = (Path(__file__).parent / "template.html").read_text()
            out, nets = Page(plan(spec)).render(template)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as e:
        stop(f"the spec is malformed: {e!r} (see The spec in SKILL.md)")
    if out and not fatal and (as_built or not errors):
        Path(sys.argv[2]).write_text(out)
        print(f"wrote {sys.argv[2]}")
    else:
        print(f"no page written; anything already at {sys.argv[2]} is out of date")
    print("nets:")
    for names in sorted(nets.values(), key=lambda n: sorted(n)[0]):
        if len(names) > 1:
            print("  " + ", ".join(dict.fromkeys(names)))
    for c in checks:
        print("checked: " + c)
    print("not checked by this script: " + NOT_CHECKED)
    for w_ in warnings:
        print("warning: " + w_)
    for e in errors:
        print("ERROR: " + e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
