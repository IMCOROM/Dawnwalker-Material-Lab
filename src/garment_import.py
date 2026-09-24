"""Folder import and validated edits. Never uses torso chunk IDs or absolute offsets."""
import hashlib
import json
import math
import os
import re
import shutil
import struct
from pathlib import Path
from weapon_support import compact_material, zen_names, vector_offset, SWORD, SIMPLE

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def package(value):
    return value.rsplit('.',1)[0] if value else ''

def references(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k=='ObjectPath' and isinstance(v,str): yield package(v)
            else: yield from references(v)
    elif isinstance(value,list):
        for v in value: yield from references(v)

def objects(folder,index=None,library=None,errors=None):
    result={}
    for p in sorted(Path(folder).rglob('*.json')):
        try: data=read_json(p)
        except (ValueError,UnicodeError,OSError): continue
        if isinstance(data,dict) and 'Parameters' in data and 'Textures' in data:
            try:
                obj=compact_material(p,data,index or {},library or Path(folder))
                if obj:data=[obj]
                elif errors is not None:errors.append(p.name+': compact material could not be validated; missing original asset or unsupported shader')
            except (ValueError,UnicodeError,struct.error) as e:
                if errors is not None:errors.append(p.name+': '+str(e))
                continue
        for obj in data if isinstance(data,list) else []:
            if isinstance(obj,dict) and obj.get('Package') and obj.get('Type'):
                result[obj['Package']]=(obj,p)
    return result

def mesh_layers(path):
    """PSK extra UVs retain top-origin V; Blender flips V on import."""
    b=Path(path).read_bytes(); pos=0; chunks={}
    while pos<len(b):
        if pos+32>len(b): raise ValueError('Truncated PSK header')
        name,flags,size,count=struct.unpack_from('<20s3i',b,pos);pos+=32
        if size<0 or count<0 or pos+size*count>len(b): raise ValueError('Invalid PSK chunk size')
        chunks[name.rstrip(b'\0').decode()]=(size,count,b[pos:pos+size*count]);pos+=size*count
    if not all(k in chunks for k in ('MATT0000','EXTRAUVS0','VTXW0000')): return {}
    s,n,m=chunks['MATT0000']; names=[m[i*s:i*s+64].split(b'\0')[0].decode() for i in range(n)]
    us,un,uv=chunks['EXTRAUVS0']; ws,wn,w=chunks['VTXW0000']
    if us!=8 or un!=wn: return {}
    face=chunks.get('FACE3200') or chunks.get('FACE0000')
    if not face: return {}
    fs,fn,fb=face;wide=fs==18
    if fs not in (12,18): return {}
    result={}
    for i in range(fn):
        off=i*fs; ids=struct.unpack_from('<3I' if wide else '<3H',fb,off); mat=fb[off+(12 if wide else 6)]
        if mat>=len(names): raise ValueError('Invalid PSK material index')
        layers=result.setdefault(names[mat],set())
        for j in ids:
            if j>=un: raise ValueError('Invalid PSK wedge')
            u,v=struct.unpack_from('<2f',uv,j*8)
            if not math.isfinite(u+v): raise ValueError('Non-finite layer coordinates')
            col=min(3,max(0,int(u*4))); row=min(3,max(0,int(v*4)))
            layers.add(row*4+col+1)
    return result

def texture_base(data, meta):
    if meta.get('PixelFormat')!='PF_FloatRGBA' or (meta.get('SizeX'),meta.get('SizeY'))!=(16,16):
        raise ValueError('Unsupported PARAM texture: expected 16×16 PF_FloatRGBA')
    # Platform-data dimensions, format string, first mip, mip count, cooked flag.
    marker=struct.pack('<4i',16,16,1,13)+b'PF_FloatRGBA\0'+struct.pack('<3i',0,1,0)
    hits=[];start=0
    while (i:=data.find(marker,start))>=0:
        base=i+len(marker);start=i+1
        if data[base+2048:base+2060]==struct.pack('<3i',16,16,1): hits.append(base)
    if len(hits)!=1: raise ValueError('PARAM payload layout is unsupported or ambiguous; no edits allowed')
    values=struct.unpack_from('<1024e',data,hits[0])
    if not all(math.isfinite(v) for v in values): raise ValueError('PARAM contains invalid numbers')
    return hits[0]

class Asset:
    def __init__(self,path,pkg,entry=None):
        self.path=Path(path);self.package=pkg;self.entry=entry
        self.saved=self.path.read_bytes();self.fields={}
    def field(self,key,offset,kind='e'):
        size=struct.calcsize('<3'+kind)
        if offset<0 or offset+size>len(self.saved): raise ValueError('Field outside asset')
        for old,(o,k,_) in self.fields.items():
            if old!=key and max(o,offset)<min(o+struct.calcsize('<3'+k),offset+size): raise ValueError('Overlapping color fields')
        rgb=struct.unpack_from('<3'+kind,self.saved,offset)
        if not all(math.isfinite(v) for v in rgb): raise ValueError('Invalid color field')
        self.fields[key]=(offset,kind,rgb)
        return rgb
    def edited(self,changes):
        if self.path.read_bytes()!=self.saved: raise ValueError('Asset changed on disk; reopen the project before saving')
        b=bytearray(self.saved)
        for key,rgb in changes.items():
            offset,kind,old=self.fields[key]
            if len(rgb)!=3 or any(not math.isfinite(v) or not 0<=v<=65504 for v in rgb):
                raise ValueError('Colors must be finite numbers between 0 and 65504')
            if tuple(round(v,6) for v in rgb)==tuple(round(v,6) for v in old): continue
            struct.pack_into('<3'+kind,b,offset,*rgb)
        return bytes(b)

class Project:
    def __init__(self,source,app_dir):
        self.source=Path(source).resolve();self.app_dir=Path(app_dir).resolve()
        if not self.source.is_dir(): raise ValueError('Choose the exported garment folder')
        self.sections=[];self.warnings=[];self.dependencies={};self.assets={}
        library=self.app_dir/'AssetLibrary'
        self.library=library
        self.index=read_json(library/'package_index.json') if (library/'package_index.json').exists() else {}
        self.local=objects(self.source,self.index,library,self.warnings)
        if not self.local: raise ValueError('No supported FModel JSON metadata found. Export material JSON and original .uasset files; PNG-only exports cannot be edited safely.')
        shared=objects(library/'Exports',self.index,library) if (library/'Exports').exists() else {}
        self.metadata={**shared,**self.local}
        # Include separate material slots (e.g. shared gold runes) referenced by the imported mesh.
        for obj,p in list(self.local.values()):
            for ref in references(obj):
                if ref in self.metadata and self.metadata[ref][0]['Type']=='MaterialInstanceConstant':
                    self.local.setdefault(ref,self.metadata[ref])
        self.kind='Weapon' if any('/Characters/Swords/' in p or '/Weapons/' in p or
            package(o.get('Properties',{}).get('Parent',{}).get('ObjectPath',''))==SWORD
            for p,(o,_) in self.local.items()) else 'Clothing'
        key=hashlib.sha256(str(self.source).encode()).hexdigest()[:10]
        self.work=self.app_dir/'Projects'/(self.source.name+'_'+key)
        self.work.mkdir(parents=True,exist_ok=True)
        self.usage={};self.mesh_usage={}
        for p in list(self.source.rglob('*.psk'))+list(self.source.rglob('*.pskx')):
            try:
                usage=mesh_layers(p);self.mesh_usage[str(p)]={name:sorted(layers) for name,layers in usage.items()}
                for name,layers in usage.items(): self.usage.setdefault(name,set()).update(layers)
            except (ValueError,struct.error,UnicodeError) as e: self.warnings.append(f'{p.name}: {e}')
        for pkg,(obj,p) in self.local.items():
            if obj['Type']!='MaterialInstanceConstant': continue
            try: self.add_material(pkg,obj,p)
            except (ValueError,OSError,KeyError,struct.error) as e: self.warnings.append(f'{obj["Name"]}: {e}')
        for s in self.sections:
            s['layer_meshes']={str(l):[Path(mesh).stem for mesh,usage in self.mesh_usage.items() if l in usage.get(s['name'],[])] for l in s['layers']}
        self.collect_dependencies()
        self.preview_resources=self.resource_manifest()
        (self.work/'import_report.json').write_text(json.dumps(self.report(),indent=2))

    def resolve_chain(self,pkg,seen=None):
        seen=set() if seen is None else seen
        if pkg in seen: raise ValueError('Material inheritance cycle')
        seen.add(pkg)
        if pkg not in self.metadata: return {},pkg
        obj,_=self.metadata[pkg];props=obj.get('Properties',{})
        parent=package(props.get('Parent',{}).get('ObjectPath',''))
        merged={};root=pkg
        if parent: merged,root=self.resolve_chain(parent,seen)
        for typ in ('TextureParameterValues','ScalarParameterValues','VectorParameterValues'):
            values=dict(merged.get(typ,{}))
            values.update({r['ParameterInfo']['Name']:r for r in props.get(typ,[])})
            merged[typ]=values
        return merged,root

    def asset(self,pkg):
        if pkg in self.assets: return self.assets[pkg]
        entries=self.index.get(pkg,[]);entry=next((e for e in entries if e['filename'].endswith('.uasset')),None)
        original=None
        if pkg in self.metadata:
            _,p=self.metadata[pkg]
            if p.with_suffix('.uasset').exists(): original=p.with_suffix('.uasset')
        if original is None and entry and (self.library/'chunks'/entry['id']).exists(): original=self.library/'chunks'/entry['id']
        if original is None: raise ValueError(f'Missing original .uasset: {pkg}')
        name=(entry['id'] if entry else hashlib.sha256(pkg.encode()).hexdigest()+'.uasset')
        path=self.work/'assets'/name;path.parent.mkdir(exist_ok=True)
        if not path.exists(): shutil.copy2(original,path)
        a=Asset(path,pkg,entry);self.assets[pkg]=a;return a

    def add_material(self,pkg,obj,p):
        params,root=self.resolve_chain(pkg)
        if root==SIMPLE and self.kind=='Weapon':
            section={'name':obj['Name'],'package':pkg,'texture':None,'layers':[],'evidence':'separate material color',
                     'fields':{},'patterns':{},'colors':{},'shader':root}
            self.add_weapon_colors(section,obj,('BaseColor',))
            if section['colors']:self.sections.append(section)
            else:raise ValueError('No supported local color override')
            return
        if not root.endswith('/M_FabricOptimized_NEW') and root!=SWORD:
            raise ValueError(f'Shader not yet supported for layer edits ({root.rsplit("/",1)[-1]}); listed read-only')
        tex=params.get('TextureParameterValues',{}).get('LayerParametersTexture')
        if not tex: raise ValueError('No LayerParametersTexture reference')
        tp=package(tex['ParameterValue']['ObjectPath'])
        if tp not in self.metadata: raise ValueError('Missing PARAM texture JSON: '+tp)
        a=self.asset(tp);base=texture_base(a.saved,self.metadata[tp][0])
        layers=sorted(self.usage.get(obj['Name'],[]))
        evidence='mesh EXTRAUV0'
        if not layers:
            # Metadata is a weaker fallback: do not claim these are active mesh regions.
            layers=sorted({int(m.group(1)) for n in params.get('ScalarParameterValues',{}) if (m:=re.match(r'L(\d+)\s',n)) and 1<=int(m.group(1))<=16})
            evidence='material parameters; mesh usage unverified'
        if not layers: layers=list(range(1,17));evidence='16 available texture slots; mesh usage unknown'
        section={'name':obj['Name'],'package':pkg,'texture':tp,'layers':layers,'evidence':evidence,'fields':{},'patterns':{},'colors':{},'shader':root}
        for l in layers:
            start=base+8+((l-1)//4)*512+((l-1)%4)*32
            for category,delta in [('Mask 1',0),('Mask 2',8),('Grime',0x110),('Scratch',0xF8)]:
                key=f'L{l} {category}';a.field(key,start+delta);section['fields'][key]=a
        if root==SWORD:self.add_weapon_colors(section,obj,('BC_Hue','COLOR'))
        # Pattern color records only. Scalars and omitted-zero fields are never written.
        own=obj.get('Properties',{}).get('VectorParameterValues',[])
        for rec in own:
            name=rec['ParameterInfo']['Name']
            if not re.fullmatch(r'Pattern [123] Color',name): continue
            mi=self.asset(pkg)
            guid=struct.pack('<4I',*[int(s,16) for s in rec['ExpressionGUID'].split('-')])
            if mi.saved.count(guid)!=1:
                self.warnings.append(obj['Name']+': '+name+' record is ambiguous');continue
            off=mi.saved.index(guid)-16
            if off<5 or mi.saved[off-5:off]!=b'\x02'+b'\xff'*4:
                self.warnings.append(obj['Name']+': '+name+' layout is unsupported');continue
            mi.field(name,off,'f');section['patterns'][name]=mi
        self.sections.append(section)

    def add_weapon_colors(self,section,obj,allowed):
        for rec in obj.get('Properties',{}).get('VectorParameterValues',[]):
            name=rec['ParameterInfo']['Name']
            if name not in allowed:continue
            try:
                a=self.asset(section['package']);off=vector_offset(a.saved,name,rec['ExpressionGUID'])
                a.field(name,off,'f');section['colors'][name]=a
            except (ValueError,KeyError) as e:self.warnings.append(obj['Name']+': '+str(e))

    def collect_dependencies(self):
        pending=list(self.local);seen=set()
        while pending:
            pkg=pending.pop()
            if pkg in seen: continue
            seen.add(pkg)
            local=self.metadata.get(pkg)
            entries=self.index.get(pkg,[])
            available=bool(local and local[1].with_suffix('.uasset').exists()) or bool(entries and all((self.library/'chunks'/e['id']).exists() for e in entries))
            self.dependencies[pkg]='available' if available else 'missing'
            if local: pending.extend(references(local[0]))
            raw=None
            if local and local[1].with_suffix('.uasset').exists():raw=local[1].with_suffix('.uasset')
            elif entries:
                e=next((e for e in entries if e['filename'].endswith('.uasset')),None)
                if e and (self.library/'chunks'/e['id']).exists():raw=self.library/'chunks'/e['id']
            if raw:
                try:pending.extend(p for p in zen_names(raw.read_bytes())[1] if not p.startswith('/Script/'))
                except (ValueError,UnicodeError,struct.error):pass
        note='Dependency traversal covers exported metadata and supported cooked package import tables. Runtime-only references and shader behavior are not reconstructed.'
        if note not in self.warnings:self.warnings.append(note)

    def report(self):
        return {'source':str(self.source),'project':str(self.work),'kind':self.kind,'mesh_usage':self.mesh_usage,'sections':[{k:v for k,v in s.items() if k not in ('fields','patterns','colors')} for s in self.sections], 'warnings':self.warnings,'dependencies':self.dependencies}

    def resource_manifest(self):
        decoded={}
        for folder in (self.library/'Exports',self.source):
            for path in folder.rglob('*'):
                if not path.is_file() or path.suffix.lower() not in ('.png','.hdr','.tga','.exr'):continue
                parts=path.with_suffix('').parts
                if '_Dawnwalker' not in parts:continue
                pkg='/Game/'+'/'.join(parts[parts.index('_Dawnwalker'):])
                pkg=re.sub(r'(?:_MIP\d+|_LAYER\d+)+$','',pkg)
                decoded.setdefault(pkg,[]).append(str(path.resolve()))
        result={}
        for s in self.sections:
            params,_=self.resolve_chain(s['package']);textures={}
            for name,rec in params.get('TextureParameterValues',{}).items():
                pkg=package(rec['ParameterValue'].get('ObjectPath',''))
                textures[name]={'package':pkg,'decoded_files':sorted(set(decoded.get(pkg,[]))),
                    'raw_chunks':[str((self.library/'chunks'/e['id']).resolve()) for e in self.index.get(pkg,[]) if (self.library/'chunks'/e['id']).exists()]}
            obj=self.metadata[s['package']][0]
            result[s['name']]={'shader':s.get('shader'),'textures':textures,
                'resolved_parameters':obj.get('MaterialLabResolvedParameters',{}),
                'scalars':{k:r.get('ParameterValue') for k,r in params.get('ScalarParameterValues',{}).items()},
                'preview_status':'assets and parameters collected; shader visual parity not yet tested'}
        return result

    def save(self,changes):
        # Validate every edit before touching any asset. Stage all writes, then commit.
        staged=[]
        for pkg,values in changes.items():
            a=self.assets[pkg];b=a.edited(values)
            if b!=a.saved: staged.append((a,b))
        backup=self.work/'Backups';backup.mkdir(exist_ok=True)
        for a,b in staged:
            bak=backup/a.path.name
            if not bak.exists(): bak.write_bytes(a.saved)
            a.path.with_suffix('.pending').write_bytes(b)
        committed=[]
        try:
            for a,b in staged:
                os.replace(a.path.with_suffix('.pending'),a.path);committed.append(a)
        except OSError:
            for a in committed:a.path.write_bytes(a.saved)
            raise
        for a,b in staged:
            a.saved=b
            for key,(off,kind,old) in list(a.fields.items()): a.fields[key]=(off,kind,struct.unpack_from('<3'+kind,b,off))
        return len(staged)

    def build_raw(self):
        raw=self.work/'BuildRaw';chunks=raw/'chunks';chunks.mkdir(parents=True,exist_ok=True)
        paths={}
        # Include only edited assets; shared textures and unrelated clothes stay vanilla.
        for a in self.assets.values():
            if not a.entry: raise ValueError('Package index does not identify '+a.package)
            original=self.work/'Backups'/a.path.name
            if not original.exists() or original.read_bytes()==a.saved: continue
            if a.saved[:4]==b'\xc1\x83\x2a\x9e': raise ValueError('Legacy asset export requires conversion before raw packing')
            entry=a.entry;paths[entry['id']]=entry['filename']
        # Clear only files produced by the prior build, using its own manifest.
        old=raw/'manifest.json'
        if old.exists():
            for cid in read_json(old).get('chunk_paths',{}):
                if re.fullmatch('[0-9a-f]{24}',cid): (chunks/cid).unlink(missing_ok=True)
        for a in self.assets.values():
            if a.entry and a.entry['id'] in paths: shutil.copy2(a.path,chunks/a.entry['id'])
        (raw/'manifest.json').write_text(json.dumps({'chunk_paths':paths,'version':'ReplaceIoChunkHashWithIoHash','mount_point':'../../../'},indent=2))
        if not paths: raise ValueError('No saved changes to build')
        return raw
