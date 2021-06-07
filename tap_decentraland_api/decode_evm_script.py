from eth_typing import HexStr
import glob, os, json
import eth_utils
import logging
import importlib.resources

CALLSCRIPT_ID = '0x00000001'
FORWARD_CALL_SIG="d948d468"

def decodeSegment(seg):
    # First 40 characters are address
    to = f"0x{seg[:40]}"
    dataSegment = seg[40:]


    #Get data
    dataLength = int(f"0x{dataSegment[:8]}", 16) * 2
    dataEnd = dataLength+8
    dataBody = f"0x{dataSegment[8:dataEnd]}"
    
    restSegment = dataSegment[dataEnd:]
    return {
        "segment": {
            "to":to,
            "data":dataBody
        },
        "scriptLeft": restSegment,
    }


def decodeCallScript(script):
    scriptData = script[len(CALLSCRIPT_ID):]

    segments = []
    while len(scriptData) > 0:
        result = decodeSegment(scriptData)
        segments.append(result["segment"])
        scriptData = result["scriptLeft"]

    return segments


def isValidForwardCall(calldata):
    calldata = calldata[2:]
    selector = calldata[:8]
    evmscriptData = calldata[8:]
    
    if selector == FORWARD_CALL_SIG and len(evmscriptData) > 128:
        return True
    else:
        return False

def parseForwardCall(calldata):
    calldata = calldata[2:]

    evmscriptData = calldata[8:]
    offset = int(f"0x{evmscriptData[0:64]}", 16) * 2
    startIndex = offset + 64

    dataLength = int(f"0x{evmscriptData[offset:startIndex]}", 16) * 2

    return f"0x{evmscriptData[startIndex:(startIndex + dataLength)]}"

def decodeStep(step):
    data = step['data']
    children = None
    if isValidForwardCall(data):
        forwardedEvmScript = parseForwardCall(data)
        children = decodeForwardingPath(forwardedEvmScript)
    return {
        "data": data,
        "to": step['to'],
        "children": children
    }


def decodeForwardingPath(script):
    path = decodeCallScript(script)

    decodedPath = [decodeStep(step) for step in path]

    return decodedPath

def get_apps():
    filename = "apps.json"
    with importlib.resources.path("tap_decentraland_api.aragon_metadata", filename) as data_path:
        with open(data_path) as f:
            apps = json.load(f)
            return apps

def get_methods(app):
    filename = f"{app}.json"
    with importlib.resources.path("tap_decentraland_api.aragon_metadata.artifacts", filename) as data_path:
        with open(data_path) as f:
            json_artifact = json.load(f)
            return json_artifact["functions"]



def findAppMethod(step, methods, provider):
    foundMethods = None
    for appAddr, appMethods in methods.items():
        if(step['to']) == appAddr:
            foundMethods = appMethods
            break
    foundMethod = None
    methodId = step['data'][:10]
    
    if foundMethods:
        for m in foundMethods:
            if 'sig' in m:
                methodSig = f"0x{eth_utils.keccak(text=m['sig']).hex()[:8]}"
                if methodSig == methodId:
                    foundMethod = m
                    break
    
    return {"method": foundMethod}

def evaluateRadSpec(step, methods, provider):
    foundAppMethod = findAppMethod(step, methods, provider)
    if not foundAppMethod:
        return ''
    method = foundAppMethod['method']
    if method and 'notice' in method:
        return method['notice']
    return ''


def describeStep(step, methods, provider):
    description = evaluateRadSpec(step, methods, provider)
    decoratedStep = {"step": step, "description":description}
    if 'children' in step and isinstance(step['children'], list):
        decoratedStep['children'] = [describeStep(child, methods, provider) for child in step['children']]

    return decoratedStep


def describePath(path, methods, provider):
    return [describeStep(step, methods, provider) for step in path]

def friendlyDescription(path, level):
    outString = ""
    for step in path:
        arrow = '->'
        if level == 0:
            arrow = ''
        outString+=f"{' ' * level}{arrow}{step['description']}\n"
        if 'children' in step and isinstance(step['children'], list):
            outString+=friendlyDescription(step['children'], level+1)
            
    return outString

apps = get_apps()
methods = dict((app, get_methods(app)) for app in apps)

def decodeScript(script: str) -> str:
    decodedPath = decodeForwardingPath(script)
    
    describedPath = describePath(decodedPath, methods, '')
    #logging.info(describedPath)
    result = friendlyDescription(describedPath, 0)
    #logging.info(f"Result: {result}")
    return result
