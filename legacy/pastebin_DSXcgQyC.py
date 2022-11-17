## for applying the same modification to all strings in nested iterables ##
## sample usage at https://pastebin.com/SGQN5pYd (part of a bigger solution)

def alterTextVals(val_to_alter, a, v):
    if type(val_to_alter) in [list, tuple, set]:
        pt = type(val_to_alter)
        al = [alterTextVals(vta, a, v) if type(vta) in [
            str, list, tuple, set # add any iterable class/type
        ] else vta for vta in val_to_alter]
        return al if pt == list else (set(al) if pt == set else tuple(al))
    
    detVal, a = str(val_to_alter), str(a)
    if a == 'split': detVal = detVal.split(v)
    elif a == 'word1': detVal = detVal.split(v)[0]
    elif a == 'replace' and v and type(v) == tuple: 
        if len(v) == 1: detVal = detVal.replace(v[0], '')
        elif len(v) == 2: 
            if type(v[1]) != int: detVal = detVal.replace(v[0], v[1])
            else: detVal = detVal.replace(v[0], '', v[1])
        else: detVal = detVal.replace(v[0], v[1], v[2])
    elif a == 'elimWhite': detVal = v.join([w for w in detVal.split() if w])
    elif a.startswith('truncate'): 
        v = v if type(v) == int and v > 10 else 10
        a = a.replace('truncate', '', 1)[:5] 
        detVal = detVal[:(v - len(a))] + (a if len(detVal) > v else '') 
    elif a.startswith('truncSplit'): 
        a = a.replace('truncSplit', '', 1)[:5] 
        v = v if type(v) == int and v > 15 else 15
        if len(detVal) > v:
            v = (int(v - int((v - len(a))/2)), -1*int((v - len(a))/2))
            detVal = detVal[:v[0]] + a + detVal[v[1]:]
    elif a == 'prefix': detVal = f'{v}{detVal}'
    elif a == 'suffix': detVal = f'{detVal}{v}'
    # elif # can add more modifiers
    else: detVal = a.join(detVal.split(str(v))) # default 
    return detVal
