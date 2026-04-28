from rest_framework.throttling import ScopedRateThrottle

class AuthRateThrottle(ScopedRateThrottle):
    scope = "auth"

class UserRateThrottle(ScopedRateThrottle):
    scope = "user"