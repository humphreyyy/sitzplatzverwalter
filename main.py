"""Main entry point for Sitzplatz-Manager application."""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sitzplatz_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main application entry point.

    Initializes the application, sets up data layer, and starts GUI.
    """
    try:
        logger.info("Starting Sitzplatz-Manager application")

        # Import and run GUI
        from gui.main_window import run_application

        logger.info("Launching Tkinter GUI")
        run_application()

    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
