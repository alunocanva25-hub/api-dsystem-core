from enum import Enum


class UserRole(str, Enum):
    master = "MASTER"
    admin = "ADMIN"
    user = "USER"


class SyncDirection(str, Enum):
    desktop_to_api = "DESKTOP_TO_API"
    api_to_mobile = "API_TO_MOBILE"
    mobile_to_api = "MOBILE_TO_API"
    api_to_desktop = "API_TO_DESKTOP"


class SyncStatus(str, Enum):
    success = "SUCCESS"
    warning = "WARNING"
    error = "ERROR"
