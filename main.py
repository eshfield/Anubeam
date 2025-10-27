import asyncio
import logging
import sys

from dbus_fast import DBusError
from dbus_fast.aio import MessageBus

from keyboard_controller import KeyboardController

START_TIMEOUT = 10

BUS_NAME = "org.gnome.InputSourceMonitor"
BUS_PATH = "/org/gnome/InputSourceMonitor"

RED = "FF0000"
WHITE = "FFFFFF"
COLORS = {
    "us": WHITE,
    "ru": RED,
}

logger = logging.getLogger("anubeam")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)


async def main():
    keyboard = KeyboardController(logger)
    result = keyboard.connect()
    if not result:
        logger.error("Keyboard connection failure")
        return

    bus = await MessageBus().connect()
    last_source = None

    try:
        for i in range(1, START_TIMEOUT + 1):
            await asyncio.sleep(1)
            try:
                introspection = await bus.introspect(BUS_NAME, BUS_PATH)
            except DBusError:
                logger.info(f"Try #{i}: DBus service is not ready, retrying")
                continue
            break
        else:
            logger.error("DBus service not available, exiting")
            return

        proxy = bus.get_proxy_object(BUS_NAME, BUS_PATH, introspection)
        interface = proxy.get_interface(BUS_NAME)

        def handle_source_change(source):
            nonlocal last_source
            if source != last_source:
                last_source = source
                color = COLORS.get(source)
                if not color:
                    logger.warning(f"Unexpected source: {source}")
                    return
                keyboard.change_color(color)

        interface.on_source_changed(handle_source_change)  # type: ignore

        stop_event = asyncio.Event()
        logger.info("Listening for source changes. Press Ctrl+C to exit")
        await stop_event.wait()
    except Exception as e:
        logger.error(f"DBUS Error: {e}")
    except asyncio.exceptions.CancelledError:
        logger.info("Shutdown requested")
    finally:
        keyboard.close()
        bus.disconnect()
        logger.info("Exit")


if __name__ == "__main__":
    asyncio.run(main())
