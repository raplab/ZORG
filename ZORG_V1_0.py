###############################################################################
# ZORG
# Rhinoscript: Convert and send Jobs to Zuend Cutting Machines using Rhino V5 
#
# Copyright (C) 2013  Daniel Bachmann, Alessandro Tellini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ZORG
# Date/Version: 04.04.2013  V1.0
#
# Written by  -  Daniel Bachmann       (daniel.bachmann@arch.ethz.ch)
#             -  Alessandro Tellini    (tellini@arch.ethz.ch)
#
# Snail-Mail Contact:
# ETH Zürich
# RAPLAB D-ARCH Daniel Bachmann
# HIL D34.2
# Wolfgang-Pauli-Str. 15
# 8093 Zürich
#
# Streamlined Zuend Machine Cutting and Engraving out of Rhino V5
# ZORG converts Curves and translates them into Zuend-HPGL, then 
# streams the Data directly to the Zuend-Cutter.
# The Script is meant to be started from Rhino Command-Line but can
# also be assigned to an Icon.
#
# Prerequisites:
# The Script is depending on pyserial http://sourceforge.net/projects/pyserial/ to send commands to the Zuend-Machine.
# Make sure you copy the serial folder of the unpacked pyserial to the same directory where the ZORG script resides.
# ->   Rhinoscriptfolder|serial
#                       |ZORG_V1_0.py
#
# To create a Rhino Command Line Alias:
# -Open Tools|Options|Aliases from the Rhino Menu
# -Press "New" to create a new Alias
# -Enter a name for the Alias. We prefer to use ZORG as command-name ;)
# -Enter the following as Command Macro:  ! _-RunPythonScript "FilePath\ScriptFileName"
# -It should look like this: ! _-RunPythonScript "C:\Users\User\AppData\Roaming\McNeel\Rhinoceros\5.0\scripts\ZORG_V1_0.py"
#
# Using the variable definitions it is possible to customize the default Workspace Area and Cutting Speeds/Depths
# Use the sendToMachine Variable-Option to save to a local file instead of sending the Data directly to the Zuend-Cutter
#
# The script does some basic error-handling:
# -Only Curves will be selectable
# -A Bounding Box is used to check if all selected Curves are in the Workspace Area
#
# Changes/Bugfixes
# ----------------
# 
#
###############################################################################


import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import serial

#Turns off Windows Popup Server Busy message in Rhino
Rhino.Runtime.HostUtils.DisplayOleAlerts(False)

#Switches from Machine to File Output
sendToMachine=True      #False for File Output

#default variables for Workspace settings
maxWSPx=1601            #Max Workspace Coordinate +1 X-Axis in mm
maxWSPy=1301            #Max Workspace Coordinate +1 Y-Axis in mm
minWSPx=-1              #Min Workspace Coordinate -1 X-Axis in mm
minWSPy=-1              #Min Workspace Coordinate -1 Y-Axis in mm

#default variables for Commandline Options
minSpeed = 1            #Min Speed in mm/s
maxSpeed = 30           #Max Speed in mm/s
defaultSpeed = 30       #Default Speed in mm/s
minDepth = 0.01         #Min Depth in mm
maxDepth = 40.00        #Max Depth in mm
defaultDepth = 1.00     #Default Depth in mm

#default variables for HPGL
VS = "VS 10, 40;"       #Default Settings for PenUp/PenDown Velocity
ZP = "ZP 1000, 200;"    #Default Settings for Z Axis Position

################################################################################
#Zorg handles the Commandline Input
def zorg():
    # Curve Selection
    objectList = rs.GetObjects("Select all curves you want to cut", rs.filter.curve)

    # Option Configuration
    go = Rhino.Input.Custom.GetOption()
    go.SetCommandPrompt("Select cutting options. Press Enter when Done:")
    rs.SelectObjects(objectList)

    #set options for CommandPrompt
    listValues = "Tool1", "Tool2", "Pen"
    DepthOpt   = Rhino.Input.Custom.OptionDouble(defaultDepth, minDepth, maxDepth)
    SpeedOpt   = Rhino.Input.Custom.OptionInteger(defaultSpeed, minSpeed, maxSpeed)
    listIndex = 0
    opList = go.AddOptionList("Tool", listValues, listIndex)
    go.AddOptionDouble("Depth", DepthOpt)
    go.AddOptionInteger("Speed", SpeedOpt)

    #Check Boundary for curves not fitting into workspace
    poschecker = checkBound(objectList)
    if poschecker:
        #Loop to set CommandPrompt variables 
        while True:
            get_rc = go.Get()
            if get_rc == Rhino.Input.GetResult.Option:
                #Refresh Option Variables
                if go.OptionIndex()==opList:
                    listIndex = go.Option().CurrentListOptionIndex
                continue
            break

        # Give Feedback about Settings
        print "Your have entered following values:"
        print " Tool =", listValues[listIndex]
        print " Depth in mm =", DepthOpt.CurrentValue
        print " Speed in mm/s =", SpeedOpt.CurrentValue

        # Send the Curves to Machine or abort
        polyline = []
        if objectList:
            for id in objectList:
                polyline.append(rs.ConvertCurveToPolyline(id,5.0,0.01,True))
        else:
            print("no lines selected")
        checkUser = rs.GetString("Do you want to send this Job to the machine?","y","y / n")
        if checkUser == "y":
            sendEverything (polyline, listIndex, DepthOpt.CurrentValue*100, SpeedOpt.CurrentValue)
            print("ZORG has finished your job successfully")
        else:
            print("Almighty ZORG forgives you!")
        return Rhino.Commands.Result.Success
    else:
        return

################################################################################
#Serial Stream, handles Baudrate, Encoding....
def serialSend(stream):
    ser=serial.Serial(0,19200)
    print("ZORG is streaming now....please wait....")
    try:
        ser.write(bytes(stream, encoding='ascii'))
    except:
        print("error from serial port")
        pass
    ser.close()
    print("....stream sent")

################################################################################
#Send the job, handles Zuend-HPGL Conversion and streams the data to the machine
def sendEverything (lineObjects, tool, depth, speed):
    #compensate for pen -> equals tool 4
    tool = tool +1
    if tool == 3: tool = tool+1
    
    if sendToMachine:
        #-----------Export to Machine-START-----------------------------------------
        header = "PS 1,1;PB 2,1;\nDT 59;\nUR ZuendTest;\nSP "+str(tool)+"; "+"TR 1;PU;PA;\nSP "+str(tool)+";\n"+"ZP 1000, "+str(int(depth))+";\nSP "+str(tool)+";\nVS "+str(speed)+", 40;"
        footer = "PU;\nPU;\nPU;PA 160000,0;BP;PS 1,0;PB 2,0;NR;"
        commands = []
        tmpcommands = []
        for pline in lineObjects:
            curve = rs.CurvePoints(pline)
            i=0
            for p in curve:
                if i < 1:
                    tmpcommands.append("\n"+"PU "+str(int(p[0]*100))+", "+str(int(p[1]*100))+";")
                else:
                    tmpcommands.append("\n"+"PD "+str(int(p[0]*100))+", "+str(int(p[1]*100))+";")
                i = i+1
        commands.append(''.join(tmpcommands))
        serialSend(header+''.join(commands)+footer)
        #-----------Export to Machine-END---------------------------------------
    else:
        #-----------Export to File-START----------------------------------------
        f = open("C:\PLT\dump.plt","w")
        header = "PS 1,1;PB 2,1;\nDT 59;\nUR ZuendTest;\nSP "+str(tool)+"; "+"TR 1;PU;PA;\nSP "+str(tool)+";\n"+"ZP 1000, "+str(int(depth))+";\nSP "+str(tool)+";\nVS "+str(speed)+", 40;"
        footer = "PU;\nPU;\nPU;PA 160000,0;BP;PS 1,0;PB 2,0;NR;"
        commands = []
        tmpcommands = []
        for pline in lineObjects:
            curve = rs.CurvePoints(pline)
            i=0
            for p in curve:
                if i < 1:
                    tmpcommands.append("\n"+"PU "+str(int(p[0]*100))+", "+str(int(p[1]*100))+";")
                else:
                    tmpcommands.append("\n"+"PD "+str(int(p[0]*100))+", "+str(int(p[1]*100))+";")
                i = i+1
        commands.append(''.join(tmpcommands))
        f.write(header)
        f.writelines(''.join(commands))
        f.write("\n"+footer)
        f.close()
        print("job sent to file...")
        #-----------Export to File-END------------------------------------------


################################################################################
# Checks if Bounding Box fits in Workspace
def checkBound(selectedObj):
    box = rs.BoundingBox(selectedObj)
    if box:
        if ((min(box)[0]) < minWSPx) or ((min(box)[1]) < minWSPy) or ((max(box)[0]) > maxWSPx) or ((max(box)[1]) > maxWSPy):
            print ("ZORG says: Curves are not in Workspace-Area. Make sure your Curves are inside the Workspace!")
            return False
        else:
            print ("ZORG says: All Curves are happily located inside the Workspace")
            return True

if __name__ == "__main__":
    zorg()