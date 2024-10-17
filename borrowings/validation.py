from datetime import date


def validate_borrowing(
        borrow_date: date,
        expected_return_date: date,
        error_to_raise: type[Exception]
) -> None:
    if (
            borrow_date
            and expected_return_date
            and expected_return_date < borrow_date
    ):
        raise error_to_raise(
            "Expected return date cannot be earlier than borrow date."
        )
