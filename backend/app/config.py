from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent
DEFAULT_DB = APP_DIR.parent / "data" / "forecast.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")
TRAINING_OUTPUTS_DIR = Path(
    os.getenv("FORECAST_ARTIFACTS_DIR", PROJECT_ROOT / "model_training" / "outputs")
)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
