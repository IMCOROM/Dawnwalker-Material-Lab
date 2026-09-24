"""Windows entry point and optional standalone runtime check."""
import sys,json,traceback
from pathlib import Path
import Material_Lab

def run():
    if '--self-test' in sys.argv:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        root=TkinterDnD.Tk();root.withdraw()
        lab=Material_Lab.Lab(root,True)
        lab.appearance.mode.set('Dark');lab.appearance.apply()
        if len(sys.argv)>3:
            from garment_import import Project
            lab.loading=True;lab.loaded(Project(sys.argv[3],Material_Lab.HOME))
            assert lab.cells
            assert not lab.dirty
        root.update()
        report={'ok':True,'frozen':bool(getattr(sys,'frozen',False)),
                'drag_drop':root.tk.call('package','require','tkdnd'),
                'tcl':root.tk.call('info','patchlevel'), 'controls':len(lab.cells),
                'asset_library':(Material_Lab.HOME/'AssetLibrary/package_index.json').exists(),
                'build_tool':(Material_Lab.HOME/'Tools/retoc.exe').exists()}
        root.destroy()
        Path(sys.argv[2]).write_text(json.dumps(report,indent=2))
    else: Material_Lab.main()

if __name__=='__main__':
    try:run()
    except Exception:
        detail=traceback.format_exc()
        if '--self-test' in sys.argv:
            Path(sys.argv[2]).write_text(detail)
        else:
            import tkinter as tk
            from tkinter import messagebox
            root=tk.Tk();root.withdraw()
            messagebox.showerror('Material Lab could not start',detail)
            root.destroy()
        sys.exit(1)
