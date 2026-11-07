from typing import Final


class DLlamaSrv:
    NAME: Final[str] = "LlamaSrv"
    VERSION: Final[str] = "0.0.0"
    CMDB_TYPE: Final[str] = "application"
    CMDB_SUBTYPE: Final[str] = "Application"
    CMDB_SUPPLIER: Final[str] = "Nadim-Daniel"
    CMDB_CODENAME: Final[str] = "Initial development"
    CMDB_COMPONENTS = ()
    CMDB_DATABASES = ()
    # Declare every owned listener; runtime defaults must use these bindings.
    CMDB_NETWORK: Final[tuple[tuple[str, str, int], ...]] = (
        ("http", "0.0.0.0", 51000),
    )
    BASE_DIR: Final[str] = "/opt/prod/llamasrv"
    LOCALES_DIR: Final[str] = "locales"
