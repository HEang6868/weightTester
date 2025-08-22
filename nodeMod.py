import maya.cmds as mc


def node_check_create(nodeName, dataName, dataType="string", defaultValue={}):
    """
    Checks if a node with a given name already exists.
    Returns its data if it does. Creates the node and returns a default value if it doesn't.
    """
    #Check if the scene already has a node with the same name.
    nodeCheck = mc.objExists(nodeName)
    #If it does, read the node and get its data.
    if nodeCheck == True:
        nodeData = mc.getAttr(f'{nodeName}.{dataName}')
        if nodeData:
            nodeData = eval(nodeData)
        else:
            nodeData = defaultValue
        return nodeData      
    #If it doesn't, create the node and set its data as the default value.
    else:
        mc.scriptNode(name=nodeName)
        mc.addAttr(nodeName, dataType=dataType, longName=f"{dataName}")
        nodeData = defaultValue 
        return nodeData


def overwrite_node(nodeData, data, dataType="string"):
    """
    Overwrites the given node's existing data with new given data.
    """
    mc.setAttr(nodeData, data, type=dataType)