## recursively parse any json within an object

import json

def deepParseJson(obj, jsonOp=False):
    if type(obj) == str:
        try: obj = json.loads(obj)
        except: pass
    if type(obj) == dict: obj = {k: deepParseJson(v) for k, v in obj.items()}
    elif type(obj) in [list, set, tuple]:
        t, obj = type(obj), [deepParseJson(o) for o in obj]
        obj = set(obj) if t == set else (tuple(obj) if t == tuple else obj)
    return json.dumps(obj) if jsonOp else obj
