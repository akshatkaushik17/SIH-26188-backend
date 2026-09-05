import re


# ==========================================================
# MRZ CHECK DIGIT FUNCTION
# ==========================================================

def calculate_check_digit(value):
    """
    Calculate the MRZ check digit.

    MRZ rules:

    0-9 = same numeric value
    A-Z = 10-35
    <   = 0

    Repeating weights:
    7, 3, 1
    """

    weights = [7, 3, 1]

    total = 0

    for i, character in enumerate(value):

        if character.isdigit():

            number = int(character)

        elif character.isalpha():

            number = (
                ord(character.upper())
                - ord("A")
                + 10
            )

        elif character == "<":

            number = 0

        else:

            number = 0

        total += number * weights[i % 3]

    return total % 10


# ==========================================================
# CHECK FIELD
# ==========================================================

def check_field(value, expected_digit):
    """
    Check whether the calculated MRZ check digit
    matches the digit present in the MRZ.
    """

    if not value:
        return False

    if (
        not expected_digit
        or not expected_digit.isdigit()
    ):
        return False

    calculated = calculate_check_digit(value)

    return str(calculated) == str(expected_digit)


# ==========================================================
# NORMALIZE MRZ
# ==========================================================

def normalize_mrz(mrz):
    """
    Clean and normalize MRZ text.
    """

    if not mrz:
        return []

    lines = mrz.splitlines()

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        line = line.replace(
            " ",
            ""
        )

        line = line.upper()

        # Keep only characters normally used in MRZ.
        line = re.sub(
            r"[^A-Z0-9<]",
            "",
            line
        )

        if line:

            cleaned_lines.append(
                line
            )

    return cleaned_lines


# ==========================================================
# EXTRACT NAME FROM MRZ
# ==========================================================

def extract_name_from_mrz(line1):
    """
    Extract surname and given names from passport
    MRZ line 1.

    Standard TD3 example:

    P<INDSURNAME<<GIVEN<NAMES<<<<<<<<<<<<

    Important:

    Position 0 = P
    Position 1 = <
    Position 2-4 = issuing country

    Therefore the actual name starts at position 5
    for a standard MRZ where positions 2-4 are country.

    However, OCR sometimes produces a passport MRZ where
    the country/issuing code is missing or inconsistent.

    We therefore locate the << separator and extract
    the name section more safely.
    """

    if not line1:

        return None


    # ------------------------------------------------------
    # Remove passport document prefix
    # ------------------------------------------------------

    if line1.startswith("P<"):

        name_part = line1[2:]

    else:

        name_part = line1


    # ------------------------------------------------------
    # Find the first << separator
    # ------------------------------------------------------

    parts = name_part.split(
        "<<",
        1
    )


    # ------------------------------------------------------
    # If there is no << separator
    # ------------------------------------------------------

    if len(parts) < 2:

        return None


    surname_part = parts[0]

    given_names_part = parts[1]


    # ------------------------------------------------------
    # Remove possible issuing-country code
    #
    # Standard MRZ:
    #
    # P<INDKUMAR<<RAHUL
    #
    # After P<:
    #
    # INDKUMAR<<RAHUL
    #
    # The first three characters are the country code.
    # ------------------------------------------------------

    if len(surname_part) >= 3:

        surname = surname_part[3:]

    else:

        surname = surname_part


    # ------------------------------------------------------
    # Convert < into spaces
    # ------------------------------------------------------

    surname = surname.replace(
        "<",
        " "
    )

    given_names = given_names_part.replace(
        "<",
        " "
    )


    # ------------------------------------------------------
    # Clean spaces
    # ------------------------------------------------------

    surname = " ".join(
        surname.split()
    )

    given_names = " ".join(
        given_names.split()
    )


    # ------------------------------------------------------
    # Create full name
    # ------------------------------------------------------

    full_name = (
        f"{surname} {given_names}"
    ).strip()


    # ------------------------------------------------------
    # Remove repeated spaces
    # ------------------------------------------------------

    full_name = " ".join(
        full_name.split()
    )


    if not full_name:

        return None


    return full_name


# ==========================================================
# PARSE MRZ
# ==========================================================

def parse_mrz(mrz):
    """
    Parse a standard two-line TD3 passport MRZ.

    Returns:

        name
        passport number
        nationality
        date of birth
        sex
        date of expiry

    Also performs MRZ check-digit validation.
    """

    lines = normalize_mrz(
        mrz
    )


    # ======================================================
    # NO MRZ
    # ======================================================

    if not lines:

        return {

            "mrz_detected": False,

            "valid": False,

            "details":
                "No MRZ detected."
        }


    # ======================================================
    # TWO LINES REQUIRED
    # ======================================================

    if len(lines) < 2:

        return {

            "mrz_detected": True,

            "valid": False,

            "details":
                "MRZ detected, but two MRZ lines "
                "were not available."
        }


    # ------------------------------------------------------
    # Use first two lines
    # ------------------------------------------------------

    line1 = lines[0]

    line2 = lines[1]


    # ======================================================
    # BASIC FORMAT CHECK
    # ======================================================

    if not line1.startswith("P<"):

        return {

            "mrz_detected": True,

            "valid": False,

            "details":
                "First MRZ line does not appear "
                "to be a passport MRZ."
        }


    # ======================================================
    # NAME
    # ======================================================

    name = extract_name_from_mrz(
        line1
    )


    # ======================================================
    # VARIABLES
    # ======================================================

    passport_number = None

    nationality = None

    date_of_birth = None

    sex = None

    date_of_expiry = None


    # ======================================================
    # SECOND MRZ LINE
    #
    # Standard TD3 positions:
    #
    # 0-8   passport number
    # 9     passport number check digit
    #
    # 10-12 nationality
    #
    # 13-18 date of birth
    # 19    DOB check digit
    #
    # 20    sex
    #
    # 21-26 date of expiry
    # 27    expiry check digit
    # ======================================================


    # ======================================================
    # PASSPORT NUMBER
    # ======================================================

    if len(line2) >= 9:

        passport_number = (
            line2[0:9]
            .replace("<", "")
        )

        if passport_number == "":

            passport_number = None


    # ======================================================
    # NATIONALITY
    # ======================================================

    if len(line2) >= 13:

        nationality = line2[10:13]

        if (
            not re.fullmatch(
                r"[A-Z]{3}",
                nationality
            )
        ):

            nationality = None


    # ======================================================
    # DATE OF BIRTH
    # ======================================================

    if len(line2) >= 19:

        dob_raw = line2[13:19]

        if re.fullmatch(
            r"\d{6}",
            dob_raw
        ):

            date_of_birth = dob_raw


    # ======================================================
    # SEX
    # ======================================================

    if len(line2) >= 21:

        sex_value = line2[20]


        if sex_value in ["M", "F"]:

            sex = sex_value

        elif sex_value == "<":

            sex = None


    # ======================================================
    # DATE OF EXPIRY
    # ======================================================

    if len(line2) >= 27:

        expiry_raw = line2[21:27]

        if re.fullmatch(
            r"\d{6}",
            expiry_raw
        ):

            date_of_expiry = expiry_raw


    # ======================================================
    # CHECK PASSPORT NUMBER
    # ======================================================

    passport_number_valid = False


    if len(line2) >= 10:

        passport_field = line2[0:9]

        passport_check_digit = line2[9]


        passport_number_valid = check_field(
            passport_field,
            passport_check_digit
        )


    # ======================================================
    # CHECK DATE OF BIRTH
    # ======================================================

    dob_valid = False


    if len(line2) >= 20:

        dob_field = line2[13:19]

        dob_check_digit = line2[19]


        dob_valid = check_field(
            dob_field,
            dob_check_digit
        )


    # ======================================================
    # CHECK DATE OF EXPIRY
    # ======================================================

    expiry_valid = False


    if len(line2) >= 28:

        expiry_field = line2[21:27]

        expiry_check_digit = line2[27]


        expiry_valid = check_field(
            expiry_field,
            expiry_check_digit
        )


    # ======================================================
    # OVERALL VALIDITY
    # ======================================================

    checks = [

        passport_number_valid,

        dob_valid,

        expiry_valid

    ]


    valid_checks = sum(
        checks
    )


    if valid_checks == 3:

        valid = True

        details = (
            "MRZ format detected and all three "
            "available check digits are valid."
        )

    else:

        valid = False

        details = (
            f"MRZ detected, but "
            f"{3 - valid_checks} "
            "check digit check(s) failed."
        )


    # ======================================================
    # RETURN RESULT
    # ======================================================

    return {

        "mrz_detected": True,

        "valid": valid,

        "name": name,

        "passport_number":
            passport_number,

        "date_of_birth":
            date_of_birth,

        "date_of_expiry":
            date_of_expiry,

        "nationality":
            nationality,

        "sex":
            sex,

        "checks": {

            "passport_number":
                passport_number_valid,

            "date_of_birth":
                dob_valid,

            "date_of_expiry":
                expiry_valid
        },

        "details":
            details
    }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    test_mrz = (
        "P<INDKUMAR<<RAHUL<<<<<<<<<<<<<<<<<<<<\n"
        "P1234567<1IND0204129M3205091<<<<<<<<"
    )


    result = parse_mrz(
        test_mrz
    )


    print()

    print(
        "========== MRZ TEST =========="
    )

    print()


    for key, value in result.items():

        print(
            key,
            ":",
            value
        )


    print()