from enum import Enum

class ToolType(Enum):
    DETECTORS_CHECK = "detectors_check"
    MINT_CHECK = "mint_check"
    UNPROTECTED_FUNC = "unprotected_func"
    SKIP_SECURITY_CHECKS = "skip_security_checks"