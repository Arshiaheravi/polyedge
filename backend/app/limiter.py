from slowapi import Limiter
from slowapi.util import get_remote_address

# Singleton rate limiter — imported by main.py (to wire into app.state)
# and by route files (to apply @limiter.limit decorators).
limiter = Limiter(key_func=get_remote_address)
