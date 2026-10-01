"""Folder-first Dawnwalker Material Lab."""
import json
import subprocess
import threading
import sys
import re
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
from garment_import import Project
from appearance import Appearance
from color_controls import ColorCell, linear_rgb_to_hex, hex_to_linear_rgb

HOME=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
sys.path.insert(0,str(HOME/'vendor'))

def output_stem(value):
    name=value.strip()
    while name.lower().startswith('zzz_'):name=name[4:]
    while name.lower().endswith('_p'):name=name[:-2]
    name=name.strip()
    if not name or len(name)>100 or not re.fullmatch(r'[\w -]+',name):
        raise ValueError('Enter an output name using letters, numbers, spaces, underscores, or hyphens (1–100 characters).')
    return 'zzz_'+name+'_P'

class Lab:
    def __init__(self,root,dnd=False):
        self.root=root;self.project=None;self.cells=[];self.dirty=False;self.loading=False
        root.title('Dawnwalker Material Lab v0.19 — Clothing & Weapons');root.geometry('1360x850')
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.appearance=Appearance(root,HOME/'appearance_settings.json')
        self.path=tk.StringVar();self.status=tk.StringVar(value='Choose an exported clothing folder to begin.')
        self.top=ttk.Frame(root,padding=15);self.top.pack(fill='x')
        heading=ttk.Frame(self.top);heading.pack(fill='x')
        ttk.Label(heading,text='Open clothing or a weapon',font=('Segoe UI',20,'bold')).pack(side='left')
        self.theme_selector=ttk.Combobox(heading,textvariable=self.appearance.mode,values=('Light','Dark'),state='readonly',width=8)
        self.theme_selector.pack(side='right')
        self.theme_selector.bind('<<ComboboxSelected>>',self.appearance.select)
        ttk.Label(heading,text='Appearance: ').pack(side='right')
        ttk.Label(self.top,text='Drop an exported item folder. Material Lab detects clothing or weapons from its materials and mesh references.').pack(anchor='w',pady=6)
        line=ttk.Frame(self.top);line.pack(fill='x')
        entry=ttk.Entry(line,textvariable=self.path);entry.pack(side='left',fill='x',expand=True,padx=(0,8))
        ttk.Button(line,text='Browse…',command=self.browse).pack(side='left',padx=4)
        ttk.Button(line,text='Open folder',command=lambda:self.open(self.path.get())).pack(side='left',padx=4)
        drop=ttk.Label(self.top,text='Drop a clothing or weapon folder here' if dnd else 'Folder browsing is ready. Run Install_Dependencies.bat to enable drag and drop.',padding=18,relief='groove')
        drop.pack(fill='x',pady=10)
        naming=ttk.Frame(self.top);naming.pack(fill='x',pady=(0,8))
        ttk.Label(naming,text='Output name:  zzz_').pack(side='left')
        self.output_name=tk.StringVar(value='DawnwalkerMaterialLab')
        ttk.Entry(naming,textvariable=self.output_name,width=32).pack(side='left')
        ttk.Label(naming,text='_P').pack(side='left')
        self.output_preview=tk.StringVar()
        ttk.Label(naming,textvariable=self.output_preview).pack(side='left',padx=16)
        self.output_name.trace_add('write',lambda *_:self.update_output_preview())
        self.update_output_preview()
        if dnd:
            from tkinterdnd2 import DND_FILES
            for widget in (root,drop,entry):
                widget.drop_target_register(DND_FILES);widget.dnd_bind('<<Drop>>',self.drop)
        actions=ttk.Frame(self.top);actions.pack(fill='x')
        for title,fn in [('Save project',self.save),('Export preview JSON',self.preview),('Build mod',self.build),('Import report',self.report),('Collect missing assets',self.collect)]:
            ttk.Button(actions,text=title,command=fn).pack(side='left',padx=4)
        self.book=ttk.Notebook(root);self.book.pack(fill='both',expand=True,padx=15,pady=8)
        ttk.Label(root,textvariable=self.status,wraplength=1300,padding=8).pack(fill='x')
        self.recent=HOME/'recent_garments.json'
        if self.recent.exists():
            try:
                recent=json.loads(self.recent.read_text())
                if recent:self.path.set(recent[0])
            except (ValueError,OSError):pass
        self.welcome()

    def welcome(self):
        frame=ttk.Frame(self.book,padding=30);self.book.add(frame,text='Welcome')
        for text in ['One folder per item. Clothing and weapons are detected automatically.',
                     'PARAM • Grime • Scratch • Patterns / Weapon colors',
                     'Import original .uasset files with FModel JSON and mesh exports. Keep their folder structure.',
                     'Vanilla exports start with vanilla colors. Saved project copies retain your edits; importing another folder does not recover another mod automatically.',
                     'The importer follows material references and checks texture layouts before enabling edits.',
                     'Mesh layer counts use PSK/PSKX EXTRAUV0. Without a mesh, layer usage is marked unverified.',
                     'Shared assets live in AssetLibrary beside this application. Working copies live in Projects.',
                     'Supported: optimized clothing, SwordClothSimplified weapon layers, and SimpleParameter weapon colors. Other shaders are reported read-only.']:
            ttk.Label(frame,text=text,wraplength=1050).pack(anchor='w',pady=10)

    def browse(self):
        path=filedialog.askdirectory(title='Select exported clothing or weapon folder')
        if path:self.path.set(path);self.open(path)
    def drop(self,event):
        paths=self.root.tk.splitlist(event.data)
        if len(paths)!=1:messagebox.showerror('Choose one item','Drop one clothing or weapon folder at a time.');return
        self.path.set(paths[0]);self.open(paths[0])
    def discard(self):
        return not self.dirty or messagebox.askyesno('Unsaved changes','Discard the unsaved color changes?')
    def open(self,path):
        if self.loading or not self.discard():return
        self.loading=True;self.status.set('Scanning materials, mesh layers, and dependencies…')
        def run():
            try:
                project=Project(path,HOME)
                self.root.after(0,lambda:self.loaded(project))
            except Exception as e:
                msg=str(e);self.root.after(0,lambda:self.failed(msg))
        threading.Thread(target=run,daemon=True).start()
    def failed(self,msg):
        self.loading=False;self.status.set('Import failed');messagebox.showerror('Import',msg)
    def loaded(self,project):
        self.project=project;self.cells=[];self.dirty=False
        name='DawnwalkerMaterialLab'
        try:name=json.loads((project.work/'build_settings.json').read_text()).get('output_name',name)
        except (OSError,ValueError):pass
        self.output_name.set(name)
        for tab in self.book.tabs():self.book.nametowidget(tab).destroy()
        for category in ('PARAM','Grime','Scratch','Weapon colors' if project.kind=='Weapon' else 'Patterns'):self.tab(category)
        self.loading=False
        if not project.sections:
            empty=ttk.Frame(self.book,padding=20);self.book.add(empty,text='Import help')
            ttk.Label(empty,text='No editable material sections were found.',font=('Segoe UI',14,'bold')).pack(anchor='w')
            ttk.Label(empty,text='Export material JSON, original .uasset files and PARAM texture metadata together. PNG-only exports cannot provide editable values.',wraplength=1000).pack(anchor='w',pady=10)
            ttk.Label(empty,text='\n'.join(project.warnings[:12]) or 'Check the Import report for missing references and supported shader details.',wraplength=1000).pack(anchor='w')
            self.book.select(empty)
        missing=sum(v=='missing' for v in project.dependencies.values())
        self.status.set(f'{project.kind} detected • {len(project.sections)} editable sections • {sum(len(s["layers"]) for s in project.sections)} layer rows • {missing} unresolved references. See Import report for details.')
        old=[]
        try:old=json.loads(self.recent.read_text())
        except (OSError,ValueError):pass
        self.recent.write_text(json.dumps([str(project.source)]+[x for x in old if x!=str(project.source)][:9],indent=2))

    def tab(self,category):
        frame=ttk.Frame(self.book);self.book.add(frame,text=category)
        canvas=tk.Canvas(frame,highlightthickness=0)
        self.appearance.refresh(canvas)
        vertical=ttk.Scrollbar(frame,orient='vertical',command=canvas.yview);vertical.pack(side='right',fill='y')
        horizontal=ttk.Scrollbar(frame,orient='horizontal',command=canvas.xview);horizontal.pack(side='bottom',fill='x')
        canvas.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set);canvas.pack(fill='both',expand=True)
        body=ttk.Frame(canvas,padding=10);canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        row=0
        for section in self.project.sections:
            if category in ('PARAM','Grime','Scratch') and not section['layers']:continue
            if row:ttk.Separator(body).grid(row=row,column=0,columnspan=5,sticky='ew',pady=15);row+=1
            title=section['name'].removeprefix('MI_').removesuffix('_OPT')
            title=title.removeprefix(self.project.source.name+'_').upper()
            ttk.Label(body,text=title,font=('Segoe UI',14,'bold')).grid(row=row,column=0,columnspan=5,sticky='w',pady=5);row+=1
            ttk.Label(body,text=f'{len(section["layers"])} layers — {section["evidence"]}').grid(row=row,column=0,columnspan=5,sticky='w');row+=1
            if category=='Weapon colors':
                ttk.Label(body,text='Colors affect every asset using this material. Some shader colors are only visible when their effect is active.').grid(row=row,column=0,columnspan=5,sticky='w');row+=1
            lookup=section.get('colors',{}) if category=='Weapon colors' else section['patterns'] if category=='Patterns' else section['fields']
            keys=list(lookup) if category in ('Patterns','Weapon colors') else [f'L{l} {c}' for l in section['layers'] for c in (('Mask 1','Mask 2') if category=='PARAM' else (category,))]
            if category=='PARAM':
                for col,label in enumerate(('Layer','Mask 1','Mask 2')):
                    ttk.Label(body,text=label).grid(row=row,column=col,sticky='w',padx=6,pady=6)
                row+=1
            for index,key in enumerate(keys):
                a=lookup[key]
                if category!='PARAM' or index%2==0:
                    label=key.split(' ',1)[0] if category=='PARAM' else key
                    ttk.Label(body,text=label,width=22).grid(row=row,column=0,sticky='w',padx=6,pady=5)
                col=2 if category=='PARAM' and index%2 else 1
                cell=ColorCell(body);cell.grid(row=row,column=col,padx=8,pady=5);cell.set(a.fields[key][2]);cell.on_change=self.changed
                self.cells.append((a,key,cell))
                if category!='PARAM' or index%2:
                    targets=(self.cells[-2][2],cell) if category=='PARAM' else (cell,)
                    actions=ttk.Frame(body);actions.grid(row=row,column=3 if category=='PARAM' else 2,columnspan=2,sticky='w',padx=4)
                    if category=='PARAM':
                        ttk.Button(actions,text='Both…',command=lambda cs=targets:self.pick_both(cs)).pack(side='left',padx=2)
                    ttk.Button(actions,text='Copy',command=lambda cs=targets:self.copy_colors(cs)).pack(side='left',padx=2)
                    ttk.Button(actions,text='Paste',command=lambda cs=targets:self.paste_colors(cs)).pack(side='left',padx=2)
                if category!='PARAM' or index%2:row+=1
            if not keys:ttk.Label(body,text='No supported local color records in this section.').grid(row=row,column=0,columnspan=4,sticky='w');row+=1
        def wheel(e):canvas.yview_scroll(-int(e.delta/120),'units')
        def bind(w):
            w.bind('<MouseWheel>',wheel)
            for c in w.winfo_children():bind(c)
        bind(body)

    def update_output_preview(self):
        try:self.output_preview.set('Builds as: '+output_stem(self.output_name.get()))
        except ValueError:self.output_preview.set('Enter a valid output name')
    def pick_both(self,cells):
        try:initial=linear_rgb_to_hex(cells[0].get())
        except ValueError:initial='#000000'
        chosen=colorchooser.askcolor(color=initial,title='Set both mask colors')[1]
        if chosen:
            for cell in cells:cell.set(hex_to_linear_rgb(chosen))
    def copy_colors(self,cells):
        try:
            colors=[cell.get() for cell in cells]
            self.validate_colors(colors)
            self.root.clipboard_clear()
            self.root.clipboard_append(json.dumps({'dawnwalker_colors':1,'colors':colors}))
            self.status.set('Copied both mask colors' if len(colors)==2 else 'Copied color')
        except (ValueError,tk.TclError) as e:messagebox.showerror('Copy colors',str(e))
    @staticmethod
    def validate_colors(colors):
        if not isinstance(colors,(list,tuple)) or len(colors) not in (1,2):raise ValueError('Copy a color row from Material Lab first.')
        for color in colors:
            if not isinstance(color,(list,tuple)) or len(color)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=65504 for v in color):
                raise ValueError('Copied colors must contain valid RGB values.')
    def paste_colors(self,cells):
        try:
            data=json.loads(self.root.clipboard_get())
            if not isinstance(data,dict) or data.get('dawnwalker_colors')!=1:raise ValueError('Copy a color row from Material Lab first.')
            colors=data.get('colors');self.validate_colors(colors)
            for i,cell in enumerate(cells):cell.set(colors[min(i,len(colors)-1)])
            self.status.set('Pasted Mask 1 color' if len(colors)==2 and len(cells)==1 else 'Pasted colors — unsaved changes')
        except (ValueError,tk.TclError) as e:messagebox.showerror('Paste colors',str(e))

    def changed(self):
        if not self.loading:self.dirty=True;self.status.set('Unsaved color changes')
    def changes(self):
        values={}
        for a,key,cell in self.cells:
            rgb=cell.get();target=values.setdefault(a.package,{})
            if key in target and target[key]!=rgb:raise ValueError(f'Two sections share {a.package}: use matching values for {key}')
            target[key]=rgb
        return values
    def save(self):
        if not self.project:return False
        try:
            stem=output_stem(self.output_name.get())
            n=self.project.save(self.changes());self.dirty=False
            (self.project.work/'build_settings.json').write_text(json.dumps({'output_name':stem[4:-2]},indent=2))
            self.preview(quiet=True);self.status.set(f'Saved {n} changed assets in {self.project.work}');return True
        except Exception as e:messagebox.showerror('Save',str(e));return False
    def preview(self,quiet=False):
        if not self.project:return
        try:
            values=self.changes();state={'format':'Dawnwalker Material Lab Weapon State v1' if self.project.kind=='Weapon' else 'Dawnwalker Material Lab Garment State v2','kind':self.project.kind,'source':str(self.project.source),'mesh_usage':self.project.mesh_usage,'resources':self.project.preview_resources,'materials':{}}
            for s in self.project.sections:
                layers={str(l):{} for l in s['layers']}
                for key,a in s['fields'].items():
                    layer,field=key.split(' ',1)
                    field={'Mask 1':'mask1_rgb_linear','Mask 2':'mask2_rgb_linear','Grime':'grime_rgb_linear','Scratch':'scratch_rgb_linear'}[field]
                    layers[layer[1:]][field]=values[a.package][key]
                state['materials'][s['name']]={'package':s['package'],'shader':s.get('shader'),'layer_meshes':s.get('layer_meshes',{}),'layers':layers,'patterns':{k:{'rgb_linear':values[a.package][k]} for k,a in s['patterns'].items()},'colors':{k:{'rgb_linear':values[a.package][k]} for k,a in s.get('colors',{}).items()}}
            path=self.project.work/'garment_state.json';path.write_text(json.dumps(state,indent=2))
            if not quiet:self.status.set('Exported '+str(path)+' — generic garment preview schema; Blender torso add-on needs an adapter.')
        except Exception as e:
            if quiet:raise
            messagebox.showerror('Preview',str(e))
    def report(self):
        if not self.project:return
        window=tk.Toplevel(self.root);window.title('Import report');window.geometry('1000x650')
        text=tk.Text(window,wrap='word');text.pack(fill='both',expand=True)
        text.insert('1.0',json.dumps(self.project.report(),indent=2));text.configure(state='disabled')
        self.appearance.refresh(window)
    def build(self):
        if not self.project or not self.save():return
        try:
            raw=self.project.build_raw()
            retoc=HOME/'Tools'/'retoc.exe'
            if not retoc.exists():raise ValueError('Missing Tools/retoc.exe. Restore the bundled Tools folder.')
            out=self.project.work/'Build';out.mkdir(exist_ok=True)
            utoc=out/(output_stem(self.output_name.get())+'.utoc')
            r=subprocess.run([str(retoc),'pack-raw',str(raw),str(utoc)],capture_output=True,text=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if r.returncode:raise ValueError(r.stdout+r.stderr)
            check=subprocess.run([str(retoc),'verify',str(utoc)],capture_output=True,text=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if check.returncode:raise ValueError(check.stdout+check.stderr)
            import shutil
            template=HOME/'Tools'/'companion.pak'
            if not template.exists():raise ValueError('Missing companion.pak in Tools')
            shutil.copy2(template,utoc.with_suffix('.pak'))
            self.status.set('Built and verified mod files in '+str(out)+'; copy the trio to your ~mods folder.')
        except Exception as e:messagebox.showerror('Build',str(e))
    def collect(self):
        if not self.project or self.loading:return
        if not any(v=='missing' for v in self.project.dependencies.values()):
            messagebox.showinfo('Asset library','All references found in this export’s metadata are available locally.');return
        archive=filedialog.askopenfilename(title='Select vanilla Dawnwalker-Windows.utoc',filetypes=[('Game archive','*.utoc')])
        if not archive:return
        key=simpledialog.askstring('Game archive key','AES key used by FModel (used for this operation only):',show='*')
        if not key:return
        from library_tools import collect
        project=self.project;self.loading=True
        def done(message):self.loading=False;self.status.set(message)
        def run():
            try:
                copied,unresolved=collect(project,archive,key,lambda text:self.root.after(0,lambda:self.status.set(text)))
                message=f'Cached {copied} additional chunks; {len(unresolved)} references were not found in the package index.'
            except Exception as e:message=str(e)
            self.root.after(0,lambda:done(message))
        threading.Thread(target=run,daemon=True).start()
    def close(self):
        if self.discard():self.root.destroy()

def main():
    try:
        from tkinterdnd2 import TkinterDnD
        root=TkinterDnD.Tk();dnd=True
    except ImportError:root=tk.Tk();dnd=False
    Lab(root,dnd);root.mainloop()
if __name__=='__main__':main()
