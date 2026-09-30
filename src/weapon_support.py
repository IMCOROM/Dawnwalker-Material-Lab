"""Read weapon exports and verify their existing cooked color records."""
import struct
import math
from pathlib import Path

SWORD='/Game/_Dawnwalker/Shaders/Characters/Clothes/M_SwordClothSimplified'
SIMPLE='/Game/_Dawnwalker/Shaders/Characters/Clothes/M_SimpleParameter'
VECTOR_GUIDS={
    'BC_Hue':'E96B27DA4453E4B63D7F9385E8FE8CF8',
    'COLOR':'FABEE9974E79158687E8AB9C2D179834',
    'BaseColor':'2859B8FD418F21E219649EB75419A536',
}

def name_batch(data,offset,limit):
    if 0<=offset and offset+4<=limit and struct.unpack_from('<I',data,offset)[0]==0:return []
    if offset<0 or offset+16>limit:raise ValueError('Missing name batch')
    count,size=struct.unpack_from('<2I',data,offset)
    if count>100000 or size>limit:raise ValueError('Invalid name batch')
    heads=offset+16+count*8;start=heads+count*2;end=start+size
    if end>limit:raise ValueError('Name batch outside package header')
    result=[];cursor=start
    for i in range(count):
        length=struct.unpack_from('>H',data,heads+2*i)[0]
        wide=bool(length&0x8000);length&=0x7fff
        nbytes=length*(2 if wide else 1)
        if cursor+nbytes>end:raise ValueError('Invalid name length')
        result.append(data[cursor:cursor+nbytes].decode('utf-16-le' if wide else 'utf-8'));cursor+=nbytes
    if cursor!=end:raise ValueError('Name batch size mismatch')
    return result

def zen_names(data):
    if len(data)<52 or struct.unpack_from('<I',data)[0]!=0:raise ValueError('Unsupported package header version')
    limit=struct.unpack_from('<I',data,4)[0]
    if not 52<=limit<=len(data):raise ValueError('Invalid package header size')
    imports=struct.unpack_from('<I',data,48)[0]
    return name_batch(data,52,limit),name_batch(data,imports,limit)

def infer_package(path,index):
    parts=path.with_suffix('').parts
    if '_Dawnwalker' in parts:return '/Game/'+'/'.join(parts[parts.index('_Dawnwalker'):])
    hits=[pkg for pkg in index if pkg.rsplit('/',1)[-1]==path.stem]
    if len(hits)==1:return hits[0]
    return None

def compact_material(path,data,index,library):
    pkg=infer_package(path,index)
    if not pkg:return None
    raw=path.with_suffix('.uasset')
    if not raw.exists():
        entry=next((e for e in index.get(pkg,[]) if e['filename'].endswith('.uasset')),None)
        if entry:raw=library/'chunks'/entry['id']
    if not raw.exists():return None
    binary=raw.read_bytes()
    names,imports=zen_names(binary)
    parents=[p for p in imports if p in (SWORD,SIMPLE) or p.endswith('/M_FabricOptimized_NEW')]
    if len(parents)!=1:return None
    parent=parents[0];textures=data.get('Textures',{})
    props={'Parent':{'ObjectPath':parent+'.0'},'TextureParameterValues':[], 'VectorParameterValues':[], 'ScalarParameterValues':[]}
    resolved=data.get('Parameters',data)
    for name,value in textures.items():
        if isinstance(value,dict):value=value.get('ObjectPath')
        if isinstance(value,str) and value.startswith(('/Game/','/Engine/')):
            props['TextureParameterValues'].append({'ParameterInfo':{'Name':name},'ParameterValue':{'ObjectPath':value}})
    for name,value in resolved.get('Colors',{}).items():
        if names.count(name)!=1:continue
        if name in VECTOR_GUIDS:
            guid=VECTOR_GUIDS[name]
        elif name in ('Pattern 1 Color','Pattern 2 Color','Pattern 3 Color'):
            marker=b'\x00\x07\x00\x07'+struct.pack('<IIBi',names.index(name),0,2,-1)
            if binary.count(marker)!=1:continue
            offset=binary.index(marker)+len(marker)
            if offset+32>len(binary):continue
            rgba=struct.unpack_from('<4f',binary,offset)
            if not isinstance(value,dict) or any(not math.isfinite(v) or not math.isclose(v,value.get(k,float('nan')),rel_tol=1e-5,abs_tol=1e-6) for k,v in zip('RGBA',rgba)):continue
            guid=''.join(f'{v:08X}' for v in struct.unpack_from('<4I',binary,offset+16))
        else:continue
        props['VectorParameterValues'].append({'ParameterInfo':{'Name':name},'ParameterValue':value,'ExpressionGUID':'-'.join(guid[i:i+8] for i in range(0,32,8))})
    props['ScalarParameterValues']=[{'ParameterInfo':{'Name':name},'ParameterValue':value} for name,value in resolved.get('Scalars',{}).items()]
    return {'Type':'MaterialInstanceConstant','Name':path.stem,'Package':pkg,'Properties':props,
            'MaterialLabExportFormat':'compact','MaterialLabImportedPackages':imports,
            'MaterialLabResolvedParameters':{key:resolved.get(key,{}) for key in ('Colors','Scalars','Switches')}}

def vector_offset(data,name,guid_string):
    names,_=zen_names(data)
    if names.count(name)!=1:raise ValueError('Color name missing or ambiguous: '+name)
    guid=struct.pack('<4I',*[int(s,16) for s in guid_string.split('-')])
    if data.count(guid)!=1:raise ValueError('Color GUID missing or ambiguous: '+name)
    offset=data.index(guid)-16
    marker=b'\x00\x07\x00\x07'+struct.pack('<IIBi',names.index(name),0,2,-1)
    if offset<len(marker) or data[offset-len(marker):offset]!=marker:
        raise ValueError('Unsupported or omitted color record: '+name)
    return offset
