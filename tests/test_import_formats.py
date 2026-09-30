import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from garment_import import objects
from weapon_support import compact_material, SWORD

class ImportFormats(unittest.TestCase):
    def test_compact_layouts(self):
        for parent in (SWORD, '/Game/Clothes/M_FabricOptimized_NEW'):
            for nested in (True,False):
                for reference in ('/Game/T_PARAM.0', {'ObjectPath':'/Game/T_PARAM.0'}):
                    with self.subTest(parent=parent,nested=nested,reference=reference), tempfile.TemporaryDirectory() as tmp:
                        p=Path(tmp)/'_Dawnwalker/MI_Test.json';p.parent.mkdir();p.with_suffix('.uasset').write_bytes(b'fixture')
                        params={'Colors':{},'Scalars':{'L1 Test':1}}
                        data={'Textures':{'LayerParametersTexture':reference}}
                        if nested:data['Parameters']=params
                        else:data.update(params)
                        p.write_text(json.dumps(data))
                        with patch('weapon_support.zen_names',return_value=([],[parent])):
                            result=objects(p.parent)
                        self.assertEqual(len(result),1)
                        obj=next(iter(result.values()))[0]
                        self.assertEqual(obj['Properties']['TextureParameterValues'][0]['ParameterValue']['ObjectPath'],'/Game/T_PARAM.0')
                        self.assertEqual(len(obj['Properties']['ScalarParameterValues']),1)
    def test_unsupported_parent_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'_Dawnwalker/MI_Test.json';p.parent.mkdir();p.with_suffix('.uasset').write_bytes(b'fixture')
            with patch('weapon_support.zen_names',return_value=([],['/Game/Unknown'])):
                self.assertIsNone(compact_material(p,{'Textures':{},'Colors':{}},{},Path(tmp)))
