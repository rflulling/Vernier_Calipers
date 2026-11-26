import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from caliper_core import (
    PLACES,
    TOOLS,
    calculate_reading,
    converted_readings,
    corrected_reading,
    load_settings,
    save_settings,
    settings_path,
)


class MeasurementPanel(ttk.Frame):
    def __init__(self, master, tool, settings, on_change):
        super().__init__(master, padding=8)
        self.tool = tool
        self.settings = settings
        self.on_change = on_change
        self.source = tk.StringVar(value="in")
        self.values = {
            unit: [tk.StringVar(value="0") for _ in PLACES]
            for unit in ("in", "mm")
        }
        self.results = {}
        self._build()
        self.update_result()

    def _build(self):
        source_row = ttk.Frame(self)
        source_row.pack(fill="x", pady=(0, 5))
        ttk.Label(source_row, text="Reading is in:").pack(side="left")
        for unit, label in (("in", "Inches"), ("mm", "Metric")):
            ttk.Radiobutton(
                source_row, text=label, value=unit, variable=self.source,
                command=self.update_result,
            ).pack(side="left", padx=(8, 0))

        stacks = ttk.Frame(self)
        stacks.pack(fill="x")
        for column, (unit, title) in enumerate((("in", "Inches"), ("mm", "Metric"))):
            group = ttk.LabelFrame(stacks, text=title, padding=5)
            group.grid(row=0, column=column, sticky="nsew", padx=(0, 5 if column == 0 else 0))
            ttk.Label(group, text="Place").grid(row=0, column=0, sticky="w")
            ttk.Label(group, text="Value").grid(row=0, column=1, sticky="e")
            for row, place in enumerate(PLACES, 1):
                ttk.Label(group, text=place).grid(row=row, column=0, sticky="w", padx=(0, 8))
                entry = ttk.Spinbox(
                    group, from_=0, to=99, width=4, textvariable=self.values[unit][row - 1],
                    command=self.update_result,
                )
                entry.grid(row=row, column=1, sticky="e")
                entry.bind("<KeyRelease>", lambda _event: self.update_result())
                entry.bind("<FocusOut>", lambda _event: self.update_result())
            stacks.columnconfigure(column, weight=1)

        output = ttk.LabelFrame(self, text="Corrected measurement", padding=6)
        output.pack(fill="x", pady=(8, 0))
        for row, unit in enumerate(("in", "mm")):
            label = "Inches" if unit == "in" else "Metric"
            ttk.Label(output, text=label).grid(row=row, column=0, sticky="w")
            result = ttk.Label(output, text="0", font=("TkDefaultFont", 11, "bold"))
            result.grid(row=row, column=1, sticky="e")
            output.columnconfigure(1, weight=1)
            self.results[unit] = result

    def update_result(self):
        try:
            reading = calculate_reading(self.values[self.source.get()])
        except (TypeError, ValueError):
            reading = 0.0
        unit = self.source.get()
        key = "offset_in" if unit == "in" else "offset_mm"
        corrected = corrected_reading(
            reading,
            self.settings[key],
            self.settings["scale_position"],
            self.settings["jaw_fit"],
            self.tool,
        )
        inches, millimeters = converted_readings(corrected, unit)
        self.results["in"].configure(text=f"{inches:.4f} in")
        self.results["mm"].configure(text=f"{millimeters:.4f} mm")
        self.on_change()


class SettingsPanel(ttk.Frame):
    def __init__(self, master, tool, values, on_change):
        super().__init__(master, padding=8)
        self.tool = tool
        self.values = values
        self.on_change = on_change
        self.offset_in = tk.StringVar(value=str(values["offset_in"]))
        self.offset_mm = tk.StringVar(value=str(values["offset_mm"]))
        self.scale_position = tk.StringVar(value=values["scale_position"])
        self.jaw_fit = tk.StringVar(value=values["jaw_fit"])
        self._build()

    def _build(self):
        offsets = ttk.LabelFrame(self, text="Closed-jaw offset", padding=6)
        offsets.pack(fill="x")
        ttk.Label(offsets, text="Inches").grid(row=0, column=0, sticky="w")
        ttk.Entry(offsets, textvariable=self.offset_in, width=11).grid(row=0, column=1, sticky="e")
        ttk.Label(offsets, text="Metric").grid(row=1, column=0, sticky="w")
        ttk.Entry(offsets, textvariable=self.offset_mm, width=11).grid(row=1, column=1, sticky="e")
        ttk.Label(offsets, text="Offsets may be positive or negative.").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        offsets.columnconfigure(1, weight=1)

        scale = ttk.LabelFrame(
            self, text="With the jaws closed, is the scale past zero or not yet complete?",
            padding=6,
        )
        scale.pack(fill="x", pady=(8, 0))
        for value, label in (
            ("past_zero", "Scale passes zero"),
            ("not_reached", "Scale has not reached zero"),
        ):
            ttk.Radiobutton(
                scale, text=label, value=value, variable=self.scale_position,
                command=self._update,
            ).pack(anchor="w")

        if self.tool == "Inner":
            fit = ttk.LabelFrame(self, text="When outer jaws are closed, inner jaws", padding=6)
            fit.pack(fill="x", pady=(8, 0))
            for value, label in (("overlap", "Slide past each other"), ("gap", "Have a gap")):
                ttk.Radiobutton(
                    fit, text=label, value=value, variable=self.jaw_fit,
                    command=self._update,
                ).pack(anchor="w")

        for variable in (self.offset_in, self.offset_mm):
            variable.trace_add("write", self._update)

    def _update(self, *_args):
        for key, variable in (("offset_in", self.offset_in), ("offset_mm", self.offset_mm)):
            try:
                number = float(variable.get())
                if math.isfinite(number):
                    self.values[key] = number
            except ValueError:
                pass
        self.values["scale_position"] = self.scale_position.get()
        self.values["jaw_fit"] = self.jaw_fit.get()
        self.on_change()


class CaliperCalculator(tk.Tk):
    def __init__(self, path=None):
        super().__init__()
        self.path = Path(path) if path else settings_path()
        self.settings = load_settings(self.path)
        self.title("Vernier Calipers")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()

    def _build(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        for tool in TOOLS:
            page = ttk.Frame(notebook)
            notebook.add(page, text=tool)
            sub_tabs = ttk.Notebook(page)
            sub_tabs.pack(fill="both", expand=True)
            reading = MeasurementPanel(
                sub_tabs, tool, self.settings[tool], self._save,
            )
            preferences = SettingsPanel(
                sub_tabs, tool, self.settings[tool], self._save,
            )
            sub_tabs.add(reading, text="Reading")
            sub_tabs.add(preferences, text="Settings")

    def _save(self):
        try:
            save_settings(self.path, self.settings)
        except OSError:
            pass

    def _close(self):
        self._save()
        self.destroy()


if __name__ == "__main__":
    CaliperCalculator().mainloop()
