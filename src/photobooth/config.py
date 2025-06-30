from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"
POSE_LITE  = ASSETS_DIR / "models" / "pose_landmarker_lite.task"
POSE_FULL  = ASSETS_DIR / "models" / "pose_landmarker_full.task"
POSE_HEAVY = ASSETS_DIR / "models" / "pose_landmarker_heavy.task"
OVERLAY    = ASSETS_DIR / "overlays" / "overlay.png"
