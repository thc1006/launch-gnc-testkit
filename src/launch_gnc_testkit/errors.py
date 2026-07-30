class GncTestkitError(Exception):
    """Base class for expected testkit errors."""


class ArtifactFormatError(GncTestkitError):
    """An artifact cannot be parsed or violates its structural contract."""


class ManifestValidationError(GncTestkitError):
    """A run manifest is invalid."""


class TraceValidationError(GncTestkitError):
    """A trace is invalid."""
