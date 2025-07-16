myDict = {"family":{"person1":{"name":"Trent", "role":"father", "year":1954}, 
                  "person2":{"name":"Emily", "role":"mother","year":1955}, 
                  "person3":{"name":"Callum", "role":"son", "year":1980},
                  "person4":{"name":"Sasha", "role":"daughter", "year":1981}
                  }
        }

#print(myDict["family"]["person2"]["year"])

#print(myDict["family"]["person3"].items())

def boolToggle(value):
        if value == 1:
            value = 0
        else:
            value = 1
        return value

jointDict = {"joint1":{"x":1, "y":1, "z":1}, "joint2":{"x":1, "y":1, "z":1}, "joint3":{"x":1, "y":1, "z":1}}

btns = {1:"x", 2:"y", 3:"z"}

jointDict["joint2"].update({"y":0})
print(jointDict)

boolCheck = jointDict["joint3"].get("x")
print(boolCheck)
jointDict["joint3"].update({"x":boolToggle(boolCheck)})

print(jointDict)


for x, y in jointDict.items():
     print(x)
     print(y)

