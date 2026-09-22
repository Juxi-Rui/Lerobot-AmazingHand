#!/usr/bin/env python

# Copyright 2026 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass, field

from ..config import RobotConfig
from ..so_follower.config_so_follower import SOFollowerRobotConfig


@dataclass(kw_only=True)
class SOAmazingHandFollowerConfig:
    """Base configuration class for an SO follower arm with an AmazingHand dexterous hand end-effector."""

    # Port to connect to the AmazingHand dexterous hand (its own serial bus, 8x scs0009 servos).
    # The hand is driven with rustypot's Scs0009PyController so it does not share the lerobot
    # FeetechMotorsBus stack (which would corrupt the arm bus when two buses coexist in-process).
    hand_port: str

    # Hand side: 1 = right hand, 2 = left hand.
    hand_side: int = 1

    # If True, the hand follows the leader gripper position proportionally: gripper positions between
    # `gripper_open_pos` and `gripper_close_pos` are linearly interpolated between `hand_open_angles`
    # and `hand_close_angles`. If False, the hand only switches between fully open and fully closed
    # (binary behavior). Default is True for AmazingHand teleoperation.
    hand_use_proportional_control: bool = True

    # Mapping from the leader arm's `gripper.pos` (range [0, 100]) to the AmazingHand open/close
    # state. Default assumes 0 = open and 100 = closed (AmazingHand official convention).
    # On robots whose leader gripper reads inverted (opening reads high, closing reads low), these
    # values are overridden at startup by `gripper_open_pos`/`gripper_close_pos` written by
    # `lerobot-calibrate-amazing-hand` (--leader_port) into `hand_angles.json`.
    gripper_open_pos: float = 0.0
    gripper_close_pos: float = 100.0

    # Default middle/zero positions (in degrees) for the 8 AmazingHand servos.
    # Servos are ordered: [index_1, index_2, middle_1, middle_2, ring_1, ring_2, thumb_1, thumb_2].
    # These are the same defaults as the AmazingHand demo scripts; edit to match your calibration.
    hand_middle_pos: list[float] = field(
        default_factory=lambda: [3.0, 0.0, -5.0, -8.0, -2.0, 5.0, -12.0, 0.0]
    )

    # Open/close target angles (in degrees) for the 8 AmazingHand servos. The last two values
    # control the thumb. These are the AmazingHand official demo defaults (opening = -35/+35,
    # closing = +90/-90); every robot should re-calibrate its own values via
    # `lerobot-calibrate-amazing-hand`, which auto-saves to `hand_angles.json`.
    hand_open_angles: list[float] = field(
        default_factory=lambda: [-35.0, 35.0, -35.0, 35.0, -35.0, 35.0, -35.0, 35.0]
    )
    hand_close_angles: list[float] = field(
        default_factory=lambda: [90.0, -90.0, 90.0, -90.0, 90.0, -90.0, 90.0, -90.0]
    )
    # Close speed for each servo. Last two entries are the thumb (CloseSpeed+1 in the original demo).
    hand_close_speeds: list[int] = field(
        default_factory=lambda: [3, 3, 3, 3, 3, 3, 4, 4]
    )
    # Max speed for opening the hand.
    hand_max_speed: int = 7

    # Baudrate of the hand serial bus.
    hand_baudrate: int = 1_000_000


@RobotConfig.register_subclass("so101_amazing_hand")
@dataclass
class SO101AmazingHandFollowerConfig(SOFollowerRobotConfig, SOAmazingHandFollowerConfig):
    pass
