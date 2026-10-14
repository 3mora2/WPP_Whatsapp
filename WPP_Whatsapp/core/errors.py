"""Public errors contain operation metadata, never message bodies or credentials."""


class WPPError(Exception):
    pass


class SessionClosedError(WPPError):
    pass


class SessionNotReadyError(WPPError):
    pass


class SessionTimeoutError(WPPError, TimeoutError):
    pass


class ProfileInUseError(WPPError):
    pass


class EventQueueFullError(WPPError):
    pass


class BridgeError(WPPError):
    def __init__(self, operation, dispatched=True):
        self.operation, self.dispatched = operation, dispatched
        super().__init__(f"Browser operation failed: {operation}")


class RuntimeCompatibilityError(WPPError):
    pass


class DeliveryUncertainError(WPPError):
    def __init__(self, operation_id):
        self.operation_id = operation_id
        super().__init__(f"Delivery requires reconciliation: {operation_id}")


class OperationConflictError(WPPError):
    """An operation ID belongs to a different (or unverifiable legacy) request."""


class OperationQueueFullError(WPPError):
    """Admission was rejected before dispatch; callers may retry the same request."""


class AcknowledgementTimeoutError(WPPError, TimeoutError):
    """Waiting ended without evidence of the requested acknowledgement."""
