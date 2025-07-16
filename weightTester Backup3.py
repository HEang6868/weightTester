import maya.cmds as mc


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
        self.winSize = (500, 500)
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

        treeLayout = mc.frameLayout(parent=mainLayout, label="Joints",
                                    collapsable=False,
                                    )
        self.jointTree = mc.treeView(parent=treeLayout, 
                                    attachButtonRight=True,
                                    numberOfButtons=3,
                                    allowDragAndDrop=True,
                                    allowReparenting=False,  
                                    selectionChangedCommand=lambda: self.TreeToSceneSelect(self.jointTree)
                                    )
        controlLayout = mc.columnLayout(parent=mainLayout, adjustableColumn=True,
                                        width=120,
                                       generalSpacing=15,
                                       margins=5,
                                       )
        self.jntHierBtn = mc.button(label="Select Joint \nHierarchy", parent = controlLayout, command=self.selHierarchy)
        self.addJntBtn = mc.button(label="Add Joint", parent = controlLayout, command=( lambda tree: self.treeAdd(self.jointTree, dictionary=self.jointDict) ) )
        self.rmvJntBtn = mc.button(label="Remove Joint", parent = controlLayout, command=( lambda tree: self.treeRemove(self.jointTree, dictionary=self.jointDict) ) )

        mc.separator(parent=controlLayout, horizontal=False, height=1)

        frmLayout = mc.columnLayout(parent=controlLayout, adjustableColumn=True)
        mc.text("Anim Cycle Length")
        self.framesInput = mc.textField(parent=frmLayout, text="5")
        self.animBtn = mc.button(label="Animate", parent = controlLayout, command=( lambda data: self.runWPT(self.jointDict) ) )

        self.timeRangeEdit = mc.checkBox(label="Adjust \nFrame Range", parent=controlLayout, value=True)

        mc.separator(parent=controlLayout, horizontal=False, height=50)

        self.clrAnimBtn = mc.button(label="Clear All \nAnimation", parent=controlLayout,
                                    command=lambda x: self.clearAnim(self.jointDict)
                                    )
        self.clearTreeBtn = mc.button(label="Empty TreeView", 
                                      parent=controlLayout, 
                                    #   command=lambda x: self.treeEmpty(self.jointTree)
                                      command=lambda x: self.checkTreeEmpty(tree=self.jointTree, dictionary=self.jointDict)
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

        #################
        ###   DEBUG   ###
        #################
        # self.debugBtn = mc.button(label="DEBUG", parent=controlLayout,
        #                         command=lambda x: self.dictOrder(self.jointTree, self.jointDict)
        #                         )
        # mc.formLayout(mainLayout, e=True,
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

    def treeExistCheck(self, tree, obj) -> bool:
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
        
    
    def parentCheck(self, tree, obj) -> str:
        """
        Checks if the given object has a parent in the scene. 
        If it does, it checks if the parent object is in the treeView as well.
        -> If it is, return the parent object. Otherwise return "".
        """
        objParent = mc.listRelatives(obj, parent=True)
        if objParent:
            objParent = objParent[0]
            parExists = mc.treeView(tree, q=True, itemExists=objParent)
            if parExists:
                return objParent
        else:
            objParent = ""
            return objParent
        
    
    def childCheck(self, tree, obj) -> list:
        """
        Checks if the given object has children in the scene. 
        If it does, it checks if the child objects are in the treeView as well.
        -> If they are, return a list of the children. Otherwise return an empty list.
        """
        #List the given object's immediate children in the scene
        sceneChildren = mc.listRelatives(obj, children=True)
        #print(f"{sceneChildren=}")
        if sceneChildren and len(sceneChildren) > 0:
            #Create a list of items in the TreeView that match children of the object.
            treeChildren = []
            for sc in sceneChildren:
                if mc.treeView(tree, q=True, itemExists=sc):
                    treeChildren.append(sc)
                    gChild = self.childCheck(tree, sc)
                    if len(gChild) < 1:
                        pass
            #print(f"{treeChildren=}")
            #Return the list of children.
            return treeChildren
        else:
            return []
                        

    
    def treeMove(self, tree, obj, parent, dictionary=False):
        """
        "Moves" a treeView item by deleting it and recreating it under a new parent item.
        Accounts for any child items under the given item as well as their button states.
        """
        #Save a list of all of the item's children.
        treeChildren = self.treeChildCheck(tree, obj)
        #Remove the given item from the list (but not the dictionary).    
        mc.treeView(tree, e=True, removeItem=obj)
        #Add the item back into the list under its parent (without affecting the dictionary).
        mc.treeView(tree, e=True, insertItem=(obj, parent, 0))
        #Rebuild the item's buttons in a default state.
        self.treeBtnSet(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(obj, "x"))
        self.treeBtnSet(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(obj, "y"))
        self.treeBtnSet(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(obj, "z"))
        #print(f"moved {obj}, under {parent}")
        #Add back any children (without affecting the dictionary).
        if len(treeChildren) > 0:
            for tc in treeChildren:
                mc.select(tc, replace=True)
                self.treeAdd(tree)
                self.treeBtnSet(tree, tc, btnNum=1, btnText="x", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(tc, "x"))
                self.treeBtnSet(tree, tc, btnNum=2, btnText="y", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(tc, "y"))
                self.treeBtnSet(tree, tc, btnNum=3, btnText="z", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(tc, "z"))
        #Rebuild the item's and its children's buttons in the states they were before they were moved.
        if dictionary:
            self.btnsRebuild(tree, obj, dictionary)
            for tc in treeChildren:
                self.btnsRebuild(tree, tc, dictionary)
            

    def btnsRebuild(self, tree, obj, dictionary)-> dict:
        """
        Reads the button states of an object in the given dictionary and recreates the buttons using that information.
        """
        #Reads the saved button states from the dictionary and sets each button to its "buttonDown" or "buttonUp" state.
        if dictionary[obj].get("x") == 0:
            self.treeBtnSet(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dictAxisToggle(obj, "x"))
        elif dictionary[obj].get("x") == 1:    
            self.treeBtnSet(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dictAxisToggle(obj, "x"))
        if dictionary[obj].get("y") == 0:
            self.treeBtnSet(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dictAxisToggle(obj, "y"))
        elif dictionary[obj].get("y") == 1: 
            self.treeBtnSet(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dictAxisToggle(obj, "y"))
        if dictionary[obj].get("z") == 0:
            self.treeBtnSet(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dictAxisToggle(obj, "z"))
        elif dictionary[obj].get("z") == 1: 
            self.treeBtnSet(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dictAxisToggle(obj, "z"))

        #Alternate version with a loop that broke the dictAxisToggle() to only work on "z" axis.
        # btnStates = [[1, "x", dictionary[obj].get("x")], [2, "y", dictionary[obj].get("y")], [3, "z", dictionary[obj].get("z")]]
        # for bs in btnStates:
        #     #Create buttons in their "down" or "up" state based on the dictionary info.
        #     if bs[2] == 0:
        #         self.treeBtnSet(tree, obj, btnNum=bs[0], btnText=bs[1], btnStyle="2StateButton", btnState="buttonDown", command=lambda obj, axis: self.dictAxisToggle(obj, bs[1]))
        #     else:
        #         self.treeBtnSet(tree, obj, btnNum=bs[0], btnText=bs[1], btnStyle="2StateButton", btnState="buttonUp", command=lambda obj, axis: self.dictAxisToggle(obj, bs[1]))


    def treeAdd(self, tree, dictionary=False):
        """
        Gets the objects selected in the Maya scene in a list and runs them through a series of checks before adding it to the treeView.
        Adds the object to the jointDict.
        Checks if each object has parents and/or children that are already in the tree and adjusts its hierarchies to match.
        """
        #List all selected objects
        objs = mc.ls(sl=True)
        for obj in objs:
            #Check if each object exists in the treeView and add it if it doesn't.
            if not self.treeExistCheck(tree, obj): #-> bool
                if not dictionary == False:
                    self.dictAdd(obj)
                #Check if the object in the scene has a parent and if that parent is in the treeView. If it is, add the new item under its parent.
                objParent = self.parentCheck(tree, obj) #-> "" or parent of obj str
                mc.treeView(tree, e=True, addItem=[obj, objParent])
                self.treeBtnSet(tree, obj, btnNum=1, btnText="x", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(obj, "x"))
                self.treeBtnSet(tree, obj, btnNum=2, btnText="y", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(obj, "y"))
                self.treeBtnSet(tree, obj, btnNum=3, btnText="z", btnStyle="2StateButton", command=lambda obj, axis: self.dictAxisToggle(obj, "z"))
                #Check if the object in the scene has any children and if those children are also items in the treeView.
                child = self.childCheck(tree, obj) #-> list of children
                #If they are, Move them under the new item.
                if child and len(child) > 0:
                    for c in child:
                        self.treeMove(tree, c, obj, self.jointDict)


    def treeBtnSet(self, tree, item, 
                  btnNum=1, 
                  btnText="", 
                  btnStyle="pushButton",
                  btnState="buttonUp",
                  command=lambda x, y: print("button Pressed") 
                  ):
        """
        Sets a treeView item's button parameters.
        """
        mc.treeView(tree, e=True, buttonStyle=(item, btnNum, btnStyle), buttonTextIcon=(item, btnNum, btnText), buttonState=(item, btnNum, btnState), pressCommand=(btnNum, command) ) 
    

    # def getTreeData(self, tree, dictionary=False):
    #     """
    #     Reads the given treeView and returns a dictionary of items and their pushed buttons.
    #     """
    #     allItems = mc.treeView(tree, q=True, children=True)

    #     for item in allItems:
    #         data = dictionary[item].items()
    #         print(data)

    
    def treeChildCheck(self, tree, obj) -> list: 
        """
        Checks if a given treeView item has any children and returns them in a list.
        """
        children = mc.treeView(tree, q=True, children=obj)[1:]
        #print(f"{children=}")
        return children

    
    def treeRemove(self, tree, dictionary=False):
        """
        Checks if the selected item has any children and
        Removes the selected items in the treeView from the treeView and from the jointDict.
        """
        #List all items selected in the treeView.
        rmvItems = mc.treeView(tree, q=True, selectItem=True)
        for ri in rmvItems:
            #Check for children under the selected items.
            leafChildren = self.treeChildCheck(tree, ri) #->children under each item in rmvItems []
            if len(leafChildren) > 0:
                #Add any children found to rmvItems.
                for lc in leafChildren:
                    if lc not in rmvItems:
                        rmvItems.append(lc)
        #Remove all items in rmvItems from the treeView.
        while len(rmvItems) > 0:
            for ri in rmvItems:
                if dictionary:
                    #Remove item from the given dictionary as well.
                    dictionary.pop(ri)
                if mc.treeView(tree, q=True, itemExists=ri):
                    mc.treeView(tree, e=True, removeItem=(ri) )
                rmvItems.remove(ri)   

    
    def treeEmpty(self, tree, dictionary=False):
        """
        Deletes all items from the given treeView and clears them from a dictionary.
        """
        #Saves all items in the treeView.
        allItems = mc.treeView(tree, q=True, children=True)
        if allItems:
            #Selects each itemsthe topmost item and deletes it from the treeView and dictionary.
            mc.treeView(tree, e=True, selectItem=[allItems[0], 1])
            self.treeRemove(tree, dictionary)
        #Repeats the above process until the treeView is empty.
        allItems = mc.treeView(tree, q=True, children=True)
        if allItems:
            self.treeEmpty(tree, dictionary)
        else:
            print("Weight paint tester treeView cleared.")
            #Just to be safe, empties the dictionary as well.
            if dictionary:
                dictionary.clear()


    def checkDialog(self, message):
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
    

    def checkTreeEmpty(self, tree, dictionary=False):
        """
        Uses a confirmation dialog to double check if you want to empty the treeView and jointDict.
        """
        check = self.checkDialog(message="Are you sure you want to clear the entire treeView?")
        if check == "Confirm":
            self.treeEmpty(tree, dictionary)
    

    def TreeToSceneSelect(self, tree):
        """
        Selects an object in the Maya scene when it is selected in the treeView.
        """
        selectedItems = mc.treeView(tree, q=True, selectItem=True)
        mc.select(selectedItems, replace=True)


    def dictOrder(self, tree, dictionary):
        """
        Reorders a dictionary to match the teeView.
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

    def selHierarchy(self, *args):
        """
        Takes the first selected joint and selects all of its child joints.
        """
        try:
            #List the first object selected.
            obj = mc.ls(sl=True)[0]
            #List any children that are joints.
            children = mc.listRelatives(obj, allDescendents=True, type="joint")
            children.reverse()
            children.insert(0, obj)
            #Select the object and its children.
            mc.select(children, replace=True)
        except ValueError: 
            print("ValueError: Duplicate objects in hierarchy or no child joints to select!")

  
    def dictAdd(self, item):
        """
        Sets up an item in the dictionary with its xyz values at 1.
        """
        self.jointDict.update({item:{"x":1, "y":1, "z":1}})
    

    def boolToggle(self, value):
        """
        Takes a boolean and reverses it.
        """
        if value == 1:
            return 0
        else:
            return 1
        

    def dictAxisToggle(self, item, axis):
        """
        Toggle an axis/value in the dictionary.
        """
        axisData = self.jointDict[item].get(axis)
        self.jointDict[item].update({axis: self.boolToggle(axisData)})
        #print(f"{item} {axis} updated to {self.boolToggle(axisData)}")
    

    def weightTestAnim(self, obj, axis, frame, len):
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
    

    def runWPT(self, dictionary):
        """
        Reads jointDict and animates each joints on the enabled axes.
        """
        #Get the number of frames from the window input.
        getFrameLen = int(mc.textField(self.framesInput, q=True, text=True) )
        #Set the frames to start at 1.
        frame = 1
        #Reorder the dictionary to match the treeView.
        dictionary = self.dictOrder(self.jointTree, dictionary)
        #For each joint in the dictionary,
        for obj in dictionary.keys():
            for axis in dictionary[obj].keys():
                #get which axes are enabled,
                if dictionary[obj].get(axis) == 1:
                    #animate the enabled axes,
                    self.weightTestAnim(obj, axis, frame, getFrameLen)
                    #and move the active frame forward.
                    frame += getFrameLen * 4
                    lastFrame = frame
                else:
                    pass
        #Save the current frame range start and end values.
        self.minFrameRange = mc.playbackOptions(q=True, minTime=True)
        self.maxFrameRange = mc.playbackOptions(q=True, maxTime=True)
        #If the 
        getTREdit = mc.checkBox(self.timeRangeEdit, q=True, value=True)
        if getTREdit:
            #print(self.minFrameRange, self.maxFrameRange)
            mc.playbackOptions(e=True, minTime=1, maxTime=lastFrame)


    def clearAnim(self, data):
        """
        Deletes all keyframes from the joints in the treeView
        """
        #Set current time to 1 to reset the skeleton pose.
        mc.currentTime(1, update=True)
        #Select all of the objects in the treeView and delete tehir animation.
        for obj in data.keys():
            mc.select(obj, add=True)
        mc.cutKey()
        #If the "Adjust Frame Range" box is checked, set the start and end frames to the values that were saved when the animation was generated.
        getTREdit = mc.checkBox(self.timeRangeEdit, q=True, value=True)
        if getTREdit:
            mc.playbackOptions(e=True, animationStartTime=self.minFrameRange, animationEndTime=self.maxFrameRange)

    



#Create an instance of the tool and launch it.
if __name__ == "__main__":
    tester = WeightTester()