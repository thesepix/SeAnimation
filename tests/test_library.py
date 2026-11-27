"""Tests für ClipPlayer (Frame-Step), Library (Scan/Repeat-Schutz) und EffectRegistry."""

import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from seanimation.library.clip_player import ClipPlayer
from seanimation.library.library import Library
from seanimation.render.effects import EFFECTS_MVP, EffectRegistry


def _make_video(path: Path, n_frames: int = 30, w: int = 64, h: int = 48, fps: float = 30.0):
    import cv2

    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(n_frames):
        frame = np.full((h, w, 3), (i * 8) % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def _make_image(path: Path, color=(200, 100, 50)):
    from PIL import Image

    Image.new("RGB", (64, 48), color).save(path)


class TestClipPlayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.vid = Path(cls.tmp.name) / "test.mp4"
        cls.img = Path(cls.tmp.name) / "test.png"
        _make_video(cls.vid, n_frames=30)
        _make_image(cls.img)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_frame_index_for_beat(self):
        # 1 Frame pro Beat, Loop über 30 Frames
        self.assertEqual(ClipPlayer.frame_index_for_beat(0, 30, 1), 0)
        self.assertEqual(ClipPlayer.frame_index_for_beat(4, 30, 1), 4)
        self.assertEqual(ClipPlayer.frame_index_for_beat(35, 30, 1), 5)  # Loop
        self.assertEqual(ClipPlayer.frame_index_for_beat(3, 30, 2), 6)   # 2 Frames/Beat

    def test_video_load_and_framestep(self):
        p = ClipPlayer(self.vid, frames_per_beat=1)
        self.assertEqual(p.kind, "video")
        self.assertEqual(p.n_frames, 30)
        f0 = p.get_frame(0)
        self.assertEqual(f0.shape[2], 4)  # RGBA
        f5 = p.get_frame(5)
        self.assertEqual(f5.shape, f0.shape)
        p.close()

    def test_image(self):
        p = ClipPlayer(self.img)
        self.assertEqual(p.kind, "image")
        f = p.get_frame(99)  # Beat-Nummer egal beim Bild
        self.assertEqual(f.shape, (48, 64, 4))


class TestLibrary(unittest.TestCase):
    def test_scan_and_no_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_image(Path(tmp) / "a.png")
            _make_image(Path(tmp) / "b.png")
            _make_video(Path(tmp) / "c.mp4", n_frames=10)
            lib = Library(tmp)
            clips = lib.scan()
            self.assertEqual(len(clips), 3)
            kinds = {c.kind for c in clips}
            self.assertEqual(kinds, {"image", "video"})
            for c in clips:
                self.assertIsNotNone(c.thumbnail)
                self.assertEqual(c.thumbnail.shape[2], 4)
            # kein direkter Repeat (A6)
            first = lib.next_clip()
            second = lib.next_clip()
            self.assertIsNotNone(first)
            self.assertNotEqual(first.path, second.path)
            # kind-Filter
            vids = lib.next_clip("video")
            self.assertEqual(vids.kind, "video")
            # Index-Zugriff
            self.assertEqual(lib.get(0).path, clips[0].path)

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Library(tmp)
            self.assertEqual(lib.scan(), [])
            self.assertIsNone(lib.next_clip())


class TestEffects(unittest.TestCase):
    def test_mvp_effects(self):
        reg = EffectRegistry()
        self.assertEqual(len(reg), 5)
        self.assertEqual(reg.get(0)["id"], "reactive_bg")
        self.assertEqual(reg.get(4)["id"], "sphere_wobble")
        self.assertEqual(reg.get(5)["id"], "reactive_bg")  # wrap
        self.assertEqual(reg.by_id("beat_ring")["kind"], "ring")
        self.assertEqual(len(EFFECTS_MVP), 5)


if __name__ == "__main__":
    unittest.main()
