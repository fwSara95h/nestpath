## for checking if a nested dictionary has a certain key
## example of usage at https://stackoverflow.com/a/74680512/6146136

## simplified version at https://pastebin.com/G92TZnnK 
#### [if you don't care about keys on paths to value/s]

## to just flatten and object, see flattenObj @ https://pastebin.com/v3Fep60B


############### gets list of keys to every value in the dict/iterable ###############
def getObjPaths(obj):
    # return [] or a list of lists    
    if type(obj) == str or not hasattr(obj, '__iter__'): return []
    pList = []    
    if type(obj) == dict:
        for k, v in obj.items():  
            pList += ([[k]] + [[k]+pli for pli in getObjPaths(v)])
        return pList
    try:
        for i, v in enumerate(obj): 
            vp = getObjPaths(v)
            pList += [[i]+pl for pl in vp if [p for p in pl if type(pl)!=int]]
        return pList
    except: return []
#####################################################################################


######### retrieved a nested value if givent the list of keys on its "path" #########
def getVal_byPath(obj, kPath:list, printError=False, returnError=False):
    try: 
        for k in kPath: obj = obj[k]
        return obj
    except Exception as e: 
        errMsg = f'could not access {kPath} - {e}'
        if printError: print(errMsg)
        return errMsg if returnError else None
#####################################################################################


###### checks if a kList ends with lastKey  AND contains parentKeys [in order] ######
def matchedPath(kList:list, lastKey:str, parentKeys:list=[]):
    if not kList[-1:] == [lastKey]: return False
    if not parentKeys: return True

    kLen = len(kList)
    pPosList = [(kList+[pk]).index(pk) for pk in parentKeys]
    pPosList = [(-1 if p==kLen else p) for p in pPosList]
    return -1 not in pPosList and sorted(pPosList) == pPosList
#####################################################################################


####### retrieves from nObj 1st or all value/s paired to "nKey"  at any depth #######
def getNestedVal(nObj,nKey:str,rForm='just_val',pKeys=[],objName='obj'):
    pathList = getObjPaths(nObj)
    if isinstance(nKey,str) or not hasattr(nKey,'__iter__'): nKey=[nKey]
    vpli = [p for p in pathList if any(
        [matchedPath(p, k, pKeys) for k in nKey]  
    )]
    if rForm[-4:] != '_all': vpli = vpli[:1]
    vpli = [{'val': getVal_byPath(nObj, p), 'path': p,  
        'expr': (f'{objName}'+''.join(f'{[k]}' for k in p)
    )} for p in vpli]
    if rForm.startswith('just_val'): vpli = [v['val'] for v in vpli]
    if rForm.startswith('just_path'): vpli = [v['path'] for v in vpli]
    if rForm.startswith('just_expr'): vpli = [v['expr'] for v in vpli]
    if rForm[-4:] == '_all': return vpli  
    return vpli[0] if vpli else None 
#####################################################################################