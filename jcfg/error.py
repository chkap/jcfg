

class JCfgError(Exception):
    pass


class JCfgInvalidKeyError(JCfgError):
    pass

class JCfgInvalidValueError(JCfgError):
    pass


class JCfgKeyNotFoundError(JCfgError):
    pass
