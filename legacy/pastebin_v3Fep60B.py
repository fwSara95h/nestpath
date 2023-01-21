################# recursively flatten nested dictionaries (or any iterable) ##################
## simplified version for just dictionaries @ https://stackoverflow.com/a/75196824/6146136 ###
## to just get individual nested values, see getNestedVal @ https://pastebin.com/NRxKRJPn ####

# only instances covered  by fTypes will be flattened (if they are iterable)
# for non-dictionary iterables [lists/tuples/sets/etc], indices will be treated as keys
# if ignore_indices is True indices of lists/tuples/sets/etc will be omitted 
# if ignore_singles is True keys/indices paired with the only iterable in a level will be omitted
# kList MUST be a list and should contain strings only
def recFlatten(obj_x, kList=[], fTypes=(dict, list), ignore_singles=False, ignore_indices=False):
    idx, is_ft = False, True if fTypes=='all' else isinstance(obj_x, fTypes)
    if not (is_ft and hasattr(obj_x,'__iter__')): return [(kList,obj_x)]
 
    try: keys, vals = list(iter(obj_x.keys())), list(iter(obj_x.values()))
    except: keys, vals, idx = list(range(len(obj_x))), list(iter(obj_x)), True
 
    vtc, tList = [type(v) for v in vals], [] 
    keys = [[str(ki) for ki in kList + ([] if (
        (ignore_singles and vtc.count(vt)==1 and isinstance(v, fTypes))
        or (ignore_indices and idx)
    ) else [k])] for vt, v, k in zip(vtc, vals, keys)]
 
    for k, v in zip(keys, vals): 
        try: tList += recFlatten(v, k, fTypes, ignore_singles, ignore_indices) 
        except Exception as e:
            print(f'Failed at {k} \ndue to {type(e)}: {e}') 
            return list(zip(keys, vals))
    return tList

# if kSep is True --> returns the list of tuples with key-lists and values
# if kSep is False --> returns a flat list of values only
# if kSep is a string --> returns a dictionary with nested keys joined by kSep UNLESS:
# if kSep is None or 'only_last' --> parent keys are not included for nested keys
def flattenObj(origObj, kSep='_', rename={}, **rfArgs):
    rk = lambda ki: rename.get(ki, ki)
    klvList = recFlatten(origObj, **rfArgs)
    
    if kSep is None or kSep=='only_last': 
        rnFunc = lambda kList: rk(kList[-1] if kList else None)
    elif not isinstance(kSep, str): 
        return klvList if kSep else [v for k, v in klvList]
    else: rnFunc = lambda kList: kSep.join([rk(k) for k in kList])

    return {rnFunc(kl): v for kl,v in klvList}