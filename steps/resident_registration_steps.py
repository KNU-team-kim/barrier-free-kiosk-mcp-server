RESIDENT_REGISTRATION_STEP = [
    (
        "registration_number",
        "Step 1, Ask the user to tell their registration number (주민등록번호). Please guide them not to say it aloud, but to enter the number using the keypad below. If provided, confirm."
    ),
    (
        "type",
        """
            Step 2, Ask the user whether they want to issue the entire document or select specific sections. If provided, confirm.
            Do NOT show any category list to the user. Instead, infer the correct category internally based on their response and store exactly one of:
                - SIMPLE(select specific sections)
                - DETAILED(entire document)
        """
    ),
    (
        "number",
        "Step 3, Ask the user to specify the number of copies they want to issue, without giving any formatting instructions. The number of copies must be integer. If provided, confirm."
    )
]