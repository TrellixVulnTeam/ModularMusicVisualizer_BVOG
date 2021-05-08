from mmv.common.cmn_piano_roll import PianoRoll
from mmv.sombrero.sombrero_constructor import *
from mmv.sombrero.sombrero_shader import *

def generate(context):
    interface = context.interface
    layers = []

    background = context.new_child()
    background.macros.load(interface.shaders_dir/"assets"/"background"/"blueprint.glsl")
    layers.append(background)

    context.main.macros.render_layers(layers, gamma_correction = True)
