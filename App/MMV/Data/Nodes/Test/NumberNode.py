import random

import dearpygui.dearpygui as Dear


def GetNode(BaseNode):
    class TestNode(BaseNode):
        def Config(self):
            self.Name = "Number Node"
            self.Category = "Numbers"

        def Render(self, parent):
            with Dear.node(label=f"{self.Name} | ({self.Category})", parent=parent) as self.DPG_NODE_ID:
                self.AddNodeDecorator()
                
                with Dear.node_attribute() as A:
                    Dear.add_text("Hello World" + f"  |  [{A}]" * int(self.Editor.Context.DotMap.DEBUG_SHOW_IDS))

                for _ in range(random.randint(30, 60)):
                    with Dear.node_attribute(attribute_type=Dear.mvNode_Attr_Output):
                        Dear.add_slider_float(label=f"Output Number {_}", width=150)
            self.ApplyTheme()
    return TestNode()
