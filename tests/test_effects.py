"""Tests for the particle system and camera (pure update logic)."""

from fx.camera import Camera
from fx.particles import ParticleSystem


def test_burst_emits_and_expires() -> None:
    ps = ParticleSystem()
    ps.emit_burst(100.0, 100.0, (255, 0, 0), count=20)
    assert len(ps) == 20
    # Run well past the max life; all particles should be gone.
    for _ in range(120):
        ps.update(1 / 60)
    assert len(ps) == 0


def test_particles_move_under_velocity_and_gravity() -> None:
    ps = ParticleSystem()
    ps.emit_burst(50.0, 50.0, (0, 255, 0), count=1, gravity=1000.0)
    p = ps.particles[0]
    y0 = p.y
    ps.update(0.1)
    assert p.y != y0  # gravity + velocity moved it


def test_confetti_uses_supplied_colors() -> None:
    ps = ParticleSystem()
    palette = ((10, 20, 30), (40, 50, 60))
    ps.emit_confetti(0.0, 0.0, palette, count=30)
    assert len(ps) == 30
    assert all(p.color in palette for p in ps.particles)


def test_camera_trauma_decays_to_zero() -> None:
    cam = Camera()
    cam.shake(1.0)
    assert cam.trauma == 1.0
    assert cam.offset() != (0, 0)
    for _ in range(120):
        cam.update(1 / 60)
    assert cam.trauma == 0.0
    assert cam.offset() == (0, 0)


def test_camera_shake_is_clamped() -> None:
    cam = Camera()
    cam.shake(0.8)
    cam.shake(0.8)
    assert cam.trauma == 1.0  # can't exceed a full shake
