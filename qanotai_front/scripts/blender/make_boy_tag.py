"""Build public/models/boy-tag.glb: one boy with two animations — "spray" (new) and "flee".

Run headless:  blender -b --factory-startup --python scripts/blender/make_boy_tag.py

"spray" is authored here procedurally on the Mixamo rig of boy.glb, so it matches the hero picture exactly:
he shakes the can, then sprays "QANOT.AI" across the wall left → right — side-stepping along it, the right arm
(IK) reaching for every stroke, the head following the nozzle — then the doodles (bulb, eagle, chart, book, cap),
crouching for the low ones; steps back, glances left (the police are coming) and turns into the first frame of
"flee", so the website can cross-fade straight into the run with the same model.

An animated empty "PaintTarget" (child of the armature) is exported with "spray": its position is where the paint
lands on the wall and its scale is the spray radius in body heights (0 = not spraying). The website reveals the
painting under it, so the drawing always follows the hand.

The wall artwork positions below are the hero photo's coordinates (running-boy.tsx SCENE); keep them in sync.
"""

import math
import os

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.normpath(os.path.join(HERE, "..", "..", "public", "models"))
OUT = os.path.join(MODELS, "boy-tag.glb")
FPS = 24

# hero photo (running-boy.tsx SCENE): fractions of the photo's width / height
ASPECT = 1671 / 941
BOY_H = 0.4  # his height × photo height
FEET = (0.5355, 0.868)  # where he starts; running-boy.tsx SCENE.feet must match
TAG = (0.585, 0.965, 0.44)  # x0, x1, y
DOODLES = [  # painted right → left after the tag (so he walks back along the wall once)
    ("bulb", 0.93, 0.245, 0.055),
    ("eagle", 0.935, 0.565, 0.07),
    ("chart", 0.858, 0.648, 0.07),
    ("book", 0.665, 0.665, 0.065),
    ("cap", 0.585, 0.345, 0.07),
]
TAG_R = 0.13  # spray radius on the tag, body heights
HAND_SIDE = 0.2  # his right hand works this far right of his centre (body heights)


def S(x: float) -> float:  # photo x → screen-right offset from the start, body heights
    return (x - FEET[0]) * ASPECT / BOY_H


def U(y: float) -> float:  # photo y → height above the floor, body heights
    return (FEET[1] - y) / BOY_H


def smooth(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


# ─── scene ───────────────────────────────────────────────────────────────────

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "boy.glb"))
scene = bpy.context.scene
scene.render.fps = FPS
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for o in [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("Icosphere")]:
    bpy.data.objects.remove(o, do_unlink=True)  # a stray helper sphere in the Tripo export
body = next(o for o in bpy.data.objects if o.type == "MESH")
flee = arm.animation_data.action
flee.name = "flee"
pb = arm.pose.bones
HIPS = "mixamorig:Hips"


def fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def mesh_box(frame: int):
    """World bounding box (min, max) of the evaluated, posed body at a frame."""
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps)
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


# the first frame of "flee" is a plain standing pose: it is the base pose of the new clip
scene.frame_set(0)
base_local = {b.name: b.matrix_basis.copy() for b in pb}
hips0 = pb[HIPS].matrix.copy()  # armature space
lo0, hi0 = mesh_box(0)
H = hi0.z - lo0.z  # body height, Blender units
ankle0 = {side: pb[f"mixamorig:{side}Foot"].head.copy() for side in ("Left", "Right")}
print(f"body height {H:.3f}")

arm.animation_data.action = None
for b in pb:
    b.matrix_basis = base_local[b.name]
bpy.context.view_layer.update()

# flee faces −Y; for the spray he faces the wall (+X), turned a little to his left so his spraying arm shows
FACE = math.radians(90 + 15)


def empty(name: str, size=0.03):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    scene.collection.objects.link(e)
    return e


hand_t, look_t, elbow_p = empty("HandTarget"), empty("LookTarget"), empty("ElbowPole")
foot_t = {s: empty(f"Foot{s}") for s in ("Left", "Right")}
knee_p = {s: empty(f"KneePole{s}") for s in ("Left", "Right")}
paint = empty("PaintTarget", 0.05)
paint.parent = arm  # exported with the model; the website reads it


def add_ik(bone: str, target, pole, chain=2):
    c = pb[bone].constraints.new("IK")
    c.target, c.pole_target, c.chain_count = target, pole, chain
    return c


ik_arm = add_ik("mixamorig:RightForeArm", hand_t, elbow_p)
ik_leg = {s: add_ik(f"mixamorig:{s}Leg", foot_t[s], knee_p[s]) for s in ("Left", "Right")}

# feet stay flat on the floor: each foot copies the world rotation it has in the base pose, turned with the body
foot_rot0 = {sd: pb[f"mixamorig:{sd}Foot"].matrix.to_3x3().copy() for sd in ("Left", "Right")}
foot_r = {}
flat = {}
for sd in ("Left", "Right"):
    foot_r[sd] = empty(f"FootRot{sd}")
    foot_r[sd].rotation_mode = "QUATERNION"
    c = pb[f"mixamorig:{sd}Foot"].constraints.new("COPY_ROTATION")
    c.target = foot_r[sd]
    flat[sd] = c

# head looks along the bone axis that points forward in the base pose
fwd0 = Vector((0, -1, 0))
hm = pb["mixamorig:Head"].matrix.to_3x3()
axes = {"X": hm.col[0], "Y": hm.col[1], "Z": hm.col[2]}
ax = max(axes, key=lambda k: abs(axes[k].dot(fwd0)))
look = pb["mixamorig:Head"].constraints.new("DAMPED_TRACK")
look.target = look_t
look.track_axis = ("TRACK_" if axes[ax].dot(fwd0) > 0 else "TRACK_NEGATIVE_") + ax
lean = pb["mixamorig:Spine2"].constraints.new("DAMPED_TRACK")
lean.target, lean.track_axis = hand_t, "TRACK_Y"


def screen(s, u, d):
    """Screen offsets (right, up, toward the wall) in body heights → Blender (X toward wall, −Y right, Z up)."""
    return Vector((d * H, -s * H, u * H))


# ─── timeline (seconds) ──────────────────────────────────────────────────────

segments = []  # (t0, t1, what): what is fn(t) → state for a working segment, None for a move between two


def seg(dur, what=None):
    t0 = segments[-1][1] if segments else 0.0
    segments.append((t0, t0 + dur, what))


def work(dur, fn):
    """A segment whose state is fn(t, t0, t1)."""
    t0 = segments[-1][1] if segments else 0.0
    segments.append((t0, t0 + dur, lambda t, a=t0, b=t0 + dur: fn(t, a, b)))


tag_s0, tag_s1, tag_u = S(TAG[0]), S(TAG[1]), U(TAG[2])
root0 = tag_s0 - HAND_SIDE


def REST(r):  # hand by the chest, holding the can
    return (r + 0.16, 0.6, 0.18)


def shake(t, t0, t1):
    s, u, d = REST(root0)
    k = (t - t0) / (t1 - t0)
    return {"hand": (s, u + 0.05 * math.sin(2 * math.pi * 4.5 * (t - t0)) * math.sin(math.pi * k), d), "paint": None, "root": root0}


def tag(t, t0, t1):
    q = (t - t0) / (t1 - t0)
    s = lerp(tag_s0, tag_s1, q)
    # letter strokes: quick up-down zigzag while travelling right
    u = tag_u + 0.11 * math.sin(2 * math.pi * 2.3 * (t - t0)) + 0.025 * math.sin(2 * math.pi * 0.9 * (t - t0))
    return {"hand": (s, u, 0.55), "paint": (s, u, TAG_R), "root": s - HAND_SIDE}


def doodle(cx, cy, w):
    def fn(t, t0, t1):
        q = (t - t0) / (t1 - t0)
        rows = 3
        row = min(int(q * rows), rows - 1)
        k = q * rows - row
        k = k if row % 2 == 0 else 1 - k  # back-and-forth passes
        s = cx + (k - 0.5) * w * 0.9
        u = cy + ((row + 0.5) / rows - 0.5) * w * 0.8
        return {"hand": (s, u, 0.5), "paint": (s, u, w * 0.36), "root": cx - HAND_SIDE}

    return fn


work(1.3, shake)
seg(0.35)  # reach up to the start of the tag
work(6.2, tag)
WALK = 0.38  # body heights per second when walking along the wall between pieces
prev_x = tag_s1
for kind, x, y, size in DOODLES:
    seg(0.35 + abs(S(x) - prev_x) / WALK)  # walk / reach to the doodle, slowly enough for the feet to keep up
    work(0.85, doodle(S(x), U(y), size * ASPECT / BOY_H))
    prev_x = S(x)
seg(0.45)  # lower the arm
seg(1.0, "back")  # step back from the wall
seg(0.9, "look")  # glance over the left shoulder
seg(0.6, "turn")  # turn into the first frame of "flee"
END = segments[-1][1]
N = round(END * FPS)


def state_at(t):
    """Hand / paint / root for time t; gaps between painted pieces are eased between their ends."""
    for i, (t0, t1, fn) in enumerate(segments):
        if t <= t1 or i == len(segments) - 1:
            break
    if callable(fn):
        st = fn(t)
        st["phase"] = "work"
        return st
    prev = segments[i - 1][2](segments[i - 1][1]) if i > 0 and callable(segments[i - 1][2]) else None
    nxt = segments[i + 1][2](segments[i + 1][0]) if i + 1 < len(segments) and callable(segments[i + 1][2]) else None
    k = smooth((t - t0) / (t1 - t0))
    if prev and nxt:  # travelling between two pieces
        hand = tuple(lerp(a, b, k) for a, b in zip(prev["hand"], nxt["hand"]))
        hand = (hand[0], hand[1] + 0.06 * math.sin(math.pi * k), min(hand[2], lerp(prev["hand"][2], nxt["hand"][2], k)) - 0.08 * math.sin(math.pi * k))
        return {"hand": hand, "paint": None, "root": lerp(prev["root"], nxt["root"], k), "phase": "work"}
    last = segments_last_work()
    r = last["root"]
    rest = REST(r)
    if fn is None:  # lowering the arm after the last doodle
        hand = tuple(lerp(a, b, k) for a, b in zip(last["hand"], rest))
        return {"hand": hand, "paint": None, "root": r, "phase": "work"}
    if fn == "back":
        return {"hand": rest, "paint": None, "root": r, "depth": -0.35 * k, "phase": "back"}
    if fn == "look":
        return {"hand": rest, "paint": None, "root": r, "depth": -0.35, "look_left": smooth(k * 1.6), "phase": "look"}
    return {"hand": rest, "paint": None, "root": r, "depth": -0.35, "look_left": 1.0, "turn": k, "phase": "turn"}


def segments_last_work():
    for t0, t1, fn in reversed(segments):
        if callable(fn):
            return fn(t1)


# ─── feet: plant, then step when the body has moved away from them ───────────

STANCE = 0.1  # half the distance between the feet, body heights
STEP_T = 0.24
MAX_STEP = 0.3  # body heights
plan = []
feet = {"Left": [root0 - STANCE, 0.0], "Right": [root0 + STANCE, 0.0]}  # planted (s, d)
stepping = {}  # side → (t0, from, to)
BODY_SPEED = 0.38  # the body follows its wanted place no faster than this (body heights / s); the arm reaches
torso = root0
for f in range(N + 1):
    t = f / FPS
    st = state_at(t)
    gap = st["root"] - torso
    torso += max(-BODY_SPEED / FPS, min(BODY_SPEED / FPS, gap))
    st["root"] = torso
    r, d = st["root"], st.get("depth", 0.0)
    for side, sign in (("Left", -1), ("Right", 1)):
        if side in stepping:
            t0, a, b = stepping[side]
            if t - t0 >= STEP_T:
                feet[side] = list(b)
                del stepping[side]
    if not stepping and st["phase"] != "turn":
        # the foot left furthest behind steps first; it lands a little ahead of where it's wanted, never past
        # the other foot (feet that cross make the leg IK flip), and no step is longer than MAX_STEP
        offs = {}
        for side, sign in (("Left", -1), ("Right", 1)):
            want = (r + sign * STANCE, d)
            cur = feet[side]
            offs[side] = (math.hypot(want[0] - cur[0], want[1] - cur[1]), want, cur, sign)
        side = max(offs, key=lambda k: offs[k][0])
        off, want, cur, sign = offs[side]
        if off > 0.09:
            ahead = [want[0] + (want[0] - cur[0]) * 0.3, want[1] + (want[1] - cur[1]) * 0.3]
            other = feet["Right" if side == "Left" else "Left"][0]
            ahead[0] = min(ahead[0], other - 2 * STANCE * 0.6) if sign < 0 else max(ahead[0], other + 2 * STANCE * 0.6)
            step = math.hypot(ahead[0] - cur[0], ahead[1] - cur[1])
            if step > MAX_STEP:
                k = MAX_STEP / step
                ahead = [cur[0] + (ahead[0] - cur[0]) * k, cur[1] + (ahead[1] - cur[1]) * k]
            stepping[side] = (t, tuple(cur), tuple(ahead))
    pos = {}
    lift = 0.0
    for side in ("Left", "Right"):
        if side in stepping:
            t0, a, b = stepping[side]
            k = smooth((t - t0) / STEP_T)
            h = math.sin(math.pi * min((t - t0) / STEP_T, 1.0)) * 0.05
            pos[side] = (lerp(a[0], b[0], k), h, lerp(a[1], b[1], k))
            lift = max(lift, h)
        else:
            pos[side] = (feet[side][0], 0.0, feet[side][1])
    plan.append((st, pos, lift))

worst = max(math.hypot(pos[sd][0] - (st["root"] + sg * STANCE * 0.5), pos[sd][2] - st.get("depth", 0.0))
            for st, pos, _ in plan for sd, sg in (("Left", -1), ("Right", 1)))
print(f"feet: worst sideways reach from the hip {worst:.2f} body heights (the leg reaches ~0.45)")

# ─── keyframes ───────────────────────────────────────────────────────────────

up0 = hips0.translation.z
ank_u = {s: ankle0[s].z / H for s in ankle0}
base_rot = hips0.to_3x3()


def key(obj_or_bone, *paths, frame):
    for p in paths:
        obj_or_bone.keyframe_insert(p, frame=frame)


def calibrate_poles():
    """Pick each IK pole angle so the elbow / knee actually points at its pole target (depends on bone roll)."""
    for c, joint in ((ik_arm, "mixamorig:RightForeArm"), (ik_leg["Left"], "mixamorig:LeftLeg"), (ik_leg["Right"], "mixamorig:RightLeg")):
        best = None
        for deg in range(-180, 180, 15):
            c.pole_angle = math.radians(deg)
            bpy.context.view_layer.update()
            dist = (arm.matrix_world @ pb[joint].head - c.pole_target.matrix_world.translation).length
            if best is None or dist < best[0]:
                best = (dist, deg)
        c.pole_angle = math.radians(best[1])
        print(f"pole angle {joint}: {best[1]}°")


DEBUG_FRAMES = set()
final_root = None
for f, (st, pos, lift) in enumerate(plan):
    t = f / FPS
    r, d = st["root"], st.get("depth", 0.0)
    turn = st.get("turn", 0.0)
    hand_u = st["hand"][1]
    crouch = smooth((0.78 - hand_u) / 0.3) * 0.045 if st["phase"] == "work" else 0.0
    bob = -0.02 * lift / 0.05
    yaw = lerp(FACE, 0.0, smooth(turn))
    rot = Matrix.Rotation(yaw, 3, "Z") @ base_rot
    loc = screen(r, 0, d) + Vector((0, 0, up0 + (bob - crouch) * H))
    loc.x += hips0.translation.x
    pb[HIPS].matrix = Matrix.Translation(loc) @ rot.to_4x4()
    bpy.context.view_layer.update()
    key(pb[HIPS], "location", "rotation_quaternion", frame=f)

    hs, hu, hd = st["hand"]
    hand_t.location = screen(hs, hu, d + hd)
    key(hand_t, "location", frame=f)
    # elbow pole: down and out to his right, behind the arm
    elbow_p.location = screen(r + 0.45, 0.35, d - 0.25)
    key(elbow_p, "location", frame=f)
    for side, sign in (("Left", -1), ("Right", 1)):
        fs, fh, fd = pos[side]
        foot_t[side].location = screen(fs, ank_u[side] + fh, d * 0 + fd)
        key(foot_t[side], "location", frame=f)
        knee_p[side].location = screen(fs + sign * 0.05, 0.3, fd + 0.6)  # knees forward, toward the wall
        key(knee_p[side], "location", frame=f)

    if f == 0:
        calibrate_poles()
    if f in DEBUG_FRAMES:
        bpy.context.view_layer.update()
        for sd in ("Left", "Right"):
            hip = arm.matrix_world @ pb[f"mixamorig:{sd}UpLeg"].head
            leg = pb[f"mixamorig:{sd}UpLeg"].length + pb[f"mixamorig:{sd}Leg"].length
            tgt = foot_t[sd].location
            print(f"f{f} {sd}: hip {tuple(round(v, 2) for v in hip)} target {tuple(round(v, 2) for v in tgt)} "
                  f"dist {(tgt - hip).length:.2f} leg {leg:.2f} stepping {pos[sd][1] > 0}")

    look_left = st.get("look_left", 0.0)
    target = Vector(st["paint"][:2] + (0.6,)) if st["paint"] else Vector((hs, hu, 0.6))
    if look_left:  # glance over the left shoulder, toward the street the police come from
        target = target.lerp(Vector((r - 1.2, 0.85, -1.5)), look_left)
    look_t.location = screen(target.x, target.y, target.z + d)
    key(look_t, "location", frame=f)

    influence = 1.0 - smooth(turn)
    for sd in ("Left", "Right"):
        foot_r[sd].rotation_quaternion = (Matrix.Rotation(yaw, 3, "Z") @ foot_rot0[sd]).to_quaternion()
        key(foot_r[sd], "rotation_quaternion", frame=f)
    for c in (ik_arm, ik_leg["Left"], ik_leg["Right"], flat["Left"], flat["Right"]):
        c.influence = influence
        c.keyframe_insert("influence", frame=f)
    look.influence = 0.65 * influence
    look.keyframe_insert("influence", frame=f)
    lean.influence = 0.18 * influence if st["phase"] == "work" else 0.0
    lean.keyframe_insert("influence", frame=f)

    if st["paint"]:
        ps, pu, pr = st["paint"]
        paint.location = screen(ps, pu, 0.9)
        paint.scale = (pr, pr, pr)
    else:
        paint.scale = (0, 0, 0)
    key(paint, "location", "scale", frame=f)
    final_root = (r, d)

# at the end of the turn every constraint is off, so the pose is flee's first frame, moved to where he stands
for o in (hand_t, look_t, elbow_p, *foot_t.values(), *knee_p.values(), *foot_r.values()):
    for fc in fcurves(o.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# ─── bake the constraints into plain bone keys ───────────────────────────────

scene.frame_start, scene.frame_end = 0, N
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")
bpy.ops.nla.bake(frame_start=0, frame_end=N, only_selected=False, visual_keying=True, clear_constraints=True,
                 use_current_action=False, bake_types={"POSE"})
bpy.ops.object.mode_set(mode="OBJECT")
spray = arm.animation_data.action
spray.name = "spray"
for o in (hand_t, look_t, elbow_p, *foot_t.values(), *knee_p.values(), *foot_r.values()):
    bpy.data.objects.remove(o, do_unlink=True)

# ─── flee starts where the spray ended ───────────────────────────────────────

offset = screen(final_root[0], 0, final_root[1])  # armature space
rest = arm.data.bones[HIPS].matrix_local.to_3x3()
delta = rest.inverted() @ offset
for fc in fcurves(flee):
    if fc.data_path == f'pose.bones["{HIPS}"].location':
        for kp in fc.keyframe_points:
            kp.co.y += delta[fc.array_index]
            kp.handle_left.y += delta[fc.array_index]
            kp.handle_right.y += delta[fc.array_index]

# ─── where the website's groundModel() puts the origin, and the paint target in those terms ─────────

arm.animation_data.action = spray
lo, hi = mesh_box(0)
center = (lo + hi) / 2
print(f"spray frame 0: height {hi.z - lo.z:.3f}  centre {tuple(round(v, 3) for v in center)}  min z {lo.z:.3f}")
print(f"spray: {N} frames = {N / FPS:.2f}s; final root (s, d) = {tuple(round(v, 3) for v in final_root)} body heights")
paint_frames = [f for f, (st, _, _) in enumerate(plan) if st["paint"]]
print(f"painting from {paint_frames[0] / FPS:.2f}s to {paint_frames[-1] / FPS:.2f}s")

# ─── NLA tracks → one glTF animation each ────────────────────────────────────

arm.animation_data.action = None
for tr in list(arm.animation_data.nla_tracks):  # the importer's own track of the original clip
    arm.animation_data.nla_tracks.remove(tr)
for name, act in (("spray", spray), ("flee", flee)):
    tr = arm.animation_data.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, int(act.frame_range[0]), act)
p_act = paint.animation_data.action
paint.animation_data.action = None
tr = paint.animation_data.nla_tracks.new()
tr.name = "spray"
tr.strips.new("spray", 0, p_act)

bpy.ops.export_scene.gltf(
    filepath=OUT,
    export_format="GLB",
    export_animation_mode="NLA_TRACKS",
    export_force_sampling=True,
    export_image_format="WEBP",
    export_image_quality=82,
    export_apply=False,
)
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
