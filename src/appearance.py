"""Application appearance, independent of material/project settings."""
import json
import tkinter as tk
from tkinter import ttk


class Appearance:
    PALETTES = {
        'Light': dict(bg='#f3f4f6', fg='#20242b', field='#ffffff', panel='#e2e5ea',
                      border='#aeb6c2', accent='#235eaa', selected='#ffffff', muted='#697381'),
        'Dark': dict(bg='#20242b', fg='#edf0f5', field='#15191f', panel='#323944',
                     border='#596474', accent='#366db0', selected='#ffffff', muted='#a4adba'),
    }

    def __init__(self, root, path):
        self.root, self.path = root, path
        self.style = ttk.Style(root)
        self.style.theme_use('clam')
        mode = 'Light'
        try:
            saved = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(saved, dict) and saved.get('mode') in self.PALETTES:
                mode = saved['mode']
        except (OSError, ValueError):
            pass
        self.mode = tk.StringVar(root, value=mode)
        self.apply()

    def apply(self):
        p = self.PALETTES[self.mode.get()]
        s = self.style
        s.configure('.', background=p['bg'], foreground=p['fg'],
                    fieldbackground=p['field'], bordercolor=p['border'],
                    lightcolor=p['border'], darkcolor=p['border'],
                    troughcolor=p['field'], selectbackground=p['accent'],
                    selectforeground=p['selected'], insertcolor=p['fg'])
        s.map('.', foreground=[('disabled', p['muted'])])
        for name in ('TButton', 'TCombobox', 'TScrollbar'):
            s.configure(name, background=p['panel'], arrowcolor=p['fg'])
            s.map(name, background=[('pressed', p['accent']), ('active', p['border'])])
        for name in ('TEntry', 'TCombobox'):
            s.map(name, fieldbackground=[('readonly', p['field']), ('disabled', p['bg'])],
                  foreground=[('disabled', p['muted']), ('readonly', p['fg'])])
        s.configure('TNotebook.Tab', padding=(12, 6), background=p['panel'])
        s.map('TNotebook.Tab', background=[('selected', p['accent']), ('active', p['border'])],
              foreground=[('selected', p['selected'])])
        # Classic widgets (including the combobox popup) need explicit defaults.
        for cls in ('Canvas', 'Text', 'Listbox'):
            self.root.option_add('*' + cls + '.background', p['field'])
            self.root.option_add('*' + cls + '.foreground', p['fg'])
            self.root.option_add('*' + cls + '.selectBackground', p['accent'])
            self.root.option_add('*' + cls + '.selectForeground', p['selected'])
        self.root.option_add('*Text.insertBackground', p['fg'])
        self.refresh()

    def refresh(self, widget=None):
        p = self.PALETTES[self.mode.get()]
        widget = self.root if widget is None else widget
        if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Canvas)):
            widget.configure(background=p['bg'])
        elif isinstance(widget, (tk.Text, tk.Listbox)):
            widget.configure(background=p['field'], foreground=p['fg'],
                             selectbackground=p['accent'], selectforeground=p['selected'])
            if isinstance(widget, tk.Text):
                widget.configure(insertbackground=p['fg'])
        # ColorCell buttons deliberately keep their material RGB swatches.
        for child in widget.winfo_children():
            self.refresh(child)

    def select(self, event=None):
        self.apply()
        # Failure to persist must not stop editing or discard material changes.
        try:
            temp = self.path.with_suffix('.tmp')
            temp.write_text(json.dumps({'mode': self.mode.get()}, indent=2), encoding='utf-8')
            temp.replace(self.path)
        except OSError:
            from tkinter import messagebox
            messagebox.showwarning('Appearance', 'Appearance changed, but the preference could not be saved beside the application.', parent=self.root)
