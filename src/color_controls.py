"""Shared color controls for Material Lab."""
import tkinter as tk
from tkinter import ttk, colorchooser

def linear_to_srgb_component(c):
    c = max(0.0, min(1.0, float(c)))
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055

def srgb_to_linear_component(c):
    c = max(0.0, min(1.0, float(c)))
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def linear_rgb_to_hex(rgb):
    vals = []
    for c in rgb:
        s = linear_to_srgb_component(c)
        vals.append(max(0, min(255, round(s * 255))))
    return "#%02X%02X%02X" % tuple(vals)

def hex_to_linear_rgb(hex_color):
    h = hex_color.lstrip("#")
    vals = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(srgb_to_linear_component(v) for v in vals)

class ColorCell:
    def __init__(self, parent, on_change=None):
        self.on_change = on_change
        self.frame = ttk.Frame(parent)
        self.vars = [tk.StringVar(value="0.000000") for _ in range(3)]
        self.button = tk.Button(self.frame, width=3, relief="raised", command=self.pick)
        self.button.grid(row=0, column=0, padx=(0,4))
        for i, (label, var) in enumerate(zip(("R","G","B"), self.vars)):
            ttk.Label(self.frame, text=label).grid(row=0, column=1+i*2, padx=(1,1))
            e = ttk.Entry(self.frame, textvariable=var, width=9)
            e.grid(row=0, column=2+i*2, padx=(0,3))
            e.bind("<FocusOut>", lambda _e: self.refresh_swatch())
            e.bind("<Return>", lambda _e: self.refresh_swatch())
        self.refresh_swatch()

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    def get(self):
        try:
            return tuple(float(v.get()) for v in self.vars)
        except ValueError:
            raise ValueError("RGB entries must be numbers.")

    def set(self, rgb):
        for v, x in zip(self.vars, rgb):
            v.set(f"{float(x):.6f}")
        self.refresh_swatch()

    def refresh_swatch(self):
        try:
            rgb = self.get()
            self.button.configure(bg=linear_rgb_to_hex(rgb), activebackground=linear_rgb_to_hex(rgb))
            if self.on_change:
                self.on_change()
        except Exception:
            self.button.configure(bg="#808080")

    def pick(self):
        try:
            initial = linear_rgb_to_hex(self.get())
        except Exception:
            initial = "#808080"
        picked = colorchooser.askcolor(color=initial, title="Choose color")
        if picked and picked[1]:
            self.set(hex_to_linear_rgb(picked[1]))

