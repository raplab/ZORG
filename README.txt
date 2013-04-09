ZORG
Rhinoscript: Convert and stream Jobs to Zuend Cutting Machines using HPGL from Rhino V5 instead of using PLT files

Copyright (C) 2013  Daniel Bachmann, Alessandro Tellini

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

ZORG
Date/Version: 04.04.2013  V1.0

Written by  -  Daniel Bachmann       (daniel.bachmann@arch.ethz.ch)
			-  Alessandro Tellini    (tellini@arch.ethz.ch)

Snail-Mail Contact:
ETH Zürich
RAPLAB D-ARCH Daniel Bachmann
HIL D34.2
Wolfgang-Pauli-Str. 15
8093 Zürich

Streamlined Zuend Machine Cutting and Engraving out of Rhino V5
ZORG converts Curves and translates them into Zuend-HPGL, then 
streams the Data directly to the Zuend-Cutter.
The Script is meant to be started from Rhino Command-Line but can
also be assigned to an Icon.

Prerequisites:
The Script is depending on pyserial http://sourceforge.net/projects/pyserial/ to send commands to the Zuend-Machine.
Make sure you copy the serial folder of the unpacked pyserial to the same directory where the ZORG script resides.
->   Rhinoscriptfolder|serial
                      |ZORG_V1_0.py

To create a Rhino Command Line Alias:
-Open Tools|Options|Aliases from the Rhino Menu
-Press "New" to create a new Alias
-Enter a name for the Alias. We prefer to use ZORG as command-name ;)
-Enter the following as Command Macro:  ! _-RunPythonScript "FilePath\ScriptFileName"
-It should look like this: ! _-RunPythonScript "C:\Users\User\AppData\Roaming\McNeel\Rhinoceros\5.0\scripts\ZORG_V1_0.py"

Using the variable definitions it is possible to customize the default Workspace Area and Cutting Speeds/Depths
Use the sendToMachine Variable-Option to save to a local file instead of sending the Data directly to the Zuend-Cutter

The script does some basic error-handling:
-Only Curves will be selectable
-A Bounding Box is used to check if all selected Curves are in the Workspace Area