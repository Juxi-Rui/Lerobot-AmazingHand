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

"""
Interactive GUI to calibrate the AmazingHand open/close angles and the leader
gripper direction.

Fingers:
  - Drag each finger slider to set the desired pose, then click:
      - "Save Open"   -> records the current angles as hand_open_angles
      - "Save Close"  -> records the current angles as hand_close_angles
      - "Reset"       -> returns every finger to its middle position
  - Each finger slider drives the finger's two servos symmetrically
    (m1 = +angle, m2 = -angle), which matches the AmazingHand parallel mechanism.

Leader gripper direction:
  - With the leader arm connected (--leader_port), hold the gripper fully OPEN
    and click "Capture Open", then hold it fully CLOSED and click "Capture Close".
    The captured normalized gripper values (0-100) are saved as
    `gripper_open_pos` / `gripper_close_pos`.

When both finger poses and both gripper captures are set, everything is
auto-saved to `hand_angles.json` in the robot calibration dir. The robot loads
this file at startup, so no manual config editing is needed.

Usage:
    python -m lerobot.scripts.lerobot_calibrate_amazing_hand \
        --hand_port COM11 --leader_port COM54
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pygame
from rustypot import Scs0009PyController

from lerobot.teleoperators.so_leader.config_so_leader import SOLeaderTeleopConfig
from lerobot.teleoperators.so_leader.so_leader import SO101Leader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# servo id -> (finger, m1/m2)
FINGERS = {
    "index":  (1, 2),
    "middle": (3, 4),
    "ring":   (5, 6),
    "thumb":  (7, 8),
}
FINGER_ORDER = ["index", "middle", "ring", "thumb"]

# Middle positions (degrees) for the 8 servos, in servo-id order 1..8.
MIDDLE_POS = [3.0, 0.0, -5.0, -8.0, -2.0, 5.0, -12.0, 0.0]

ANGLE_MIN, ANGLE_MAX = -144, 144  # scs0009 angle limits

# pygame colors
BG = (30, 30, 30)
SLIDER_BG = (60, 60, 60)
SLIDER_ACTIVE = (60, 200, 60)
HANDLE = (240, 240, 240)
TEXT = (240, 240, 240)
BTN = (80, 80, 80)
BTN_HL = (120, 120, 120)
YELLOW = (220, 200, 40)

ROW_H = 50
SLIDER_X0 = 200
SLIDER_W = 380
TOP_GAP = 60
BTN_H = 32
BTN_W = 130


def val(v):
    if isinstance(v, (list, np.ndarray)):
        return float(v[0]) if len(v) else float(v)
    return float(v)


class FingerSlider:
    """One slider per finger. angle is relative to the finger's middle position."""

    def __init__(self, finger, idx, ctrl, base_y):
        self.finger = finger
        self.idx = idx
        self.ctrl = ctrl
        self.y = base_y + idx * ROW_H
        self.angle = 0.0
        self.dragging = False
        self.font = pygame.font.Font(None, 22)

    def servo_ids(self):
        return list(FINGERS[self.finger])

    def _x_from_angle(self, angle):
        frac = (angle - ANGLE_MIN) / (ANGLE_MAX - ANGLE_MIN)
        return SLIDER_X0 + frac * SLIDER_W

    def _angle_from_x(self, x):
        frac = max(0.0, min(1.0, (x - SLIDER_X0) / SLIDER_W))
        return ANGLE_MIN + frac * (ANGLE_MAX - ANGLE_MIN)

    def write(self):
        # m1 = +angle, m2 = -angle, applied as offsets from each servo's middle position.
        targets = []
        ids = self.servo_ids()
        for sid in ids:
            mid = MIDDLE_POS[sid - 1]
            offset = self.angle if sid == ids[0] else -self.angle
            targets.append(np.deg2rad(mid + offset))
        self.ctrl.sync_write_goal_speed(ids, [5] * len(ids))
        self.ctrl.sync_write_goal_position(ids, targets)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            hx = self._x_from_angle(self.angle)
            if abs(e.pos[0] - hx) <= 12 and abs(e.pos[1] - self.y) <= 10:
                self.dragging = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.angle = round(self._angle_from_x(e.pos[0]))
            self.write()

    def draw(self, surf):
        surf.blit(self.font.render(self.finger, True, TEXT), (12, self.y - 8))
        pygame.draw.rect(surf, SLIDER_BG, (SLIDER_X0, self.y - 4, SLIDER_W, 8))
        mid_x = self._x_from_angle(0.0)
        hx = self._x_from_angle(self.angle)
        lo, hi = sorted((mid_x, hx))
        pygame.draw.rect(surf, SLIDER_ACTIVE, (lo, self.y - 4, hi - lo, 8))
        pygame.draw.circle(surf, HANDLE, (int(hx), self.y), 9)
        surf.blit(self.font.render(f"{self.angle:.0f}°", True, YELLOW), (SLIDER_X0 + SLIDER_W + 16, self.y - 8))


def draw_button(surf, rect, text, font, hover):
    clr = BTN_HL if hover else BTN
    pygame.draw.rect(surf, clr, rect, border_radius=6)
    t = font.render(text, True, TEXT)
    surf.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hand_port", required=True, help="Serial port of the AmazingHand (e.g. COM11)")
    parser.add_argument("--baudrate", type=int, default=1_000_000)
    parser.add_argument(
        "--leader_port",
        type=str,
        default=None,
        help="Serial port of the leader arm (e.g. COM54). Enables gripper-direction calibration "
        "(Capture Open / Capture Close). If omitted, only hand finger angles are calibrated.",
    )
    parser.add_argument(
        "--leader_id",
        type=str,
        default="amazing_hand_leader",
        help="Robot id of the leader arm, used to find its calibration file (default: amazing_hand_leader).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON file to auto-save open/close angles to when both are set (default: "
        "~/.cache/huggingface/lerobot/calibration/robots/so101_amazing_hand/hand_angles.json). "
        "The robot loads this file at startup to override the config defaults.",
    )
    args = parser.parse_args()

    ctrl = Scs0009PyController(serial_port=args.hand_port, baudrate=args.baudrate, timeout=0.5)
    servo_ids = list(range(1, 9))
    ctrl.sync_write_torque_enable(servo_ids, [1] * 8)
    logger.info("AmazingHand torque enabled on %s", args.hand_port)

    # Optional leader arm for gripper-direction calibration.
    leader = None
    if args.leader_port:
        leader_cfg = SOLeaderTeleopConfig(
            port=args.leader_port,
            id=args.leader_id,
            use_degrees=True,
            num_read_retries=2,
        )
        leader = SO101Leader(leader_cfg)
        leader.connect(calibrate=True)
        logger.info("Leader arm connected on %s", args.leader_port)

    pygame.init()
    width = SLIDER_X0 + SLIDER_W + 180
    height = TOP_GAP + len(FINGER_ORDER) * ROW_H + 110
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("AmazingHand open/close calibration")
    font = pygame.font.Font(None, 24)
    small = pygame.font.Font(None, 20)

    sliders = [
        FingerSlider(finger, i, ctrl, TOP_GAP + 20) for i, finger in enumerate(FINGER_ORDER)
    ]

    # buttons
    btn_y = TOP_GAP + len(FINGER_ORDER) * ROW_H + 8
    save_open_btn = pygame.Rect(40, btn_y, BTN_W, BTN_H)
    save_close_btn = pygame.Rect(40 + BTN_W + 10, btn_y, BTN_W, BTN_H)
    reset_btn = pygame.Rect(40 + 2 * (BTN_W + 10), btn_y, BTN_W, BTN_H)
    gripper_btn_y = btn_y + BTN_H + 12
    cap_open_btn = pygame.Rect(40, gripper_btn_y, BTN_W, BTN_H)
    cap_close_btn = pygame.Rect(40 + BTN_W + 10, gripper_btn_y, BTN_W, BTN_H)

    saved_open = None
    saved_close = None
    gripper_open = None
    gripper_close = None
    save_msg = ""
    msg_until = 0
    running = True
    clock = pygame.time.Clock()

    def current_angles():
        """Return the 8 open-angle-style offsets for the current pose."""
        angles = [0.0] * 8
        for slider in sliders:
            id1, id2 = FINGERS[slider.finger]
            angles[id1 - 1] = slider.angle
            angles[id2 - 1] = -slider.angle
        return angles

    def read_gripper_pos() -> float | None:
        """Read the leader gripper normalized position (0-100). Returns None on failure."""
        if leader is None:
            return None
        try:
            action = leader.get_action()
            return float(action["gripper.pos"])
        except Exception:
            return None

    def maybe_autosave() -> Path | None:
        """Write hand_angles.json once all four calibration values are known.

        Returns the saved path if a save happened, else None.
        """
        if saved_open is None or saved_close is None:
            return None
        if leader is not None and (gripper_open is None or gripper_close is None):
            return None
        out = args.output if args.output is not None else (
            Path.home()
            / ".cache"
            / "huggingface"
            / "lerobot"
            / "calibration"
            / "robots"
            / "so101_amazing_hand"
            / "hand_angles.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "hand_open_angles": saved_open,
            "hand_close_angles": saved_close,
        }
        if leader is not None:
            data["gripper_open_pos"] = gripper_open
            data["gripper_close_pos"] = gripper_close
        out.write_text(json.dumps(data, indent=4))
        print(f"AmazingHand calibration auto-saved to {out}")
        return out

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if save_open_btn.collidepoint(e.pos):
                    saved_open = current_angles()
                    save_msg = f"Open saved: {[round(a) for a in saved_open]}"
                    msg_until = pygame.time.get_ticks() + 3000
                elif save_close_btn.collidepoint(e.pos):
                    saved_close = current_angles()
                    save_msg = f"Close saved: {[round(a) for a in saved_close]}"
                    msg_until = pygame.time.get_ticks() + 3000
                elif cap_open_btn.collidepoint(e.pos):
                    val = read_gripper_pos()
                    if val is None:
                        save_msg = "Could not read gripper - is the leader connected?"
                    else:
                        gripper_open = round(val, 1)
                        save_msg = f"Gripper OPEN captured: {gripper_open}"
                    msg_until = pygame.time.get_ticks() + 3000
                elif cap_close_btn.collidepoint(e.pos):
                    val = read_gripper_pos()
                    if val is None:
                        save_msg = "Could not read gripper - is the leader connected?"
                    else:
                        gripper_close = round(val, 1)
                        save_msg = f"Gripper CLOSED captured: {gripper_close}"
                    msg_until = pygame.time.get_ticks() + 3000
                elif reset_btn.collidepoint(e.pos):
                    for s in sliders:
                        s.angle = 0.0
                        s.write()
                saved = maybe_autosave()
                if saved is not None:
                    save_msg = f"AUTO-SAVED to {saved}"
                    msg_until = pygame.time.get_ticks() + 4000
            for s in sliders:
                s.handle_event(e)

        mouse = pygame.mouse.get_pos()
        screen.fill(BG)

        # flashing "saved" confirmation banner
        if save_msg and pygame.time.get_ticks() < msg_until:
            banner = pygame.Surface((width, 34))
            banner.fill((40, 160, 60))
            banner.blit(font.render(save_msg, True, (255, 255, 255)), (16, 6))
            screen.blit(banner, (0, 0))

        # instructions
        instr = (
            "Drag each finger to the fully OPEN pose, click [Save Open]; then to the fully CLOSED pose, click [Save Close]."
            if leader is None
            else "Fingers: [Save Open] at open pose, [Save Close] at closed pose. Then gripper: [Capture Open] while OPEN, [Capture Close] while CLOSED."
        )
        screen.blit(small.render(instr, True, TEXT), (20, 12))

        for s in sliders:
            s.draw(screen)

        draw_button(screen, save_open_btn, "Save Open", font, save_open_btn.collidepoint(mouse))
        draw_button(screen, save_close_btn, "Save Close", font, save_close_btn.collidepoint(mouse))
        draw_button(screen, reset_btn, "Reset", font, reset_btn.collidepoint(mouse))
        if leader is not None:
            draw_button(screen, cap_open_btn, "Capture Open", font, cap_open_btn.collidepoint(mouse))
            draw_button(screen, cap_close_btn, "Capture Close", font, cap_close_btn.collidepoint(mouse))

        y = btn_y + BTN_H + 6
        if saved_open is not None:
            screen.blit(font.render(f"Open saved: {[round(a) for a in saved_open]}", True, YELLOW), (20, y))
            y += 22
        if saved_close is not None:
            screen.blit(font.render(f"Close saved: {[round(a) for a in saved_close]}", True, YELLOW), (20, y))
            y += 22
        if leader is not None:
            live = read_gripper_pos()
            live_txt = f"gripper.pos={live:.1f}" if live is not None else "gripper read failed"
            screen.blit(font.render(f"Leader gripper: {live_txt}", True, YELLOW), (20, y))
            y += 22
            if gripper_open is not None:
                screen.blit(font.render(f"Gripper OPEN captured: {gripper_open}", True, YELLOW), (20, y))
                y += 22
            if gripper_close is not None:
                screen.blit(font.render(f"Gripper CLOSED captured: {gripper_close}", True, YELLOW), (20, y))

        pygame.display.flip()
        clock.tick(60)

    ctrl.sync_write_torque_enable(servo_ids, [0] * 8)
    pygame.quit()
    if leader is not None:
        leader.disconnect()
    logger.info("AmazingHand torque disabled, done.")


if __name__ == "__main__":
    main()
