"""
===============================================================================
                                GPL v3 License                                
===============================================================================

Copyright (c) 2020 - 2021,
  - Tremeschin < https://tremeschin.gitlab.io > 

===============================================================================

Purpose: Global controller and wrapper on mapping, rendering shaders, vertex
and geometry shaders generation.

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
from mmv.sombrero.sombrero_window import SombreroWindow
from mmv.sombrero.sombrero_constructor import *
from mmv.sombrero.sombrero_shader import *
from mmv.mmv_enums import *
from enum import Enum, auto
from PIL import Image
import numpy as np
import moderngl
import logging


class FakeUniform:
    value = None


def pretty_lines_counter(data):
    for number, line in enumerate(data.split('\n')):
        yield f"[{number:05}] | {line}"


class SombreroMGL:
    def __init__(self, mmv_interface, master_shader = False, gl_context = None, flip = False):

        # # Constructor
        self.mmv_interface = mmv_interface
        self.shaders_dir = self.mmv_interface.shaders_dir

        # Do flip coordinates vertically? OpenGL context ("shared" with main class)
        self.gl_context = gl_context
        self.flip = flip

        # # Standard attributes

        self.master_shader = master_shader

        # Contents dictionary that holds instruction, other classes and all
        self.contents = {}

        # Pending uniforms to be passed values after shader is loaded
        self.pending_uniforms = []

        # SuperSampling Anti Aliasing
        self.ssaa = 1

        # Class that deals with window creation etc
        self.window = SombreroWindow(sombrero = self)

        # Fragment Shader related, geometry is done via constructor
        self.macros = SombreroShaderMacros(self)
        self.shader = SombreroShader()
        self.constructor = None

        # Shader defined values (GUI ones on next() method)
        if self.master_shader:
            self.freezed_pipeline = False
            self.pipeline = {
                "mTime": 0.0, "mFrame": 0,
                "mResolution": np.array([0, 0], dtype = np.int32),
            }
    
    def new_child(self,):
        child = SombreroMGL(mmv_interface = self.mmv_interface, master_shader = False, gl_context = self.gl_context)
        child.configure(width = self.width, height = self.height, fps = self.fps, ssaa = self.ssaa)
        return child

    # # Config

    def configure(self, width, height, fps, ssaa = 1):
        (self.width, self.height, self.fps, self.ssaa) = (width, height, fps, ssaa)

    # # Constructors

    # # Mappings

    def assign_content(self, dictionary):
        self.contents[len(list(self.contents.keys()))] = dictionary
        return dictionary

    # Shorthand
    def __mipmap_anisotropy_repeat_texture(self, texture, context):
        texture.anisotropy = context.get("anisotropy", 1)
        texture.repeat_x = context.get("repeat_x", True)
        texture.repeat_y = context.get("repeat_y", True)
        if context.get("mipmaps", False): texture.build_mipmaps()

    # Image mapping as texture
    def map_image(self, name, path, repeat_x = True, repeat_y = True, mipmap = True, anisotropy = 16):
        img = Image.open(path).convert("RGBA")
        texture = self.gl_context.texture(img.size, 4, img.tobytes())
        self.__mipmap_anisotropy_repeat_texture(texture, locals())

        uniforms = [["sampler2D", name, None], ["vec2", f"{name}_resolution", img.size]]
        self.pending_uniforms += uniforms

        self.assign_content({
            "name": name, "loader": ContentType.Image,
            "resolution": img.size,
            "texture": texture,
        })
        print("Map image", name, path, texture, uniforms)

        return uniforms
    
    def map_shader(self, name, sombrero_mgl):
        uniforms = [["sampler2D", name, None]]
        self.pending_uniforms += uniforms
        self.assign_content({
            "name": name, "loader": "fragment_shader",
            "SombreroMGL": sombrero_mgl,
            "texture": sombrero_mgl.texture,
        })
        return [Uniform("sampler2D", name)]

    # # GL objects

    # Create one texture attached to some FBO. Depth = 4 -> RGBA
    def create_texture_fbo(self, width, height, depth = 4) -> list:
        texture = self.gl_context.texture((width * self.ssaa, self.height * self.ssaa), depth)
        fbo = self.gl_context.framebuffer(color_attachments = [texture])
        return [texture, fbo]

    # Get the uniform if exists, enforce tuple if isn't tuple or int and assign the value
    def set_uniform(self, name, value):
        if (not isinstance(value, float)) and (not isinstance(value, int)): value = tuple(value)
        self.program.get(name, FakeUniform()).value = value
        return name
    
    # Write uniform values on the list of pending uniforms
    def solve_pending_uniforms(self):
        for item in self.pending_uniforms:
            name, value = item[1], item[2]
            if value is not None: self.set_uniform(name, value)
        self.pending_uniforms = []

    # Pipe a global pipeline
    def pipe_pipeline(self, pipeline):
        for name, value in pipeline.items(): self.set_uniform(name, value)
    
    # # Load

    # Load shader from this class's SombreroConstructor
    def finish(self):

        # Default constructor is Fullscreen if not set
        if self.constructor is None: self.constructor = FullScreenConstructor(self)

        self.constructor.treat_fragment_shader(self.shader)
        frag = self.shader.build()

        for pretty in pretty_lines_counter(frag): print(pretty)

        # The FBO and texture so we can use on parent shaders, master shader doesn't require since it haves window fbo
        if not self.master_shader:
            self.texture, self.fbo = self.create_texture_fbo(width = self.width * self.ssaa, height = self.height * self.ssaa)

        self.program = self.gl_context.program(
            vertex_shader = self.constructor.vertex_shader,
            geometry_shader = self.constructor.geometry_shader,
            fragment_shader = frag,
        )
        self.solve_pending_uniforms()

    def get_vao(self):
        if instructions := self.constructor.vao():
            self.vao = self.gl_context.vertex_array(self.program, instructions, skip_errors = True)

    # # Render

    # Next iteration, also render
    def next(self, custom_pipeline = {}):

        # # Update pipeline

        # Get current window "state"
        self.pipeline["mResolution"] = (self.width * self.ssaa, self.height * self.ssaa)
        self.pipeline["mRotation"] = self.window.rotation
        self.pipeline["mZoom"] = self.window.zoom
        self.pipeline["mDrag"] = self.window.drag

        # Calculate Sombrero values
        if not self.freezed_pipeline:
            self.pipeline["mFrame"] += 1
            self.pipeline["mFlip"] = -1 if self.flip else 1
            self.pipeline["mTime"] = self.pipeline["mFrame"] / self.fps

        # Gui
        self.pipeline["mIsDraggingMode"] = self.window.is_dragging_mode
        self.pipeline["mIsDragging"] = self.window.is_dragging
        self.pipeline["mIsGuiVisible"] = self.window.show_gui
        self.pipeline["mIsDebugMode"] = self.window.debug_mode

        self.pipeline["mKeyCtrl"] = self.window.ctrl_pressed
        self.pipeline["mKeyShift"] = self.window.shift_pressed
        self.pipeline["mKeyAlt"] = self.window.alt_pressed

        # Merge the two dictionaries
        for key, value in custom_pipeline.values():
            self.pipeline[key] = value

        # Render, update window
        self._render(pipeline = self.pipeline)
        self.window.update_window()

    # Internal function for rendering (some stuff needs to be called like getting next image of video)
    def _render(self, pipeline = []):
        self.pipeline = pipeline

        # VAO, constructor
        self.constructor.next()
        self.get_vao()

        # Pipe to self
        self.pipe_pipeline(self.pipeline)

        # Pipe the pipeline to child shaders and render them
        for index, item in self.contents.items():
            if item["loader"] == "fragment_shader":
                item["SombreroMGL"].pipe_pipeline(pipeline)
                item["SombreroMGL"]._render(pipeline)

        # Which FBO to use
        if self.master_shader:
            self.window.window.use(); self.window.window.clear()
        else:
            self.fbo.use(); self.fbo.clear()

        # Use textures at specific indexes
        for index, item in self.contents.items():

            # Read next frame of video
            if item["loader"] == "video":
                raise NotImplementedError("Video TODO")
            
            # Where texture will be used
            item["texture"].use(location = index)
            self.program[item["name"]] = index

        # Render the content
        # self.vao.render(mode = moderngl.TRIANGLE_STRIP)
        if nvert := self.constructor.num_vertices:
            self.vao.render(mode = moderngl.POINTS, vertices = nvert)

        # Draw UI
        if self.master_shader and (not self.window.headless) and (self.window.show_gui):
            self.window.render_ui()
            self.gl_context.enable_only(moderngl.NOTHING)
    
    # Read contents from window FBO, chose one
    def read(self): return self.window.window.fbo.read()
    def read_into_subprocess_stdin(self, target): target.write(self.read())

    @property
    def fbo_size(self): return self.window.window.fbo.size
    