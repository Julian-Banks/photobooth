from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"
POSE_LITE = ASSETS_DIR / "models" / "pose_landmarker_lite.task"
POSE_FULL = ASSETS_DIR / "models" / "pose_landmarker_full.task"
POSE_HEAVY = ASSETS_DIR / "models" / "pose_landmarker_heavy.task"
ASSET1 = ASSETS_DIR / "overlays" / "asset1.png"
ASSET = ASSETS_DIR / "overlays" / "asset.png"
BACKGROUND = ASSETS_DIR / "backgrounds"
OVERLAY = ASSETS_DIR / "overlays"
PATH_TO_SAVED_IMAGE = ROOT / "src" / "web" / "static" / "image.jpg"
PATH_TO_SAVED_IMAGE_LOAD = ROOT / "src" / "web" / "static" / "image2.jpg"
