import bpy
from bpy.types import Menu
from bpy.props import FloatProperty, IntProperty, BoolProperty, StringProperty, CollectionProperty, FloatVectorProperty, EnumProperty, IntVectorProperty
from .. functions import *

class VIEW3D_PIE_coa_menu(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "COA Tools"
    bl_idname = "view3d.coa_pie_menu"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        sprite_object = get_sprite_object(obj)
        if (obj != None and "coa_sprite" in obj) or (sprite_object != None and obj.type == "ARMATURE"):
            return True
    
    def draw(self, context):
        obj = context.active_object
        
        layout = self.layout
        pie = layout.menu_pie()
        if obj != None:
            #pie.operator_enum("view3d.coa_pie_menu_options", "selected_mode")
            if obj.type == "MESH":
                pie.operator("my_operator.select_frame_thumb",text="Select Frame",icon="IMAGE_COL")
                pie.operator("wm.call_menu_pie", icon="SPACE3", text="Delete Keyframe(s)").name = "view3d.coa_pie_keyframe_menu_remove"
                pie.operator("object.coa_edit_weights",text="Edit Weights",icon="MOD_VERTEX_WEIGHT")
                pie.operator("object.coa_edit_mesh",text="Edit Mesh",icon="GREASEPENCIL")
                pie.operator("scene.coa_quick_armature",text="Edit Armature",icon="ARMATURE_DATA")
                pie.operator("wm.call_menu_pie", icon="SPACE2", text="Add Keyframe(s)").name = "view3d.coa_pie_keyframe_menu_add"
                
            elif obj.type == "ARMATURE":
                pie.operator("object.coa_set_ik",text="Create IK Bone",icon="CONSTRAINT_BONE")
                pie.operator("wm.call_menu_pie", icon="SPACE3", text="Delete Keyframe(s)").name = "view3d.coa_pie_keyframe_menu_remove"
                pie.operator("bone.coa_draw_bone_shape",text="Draw Bone Shape",icon="BONE_DATA")
                pie.operator("scene.coa_quick_armature",text="Edit Armature",icon="ARMATURE_DATA")
                pie.operator("bone.coa_set_stretch_bone",text="Create Stretch Bone",icon="CONSTRAINT_BONE")
                pie.operator("wm.call_menu_pie", icon="SPACE2", text="Add Keyframe(s)").name = "view3d.coa_pie_keyframe_menu_add"

class VIEW3D_PIE_coa_keyframe_menu_01(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "COA Tools"
    bl_idname = "view3d.coa_pie_keyframe_menu_01"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        sprite_object = get_sprite_object(obj)
        if (obj != None and "coa_sprite" in obj) or (sprite_object != None and obj.type == "ARMATURE"):
            return True
    
    def draw(self, context):
        obj = context.active_object
        
        layout = self.layout
        pie = layout.menu_pie()
        if obj != None:
            pie.operator("wm.call_menu_pie", icon="SPACE2", text="Add Keyframe(s)").name = "view3d.coa_pie_keyframe_menu_add"
            pie.operator("wm.call_menu_pie", icon="SPACE3", text="Delete Keyframe(s)").name = "view3d.coa_pie_keyframe_menu_remove"

class VIEW3D_PIE_coa_keyframe_menu_add(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "COA Add Keyframe"
    bl_idname = "view3d.coa_pie_keyframe_menu_add"
    
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        add_remove_keyframe(pie,True)
        
class VIEW3D_PIE_coa_keyframe_menu_remove(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "COA Remove Keyframe"
    bl_idname = "view3d.coa_pie_keyframe_menu_remove"
    
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        add_remove_keyframe(pie,False)        

def add_remove_keyframe(pie,add):
    context= bpy.context
    obj = context.active_object
    if obj.type == "MESH":
        op = pie.operator("my_operator.add_keyframe",text="Sprite Frame",icon="IMAGE_COL")
        op.prop_name = "coa_sprite_frame"
        op.add_keyframe = add
        op.default_interpolation = "CONSTANT"
        
        op = pie.operator("my_operator.add_keyframe",text="Sprite Alpha",icon="RESTRICT_VIEW_OFF")
        op.prop_name = "coa_alpha"
        op.add_keyframe = add
        op.default_interpolation = "BEZIER"
        
        op = pie.operator("my_operator.add_keyframe",text="Modulate Color",icon="COLOR")
        op.prop_name = "coa_modulate_color"
        op.add_keyframe = add
        op.default_interpolation = "BEZIER"
        
        op = pie.operator("my_operator.add_keyframe",text="Z Value",icon="IMAGE_ZDEPTH")
        op.prop_name = "coa_z_value"
        op.add_keyframe = add
        op.default_interpolation = "CONSTANT"
    elif obj.type == "ARMATURE":
        bone = context.active_pose_bone
        op = pie.operator("my_operator.add_keyframe",text="Location",icon="MAN_TRANS")
        op.prop_name = 'pose.bones["'+str(bone.name)+'"].location'
        op.add_keyframe = add
        op.default_interpolation = "BEZIER"
        
        
        op = pie.operator("my_operator.add_keyframe",text="Scale",icon="MAN_SCALE")
        op.prop_name = 'pose.bones["'+str(bone.name)+'"].scale'
        op.add_keyframe = add
        op.default_interpolation = "BEZIER"
        
        op = pie.operator("my_operator.add_keyframe",text="Rotation",icon="MAN_ROT")
        if bone.rotation_mode == "QUATERNION":
            op.prop_name = 'pose.bones["'+str(bone.name)+'"].rotation_quaternion'
        else:
            op.prop_name = 'pose.bones["'+str(bone.name)+'"].rotation_euler'
            
        op.add_keyframe = add
        op.default_interpolation = "BEZIER" 