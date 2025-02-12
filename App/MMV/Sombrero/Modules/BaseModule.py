"""
===============================================================================
                                GPL v3 License                                
===============================================================================

Copyright (c) 2020 - 2021, Tremeschin

===============================================================================

Purpose: Base module abstraction

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

class BaseModule:
    def init(self, SombreroWindow):
        self.SombreroWindow = SombreroWindow
        self.SombreroContext = self.SombreroWindow.SombreroContext
        self.messages = self.SombreroWindow.messages
        self.SombreroMain = self.SombreroWindow.SombreroMain
        self.ACTION_MESSAGE_TIMEOUT = self.SombreroWindow.ACTION_MESSAGE_TIMEOUT
        