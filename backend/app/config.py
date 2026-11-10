from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB = APP_DIR.parent / "data" / "forecast.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")
ARTIFACTS_DIR = Path(os.getenv("FORECAST_ARTIFACTS_DIR", APP_DIR.parent / "artifacts"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
