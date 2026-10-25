"""Account use cases: registering and authenticating users."""

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from dealership.models import AppUser, Customer, Party, Person


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_is_registered(email: str) -> bool:
    return AppUser.objects.filter(email__iexact=normalize_email(email)).exists()


@transaction.atomic
def register_user(*, first_name: str, last_name: str, email: str, password: str) -> AppUser:
    """
    Create the person's party, their customer role and a login account.

    Everyone who registers can buy cars, so they become a customer. Staff
    roles are granted separately per dealership.
    """
    email = normalize_email(email)
    if email_is_registered(email):
        raise EmailAlreadyRegistered

    first_name, last_name = first_name.strip(), last_name.strip()
    party = Party.objects.create(
        party_type=Party.Type.PERSON,
        display_name=f"{first_name} {last_name}",
        email=email,
    )
    person = Person.objects.create(party=party, given_name=first_name, family_name=last_name)
    Customer.objects.create(party=party)

    user = AppUser(person=person, email=email)
    user.set_password(password)
    try:
        with transaction.atomic():
            user.save(force_insert=True)
    except IntegrityError as exc:  # Lost a race with a concurrent registration.
        raise EmailAlreadyRegistered from exc
    return user


def authenticate_user(*, email: str, password: str) -> AppUser:
    user = AppUser.objects.filter(email__iexact=normalize_email(email)).first()
    if user is None:
        make_password(password)  # Spend the same time as a real check so emails cannot be probed.
        raise InvalidCredentials
    if not user.check_password(password) or not user.is_active:
        raise InvalidCredentials
    return user
