def validate_borrowing(
        borrow_date,
        expected_return_date,
        error_to_raise
) -> None:
    if (
            borrow_date
            and expected_return_date
            and expected_return_date < borrow_date
    ):
        raise error_to_raise(
            "Expected return date cannot be earlier than borrow date."
        )
