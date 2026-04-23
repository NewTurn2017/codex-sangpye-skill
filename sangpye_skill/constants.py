"""Constants extracted from the original app/config.py.

Only the ones used by vendored Pillow/Pydantic modules are kept. Server/queue
constants (REDIS_URL, HOST, PORT, JOB_TTL_SECONDS) are intentionally dropped.
"""
IMAGE_SIZE = 1080
SECTION_COUNT = 13
MAX_UPLOAD_IMAGES = 14
