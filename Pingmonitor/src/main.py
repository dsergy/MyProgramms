"""
Application Entry Point
Starts the Ping Monitor application
"""
import sys
import logging
from typing import Optional

from app import PingMonitorApp


def main() -> int:
    """
    Main entry point

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create and initialize application
    app: Optional[PingMonitorApp] = None
    try:
        app = PingMonitorApp()
        app.setup_exception_handler()

        if not app.initialize():
            logging.error("Failed to initialize application")
            return 1

        logging.info("Application initialized successfully")
        app.run()
        return 0

    except Exception as e:
        logging.error(f"Application error: {e}")
        return 1

    finally:
        if app:
            app.cleanup()


if __name__ == "__main__":
    sys.exit(main())
