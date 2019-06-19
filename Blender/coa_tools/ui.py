'''
Copyright (C) 2015 Andreas Esau
andreasesau@gmail.com

Created by Andreas Esau

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
'''

import bpy
import bpy_extras
import bpy_extras.view3d_utils
from math import radians
import mathutils
from mathutils import Vector, Matrix, Quaternion
import math
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty, StringProperty, CollectionProperty, FloatVectorProperty, EnumProperty, IntVectorProperty, PointerProperty
import os
from bpy_extras.io_utils import ExportHelper, ImportHelper
import json
from . import functions
#from . import preview_collections

bone_layers = []
armature_mode = None
armature_select = False

class COATOOLS_OT_ChangeShadingMode(bpy.types.Operator):
    bl_idname = "coa_tools.change_shading_mode"
    bl_label = "Change Shading Mode"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.space_data.shading.type = 'RENDERED'
        context.scene.view_settings.view_transform = "Standard"
        return {"FINISHED"}


class COATOOLS_PT_Info(bpy.types.Panel):
    bl_idname = "COATOOLS_PT_social"
    bl_label = "Info Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "COA Tools"

    @classmethod
    def poll(cls, context):
        return context


    def draw(self, context):

        layout = self.layout

        if functions.get_addon_prefs(context).show_donate_icon:
            row = layout.row()
            row.alignment = "CENTER"

            pcoll = preview_collections["main"]
            donate_icon = pcoll["donate_icon"]
            twitter_icon = pcoll["twitter_icon"]
            row.operator("coa_operator.coa_donate",text="Show Your Love",icon_value=donate_icon.icon_id,emboss=True)
            row = layout.row()
            row.alignment = "CENTER"
            row.scale_x = 1.75
            op = row.operator("coa_operator.coa_tweet",text="Tweet",icon_value=twitter_icon.icon_id,emboss=True)
            op.link = "https://www.youtube.com/ndee85"
            op.text = "Check out CutoutAnimation Tools Addon for Blender by Andreas Esau."
            op.hashtags = "b3d,coatools"
            op.via = "ndee85"

last_obj = None
class COATOOLS_PT_ObjectProperties(bpy.types.Panel):
    bl_idname = "COATOOLS_PT_object_properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Object Properties"
    bl_category = "COA Tools"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        global last_obj

        layout = self.layout
        obj = context.active_object
        if obj != None:
            last_obj = obj.name
        elif obj == None and last_obj != None and last_obj in bpy.data.objects:
            obj = bpy.data.objects[last_obj] if last_obj in bpy.data.objects else None
        sprite_object = functions.get_sprite_object(obj)
        scene = context.scene

        if context.space_data.shading.type != "RENDERED" or context.scene.view_settings.view_transform != "Standard":
            layout.operator("coa_tools.change_shading_mode", text="Set Proper Shading Mode", icon="ERROR")
        functions.display_children(self,context,obj)

        if sprite_object != None and obj != None:
            row = layout.row(align=True)

            col = row.column(align=True)

            icon = "NONE"
            if obj.type == "ARMATURE":
                icon = "ARMATURE_DATA"
            elif obj.type == "MESH":
                icon = "OBJECT_DATA"
            elif obj.type == "LAMP":
                icon = "LAMP"

            col.prop(obj, "name", text="", icon=icon)
            if obj.type == "MESH" and obj.coa_tools.type == "SLOT":
                col.prop(obj.coa_slot[obj.coa_slot_index].mesh,"name",text="",icon="OUTLINER_DATA_MESH")
            if obj.type == "ARMATURE":
                row = layout.row(align=True)
                if context.active_bone != None:

                    col.prop(context.active_bone, 'name', text="", icon="BONE_DATA")
                    ### remove bone ik constraints
                    pose_bone = context.active_pose_bone
                    if pose_bone != None:
                        for bone in context.active_object.pose.bones:
                            for const in bone.constraints:
                                if const.type == "IK":
                                    if const.subtarget == pose_bone.name:
                                        row = col.row()
                                        row.operator("coa_tools.remove_ik",text="Remove Bone IK", icon="CONSTRAINT_BONE")



                    ### remove bone stretch ik constraints
                    if context.active_pose_bone != None and "coa_stretch_ik_data" in context.active_pose_bone:
                        col = layout.box().column(align=True)

                        for bone in obj.pose.bones:
                            if "coa_stretch_ik_data" in bone:
                                if eval(bone["coa_stretch_ik_data"])[0] == eval(context.active_pose_bone["coa_stretch_ik_data"])[0]:
                                    if "c_bone_ctrl" == eval(bone["coa_stretch_ik_data"])[1]:
                                        row = col.row()
                                        row.label(text="Stretch IK Constraint",icon="CONSTRAINT_BONE")
                                        op = row.operator("coa_tools.remove_stretch_ik",icon="X",emboss=False, text="")
                                        op.stretch_ik_name = eval(bone["coa_stretch_ik_data"])[0]
                                    elif eval(bone["coa_stretch_ik_data"])[1] in ["ik_bone_ctrl","p_bone_ctrl"]:
                                        col.prop(bone,"ik_stretch",text=bone.name)

            if obj != None and obj.type == "MESH" and obj.mode == "OBJECT":
                row = layout.row(align=True)
                row.label(text="Sprite Properties:")

            if obj != None and obj.type == "MESH" and "coa_sprite" in obj and "coa_base_sprite" in obj.modifiers:
                row = layout.row(align=True)
                row.prop(obj.data.coa_tools, 'hide_base_sprite', text="Hide Base Sprite")
                if len(obj.data.vertices) > 4 and obj.data.coa_tools.hide_base_sprite == False:
                    row.prop(obj.data.coa_tools, 'hide_base_sprite', text="", icon="ERROR", emboss=False)

            if obj != None and obj.type == "MESH" and obj.mode == "OBJECT":
                row = layout.row(align=True)
                if obj.coa_tools.type == "SLOT":
                    text = str(len(obj.coa_tools.slot)) + " Slot(s) total"
                    row.label(text=text)

                if obj.coa_tools.type == "SLOT" and len(obj.coa_tools.slot) > 0:
                    row = layout.row(align=True)
                    slot_text = "Slot Index (" + str(len(obj.coa_tools.slot)) + ")"
                    row.prop(obj.coa_tools,'slot_index',text="Slot Index")
                    op = row.operator("coa_tools.select_frame_thumb",text="",icon="IMAGE_COL")
                    op = row.operator("coa_tools.add_keyframe",text="",icon="KEYTYPE_MOVING_HOLD_VEC")
                    op.prop_name = "coa_slot_index"
                    op.add_keyframe = True
                    op.default_interpolation = "CONSTANT"
                    op = row.operator("coa_tools.add_keyframe",text="",icon="HANDLETYPE_ALIGNED_VEC")
                    op.prop_name = "coa_slot_index"
                    op.add_keyframe = False

            if obj != None and obj.type == "MESH" and obj.mode == "OBJECT":
                row = layout.row(align=True)
                row.prop(obj.coa_tools ,'z_value',text="Z Depth")
                op = row.operator("coa_tools.add_keyframe",text="",icon="KEYTYPE_MOVING_HOLD_VEC")
                op.prop_name = "coa_z_value"
                op.add_keyframe = True
                op.default_interpolation = "CONSTANT"
                op = row.operator("coa_tools.add_keyframe",text="",icon="HANDLETYPE_ALIGNED_VEC")
                op.prop_name = "coa_z_value"
                op.add_keyframe = False

                row = layout.row(align=True)
                row.prop(obj.coa_tools,'alpha',text="Alpha",icon="TEXTURE")
                op = row.operator("coa_tools.add_keyframe",text="",icon="KEYTYPE_MOVING_HOLD_VEC")
                op.prop_name = "coa_alpha"
                op.add_keyframe = True
                op.default_interpolation = "BEZIER"
                op = row.operator("coa_tools.add_keyframe",text="",icon="HANDLETYPE_ALIGNED_VEC")
                op.prop_name = "coa_alpha"
                op.add_keyframe = False

                row = layout.row(align=True)
                row.prop(obj.coa_tools,'modulate_color',text="")
                op = row.operator("coa_tools.add_keyframe",text="",icon="KEYTYPE_MOVING_HOLD_VEC")
                op.prop_name = "coa_modulate_color"
                op.add_keyframe = True
                op.default_interpolation = "LINEAR"
                op = row.operator("coa_tools.add_keyframe",text="",icon="HANDLETYPE_ALIGNED_VEC")
                op.prop_name = "coa_modulate_color"
                op.add_keyframe = False

        if obj != None and obj.type == "CAMERA":
            row = layout.row(align=True)
            row.label(text="Camera Properties:")
            row = layout.row(align=True)
            row.prop(obj.data,"ortho_scale",text="Camera Zoom")
            row = layout.row(align=True)
            rd = context.scene.render
            col = row.column(align=True)
            col.label(text="Resolution:")
            col.prop(rd, "resolution_x", text="X")
            col.prop(rd, "resolution_y", text="Y")
            col.prop(rd, "resolution_percentage", text="")

            col.label(text="Path:")
            col.prop(rd, "filepath", text="")

            row = layout.row(align=True)
            col = row.column(align=True)
            col.prop(obj, "location")

######################################################################################################################################### Cutout Animation Tools Panel
class COATOOLS_PT_Tools(bpy.types.Panel):
    bl_idname = "COATOOLS_PT_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Cutout Tools"
    bl_category = "COA Tools"

    bpy.types.WindowManager.coa_show_help: BoolProperty(default=False,description="Hide Help")

    def draw(self, context):
        global last_obj
        wm = context.window_manager
        layout = self.layout
        obj = context.active_object
        if obj == None and last_obj != None and last_obj in bpy.data.objects:
            obj = bpy.data.objects[last_obj]

        sprite_object = functions.get_sprite_object(obj)
        scene = context.scene
        screen = context.screen

        col = layout.column()

        subrow = col.row()
        subrow.prop(screen.coa_tools,"view",expand=True)

        col.operator("coa_tools.create_sprite_object", text="Create new Sprite Object", icon="TEXTURE_DATA")
        if sprite_object != None:
            col.operator("coa_tools.import_sprites", text="Re/Import Sprites", icon="FILEBROWSER")
            if obj != None and obj.type == "MESH":
                col.operator("coa_tools.edit_mesh", text="Edit Mesh", icon="GREASEPENCIL")

### Custom template_list look
class COATOOLS_UL_AnimationCollections(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ob = data
        slot = item
        col = layout.row(align=True)
        if item.name not in ["NO ACTION","Restpose"]:
            col.label(icon="ACTION")
            col.prop(item,"name",emboss=False,text="")
        elif item.name == "NO ACTION":
            col.label(icon="RESTRICT_SELECT_ON")
            col.label(text=item.name)
        elif item.name == "Restpose":
            col.label(icon="ARMATURE_DATA")
            col.label(text=item.name)

        if context.scene.coa_nla_mode == "NLA" and item.name not in ["NO ACTION","Restpose"]:
            col = layout.row(align=False)
            op = col.operator("coa_operator.create_nla_track",icon="NLA",text="")
            op.anim_collection_name = item.name

### Custom template_list look for event lists
class COATOOLS_UL_EventCollection(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ob = data
        slot = item
        # col = layout.column(align=False)
        box = layout.box()
        col = box.column(align=False)

        row = col.row(align=False)
        # row.label(text="", icon="TIME")
        if item.collapsed:
            row.prop(item,"collapsed",emboss=False, text="", icon="TRIA_RIGHT")
        else:
            row.prop(item, "collapsed", emboss=False, text="", icon="TRIA_DOWN")
        row.prop(item, "frame", emboss=True, text="Frame")
        op = row.operator("coa_tools.remove_timeline_event", text="", icon="PANEL_CLOSE", emboss=False)
        op.index = index


        # row = col.row(align=True)
        if not item.collapsed:
            row = col.row(align=True)
            # row.alignment = "RIGHT"
            op = row.operator("coa_tools.add_event", icon="ZOOMIN", text="Add new Event", emboss=True)
            op.index = index
            for i, event in enumerate(item.event):
                row = col.row(align=True)
                row.prop(event, "type",text="")
                row.prop(event, "value",text="")
                op = row.operator("coa_tools.remove_event", icon="PANEL_CLOSE", text="", emboss=True)
                op.index = index
                op.event_index = i

######################################################################################################################################### Select Child Operator
class COATOOLS_OT_SelectChild(bpy.types.Operator):
    bl_idname = "coa_tools.show_children"
    bl_label = "select_child"

    ob_name: StringProperty()
    bone_name: StringProperty()

    def __init__(self):
        self.sprite_object = None

    mode: EnumProperty(items=(("object","object","object"),("bone","bone","bone")))
    armature = None

    def change_object_mode(self,context):
        obj = context.active_object
        if obj != None and self.ob_name != obj.name:
            if obj.mode == "EDIT" and obj.type == "MESH":
                bpy.ops.object.mode_set(mode="OBJECT")
            elif obj.mode == "EDIT" and obj.type == "ARMATURE":
                bpy.ops.object.mode_set(mode="POSE")


    def select_child(self,context,event):
        global last_obj
        self.change_object_mode(context)

        if self.mode == "object":
            ob = bpy.data.objects[self.ob_name]
            ob.select_set(True)
            context.view_layer.objects.active = ob
            if ob != None:
                last_obj = ob.name

            if not event.ctrl and not event.shift:
                for obj in context.scene.objects:
                    if obj != ob:
                        obj.select_set(False)

        elif self.mode == "bone":
            armature_ob = bpy.data.objects[self.ob_name]
            armature = bpy.data.armatures[armature_ob.data.name]
            bone = armature.bones[self.bone_name]
            bone.select = not bone.select
            bone.select_tail = not bone.select_tail
            bone.select_head = not bone.select_head
            if bone.select == True:
                armature.bones.active = bone
            else:
                armature.bones.active = None

    def shift_select_child(self,context,event):
        self.change_object_mode(context)

        sprite_object = functions.get_sprite_object(context.active_object)
        children = []
        armature = None
        if self.mode == "object":
            children = functions.get_children(context,sprite_object,ob_list=[])
            ### sort children
            children = sorted(children, key=lambda x: x.location[1] if type(x) == bpy.types.Object else x.name,reverse=False)
            children = sorted(children, key=lambda x: x.type if type(x) == bpy.types.Object else x.name,reverse=False)
            if len(children) > 1 and type(children[1]) == bpy.types.Object and children[1].type == "CAMERA":
                children.insert(0,children.pop(1))
        else:
            armature = bpy.data.armatures[self.ob_name]
            for bone in armature.bones:
                children.append(bone)

        from_index = 0
        to_index = 0
        for i,child in enumerate(children):
            if self.mode == "object":
                if child.name == self.ob_name:
                    to_index = i
            elif self.mode == "bone":
                if child.name == self.bone_name:
                    to_index = i
            if child.select_get():
                from_index = i

        select_range = []
        if from_index < to_index:
            for i in range(from_index,to_index+1):
                select_range.append(i)
        else:
            for i in range(to_index,from_index):
                select_range.append(i)
        for i,child in enumerate(children):
            if i in select_range:
                child.select_set(True)

        if self.mode == "object":
            context.view_layer.objects.active = bpy.data.objects[self.ob_name]
        elif self.mode == "bone":
            context.view_layer.objects.active = bpy.data.objects[self.ob_name]
            armature.bones.active = armature.bones[self.bone_name]

    def change_weight_mode(self, context, mode):
        if self.sprite_object.coa_tools.edit_weights:
            armature = functions.get_armature(self.sprite_object)
            armature.select = True
            bpy.ops.view3d.localview()
            bpy.context.space_data.viewport_shade = 'TEXTURED'

            ### zoom to selected mesh/sprite
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            obj = bpy.data.objects[context.active_object.name]
            obj.select = True
            context.scene.objects.active = obj
            bpy.ops.view3d.view_selected()

            ### set uv image
            functions.set_uv_image(obj)


            bpy.ops.object.mode_set(mode=mode)

    def invoke(self, context, event):
        self.sprite_object = functions.get_sprite_object(context.active_object)
        self.armature = functions.get_armature(self.sprite_object)

        if self.sprite_object.coa_tools.edit_mesh:
            obj = bpy.data.objects[self.ob_name]
            obj.hide = False

        if self.sprite_object != None:
            self.change_weight_mode(context,"OBJECT")

        if self.sprite_object != None:
            if context.active_object != None and context.active_object.type == "ARMATURE" and context.active_object.mode == "EDIT" and event.alt:
                obj = bpy.data.objects[self.ob_name]
                if obj.type == "MESH":
                    functions.set_weights(self,context,obj)
                    msg = '"'+self.ob_name+'"' + " has been bound to selected Bones."
                    self.report({'INFO'},msg)
                else:
                    self.report({'WARNING'},"Can only bind Sprite Meshes to Bones")
                return{"FINISHED"}

            if event.shift and not self.sprite_object.coa_tools.edit_weights:
                self.shift_select_child(context,event)
            if not self.sprite_object.coa_tools.edit_weights or ( self.sprite_object.coa_tools.edit_weights and bpy.data.objects[self.ob_name].type == "MESH"):
                if not event.ctrl and not event.shift:
                    if self.mode == "bone":
                        for bone in bpy.data.objects[self.ob_name].data.bones:
                            bone.select = False
                            bone.select_head = False
                            bone.select_tail = False
                if not event.shift:
                    self.select_child(context,event)

            if self.sprite_object.coa_tools.edit_weights:
                functions.create_armature_parent(context)
            self.change_weight_mode(context,"WEIGHT_PAINT")
        else:
            self.shift_select_child(context,event)

        return{'FINISHED'}

class COATOOLS_PT_Collections(bpy.types.Panel):
    bl_idname = "COATOOLS_PT_collections"
    bl_label = "Cutout Animations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "COA Tools"


    def set_actions(self,context):
        scene = context.scene
        sprite_object = functions.get_sprite_object(context.active_object)

        if context.scene.coa_nla_mode == "ACTION":
            scene.frame_start = sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index].frame_start
            scene.frame_end = sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index].frame_end
            functions.set_action(context)
        for obj in context.visible_objects:
            if obj.type == "MESH" and "coa_sprite" in obj:
                functions.update_uv(context,obj)
                functions.set_alpha(obj,bpy.context,obj.coa_alpha)
                functions.set_z_value(context,obj,obj.coa_z_value)
                functions.set_modulate_color(obj,context,obj.coa_modulate_color)

        ### set export name
        if scene.coa_nla_mode == "ACTION":
            action_name = sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index].name
            if action_name in ["Restpose","NO ACTION"]:
                action_name = ""
            else:
                action_name += "_"
            path = context.scene.render.filepath.replace("\\","/")
            dirpath = path[:path.rfind("/")]
            final_path = dirpath + "/" + action_name
            context.scene.render.filepath = final_path


    def set_nla_mode(self,context):
        sprite_object = functions.get_sprite_object(context.active_object)
        children = functions.get_children(context,sprite_object,ob_list=[])
        if self.coa_nla_mode == "NLA":
            for child in children:
                if child.animation_data != None:
                    child.animation_data.action = None
            context.scene.frame_start = context.scene.coa_frame_start
            context.scene.frame_end = context.scene.coa_frame_end

            for child in children:
                if child.animation_data != None:
                    for track in child.animation_data.nla_tracks:
                        track.mute = False
        else:
            if len(sprite_object.coa_anim_collections) > 0:
                anim_collection = sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index]
                context.scene.frame_start = anim_collection.frame_start
                context.scene.frame_end = anim_collection.frame_end
                functions.set_action(context)
                for obj in context.visible_objects:
                    if obj.type == "MESH" and "coa_sprite" in obj:
                        functions.update_uv(context,obj)
                        functions.set_alpha(obj,bpy.context,obj.coa_alpha)
                        functions.set_z_value(context,obj,obj.coa_z_value)
                        functions.set_modulate_color(obj,context,obj.coa_modulate_color)
                for child in children:
                    if child.animation_data != None:
                        for track in child.animation_data.nla_tracks:
                            track.mute = True

        bpy.ops.coa_tools.toggle_animation_area(mode="UPDATE")




    def update_frame_range(self,context):
        sprite_object = functions.get_sprite_object(context.active_object)
        if len(sprite_object.coa_anim_collections) > 0:
            anim_collection = sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index]

        if context.scene.coa_nla_mode == "NLA" or len(sprite_object.coa_anim_collections) == 0:
            context.scene.frame_start = self.coa_frame_start
            context.scene.frame_end = self.coa_frame_end

    bpy.types.Object.coa_anim_collections_index: IntProperty(update=set_actions)
    bpy.types.Scene.coa_nla_mode: EnumProperty(description="Animation Mode. Can be set to NLA or Action to playback all NLA Strips or only Single Actions",items=(("ACTION","ACTION","ACTION","ACTION",0),("NLA","NLA","NLA","NLA",1)),update=set_nla_mode)
    bpy.types.Scene.coa_frame_start: IntProperty(name="Frame Start",default=0,min=0,update=update_frame_range)
    bpy.types.Scene.coa_frame_end: IntProperty(name="Frame End",default=250,min=1,update=update_frame_range)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene
        sprite_object = functions.get_sprite_object(obj)
        if sprite_object != None:


            row = layout.row()
            row.prop(sprite_object,"coa_animation_loop",text="Wrap Animation Playback")

            row = layout.row()
            row.prop(scene,"coa_nla_mode",expand=True)

            if scene.coa_nla_mode == "NLA":
                row = layout.row(align=True)
                row.prop(scene,"coa_frame_start")
                row.prop(scene,"coa_frame_end")

            row = layout.row()
            row.template_list("COATOOLS_UL_AnimationCollections","dummy",sprite_object, "coa_anim_collections", sprite_object, "coa_anim_collections_index",rows=2,maxrows=10,type='DEFAULT')
            col = row.column(align=True)
            col.operator("coa_tools.add_animation_collection",text="",icon="ZOOMIN")
            col.operator("coa_tools.remove_animation_collection",text="",icon="ZOOMOUT")

            if len(sprite_object.coa_anim_collections) > 2 and sprite_object.coa_anim_collections_index > 1:
                col.operator("coa_tools.duplicate_animation_collection",text="",icon="COPY_ID")

            if not "-nonnormal" in context.screen.name:
                col.operator("coa_tools.toggle_animation_area",text="",icon="ACTION")

            if  len(sprite_object.coa_anim_collections) > 0 and sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index].action_collection:
                row = layout.row(align=True)
                item = sprite_object.coa_anim_collections[sprite_object.coa_anim_collections_index]
                row.prop(item,"frame_end",text="Animation Length")


                # if get_addon_prefs(context).dragon_bones_export:
                row = layout.row(align=True)
                row.label(text="Timeline Events",icon="TIME")
                row = layout.row(align=False)
                row.template_list("COATOOLS_UL_EventCollection","dummy",item, "timeline_events", item, "event_index",rows=1,maxrows=10,type='DEFAULT')
                col = row.column(align=True)
                col.operator("coa_tools.add_timeline_event",text="",icon="ZOOMIN")

            row = layout.row(align=True)
            if context.scene.coa_nla_mode == "ACTION":

                operator = row.operator("coa_tools.batch_render",text="Batch Render Animations",icon="RENDER_ANIMATION")
            else:
                operator = row.operator("render.render",text="Render Animation",icon="RENDER_ANIMATION")
                operator.animation = True

preview_collections = {}
