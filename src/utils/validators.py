from datetime import date, datetime
from typing import Any

import phonenumbers


def name_validator(value: Any):
    """Для ФИО — только буквы, Title Case."""
    if not isinstance(value, str):
        raise ValueError("Field must be a string")
    value = value.strip()
    for i in value:
        if not i.isalpha() and i != " " and i != "-" and i != "_" and i != "`":
            raise ValueError(f"Invalid character")
    if "  " in value:
        raise ValueError("Field cannot contain consecutive spaces")
    if "--" in value:
        raise ValueError("Field cannot contain consecutive hyphens")
    if "``" in value:
        raise ValueError("Field cannot contain consecutive apostrophes")
    if "__" in value:
        raise ValueError("Field cannot contain consecutive underscores")
    if value.startswith("-"):
        raise ValueError("Field cannot start with a hyphen")
    if value.startswith("`"):
        raise ValueError("Field cannot start with an apostrophe")
    if value.startswith("_"):
        raise ValueError("Field cannot start with an underscore")
    if value.endswith("-"):
        raise ValueError("Field cannot end with a hyphen")
    if value.endswith("`"):
        raise ValueError("Field cannot end with an apostrophe")
    if value.endswith("_"):
        raise ValueError("Field cannot end with an underscore")
    if " -" in value or "- " in value:
        raise ValueError("Space and hyphen cannot be adjacent")
    if " `" in value or "` " in value:
        raise ValueError("Space and apostrophe cannot be adjacent")
    if " _" in value or "_ " in value:
        raise ValueError("Space and underscore cannot be adjacent")

    return value.title()


def generic_name_validator(value: Any):
    """Для названий комнат и др. — буквы, цифры, пробелы, дефисы. Регистр сохраняется."""
    if not isinstance(value, str):
        raise ValueError("Field must be a string")
    value = value.strip()
    for i in value:
        if not i.isalnum() and i != " " and i != "-" and i != "_":
            raise ValueError(f"Invalid character: {i}")
    if "  " in value:
        raise ValueError("Cannot contain consecutive spaces")
    if "--" in value:
        raise ValueError("Cannot contain consecutive hyphens")
    if "__" in value:
        raise ValueError("Cannot contain consecutive underscores")
    if value.startswith("-"):
        raise ValueError("Cannot start with a hyphen")
    if value.startswith("_"):
        raise ValueError("Cannot start with an underscore")
    if value.endswith("-"):
        raise ValueError("Cannot end with a hyphen")
    if value.endswith("_"):
        raise ValueError("Cannot end with an underscore")
    if " -" in value or "- " in value:
        raise ValueError("Space and hyphen cannot be adjacent")
    if " _" in value or "_ " in value:
        raise ValueError("Space and underscore cannot be adjacent")

    # Capitalize first letter only
    if value:
        return value[0].upper() + value[1:]
    return value


def phone_validator(value: Any):
    if not value:
        raise ValueError("phone_number cannot be empty")
    try:
        parsed = phonenumbers.parse(str(value), "RU")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        raise ValueError('Invalid phone')
    except Exception:
        raise ValueError('Invalid phone format')


def date_validator(value: Any):
    if value is None:
        raise ValueError("Date cannot be null")
    if isinstance(value, datetime):
        if value.date() < date.today():
            raise ValueError("Date cannot be in the past")
    elif value < date.today():
        raise ValueError("Date cannot be in the past")
    return value


def time_range_validator(start: datetime, end: datetime):
    if end <= start:
        raise ValueError("End time must be after start time")
    duration = (end - start).total_seconds() / 60
    if duration < 30:
        raise ValueError("Lesson duration must be at least 30 minutes")

    return start, end