"""
===============================================================================
                                GPL v3 License                                
===============================================================================

Copyright (c) 2020 - 2021, Tremeschin

===============================================================================

Purpose: Packaging / Developer utils:
  - SVG flags icons -> PNG images

===============================================================================

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

===============================================================================
"""
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import MMV
from MMV.Common.Download import Download
from MMV.Common.Polyglot import Languages

PackageInterface = MMV.mmvPackageInterface()

# Need: inkscape on PATH
def MakeCountryFlags():
    dpfx = "[Magic.MakeCountryFlags]"

    for CountryFlag in Languages.MakeCountries.split(" "):
        TempSourceSVGPath = PackageInterface.TempDir/"TempCountryFlag.svg"
        with open(TempSourceSVGPath, "w") as SourceSVG:
            URL = f"https://hatscripts.github.io/circle-flags/flags/{CountryFlag}.svg"
            SVG = Download.GetHTMLContent(URL)
            logging.info(f"{dpfx} SVG content is: {SVG}")
            SourceSVG.write(SVG)
        FinalPNG = PackageInterface.DataDir/"Image"/"Icon"/"Flags"/f"{CountryFlag}.png"
        FinalPNG.parent.mkdir(exist_ok=True)
        logging.info(f"{dpfx} Final PNG is {FinalPNG}")
        Command = ["inkscape", "-w", "1024", "-h", "1024", str(TempSourceSVGPath), "-o", str(FinalPNG)]
        logging.info(f"{dpfx} Run command: {Command}")
        subprocess.run(Command)
        os.remove(str(TempSourceSVGPath))

def TestExternalsManager():
    for Platform in ["Linux", "Windows"]:
        MMV = MMV.mmvPackageInterface(ForcePlatform=Platform)
        for External in (MMV.Externals.AvailableExternals.ListOfAll):
            MMV.Externals.DownloadInstallExternal(TargetExternals=External, _ForceNotFound=True)

def Main():
    if "MakeCountryFlags" in sys.argv: MakeCountryFlags()
    if "TestExternalsManager" in sys.argv: TestExternalsManager()

if __name__ == "__main__":
    Main()
