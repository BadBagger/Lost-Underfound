#!/usr/bin/env python3
"""Render custom Pip/Otto story-action clips from the Meshy humanoid rig."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector


BONES = {
    "hips": "Hips",
    "spine2": "Spine02",
    "spine1": "Spine01",
    "spine": "Spine",
    "neck": "neck",
    "head": "Head",
    "l_arm": "LeftArm",
    "l_fore": "LeftForeArm",
    "l_hand": "LeftHand",
    "r_arm": "RightArm",
    "r_fore": "RightForeArm",
    "r_hand": "RightHand",
    "l_up": "LeftUpLeg",
    "l_leg": "LeftLeg",
    "l_foot": "LeftFoot",
    "r_up": "RightUpLeg",
    "r_leg": "RightLeg",
    "r_foot": "RightFoot",
}


CLIPS = {
    "inspect_talk": {
        "fps": 12,
        "frames": 12,
        "view": "three-quarter-left",
        "description": "Pip leans in, glances, gestures, and settles for inspect/talk lines; nervous kid energy, not adult poise.",
        "keys": [
            (0, {"spine_x": 0, "spine_y": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "r_fore_x": 0, "l_arm_z": 6}),
            (2, {"spine_x": 7, "spine_y": -4, "head_x": -5, "head_z": -8, "r_arm_z": -18, "r_fore_x": -24, "l_arm_z": 8}),
            (4, {"spine_x": 9, "spine_y": -6, "head_x": -8, "head_z": 7, "r_arm_z": -12, "r_fore_x": -36, "l_arm_z": 12}),
            (7, {"spine_x": 3, "spine_y": 2, "head_x": 3, "head_z": -4, "r_arm_z": -38, "r_fore_x": -18, "l_arm_z": -4}),
            (9, {"spine_x": -3, "spine_y": -2, "head_x": 2, "head_z": 3, "r_arm_z": -12, "r_fore_x": -8, "l_arm_z": 13}),
            (10, {"spine_x": 0, "spine_y": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "r_fore_x": 0, "l_arm_z": 6}),
            (11, {"spine_x": 0, "spine_y": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "r_fore_x": 0, "l_arm_z": 6}),
        ],
    },
    "pickup_button": {
        "fps": 12,
        "frames": 14,
        "view": "three-quarter-left",
        "description": "Crouch, reach into dust, hold anticipation, rise presenting the found button with a small kid stumble-recover.",
        "keys": [
            (0, {"hips_x": 0, "spine_x": 0, "head_x": 0, "r_arm_z": -6, "r_fore_x": 0, "l_up_x": 0, "r_up_x": 0}),
            (2, {"hips_x": 8, "spine_x": 12, "head_x": -8, "r_arm_z": -20, "r_fore_x": -18, "l_up_x": -14, "r_up_x": -12}),
            (4, {"hips_x": 20, "spine_x": 28, "head_x": -16, "r_arm_z": -48, "r_fore_x": -52, "l_up_x": -34, "r_up_x": -28, "l_leg_x": 18, "r_leg_x": 16}),
            (6, {"hips_x": 22, "spine_x": 32, "head_x": -18, "r_arm_z": -58, "r_fore_x": -70, "l_up_x": -36, "r_up_x": -30, "l_leg_x": 20, "r_leg_x": 18}),
            (8, {"hips_x": 18, "spine_x": 25, "head_x": -10, "r_arm_z": -50, "r_fore_x": -58, "l_up_x": -30, "r_up_x": -26}),
            (10, {"hips_x": 7, "spine_x": 8, "head_x": 2, "r_arm_z": -72, "r_fore_x": -12, "l_arm_z": 10, "l_up_x": -8, "r_up_x": -6}),
            (11, {"hips_x": -4, "hips_z": -5, "spine_x": -6, "spine_y": 4, "head_x": 7, "head_z": -6, "r_arm_z": -84, "r_fore_x": 8, "l_arm_z": 24, "l_up_x": 4, "r_up_x": -10}),
            (12, {"hips_x": 0, "spine_x": -2, "head_x": 4, "r_arm_z": -80, "r_fore_x": 5, "l_arm_z": 8, "l_up_x": 0, "r_up_x": 0}),
            (13, {"hips_x": 0, "spine_x": -2, "head_x": 4, "r_arm_z": -80, "r_fore_x": 5, "l_arm_z": 8, "l_up_x": 0, "r_up_x": 0}),
        ],
    },
    "handoff_button": {
        "fps": 12,
        "frames": 10,
        "view": "three-quarter-left",
        "description": "Windup, extend/toss button to Old Bottlecap, follow-through, then a small off-balance empty-hand recover.",
        "keys": [
            (0, {"spine_y": 0, "head_z": 0, "r_arm_z": -74, "r_fore_x": 4, "l_arm_z": 6}),
            (2, {"spine_y": 7, "head_z": 5, "r_arm_z": -48, "r_fore_x": -35, "l_arm_z": -10}),
            (4, {"spine_y": -9, "head_z": -8, "r_arm_z": -104, "r_fore_x": -6, "l_arm_z": 12}),
            (5, {"spine_y": -13, "head_z": -10, "r_arm_z": -112, "r_fore_x": 10, "l_arm_z": 16}),
            (6, {"spine_x": 4, "spine_y": -15, "hips_z": -4, "head_z": -12, "r_arm_z": -106, "r_fore_x": 18, "l_arm_z": 28, "r_up_x": -6, "l_up_x": 3}),
            (7, {"spine_y": -5, "head_z": -4, "r_arm_z": -80, "r_fore_x": -8, "l_arm_z": 8}),
            (9, {"spine_y": 0, "head_z": 0, "r_arm_z": -10, "r_fore_x": 0, "l_arm_z": 6}),
        ],
    },
    "relief_transition": {
        "fps": 12,
        "frames": 12,
        "view": "three-quarter-left",
        "description": "After toll accepted: tense, exhale, excited kid bounce, tiny stumble, look toward grate, pre-exit step.",
        "keys": [
            (0, {"spine_x": 3, "head_x": -6, "head_z": 3, "r_arm_z": -20, "l_arm_z": 20}),
            (2, {"spine_x": -4, "head_x": 3, "head_z": 0, "r_arm_z": -6, "l_arm_z": 6}),
            (4, {"spine_x": -8, "head_x": 8, "head_z": -4, "r_arm_z": -30, "l_arm_z": 32, "hips_z": 4}),
            (5, {"spine_x": -2, "spine_y": 5, "head_x": 5, "head_z": -9, "r_arm_z": -38, "l_arm_z": 40, "hips_z": -6, "r_up_x": -8, "l_up_x": 6}),
            (6, {"spine_x": 2, "head_x": 2, "head_z": -12, "r_arm_z": -16, "l_arm_z": 10, "hips_z": -2}),
            (8, {"spine_x": 5, "head_x": -4, "head_z": -20, "r_arm_z": -10, "l_arm_z": 8, "r_up_x": -18, "l_up_x": 12}),
            (11, {"spine_x": 5, "head_x": -4, "head_z": -20, "r_arm_z": -10, "l_arm_z": 8, "r_up_x": -18, "l_up_x": 12}),
        ],
    },
    "scuttle_react": {
        "fps": 12,
        "frames": 8,
        "view": "three-quarter-left",
        "description": "Pip reacts to Scuttle's one-shot dash through the cobweb with a startled kid flinch, then settles.",
        "keys": [
            (0, {"spine_x": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
            (1, {"spine_x": 6, "head_x": -7, "head_z": 18, "r_arm_z": -20, "l_arm_z": 18}),
            (3, {"spine_x": -7, "head_x": 10, "head_z": 24, "r_arm_z": -42, "l_arm_z": 36, "hips_z": -5, "r_up_x": -10, "l_up_x": 7}),
            (5, {"spine_x": 3, "head_x": 4, "head_z": 8, "r_arm_z": -16, "l_arm_z": 14, "hips_z": 3}),
            (7, {"spine_x": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
        ],
    },
    "blocked_exit": {
        "fps": 12,
        "frames": 10,
        "view": "three-quarter-left",
        "description": "Try to leave before gate is open: small kid step, catches himself, turns back determined.",
        "keys": [
            (0, {"spine_y": 0, "head_z": 0, "r_up_x": 0, "l_up_x": 0}),
            (2, {"spine_y": -7, "head_z": -12, "r_up_x": -20, "l_up_x": 10, "r_arm_z": -12, "l_arm_z": 8}),
            (4, {"spine_y": -10, "head_z": -20, "r_up_x": -8, "l_up_x": 6, "r_arm_z": -8, "l_arm_z": 6}),
            (5, {"spine_x": 5, "spine_y": -8, "head_z": -18, "hips_z": -6, "r_up_x": -16, "l_up_x": 12, "r_arm_z": -28, "l_arm_z": 20}),
            (6, {"spine_y": 4, "head_z": 10, "r_arm_z": -32, "l_arm_z": 22}),
            (9, {"spine_y": 0, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
        ],
    },
    "mend_reach": {
        "fps": 12,
        "frames": 16,
        "view": "three-quarter-left",
        "description": "Act 2 gentle mend action: Pip crouches carefully, reaches with both hands, holds the delicate repair, then eases back without a pickup pop.",
        "keys": [
            (0, {"hips_x": 0, "spine_x": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
            (2, {"hips_x": 5, "spine_x": 9, "head_x": -8, "head_z": -5, "r_arm_z": -26, "r_fore_x": -18, "l_arm_z": -16, "l_fore_x": -16, "l_up_x": -8, "r_up_x": -7}),
            (4, {"hips_x": 14, "spine_x": 20, "head_x": -14, "head_z": -9, "r_arm_z": -48, "r_fore_x": -42, "l_arm_z": -40, "l_fore_x": -36, "l_up_x": -24, "r_up_x": -22, "l_leg_x": 14, "r_leg_x": 13}),
            (6, {"hips_x": 19, "spine_x": 27, "head_x": -17, "head_z": -12, "r_arm_z": -58, "r_fore_x": -55, "l_arm_z": -51, "l_fore_x": -49, "l_up_x": -31, "r_up_x": -29, "l_leg_x": 18, "r_leg_x": 17}),
            (8, {"hips_x": 19, "spine_x": 26, "head_x": -15, "head_z": -10, "r_arm_z": -60, "r_fore_x": -58, "l_arm_z": -53, "l_fore_x": -51, "l_up_x": -31, "r_up_x": -29, "l_leg_x": 18, "r_leg_x": 17}),
            (10, {"hips_x": 16, "spine_x": 22, "head_x": -12, "head_z": -7, "r_arm_z": -54, "r_fore_x": -46, "l_arm_z": -46, "l_fore_x": -40, "l_up_x": -26, "r_up_x": -24}),
            (12, {"hips_x": 6, "spine_x": 8, "head_x": -2, "head_z": 2, "r_arm_z": -28, "r_fore_x": -18, "l_arm_z": -16, "l_fore_x": -12, "l_up_x": -8, "r_up_x": -7}),
            (14, {"hips_x": -2, "spine_x": -3, "head_x": 5, "head_z": 4, "hips_z": -3, "r_arm_z": -14, "l_arm_z": 10, "l_up_x": 3, "r_up_x": -5}),
            (15, {"hips_x": 0, "spine_x": 0, "head_x": 2, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
        ],
    },
    "worried_grommet": {
        "fps": 12,
        "frames": 12,
        "view": "three-quarter-left",
        "description": "Act 3 worried-for-Grommet reaction: sudden fear, kid overstep, both hands lifted, then a held scared check-in.",
        "keys": [
            (0, {"spine_x": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
            (1, {"hips_z": -4, "spine_x": 8, "spine_y": -8, "head_x": -10, "head_z": 15, "r_arm_z": -32, "r_fore_x": -18, "l_arm_z": 30, "l_fore_x": -15}),
            (3, {"hips_z": -10, "spine_x": 20, "spine_y": -12, "head_x": -18, "head_z": 28, "r_arm_z": -78, "r_fore_x": -44, "r_hand_z": 18, "l_arm_z": 78, "l_fore_x": -40, "l_hand_z": -18, "r_up_x": -18, "l_up_x": 14}),
            (4, {"hips_z": -13, "spine_x": 17, "spine_y": -8, "head_x": -15, "head_z": 23, "r_arm_z": -88, "r_fore_x": -50, "r_hand_z": 25, "l_arm_z": 86, "l_fore_x": -48, "l_hand_z": -25, "r_up_x": -12, "l_up_x": 10}),
            (6, {"hips_z": -5, "spine_x": 12, "spine_y": -5, "head_x": -11, "head_z": 18, "r_arm_z": -62, "r_fore_x": -38, "l_arm_z": 64, "l_fore_x": -35, "r_up_x": -8, "l_up_x": 7}),
            (8, {"spine_x": 8, "spine_y": -3, "head_x": -7, "head_z": 13, "r_arm_z": -48, "r_fore_x": -28, "l_arm_z": 45, "l_fore_x": -24}),
            (11, {"spine_x": 8, "spine_y": -3, "head_x": -7, "head_z": 13, "r_arm_z": -48, "r_fore_x": -28, "l_arm_z": 45, "l_fore_x": -24}),
        ],
    },
    "relief_grommet": {
        "fps": 12,
        "frames": 16,
        "view": "three-quarter-left",
        "description": "Act 3 relief-for-Grommet reaction: scared hold, shoulders drop, small kid exhale, hands soften, then a quiet grateful look up.",
        "keys": [
            (0, {"hips_z": -5, "spine_x": 9, "spine_y": -3, "head_x": -8, "head_z": 13, "r_arm_z": -48, "r_fore_x": -28, "l_arm_z": 45, "l_fore_x": -24}),
            (2, {"hips_z": -6, "spine_x": 10, "spine_y": -4, "head_x": -9, "head_z": 12, "r_arm_z": -45, "r_fore_x": -26, "l_arm_z": 42, "l_fore_x": -23}),
            (4, {"hips_z": -2, "spine_x": 4, "spine_y": -2, "head_x": -3, "head_z": 8, "r_arm_z": -33, "r_fore_x": -18, "l_arm_z": 30, "l_fore_x": -16}),
            (6, {"hips_z": 2, "spine_x": -6, "spine_y": 1, "head_x": 5, "head_z": 2, "r_arm_z": -22, "r_fore_x": -10, "l_arm_z": 20, "l_fore_x": -8}),
            (8, {"hips_z": 5, "spine_x": -10, "spine_y": 3, "head_x": 8, "head_z": -3, "r_arm_z": -13, "r_fore_x": -5, "l_arm_z": 12, "l_fore_x": -4}),
            (9, {"hips_z": -3, "spine_x": -4, "spine_y": 4, "head_x": 8, "head_z": -5, "r_arm_z": -22, "r_fore_x": -8, "l_arm_z": 22, "l_fore_x": -7, "r_up_x": -5, "l_up_x": 4}),
            (11, {"hips_z": 0, "spine_x": -2, "spine_y": 2, "head_x": 4, "head_z": -8, "r_arm_z": -12, "r_fore_x": -4, "l_arm_z": 10, "l_fore_x": -3}),
            (13, {"hips_z": 0, "spine_x": 1, "spine_y": 0, "head_x": 0, "head_z": -5, "r_arm_z": -8, "r_fore_x": 0, "l_arm_z": 6, "l_fore_x": 0}),
            (15, {"hips_z": 0, "spine_x": 1, "spine_y": 0, "head_x": 0, "head_z": -5, "r_arm_z": -8, "r_fore_x": 0, "l_arm_z": 6, "l_fore_x": 0}),
        ],
    },
    "marble_search": {
        "fps": 12,
        "frames": 18,
        "view": "three-quarter-left",
        "description": "Act 3 repeatable marble search: crouch, sift carefully left-to-right, hesitate, check one candidate, and reset for another inspect/take loop.",
        "keys": [
            (0, {"hips_x": 0, "spine_x": 0, "head_x": 0, "r_arm_z": -8, "l_arm_z": 6}),
            (2, {"hips_x": 9, "spine_x": 12, "head_x": -8, "head_z": -8, "r_arm_z": -27, "r_fore_x": -18, "l_arm_z": -12, "l_fore_x": -12, "l_up_x": -14, "r_up_x": -12}),
            (4, {"hips_x": 22, "spine_x": 30, "head_x": -18, "head_z": -14, "r_arm_z": -58, "r_fore_x": -55, "l_arm_z": -42, "l_fore_x": -36, "l_up_x": -36, "r_up_x": -30, "l_leg_x": 20, "r_leg_x": 18}),
            (6, {"hips_x": 24, "spine_x": 32, "spine_y": -5, "head_x": -20, "head_z": -22, "r_arm_z": -70, "r_fore_x": -52, "l_arm_z": -36, "l_fore_x": -38, "l_up_x": -38, "r_up_x": -31}),
            (8, {"hips_x": 24, "spine_x": 31, "spine_y": 5, "head_x": -17, "head_z": 8, "r_arm_z": -44, "r_fore_x": -46, "l_arm_z": -66, "l_fore_x": -52, "l_up_x": -38, "r_up_x": -31}),
            (10, {"hips_x": 23, "spine_x": 28, "head_x": -22, "head_z": -3, "r_arm_z": -61, "r_fore_x": -60, "l_arm_z": -58, "l_fore_x": -48, "l_up_x": -35, "r_up_x": -30}),
            (12, {"hips_x": 18, "spine_x": 21, "head_x": -9, "head_z": -12, "r_arm_z": -76, "r_fore_x": -24, "l_arm_z": -34, "l_fore_x": -20, "l_up_x": -27, "r_up_x": -24}),
            (14, {"hips_x": 12, "spine_x": 13, "head_x": -5, "head_z": -8, "r_arm_z": -68, "r_fore_x": -12, "l_arm_z": -20, "l_fore_x": -14, "l_up_x": -16, "r_up_x": -15}),
            (16, {"hips_x": 5, "spine_x": 5, "head_x": 3, "head_z": 3, "r_arm_z": -25, "r_fore_x": -5, "l_arm_z": 4, "l_up_x": -6, "r_up_x": -5}),
            (17, {"hips_x": 0, "spine_x": 0, "head_x": 0, "head_z": 0, "r_arm_z": -8, "l_arm_z": 6}),
        ],
    },
    "urgent_stumble_step": {
        "fps": 12,
        "frames": 12,
        "view": "three-quarter-left",
        "description": "Act 3 urgency movement proof: Pip tries to hurry like a kid, oversteps, arms windmill, catches balance, and pushes forward.",
        "keys": [
            (0, {"spine_y": 0, "head_z": 0, "r_up_x": 0, "l_up_x": 0, "r_arm_z": -10, "l_arm_z": 8}),
            (1, {"hips_z": 7, "spine_x": 5, "spine_y": -12, "head_x": -5, "head_z": -17, "r_up_x": -30, "l_up_x": 18, "r_leg_x": 16, "l_leg_x": -8, "r_arm_z": -36, "r_fore_x": -18, "l_arm_z": 38, "l_fore_x": -14}),
            (3, {"hips_z": -12, "spine_x": 12, "spine_y": -22, "head_x": -12, "head_z": -30, "r_up_x": -48, "l_up_x": 30, "r_leg_x": 34, "l_leg_x": -18, "r_arm_z": -82, "r_fore_x": -32, "l_arm_z": 84, "l_fore_x": -28}),
            (4, {"hips_z": -16, "spine_x": -14, "spine_y": -17, "head_x": 14, "head_z": -25, "r_up_x": -24, "l_up_x": 39, "r_leg_x": 16, "l_leg_x": -24, "r_arm_z": -104, "r_fore_x": -12, "l_arm_z": 105, "l_fore_x": -12}),
            (5, {"hips_z": -8, "spine_x": -20, "spine_y": -8, "head_x": 17, "head_z": -12, "r_up_x": 5, "l_up_x": 22, "r_leg_x": -6, "l_leg_x": -12, "r_arm_z": -74, "l_arm_z": 76}),
            (7, {"hips_z": 9, "spine_x": 8, "spine_y": -11, "head_x": 5, "head_z": -14, "r_up_x": 29, "l_up_x": -38, "r_leg_x": -16, "l_leg_x": 28, "r_arm_z": -38, "r_fore_x": -10, "l_arm_z": 42, "l_fore_x": -8}),
            (9, {"hips_z": -7, "spine_y": -12, "head_z": -18, "r_up_x": 14, "l_up_x": -30, "r_leg_x": -8, "l_leg_x": 20, "r_arm_z": -58, "l_arm_z": 62}),
            (10, {"spine_y": -7, "head_z": -12, "r_up_x": -12, "l_up_x": 11, "r_arm_z": -28, "l_arm_z": 28}),
            (11, {"spine_y": -5, "head_z": -9, "r_up_x": -12, "l_up_x": 11, "r_arm_z": -24, "l_arm_z": 22}),
        ],
    },
}


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--clip", choices=sorted(CLIPS), required=True)
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--texture", default="")
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_model(path: Path) -> None:
    resolved = path.resolve()
    if resolved.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(resolved))
    else:
        bpy.ops.import_scene.gltf(filepath=str(resolved))


def meshes() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def armatures() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]


def world_bbox(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    for obj in objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, point.x)
            mins.y = min(mins.y, point.y)
            mins.z = min(mins.z, point.z)
            maxs.x = max(maxs.x, point.x)
            maxs.y = max(maxs.y, point.y)
            maxs.z = max(maxs.z, point.z)
    return mins, maxs


def center_and_floor() -> None:
    render_meshes = [obj for obj in meshes() if obj.name.lower() != "icosphere"]
    mins, maxs = world_bbox(render_meshes)
    center = (mins + maxs) * 0.5
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location -= center
    mins, _ = world_bbox(render_meshes)
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location.z -= mins.z


def normalize_model_height(target_height: float = 1.72) -> None:
    render_meshes = [obj for obj in meshes() if obj.name.lower() != "icosphere"]
    mins, maxs = world_bbox(render_meshes)
    height = maxs.z - mins.z
    if height <= 0:
        return
    scale = target_height / height
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.scale *= scale
    bpy.context.view_layer.update()


def hide_helpers() -> None:
    for obj in bpy.context.scene.objects:
        if obj.name.lower().startswith("icosphere"):
            obj.hide_render = True
            obj.hide_viewport = True


def apply_texture_override(texture_path: Path) -> None:
    if not texture_path:
        return
    resolved = texture_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Texture override not found: {resolved}")

    image = bpy.data.images.load(str(resolved), check_existing=True)
    material = bpy.data.materials.new("pip_texture_override")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    tex = nodes.new(type="ShaderNodeTexImage")
    tex.image = image
    if bsdf:
        material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.78

    for obj in meshes():
        if obj.name.lower().startswith("icosphere"):
            continue
        obj.data.materials.clear()
        obj.data.materials.append(material)


def setup_render(resolution: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.78, 0.76, 0.70)

    bpy.ops.object.light_add(type="AREA", location=(-3.4, -4.2, 5.3))
    light = bpy.context.object
    light.name = "warm_upper_left_key"
    light.data.energy = 460
    light.data.size = 4.3

    bpy.ops.object.camera_add(location=(0, -5.5, 1.35))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.55
    look_at(cam, Vector((0, 0, 0.92)))


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def set_view(view: str) -> None:
    cam = bpy.context.scene.camera
    positions = {
        "front": Vector((0, -5.5, 1.35)),
        "three-quarter-left": Vector((2.1, -5.25, 1.35)),
        "three-quarter-right": Vector((-2.1, -5.25, 1.35)),
    }
    cam.location = positions.get(view, positions["three-quarter-left"])
    look_at(cam, Vector((0, 0, 0.92)))


def reset_pose(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0, 0, 0), "XYZ")
    bpy.ops.object.mode_set(mode="OBJECT")


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def pose_at(keys: list[tuple[int, dict[str, float]]], frame: int) -> dict[str, float]:
    if frame <= keys[0][0]:
        return dict(keys[0][1])
    if frame >= keys[-1][0]:
        return dict(keys[-1][1])
    for (fa, pa), (fb, pb) in zip(keys, keys[1:]):
        if fa <= frame <= fb:
            t = ease((frame - fa) / max(1, fb - fa))
            names = set(pa) | set(pb)
            return {name: pa.get(name, 0.0) * (1.0 - t) + pb.get(name, 0.0) * t for name in names}
    return {}


def apply_rot(armature: bpy.types.Object, name: str, degrees_xyz: tuple[float, float, float]) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = Euler(tuple(math.radians(v) for v in degrees_xyz), "XYZ")


def apply_pose(armature: bpy.types.Object, values: dict[str, float]) -> None:
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")

    hips_x = values.get("hips_x", 0.0)
    hips_z = values.get("hips_z", 0.0)
    spine_x = values.get("spine_x", 0.0)
    spine_y = values.get("spine_y", 0.0)
    head_x = values.get("head_x", 0.0)
    head_z = values.get("head_z", 0.0)
    apply_rot(armature, BONES["hips"], (hips_x, 0, hips_z))
    apply_rot(armature, BONES["spine2"], (spine_x * 0.35, spine_y * 0.25, 0))
    apply_rot(armature, BONES["spine1"], (spine_x * 0.55, spine_y * 0.35, 0))
    apply_rot(armature, BONES["spine"], (spine_x * 0.75, spine_y * 0.45, 0))
    apply_rot(armature, BONES["neck"], (head_x * 0.35, 0, head_z * 0.35))
    apply_rot(armature, BONES["head"], (head_x, 0, head_z))

    apply_rot(armature, BONES["r_arm"], (values.get("r_arm_x", 0.0), 0, values.get("r_arm_z", -8.0)))
    apply_rot(armature, BONES["r_fore"], (values.get("r_fore_x", 0.0), 0, values.get("r_fore_z", 0.0)))
    apply_rot(armature, BONES["r_hand"], (values.get("r_hand_x", 0.0), 0, values.get("r_hand_z", 0.0)))
    apply_rot(armature, BONES["l_arm"], (values.get("l_arm_x", 0.0), 0, values.get("l_arm_z", 6.0)))
    apply_rot(armature, BONES["l_fore"], (values.get("l_fore_x", 0.0), 0, values.get("l_fore_z", 0.0)))
    apply_rot(armature, BONES["l_hand"], (values.get("l_hand_x", 0.0), 0, values.get("l_hand_z", 0.0)))

    apply_rot(armature, BONES["r_up"], (values.get("r_up_x", 0.0), 0, values.get("r_up_z", 0.0)))
    apply_rot(armature, BONES["r_leg"], (values.get("r_leg_x", 0.0), 0, 0))
    apply_rot(armature, BONES["r_foot"], (values.get("r_foot_x", 0.0), 0, 0))
    apply_rot(armature, BONES["l_up"], (values.get("l_up_x", 0.0), 0, values.get("l_up_z", 0.0)))
    apply_rot(armature, BONES["l_leg"], (values.get("l_leg_x", 0.0), 0, 0))
    apply_rot(armature, BONES["l_foot"], (values.get("l_foot_x", 0.0), 0, 0))

    bpy.ops.object.mode_set(mode="OBJECT")


def main() -> None:
    args = parse_args()
    spec = CLIPS[args.clip]
    out = Path(args.out)
    raw = out / args.clip / "frames_raw"
    raw.mkdir(parents=True, exist_ok=True)

    clear_scene()
    import_model(Path(args.input))
    if args.texture:
        apply_texture_override(Path(args.texture))
    hide_helpers()
    center_and_floor()
    normalize_model_height()
    center_and_floor()
    setup_render(args.resolution)
    set_view(spec["view"])
    armature = armatures()[0]

    metadata = {
        "input": str(Path(args.input).resolve()),
        "texture_override": str(Path(args.texture).resolve()) if args.texture else "",
        "clip": args.clip,
        "fps": spec["fps"],
        "frames": spec["frames"],
        "view": spec["view"],
        "armature": armature.name,
        "description": spec["description"],
        "source_script": "script/ACT_01_SCRIPT.json" if args.clip in {"inspect_talk", "pickup_button", "handoff_button", "relief_transition", "scuttle_react", "blocked_exit"} else "script/ACT_02_SCRIPT.json + script/ACT_03_SCRIPT.json",
        "pose_values": [],
    }

    scene = bpy.context.scene
    for frame in range(spec["frames"]):
        scene.frame_set(frame)
        values = pose_at(spec["keys"], frame)
        apply_pose(armature, values)
        metadata["pose_values"].append({"frame": frame, **{k: round(v, 3) for k, v in sorted(values.items())}})
        scene.render.filepath = str(raw / f"pip_{args.clip}_raw_{frame:03d}.png")
        bpy.ops.render.render(write_still=True)

    (out / args.clip / f"pip_{args.clip}_blender_manifest.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"clip": args.clip, "frames": spec["frames"], "out": str(out / args.clip)}, indent=2))


if __name__ == "__main__":
    main()
