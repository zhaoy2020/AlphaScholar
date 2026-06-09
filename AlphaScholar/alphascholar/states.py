import reflex as rx 


class AuthState(rx.State):
    """The app state."""

    # Whether the user is authenticated.
    is_authenticated: bool = False

    def login(self):
        """Log the user in."""
        self.is_authenticated = True

    def logout(self):
        """Log the user out."""
        self.is_authenticated = False