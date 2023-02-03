## get a nested value from a dictionary or [non-string] iterable with only the final key ##
### simplified version of https://pastebin.com/NRxKRJPn ###################################
### [ this version does not keep track of keys on the paths to the value/s ] ##############
### for values with specific data-type, use version at https://pastebin.com/LsZUiRW2 ######
### example of usage at https://stackoverflow.com/a/75338566/6146136 ######################

# a generator for the values
def yieldNestedVals(obj, keysList):
    if isinstance(obj, str) or not keysList: return
    try: 
        nextVal, nextKeys = obj[keysList[0]], keysList[1:]
        vList = yieldNestedVals(nextVal, nextKeys) if nextKeys else [nextVal]
    except: vList = []
    for v in vList: yield v
    if isinstance(obj, dict): obj = obj.values()
    for i in (obj if hasattr(obj, '__iter__') else []):
        for v in yieldNestedVals(i, keysList): yield v

# returns either a list [if returnAll is True] or a single value [or `None`]
def getNestedVal(fObj, gKey, returnAll=False):
    gKey = gKey if isinstance(gKey, list) else [gKey]
    gKey = [k for k in gKey if isinstance(k, (str, int))]
    vGen = yieldNestedVals(fObj, gKey)
    if returnAll: return list(vGen)
    for v in vGen: return v