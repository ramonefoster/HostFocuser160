from src.core.log import init_logging
from src.core.app import App
from threading import Thread

if __name__ == "__main__":
    logger = init_logging()
    control = App(logger)
    run_thread = Thread(target = control.run)
    run_thread.start()

