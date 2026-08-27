import tkinter as tk
from tkinter import ttk
import json
import os

import pathlib
CONFIG_FILE = os.path.join(pathlib.Path.home(), ".calipers_settings.json")

MULT = {
    "in": [1.0, 0.1, 0.025, 0.001],
    "mm": [10.0, 1.0, 0.1, 0.02]
}

class CaliperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vernier Calipers")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)
        
        self.settings = {
            "outer_in_sign": 1,
            "outer_mm_sign": 1,
            "inner_in_sign": 1,
            "inner_mm_sign": 1,
            "set_outer_in_vals": ["", "", "", ""],
            "set_outer_mm_vals": ["", "", "", ""],
            "set_inner_in_vals": ["", "", "", ""],
            "set_inner_mm_vals": ["", "", "", ""]
        }
        self.load_settings()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.tabs = {}
        self.tabs["Outer"] = ttk.Frame(self.notebook)
        self.tabs["Inner"] = ttk.Frame(self.notebook)
        self.tabs["Settings"] = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tabs["Outer"], text="Outer")
        self.notebook.add(self.tabs["Inner"], text="Inner")
        self.notebook.add(self.tabs["Settings"], text="Settings")
        
        set_nb = ttk.Notebook(self.tabs["Settings"])
        set_nb.pack(fill='both', expand=True)
        self.tabs["Set Outer"] = ttk.Frame(set_nb)
        self.tabs["Set Inner"] = ttk.Frame(set_nb)
        set_nb.add(self.tabs["Set Outer"], text="Set Outer Offset")
        set_nb.add(self.tabs["Set Inner"], text="Set Inner Offset")
        
        self.widgets = {}
        
        self.build_tab(self.tabs["Outer"], "outer", is_settings=False)
        self.build_tab(self.tabs["Inner"], "inner", is_settings=False)
        self.build_tab(self.tabs["Set Outer"], "outer", is_settings=True)
        self.build_tab(self.tabs["Set Inner"], "inner", is_settings=True)

        self.update_all()

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception:
                pass

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f)
        except Exception:
            pass

    def validate_2digits(self, P):
        if P == "":
            return True
        if P.isdigit() and len(P) <= 2:
            return True
        return False

    def build_tab(self, parent, tab_type, is_settings):
        key_prefix = f"set_{tab_type}" if is_settings else tab_type
        self.widgets[key_prefix] = {"in": {}, "mm": {}}
        
        vcmd = (self.root.register(self.validate_2digits), '%P')
        
        for unit in ["in", "mm"]:
            frame = ttk.LabelFrame(parent, text="Inches" if unit == "in" else "Metric")
            frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            
            entries = []
            for i in range(4):
                e = ttk.Entry(frame, width=6, validate='key', validatecommand=vcmd, justify='center')
                e.pack(pady=2)
                e.bind('<KeyRelease>', lambda event, k=key_prefix: self.on_entry_change(k))
                entries.append(e)
                
                if is_settings:
                    val = self.settings.get(f"{key_prefix}_{unit}_vals", ["","","",""])[i]
                    e.insert(0, val)
                    
            self.widgets[key_prefix][unit]["entries"] = entries
            
            if is_settings:
                # Sign selection
                sign_var = tk.IntVar(value=self.settings.get(f"{tab_type}_{unit}_sign", 1))
                txt_minus = "Past end of scale / slides past (-)"
                txt_plus = "Not yet completed / gap (+)"
                rb1 = ttk.Radiobutton(frame, text=txt_minus, variable=sign_var, value=-1, command=self.on_settings_change)
                rb2 = ttk.Radiobutton(frame, text=txt_plus, variable=sign_var, value=1, command=self.on_settings_change)
                if tab_type == "outer":
                    ttk.Label(frame, text="When jaws closed, does measurement\ngo past the end of the scale or\nhas the scale not yet completed?", wraplength=150, justify="left").pack(anchor="w", pady=(5,0))
                else:
                    ttk.Label(frame, text="When outer jaws closed, do the inner jaws\nslide past each other, or is there a gap?\nGo past end of scale or not yet completed?", wraplength=150, justify="left").pack(anchor="w", pady=(5,0))
                rb1.pack(anchor="w", pady=(5,0))
                rb2.pack(anchor="w")
                self.widgets[key_prefix][unit]["sign_var"] = sign_var
                
                # Show computed offset
                ttk.Label(frame, text="Total Offset:", foreground="blue").pack(pady=(5,0))
                offset_val_var = tk.StringVar(value="0.000")
                off_entry = ttk.Entry(frame, textvariable=offset_val_var, state="readonly", width=12, justify='center')
                off_entry.pack()
                self.widgets[key_prefix][unit]["offset_val_var"] = offset_val_var
            else:
                # Main tab: Show offset from settings
                ttk.Label(frame, text="Offset:", foreground="gray").pack(pady=(5,0))
                offset_var = tk.StringVar(value="0.000")
                off_entry = ttk.Entry(frame, textvariable=offset_var, state="readonly", width=12, justify='center')
                off_entry.pack()
                self.widgets[key_prefix][unit]["offset_var"] = offset_var
                
                # Totals
                total_main = tk.StringVar(value="Total: 0.000")
                total_conv = tk.StringVar(value="")
                ttk.Label(frame, textvariable=total_main, foreground="blue", font=("Arial", 9, "bold")).pack(pady=(5,0))
                ttk.Label(frame, textvariable=total_conv, foreground="blue").pack()
                
                self.widgets[key_prefix][unit]["total_main"] = total_main
                self.widgets[key_prefix][unit]["total_conv"] = total_conv

    def on_entry_change(self, prefix):
        if prefix.startswith("set_"):
            self.on_settings_change()
        else:
            self.update_all()

    def on_settings_change(self):
        for tab_type in ["outer", "inner"]:
            for unit in ["in", "mm"]:
                key = f"set_{tab_type}"
                vals = [e.get() for e in self.widgets[key][unit]["entries"]]
                self.settings[f"{key}_{unit}_vals"] = vals
                
                sign = self.widgets[key][unit]["sign_var"].get()
                self.settings[f"{tab_type}_{unit}_sign"] = sign
                
        self.save_settings()
        self.update_all()

    def calc_entries(self, entries, unit):
        total = 0.0
        for i, e in enumerate(entries):
            val = e.get()
            if val.isdigit():
                total += int(val) * MULT[unit][i]
        return total

    def update_all(self):
        offsets = {"outer": {"in": 0.0, "mm": 0.0}, "inner": {"in": 0.0, "mm": 0.0}}
        
        for tab_type in ["outer", "inner"]:
            for unit in ["in", "mm"]:
                set_key = f"set_{tab_type}"
                val = self.calc_entries(self.widgets[set_key][unit]["entries"], unit)
                sign = self.settings.get(f"{tab_type}_{unit}_sign", 1)
                offset = val * sign
                offsets[tab_type][unit] = offset
                
                fmt = f"{offset:.4f} {unit}" if unit == "in" else f"{offset:.3f} {unit}"
                self.widgets[set_key][unit]["offset_val_var"].set(fmt)
                
        for tab_type in ["outer", "inner"]:
            for unit in ["in", "mm"]:
                main_key = tab_type
                offset = offsets[tab_type][unit]
                
                fmt_off = f"{offset:.4f} {unit}" if unit == "in" else f"{offset:.3f} {unit}"
                self.widgets[main_key][unit]["offset_var"].set(fmt_off)
                
                meas = self.calc_entries(self.widgets[main_key][unit]["entries"], unit)
                total = meas + offset
                
                if unit == "in":
                    total_in = total
                    total_mm = total * 25.4
                    self.widgets[main_key][unit]["total_main"].set(f"Total: {total_in:.4f} in")
                    self.widgets[main_key][unit]["total_conv"].set(f"({total_mm:.3f} mm)")
                else:
                    total_mm = total
                    total_in = total / 25.4
                    self.widgets[main_key][unit]["total_main"].set(f"Total: {total_mm:.3f} mm")
                    self.widgets[main_key][unit]["total_conv"].set(f"({total_in:.4f} in)")

def main():
    root = tk.Tk()
    app = CaliperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
