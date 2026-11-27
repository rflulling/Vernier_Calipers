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
inputs are not saved. Enter a signed correction directly in either closed-jaw
offset field, or calculate it using the corresponding place-value stack under
Closed-jaw reading. For calculated offsets, a scale that passes zero reverses
the offset; a scale that has not reached zero applies it as entered. For inner
jaws, selecting a gap reverses that direction and selecting overlap leaves it
unchanged. These choices do not change a manually entered offset. The signed
offset for the selected reading unit is added to the reading. Calculator inputs
are not saved, so after restarting, enter a closed-jaw reading again to
recalculate an offset with different calibration choices.

Run the focused calculator tests with:

```sh
python -m unittest discover -s tests
```
