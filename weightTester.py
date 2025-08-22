import maya.cmds as mc
import weightTester.nodeMod as nodes


"""
Tool for creating skin weight test animations on joints.
"""

############################
###   BUILD THE WINDOW   ###
############################

class WeightTester():
    def __init__(self):
        #Define basic window parameters.
        self.app = "WeightPaintTester"
        self.title = "Weight Paint Tester"
        self.winSize = (500, 550)
        #Setup dictionary that will hold data for the tool.
        self.jointDict={}
        self.minFrameRange = mc.playbackOptions(q=True, minTime=True)
        self.maxFrameRange = mc.playbackOptions(q=True, maxTime=True)

        #Check if the window is already open and closes it if it is.
        if mc.window(self.app, exists=True):
            mc.deleteUI(self.app, window=True)
        
        #Create the window.
        self.window = mc.window(self.app, title=self.title, widthHeight=self.winSize)

        #Set up the window's layouts and inputs.
        mainLayout = mc.formLayout(numberOfDivisions=100)

        treeLayout = mc.frameLayout(parent=mainLayout, label="Objects to Test",
                                    collapsable=False,
                                    )
        self.jointTree = mc.treeView(parent=treeLayout, 
                                    attachButtonRight=True,
                                    numberOfButtons=3,
                                    allowDragAndDrop=True,
                                    allowReparenting=False,  
                                    selectionChangedCommand=lambda: self.Tree_to_scene_select(self.jointTree)
                                    )
        controlLayout = mc.columnLayout(parent=mainLayout, adjustableColumn=True,
                                        width=120,
                                       generalSpacing=15,
                                       margins=5,
                                       )
        self.jntHierBtn = mc.button(label="Select Object \nHierarchy", parent = controlLayout, command=self.select_object_hierarchy)
        self.addJntBtn = mc.button(label="Add Selected \nObjects", parent = controlLayout, command=( lambda tree: self.tree_add(self.jointTree, dictionary=self.jointDict) ) )
        self.rmvJntBtn = mc.button(label="Remove Selected \nObject", parent = controlLayout, command=( lambda tree: self.tree_remove(self.jointTree, dictionary=self.jointDict) ) )

        mc.separator(parent=controlLayout, horizontal=False, height=1)

        #Create a small layout for the axis toggle buttons.
        axisBtnColumn = mc.columnLayout(parent=controlLayout, adjustableColumn=True, columnAlign="center")
        mc.text("Axis Toggles", align="center")
        axisBtnLayout = mc.rowLayout(parent=axisBtnColumn, numberOfColumns=3, adjustableColumn=3, columnAlign=(1, "center"))
        xCheckBox = mc.checkBox(label="X",  parent=axisBtnLayout, value=True, changeCommand=lambda x: self.toggle_all_btns(self.jointTree, xCheckBox, 1, self.jointDict))
        yCheckBox = mc.checkBox(label="Y",  parent=axisBtnLayout, value=True, changeCommand=lambda x: self.toggle_all_btns(self.jointTree, yCheckBox, 2, self.jointDict))
        zCheckBox = mc.checkBox(label="Z",  parent=axisBtnLayout, value=True, changeCommand=lambda x: self.toggle_all_btns(self.jointTree, zCheckBox, 3, self.jointDict))
        self.BtnStatus = [1, 1, 1]


        #Create a small layout for the frame input.
        frmLayout = mc.columnLayout(parent=controlLayout, adjustableColumn=True)
        mc.text("Anim Cycle Length")
        self.framesInput = mc.textField(parent=frmLayout, text="5")
        self.animBtn = mc.button(label="Animate", parent = controlLayout, command=( lambda data: self.run_wpt(self.jointDict) ) )

        self.timeRangeEdit = mc.checkBox(label="Adjust \nFrame Range", parent=controlLayout, value=True)

        mc.separator(parent=controlLayout, horizontal=False, height=20)

        self.clrAnimBtn = mc.button(label="Clear All \nAnimation", parent=controlLayout,
                                    command=lambda x: self.clear_anim(self.jointDict)
                                    )
        self.clearTreeBtn = mc.button(label="Empty TreeView", 
                                      parent=controlLayout, 
                                    #   command=lambda x: self.treeEmpty(self.jointTree)
                                      command=lambda x: self.check_tree_empty(tree=self.jointTree, dictionary=self.jointDict)
                                    #   command=lambda x: self.checkDialog(message="Are you sure you want to clear the entire treeView???", 
                                    #                                     action=lambda y:self.treeEmpty(self.jointTree) )
                                    )

        #Arrange the layouts inside the main layout.
        mc.formLayout(mainLayout, e=True, 
                      attachForm=[(treeLayout, "top", 5), 
                                (treeLayout, "left", 5),
                                (treeLayout, "bottom", 5),
                                (controlLayout, "top", 5), 
                                (controlLayout, "right", 5),
                                (controlLayout, "bottom", 5)
                                ],
                    attachControl=[ (treeLayout, "right", 10, controlLayout)]
                                        )
        
        #Check for, then read/create, the dictionary node.
        self.jointDict = nodes.node_check_create("WeightTesterNode", "WeightTestDict")
        if len(self.jointDict) > 0:
            #Clear the selection then select all objects listed in the dictionary node.
            mc.select(clear=True)
            for obj in self.jointDict.keys():
                if mc.objExists(obj):
                    mc.select(obj, add=True)
                else:
                    print(f"{obj} not found. Skipping.")
            #Add the selected objects to the treeView and sets their buttons.
            self.tree_add(self.jointTree)
            for item in mc.treeView(self.jointTree, q=True, children=True):
                self.btns_rebuild(self.jointTree, item, self.jointDict)
            mc.select(clear=True)


        #################
        ###   DEBUG   ###
        #################
        #self.debugBtn = mc.button(label="DEBUG", parent=controlLayout, command=lambda x: print(self.jointDict))
        # debugLayout = mc.formLayout(mainLayout, e=True,
        #               attachForm=[(self.debugBtn, "bottom", 20),
        #                           (self.debugBtn, "right", 20),
        #                           (self.debugBtn, "left", 20),],
        #                 attachControl=[(self.debugBtn, "top", 20, treeLayout)]
        #               )

        #Open the window and reset its size.
        mc.showWindow()
        mc.window(self.app, edit=True, widthHeight=self.winSize)



##############################
###   TREEVIEW FUNCTIONS   ###
##############################
    def toggle_all_btns(self, tree, chkBx, btnNum, dictionary=False):
        """
        Turns all buttons of the given position on or off and toggles the corresponding dictionary values.
        """
        #Gets the value of the given checkbox.
        value = mc.checkBox(chkBx, q=True, value=True)
        #Uses the given number to decide which axis the button will affect
        if btnNum == 1:
            axis = "x"
        if btnNum == 2:
            axis = "y"
        if btnNum == 3:
            axis = "z"
        #List all items int eh treeView.
        allItems = mc.treeView(tree, q=True, children=True)
        if allItems:
            #Set the button and dictionary values for each item based on the checkbox's value.
            for item in allItems:
                if value:
                    #print(f"{item=} {axis=}")
                    self.tree_btn_set(tree, item, btnNum=btnNum, btnText=axis, btnStyle="2StateButton", btnState="buttonUp", command=lambda item, y: self.dict_axis_toggle(item, axis))
                    dictionary[item][axis] = 1
                else:
                    self.tree_btn_set(tree, item, btnNum=btnNum, btnText=axis, btnStyle="2StateButton", btnState="buttonDown", command=lambda item, y: self.dict_axis_toggle(item, axis))
                    dictionary[item][axis] = 0
        #Update the data node.
        nodes.overwrite_node("WeightTesterNode.WeightTestDict", self.jointDict)


    def tree_exist_check(self, tree, obj) -> bool:
        """
        Checks if the given object already exists in the treeView.
        -> Returns a boolean variable.
        """
        objExists = mc.treeView(tree, q=True, itemExists=obj)
        #self.exists = False
        if objExists:
            print(f"Skipping {obj}: {obj} already exists in the treeView.")
            return True
        else:
            return False
        
    
    def parent_check(self, tree, obj) -> str:
        """
        Checks if the given object has any parents in the scene. If it does, it checks if the parent object is in the treeView as well.
        -> If it is, return the parent object. Otherwise return "".
        """
        allParents = mc.listRelatives(obj, parent=True, fullPath=True)
        #print(f"{obj}: {allParents=}")
        if allParents:
            parents = allParents[0].split("|")
            parents.reverse()
            #print(f"{parents=}")
            for parent in parents:
                parExists = mc.treeView(tree, q=True, itemExists=parent)
                if parExists:
                    #print(f"{obj}: {parent=}")
                    return parent
        else:
            objParent = ""
            return objParent
        
    
    def child_check(self, tree, obj) -> list:
        """
        Checks if the given object has children in the scene. If it does, it checks if the child objects are in the treeView as well.
        -> If they are, return a list of the children. Otherwise return an empty list.
        """
        #List the given object's immediate children in the scene
        sceneChildren = mc.listRelatives(obj, allDescendents=True)
        #print(f"{sceneChildren=}")
        if sceneChildren and len(sceneChildren) > 0:
            #Create a list of items in the TreeView that match children of the object.
            treeChildren = []
            for sc in sceneChildren:
                if mc.treeView(tree, q=True, itemExists=sc):
                    treeChildren.append(sc)
                    gChild = self.child_check(tree, sc)
                    if len(gChild) < 1:
                        pass
            #print(f"{treeChildren=}")
            #Return the list of children.
            return treeChildren
        else:
            return []
                        

    
    def tree_move(self, tree, obj, parent, dictionary=False):
        """
        "Moves" a treeView item by deleting it and recreating it under a new parent item.
        Accounts for any child items under the given item as well as their button states.
        """
        #Save a list of all of the item's children.
        treeChildren = self.tree_child_check(tree, obj)
        #Remove the given item from the list (but not the dictionary).    
        mc.treeView(tree, e=True, removeItem=obj)
        #Add the item back into the list under its parent (without affecting the dictionary).
        mc.treeView(tree, e=True, insertItem=(obj, parent, 0))
        #Rebuild the item's buttons in a default state.
        self.tree_btn_set(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(obj, "x"))
        self.tree_btn_set(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(obj, "y"))
        self.tree_btn_set(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(obj, "z"))
        #print(f"moved {obj}, under {parent}")
        #Add back any children (without affecting the dictionary).
        if len(treeChildren) > 0:
            for tc in treeChildren:
                mc.select(tc, replace=True)
                self.tree_add(tree)
                self.tree_btn_set(tree, tc, btnNum=1, btnText="x", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(tc, "x"))
                self.tree_btn_set(tree, tc, btnNum=2, btnText="y", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(tc, "y"))
                self.tree_btn_set(tree, tc, btnNum=3, btnText="z", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(tc, "z"))
        #Rebuild the item's and its children's buttons in the states they were before they were moved.
        if dictionary:
            self.btns_rebuild(tree, obj, dictionary)
            for tc in treeChildren:
                self.btns_rebuild(tree, tc, dictionary)
            

    def btns_rebuild(self, tree, obj, dictionary)-> dict:
        """
        Reads the button states of an object in the given dictionary and recreates the buttons using that information.
        """
        #Reads the saved button states from the dictionary and sets each button to its "buttonDown" or "buttonUp" state.
        if dictionary[obj].get("x") == 0:
            self.tree_btn_set(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dict_axis_toggle(obj, "x"))
        elif dictionary[obj].get("x") == 1:    
            self.tree_btn_set(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dict_axis_toggle(obj, "x"))
        if dictionary[obj].get("y") == 0:
            self.tree_btn_set(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dict_axis_toggle(obj, "y"))
        elif dictionary[obj].get("y") == 1: 
            self.tree_btn_set(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dict_axis_toggle(obj, "y"))
        if dictionary[obj].get("z") == 0:
            self.tree_btn_set(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dict_axis_toggle(obj, "z"))
        elif dictionary[obj].get("z") == 1: 
            self.tree_btn_set(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dict_axis_toggle(obj, "z"))

        #Alternate version with a loop that broke the dictAxisToggle() to only work on "z" axis.
        # btnStates = [[1, "x", dictionary[obj].get("x")], [2, "y", dictionary[obj].get("y")], [3, "z", dictionary[obj].get("z")]]
        # for bs in btnStates:
        #     #Create buttons in their "down" or "up" state based on the dictionary info.
        #     if bs[2] == 0:
        #         self.treeBtnSet(tree, obj, btnNum=bs[0], btnText=bs[1], btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dictAxisToggle(obj, bs[1]))
        #     else:
        #         self.treeBtnSet(tree, obj, btnNum=bs[0], btnText=bs[1], btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dictAxisToggle(obj, bs[1]))


    def tree_add(self, tree, dictionary=False):
        """
        Lists the objects selected in the Maya scene and runs them through a series of checks before adding them to the treeView.
        Adds the object to the jointDict.
        Checks if each object has parents and/or children that are already in the tree and adjusts its hierarchies to match.
        """
        #List all selected objects
        objs = mc.ls(sl=True)
        for obj in objs:
            self.attr_check(obj, ["rotateX", "rotateY", "rotateZ"])
            #Check if each object exists in the treeView and add it if it doesn't.
            if not self.tree_exist_check(tree, obj): #-> bool
                if not dictionary == False:
                    self.dict_add(obj)
                #Check if the object in the scene has a parent and if that parent is in the treeView. If it is, add the new item under its parent.
                objParent = self.parent_check(tree, obj) #-> "" or parent of obj str
                mc.treeView(tree, e=True, addItem=[obj, objParent])
                self.tree_btn_set(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(obj, "x"))
                self.tree_btn_set(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(obj, "y"))
                self.tree_btn_set(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", command=lambda obj, axis: self.dict_axis_toggle(obj, "z"))
                #Check if the object in the scene has any children and if those children are also items in the treeView.
                children = self.child_check(tree, obj) #-> list of children
                #If they are, Move them under the new item.
                if children and len(children) > 0:
                    for c in children:
                        cParent = self.parent_check(tree, c)
                        self.tree_move(tree, c, cParent, self.jointDict)
        #Update the data node.
        nodes.overwrite_node("WeightTesterNode.WeightTestDict", self.jointDict)
    

    def attr_check(self, obj, attrs=[]):
        """
        Checks a given object's given attributes if they're locked or connected to something else. 
        """
        #Set some variables that will be checked at the the end.
        lockCheck = False
        consCheck = False
        for attr in attrs:
            #Attach the object to the attribute.
            fullAttr = f"{obj}.{attr}"
            #Check if the attribute is locked.
            if mc.getAttr(fullAttr, lock=True):
                lockCheck = True
            #Check if the attribute is attached to a constraint.
            constraintCheck = mc.listConnections(fullAttr, skipConversionNodes=True)
            #print(f"{fullAttr=}:{constraintCheck=}")
            if constraintCheck:
                for connection in constraintCheck:
                    #print(connection)
                    if "Constraint" in connection:
                        consCheck = True
        #Print a warning if any of the object's attributes are locked or constrained.
        if lockCheck:
            print(f"{obj} has locked attributes! Proceed with caution.")
        if consCheck:
            print(f"{obj} has constrained attributes! Proceed with caution.")
            

    def tree_btn_set(self, tree, item, 
                  btnNum=1, 
                  btnText="", 
                  btnStyle="pushButton",
                  btnState="buttonUp",
                  command=lambda x, y: print("button Pressed") 
                  ):
        """
        Sets a treeView item's button parameters.
        """
        mc.treeView(tree, e=True, buttonStyle=(item, btnNum, btnStyle), 
                    buttonTextIcon=(item, btnNum, btnText), 
                    buttonState=(item, btnNum, btnState), 
                    pressCommand=(btnNum, command) 
                    ) 

    
    def tree_child_check(self, tree, obj) -> list: 
        """
        Checks if a given treeView item has any children and returns them in a list.
        """
        children = mc.treeView(tree, q=True, children=obj)[1:]
        #print(f"{children=}")
        return children

    
    def tree_remove(self, tree, dictionary=False):
        """
        Checks if the selected item has any children and
        Removes the selected items in the treeView from the treeView and from the jointDict.
        """
        #List all items selected in the treeView.
        rmvItems = mc.treeView(tree, q=True, selectItem=True)
        strayChildren = []
        for ri in rmvItems:
            #Check for children under the selected items.
            leafChildren = self.tree_child_check(tree, ri) #->children under each item in rmvItems []
            if len(leafChildren) > 0:
                #Move any children to the root so they're not deleted with their parent.
                #print(f"{leafChildren=}")
                for lc in leafChildren:
                    godParent = mc.treeView(tree, q=True, itemParent=ri)
                    while godParent in rmvItems:
                        godParent = mc.treeView(tree, q=True, itemParent=godParent)
                    self.tree_move(tree, lc, godParent, dictionary)
                    strayChildren.append(lc)
        while len(rmvItems) > 0:
            for ri in rmvItems:
                if dictionary:
                    #Remove the item from the given dictionary as well.
                    dictionary.pop(ri)
                if mc.treeView(tree, q=True, itemExists=ri):
                    #Remove the item from the treeView.
                    mc.treeView(tree, e=True, removeItem=(ri) )
                #Remove the item from the list of items to remove.
                rmvItems.remove(ri)
                #Remove the item from the list of children if it's in there.
                if ri in strayChildren:
                    strayChildren.remove(ri)
        #print(f"final {strayChildren=}")
        for sc in strayChildren:
            parent = self.parent_check(tree, sc)
            #print(f"{sc=},{parent=}")
            self.tree_move(tree, sc, parent, dictionary)
        #Update the data node.
        nodes.overwrite_node("WeightTesterNode.WeightTestDict", self.jointDict)

    
    def tree_empty(self, tree, dictionary=False):
        """
        Deletes all items from the given treeView and clears them from a dictionary.
        """
        #Saves all items in the treeView.
        allItems = mc.treeView(tree, q=True, children=True)
        if allItems:
            #Selects each itemsthe topmost item and deletes it from the treeView and dictionary.
            mc.treeView(tree, e=True, selectItem=[allItems[0], 1])
            self.tree_remove(tree, dictionary)
        #Repeats the above process until the treeView is empty.
        allItems = mc.treeView(tree, q=True, children=True)
        if allItems:
            self.tree_empty(tree, dictionary)
        else:
            print("Weight paint tester treeView cleared.")
            #Just to be safe, empties the dictionary as well.
            if dictionary:
                dictionary.clear()
                #Update the data node.
                nodes.overwrite_node("WeightTesterNode.WeightTestDict", self.jointDict)


    def check_dialog(self, message):
        """
        Creates a confirmation dialog that double checks if you want to perform an action.
        """
        #Creates the dialog popup with the following settings and options.
        check = mc.confirmDialog(title="Are You Sure?", 
                                 message=message, 
                                 button=["Confirm", "Cancel"], 
                                 cancelButton="Cancel", 
                                 defaultButton="Cancel")
        if check == "Confirm":
            return "Confirm"
        else:
            return print("Action cancelled.")
    

    def check_tree_empty(self, tree, dictionary=False):
        """
        Uses a confirmation dialog to double check if you want to empty the treeView and jointDict.
        Then opens a confirmation dialog to check if you want to delete the weightTester node.
        """
        animCheck = self.check_anim(dictionary)
        if animCheck == "Confirm":
            self.tree_empty(tree, dictionary)
        elif animCheck == "Cancel":
            return
        else:
            check = self.check_dialog(message="Are you sure you want to clear the entire treeView?")
            if check == "Confirm":
                self.tree_empty(tree, dictionary)
        
        if mc.objExists("WeightTesterNode"):
            nodeCheck = self.check_dialog(message="Do you want to delete the \nWeightTesterNode as well?")
            if nodeCheck == "Confirm":
                mc.delete("WeightTesterNode")
    

    def Tree_to_scene_select(self, tree):
        """
        Selects an object in the Maya scene when it is selected in the treeView.
        """
        selectedItems = mc.treeView(tree, q=True, selectItem=True)
        mc.select(selectedItems, replace=True)


    def dict_order(self, tree, dictionary):
        """
        Reorders a dictionary to match the treeView.
        """
        #print(f"{dictionary=}")
        treeOrder = mc.treeView(tree, q=True, children=True)
        #print(treeOrder)
        dictionary = {jnt: dictionary[jnt] for jnt in treeOrder}
        #print(f"reordered {dictionary=}")
        return dictionary



##########################
###   TOOL FUNCTIONS   ###
##########################

    def select_object_hierarchy(self, *args):
        """
        Takes the first selected object and selects all of its children that share its object type.
        """
        try:
            #List the first object selected.
            objs = mc.ls(sl=True)
            allObjs = []
            for obj in objs:
                #Get teh object's type.
                objType = mc.objectType(obj)
                #print(objType)
                #If the object is a joint, return all of its child joints.
                if objType == "joint":
                    children = mc.listRelatives(obj, allDescendents=True, noIntermediate=True, type="joint")
                #Otherwise return all children of the same object type that have a shape.
                else:
                    children=[]
                    #print(objType)
                    allChildren = mc.listRelatives(obj, allDescendents=True, noIntermediate=True, type=objType)
                    #print(f"{allChildren=}")
                    if allChildren:
                        for child in allChildren:
                            childShape = mc.listRelatives(child, shapes=True)
                            #print(f"{child=}, {childShape=}")
                            if childShape:
                                children.append(child)
                if children == None:
                    return print("Object has no children.")
                else:
                    #Reverse the list of children and place the selected object at the top of the list.
                    children.reverse()
                    children.insert(0, obj)
                    #print(f"{children=}")
                    #Add the objects to a list.
                    for child in children:
                        allObjs.append(child)
            #Select the object and its children.
            mc.select(allObjs, replace=True)
        except ValueError: 
            print("ValueError: Duplicate objects in hierarchy or no child joints to select!")


  
    def dict_add(self, item):
        """
        Sets up an item in the dictionary with its xyz values at 1.
        """
        self.jointDict.update({item:{"x":1, "y":1, "z":1}})
    

    def bool_toggle(self, value):
        """
        Takes a boolean and reverses it.
        """
        if value == 1:
            return 0
        else:
            return 1
        
        

    def dict_axis_toggle(self, item, axis):
        """
        Toggle an axis/value in the dictionary.
        """
        #print(f"{item=} {axis=}")
        axisData = self.jointDict[item].get(axis)
        self.jointDict[item].update({axis: self.bool_toggle(axisData)})
        #print(f"{item} {axis} updated to {self.boolToggle(axisData)}")
        #Update the data node.
        nodes.overwrite_node("WeightTesterNode.WeightTestDict", self.jointDict)
    

    def weight_test_anim(self, obj, axis, frame, len):
        """
        Animates a given object to rotate on a given axis from 90 to -90 degrees over a given number of frames.
        """
        #Save the object's current value.
        startValue = mc.getAttr(f"{obj}.rotate{axis.upper()}")
        mc.setKeyframe(obj, respectKeyable=True, attribute=f"rotate{axis.upper()}", time=frame)
        mc.setKeyframe(obj, respectKeyable=True, attribute=f"rotate{axis.upper()}", time=frame+len, value=90)
        mc.setKeyframe(obj, respectKeyable=True, attribute=f"rotate{axis.upper()}", time=frame+(len*3), value=-90)
        #Key the object attribute back to its starting value.
        mc.setKeyframe(obj, respectKeyable=True, attribute=f"rotate{axis.upper()}", time=frame+(len*4), value=startValue)
    

    def run_wpt(self, dictionary):
        """
        Reads jointDict and animates each joints on the enabled axes.
        """
        #Get the number of frames from the window input.
        getFrameLen = int(mc.textField(self.framesInput, q=True, text=True) )
        #Set the frames to start at 1.
        frame = 1
        #Reorder the dictionary to match the treeView.
        dictionary = self.dict_order(self.jointTree, dictionary)
        #For each joint in the dictionary,
        for obj in dictionary.keys():
            for axis in dictionary[obj].keys():
                #get which axes are enabled,
                if dictionary[obj].get(axis) == 1:
                    #animate the enabled axes,
                    self.weight_test_anim(obj, axis, frame, getFrameLen)
                    #and move the active frame forward.
                    frame += getFrameLen * 4
                    lastFrame = frame
                else:
                    pass
        #Save the current frame range start and end values.
        self.minFrameRange = mc.playbackOptions(q=True, minTime=True)
        self.maxFrameRange = mc.playbackOptions(q=True, maxTime=True)
        #If the 
        getTrEdit = mc.checkBox(self.timeRangeEdit, q=True, value=True)
        if getTrEdit:
            #print(self.minFrameRange, self.maxFrameRange)
            mc.playbackOptions(e=True, minTime=1, maxTime=lastFrame)
    

    def clear_anim(self, data):
        """
        Deletes all keyframes from the joints in the treeView
        """
        #Set current time to 1 to reset the skeleton pose.
        mc.currentTime(1, update=True)
        #Select all of the objects in the treeView and delete their animation.
        for obj in data.keys():
            mc.select(obj, add=True)
        mc.cutKey()
        #If the "Adjust Frame Range" box is checked, set the start and end frames to the values that were saved when the animation was generated.
        getTREdit = mc.checkBox(self.timeRangeEdit, q=True, value=True)
        if getTREdit:
            mc.playbackOptions(e=True, animationStartTime=self.minFrameRange, animationEndTime=self.maxFrameRange)
            
    

    def check_anim(self, data):
        """
        Checks if the objects in the given dictionary have any animation on them and brings up a warning if they do.
        """
        keyedObj = []
        #Check each object for keyframes.
        for obj in data.keys():
            if mc.keyframe(obj, q=True, keyframeCount=True) > 0:
                keyedObj.append(obj)
        if len(keyedObj) > 0:
            confirm = self.check_dialog(message=f"{keyedObj} have keyframes. Are you sure you want to continue?")
            if confirm == "Confirm":
                return confirm
            else:
                return "Cancel"
        else:
            return "Clear"

    


#Create an instance of the tool and launch it.
if __name__ == "__main__":
    tester = WeightTester()