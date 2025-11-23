import cadquery as cq
import math
import os
from cadquery import exporters

# ====== PARAMETERS (inches where noted) ======
lip_thickness_inch = 0.8       # A = 0.8" door-pocket lip
pocket_height_inch = 6.0       # B = 6" inside pocket height
pocket_depth_inch = 1.8        # C = 1.8" inside depth (lip -> back wall)

# Convert to mm
lip_thickness = lip_thickness_inch * 25.4
pocket_height = pocket_height_inch * 25.4
pocket_depth = pocket_depth_inch * 25.4

# JBL Clip 4 body (from spec, mm)
clip_width = 86.3              # left-right
clip_height = 134.5            # top-bottom
clip_depth = 46.0              # front-back

# Clearances and wall sizes (mm)
lip_channel_clearance = 1.0
lip_clamp_height = 25.0        # part that sits over the lip above pocket
lip_wall_thickness = 3.0

# Put the cradle roughly centered vertically in the pocket
inner_brace_height = max(40.0, pocket_height / 2.0)

cradle_clearance = 1.0         # gap around speaker
cradle_wall_thickness = 3.0
bottom_shelf_height = 8.0

tilt_angle_deg = 20.0          # tilt cradle toward cabin

# ====== DERIVED DIMENSIONS ======
lip_channel_width = lip_thickness + lip_channel_clearance

# First compute "ideal" cradle size
ideal_cradle_inner_depth = clip_depth + cradle_clearance
ideal_cradle_outer_depth = ideal_cradle_inner_depth + cradle_wall_thickness

# Limit intrusion so it doesn't hit the back of the pocket
back_gap = 3.0  # mm clearance to pocket back wall
max_intrusion = max(ideal_cradle_outer_depth, 0.1)  # avoid negatives
max_intrusion = min(max_intrusion, pocket_depth - back_gap)

cradle_outer_depth = max_intrusion
cradle_inner_depth = cradle_outer_depth - cradle_wall_thickness

cradle_inner_width = clip_width + cradle_clearance
cradle_outer_width = cradle_inner_width + 2 * cradle_wall_thickness

# Slightly wider than the speaker so the mount has some "ears"
mount_width = cradle_outer_width + 4.0

# ====== BUILD LIP CLAMP (U-channel) ======
lip_block = (
    cq.Workplane("XY")
    .box(
        lip_channel_width + 2 * lip_wall_thickness,  # X
        mount_width,                                 # Y
        lip_clamp_height + inner_brace_height        # Z
    )
)

# Cut the lip channel from the top down
lip_block = (
    lip_block
    .faces(">Z").workplane(centerOption="CenterOfBoundBox")
    .rect(
        lip_channel_width,
        mount_width - 2 * lip_wall_thickness
    )
    .cutBlind(-lip_clamp_height)
)

# ====== BUILD CLIP 4 CRADLE ======
tilt_angle_rad = math.radians(tilt_angle_deg)

# Base block for cradle (lower half of speaker)
cradle_block = (
    cq.Workplane("XY")
    .box(
        cradle_outer_depth,      # X (into pocket)
        cradle_outer_width,      # Y (along door)
        clip_height / 2.0        # Z (vertical)
    )
)

# Hollow into C-shaped cradle with bottom shelf
cradle_block = (
    cradle_block
    .faces(">X").workplane(centerOption="CenterOfBoundBox")
    .rect(
        cradle_inner_depth,
        cradle_inner_width
    )
    .cutBlind(-clip_height / 2.0 + bottom_shelf_height)
)

# Bottom lip to keep speaker from sliding out
bottom_lip = (
    cq.Workplane("XY")
    .box(
        cradle_outer_depth,
        cradle_outer_width,
        bottom_shelf_height
    )
    .translate(
        (0, 0, -clip_height / 4.0 - bottom_shelf_height / 2.0)
    )
)

cradle = cradle_block.union(bottom_lip)

# Tilt cradle toward cabin
cradle = cradle.rotate((0, 0, 0), (0, 1, 0), tilt_angle_deg)

# Position cradle so its back sits just inside the inner face of the lip clamp
cradle = cradle.translate((
    -(lip_channel_width / 2.0 + lip_wall_thickness + cradle_outer_depth / 2.0),
    0,
    inner_brace_height / 2.0
))

# ====== COMBINE PARTS (BASE MOUNT) ======
base_mount = lip_block.union(cradle)

# Soften vertical edges
#base_mount = base_mount.edges("|Z").chamfer(1.0)

# ====== MIRRORED PAIR ======
mount_left = base_mount.translate((- (cradle_outer_width / 2.0 + 30.0), 0, 0))

mount_right = (
    base_mount
    .mirror(mirrorPlane="YZ", basePointVector=(0, 0, 0))
    .translate((cradle_outer_width / 2.0 + 30.0, 0, 0))
)

# Optional viewer (works in cq-editor; no-op in plain Python)
try:
    from cq_server.ui import show_object
except ImportError:
    def show_object(*args, **kwargs):
        pass

show_object(mount_left, name="JBL_Clip4_Pilot_LeftDoor")
show_object(mount_right, name="JBL_Clip4_Pilot_RightDoor")

# ====== EXPORT GEOMETRY ======
# Use the folder where this script lives
script_dir = os.path.dirname(os.path.abspath(__file__))

left_stl  = os.path.join(script_dir, "JBL_Clip4_Pilot_LeftDoor.stl")
right_stl = os.path.join(script_dir, "JBL_Clip4_Pilot_RightDoor.stl")

left_step  = os.path.join(script_dir, "JBL_Clip4_Pilot_LeftDoor.step")
right_step = os.path.join(script_dir, "JBL_Clip4_Pilot_RightDoor.step")

print("Exporting STL and STEP to:", script_dir)

exporters.export(mount_left,  left_stl)
exporters.export(mount_right, right_stl)

exporters.export(mount_left,  left_step)
exporters.export(mount_right, right_step)

print("Done.")
