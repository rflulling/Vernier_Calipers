import tempfile
import unittest
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
    from calipers import CaliperCalculator, MeasurementPanel, SettingsPanel
except ImportError:
    tk = None


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


@unittest.skipIf(tk is None, "Tkinter is not installed")
class CalculatorGuiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "settings.json"
        try:
            self.app = CaliperCalculator(self.path)
        except tk.TclError as error:
            self.skipTest(f"Tk display unavailable: {error}")
        self.addCleanup(lambda: self.app.destroy())
        widgets = list(descendants(self.app))
        self.readings = {
            widget.tool: widget for widget in widgets
            if isinstance(widget, MeasurementPanel)
        }
        self.settings = {
            widget.tool: widget for widget in widgets
            if isinstance(widget, SettingsPanel)
        }

    def select(self, panel, value):
        button = next(
            widget for widget in descendants(panel)
            if isinstance(widget, ttk.Radiobutton) and widget.cget("value") == value
        )
        button.invoke()

    def result(self, tool):
        panel = self.readings[tool]
        return tuple(panel.results[unit].cget("text") for unit in ("in", "mm"))

    def test_readings_and_calibration_refresh_for_each_mode(self):
        self.assertEqual(set(self.readings), {"Inner", "Outer", "Probe"})
        for tool in ("Inner", "Outer", "Probe"):
            with self.subTest(tool=tool):
                reading = self.readings[tool]
                settings = self.settings[tool]
                sub_tabs = reading.master
                sub_tabs.master.master.select(sub_tabs.master)
                sub_tabs.select(reading)
                entry = next(
                    widget for widget in descendants(reading)
                    if isinstance(widget, ttk.Spinbox)
                    and widget.cget("textvariable") == str(reading.values["in"][0])
                )
                self.app.update()
                entry.focus_force()
                entry.delete(0, "end")
                entry.insert(0, "1")
                entry.event_generate("<KeyRelease>")
                self.app.update()
                self.assertEqual(self.result(tool), ("1.0000 in", "25.4000 mm"))
                settings.offset_in.set("0.1")
                self.assertEqual(self.result(tool), ("1.1000 in", "27.9400 mm"))

                reading.values["mm"][0].set("25")
                reading.values["mm"][1].set("4")
                settings.offset_mm.set("0.4")
                self.select(reading, "mm")
                self.assertEqual(self.result(tool), ("1.0157 in", "25.8000 mm"))
                self.select(settings, "past_zero")
                self.assertEqual(self.result(tool), ("1.0157 in", "25.8000 mm"))

        self.select(self.settings["Inner"], "overlap")
        self.assertEqual(self.result("Inner"), ("1.0157 in", "25.8000 mm"))

    def test_calculated_offsets_follow_calibration_controls_independently(self):
        for tool in ("Inner", "Outer", "Probe"):
            with self.subTest(tool=tool):
                settings = self.settings[tool]
                settings.offset_mm.set("2")
                sub_tabs = settings.master
                sub_tabs.master.master.select(sub_tabs.master)
                sub_tabs.select(settings)
                self.app.update()
                entry = next(
                    widget for widget in descendants(settings)
                    if isinstance(widget, ttk.Spinbox)
                    and widget.cget("textvariable") == str(settings.digits["in"][1])
                )
                entry.focus_force()
                entry.delete(0, "end")
                entry.insert(0, "1")
                entry.event_generate("<KeyRelease>")
                self.app.update()
                expected = -0.1 if tool == "Inner" else 0.1
                self.assertAlmostEqual(float(settings.offset_in.get()), expected)
                self.assertEqual(float(settings.offset_mm.get()), 2)
                self.select(settings, "past_zero")
                self.assertAlmostEqual(float(settings.offset_in.get()), -expected)
                self.assertEqual(float(settings.offset_mm.get()), 2)
                if tool == "Inner":
                    self.select(settings, "overlap")
                    self.assertAlmostEqual(float(settings.offset_in.get()), expected)
                settings.offset_in.set("-0.3")
                self.select(settings, "not_reached")
                self.assertEqual(float(settings.offset_in.get()), -0.3)
                settings.digits["mm"][0].set("4")
                settings._calculate("mm")
                self.assertEqual(float(settings.offset_in.get()), -0.3)
                self.assertEqual(float(settings.offset_mm.get()), 4)
                settings.digits["mm"][0].set("invalid")
                settings._calculate("mm")
                self.assertEqual(float(settings.offset_mm.get()), 4)

    def test_tab_order_and_size(self):
        self.app.update()
        notebook = self.readings["Outer"].master
        self.assertEqual([notebook.tab(tab, "text") for tab in notebook.tabs()],
                         ["Reading", "Settings"])
        outer = notebook.master.master
        self.assertEqual([outer.tab(tab, "text") for tab in outer.tabs()],
                         ["Inner", "Outer", "Probe"])
        width = round(self.app.winfo_fpixels("1i"))
        self.assertEqual(str(outer.tk.call(outer._w, "identify", "tab", width - 1, 10)), "0")

    def test_six_offsets_persist_without_measurement_inputs(self):
        for index, tool in enumerate(("Inner", "Outer", "Probe"), 1):
            self.settings[tool].offset_in.set(str(index / 10))
            self.settings[tool].offset_mm.set(str(-index))
            self.readings[tool].values["in"][0].set("8")
        self.app._close()
        self.app = CaliperCalculator(self.path)
        widgets = list(descendants(self.app))
        settings = {w.tool: w for w in widgets if isinstance(w, SettingsPanel)}
        readings = {w.tool: w for w in widgets if isinstance(w, MeasurementPanel)}
        for index, tool in enumerate(("Inner", "Outer", "Probe"), 1):
            self.assertEqual(float(settings[tool].offset_in.get()), index / 10)
            self.assertEqual(float(settings[tool].offset_mm.get()), -index)
            self.assertEqual(readings[tool].values["in"][0].get(), "0")
