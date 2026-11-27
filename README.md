# Vernier Calipers

A compact, always-on-top caliper calculator for Windows and Linux. It uses
Python's standard-library Tkinter GUI and requires no third-party packages.

Run it with:

```sh
python calipers.py
```

Each Inner, Outer, and Probe tab has a Reading page and its own Settings page. Enter a
reading as five place-value contributions (each from 0 to 99) in either the
inch or metric stack, then select that stack as the source. The corrected
measurement is shown in both inches and millimeters. The inch-to-millimeter
conversion uses 25.4 mm per inch.

Each mode has separate inch and metric offsets. Settings save automatically in
the user's configuration directory and are retained between runs; measurement
inputs are not saved. The closed-jaw offset is signed. A scale that passes
zero reverses the offset; a scale that has not reached zero applies it as
entered. For inner jaws, selecting a gap reverses that direction and selecting
overlap leaves it unchanged.

Run the focused calculator tests with:

```sh
python -m unittest discover -s tests
```
