This Maya tool is meant help with testing deformation on rigged meshes. It lists skeleton joints and animates them to rotate 180 degrees on their chosen axes.

INSTALLATION:
- Save the folder this file is in to your maya/scripts directory.
- Drag and drop weightTester_INSTALL.py into your Maya viewport.
- A button should be created in your "custom" shelf.

Press the button to open the tool.

USING THE TOOL

Use the following controls on the right side of the Weight Paint Tester to select, add, remove, and animate joints in the tree view on the left side of the window.
Select Joint Hierarchy: Selects all child and grandchild joints of whichever joints you have selected.
Add Object: Adds all selected objects to the tree view, parenting them accordingly if their parents are included.
Remove Object: Removes any selected objects from the tool that you've selected in the tree view.
Axis Toggles: Turn all buttons of the chosen axis on and off for every item in the treeView
Anim Cycle Length: Set how many frames you want the tool to put between keyframes.
Animate: Runs the tool and animates each joint listed in the tree view to bend back and forth. If "Adjust Frame Range" is checked, it will set the viewport timeline to show the entire length of its animation.
Clear All Animation: Deletes all keyframes from the listed joints and sets their rotations back to 0. If "Adjust Frame Range" is checked, it will revert the viewport timeline to the values it was at when "Animate" was pressed.
Empty TreeView: Removes all joints from the tool's tree view. NOTE: This does not reset the joints nor does it clear animation.