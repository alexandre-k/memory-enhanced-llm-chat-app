import logging
import sys
import colorlog

root = logging.getLogger()
root.setLevel(logging.INFO)

# Remove any existing handlers first
for handler in root.handlers[:]:
    root.removeHandler(handler)

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))

# handler = logging.StreamHandler(sys.stdout)
# handler.setFormatter(logging.Formatter(
#     "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
# ))

root.addHandler(handler)

log = logging.getLogger("hackathon-app")
log.setLevel(logging.DEBUG)

log.info("Server started")
log.debug("Config loaded")


# import logging
# logger.addHandler(handler)
# logger.setLevel(logging.DEBUG)
