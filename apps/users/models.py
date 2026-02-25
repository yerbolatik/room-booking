from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(DjangoUserManager["User"]):  # type: ignore[type-arg]
    """
    Extends the default UserManager to validate username uniqueness before
    attempting the INSERT in create_superuser.

    Django's built-in createsuperuser command only validates uniqueness for
    USERNAME_FIELD (email here).  Fields in REQUIRED_FIELDS — including
    username — skip that check, causing a raw IntegrityError on INSERT when a
    duplicate exists.  Raising ValidationError here lets createsuperuser catch
    it and surface a clean CommandError instead of a traceback.
    """

    def create_superuser(
        self,
        username: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: object,
    ) -> "User":
        if self.filter(username=username).exists():
            raise ValidationError(f"A user with username '{username}' already exists.")
        return super().create_superuser(username, email, password, **extra_fields)  # type: ignore[return-value, no-any-return]


class User(AbstractUser):
    """
    Custom user model — extends AbstractUser so we can add fields later
    without a migration headache.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)

    objects = UserManager()  # type: ignore[misc]

    # Use email as the primary identifier for login.
    USERNAME_FIELD = "email"
    # username is still required by Django internals; remove from REQUIRED_FIELDS.
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
