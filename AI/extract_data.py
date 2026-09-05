import re

from AI.mrz import parse_mrz


# ==========================================================
# HELPER FUNCTION
# ==========================================================

def clean_text(value):
    """
    Remove unnecessary spaces from extracted text.
    """

    if value is None:
        return None

    return " ".join(value.strip().split())


# ==========================================================
# DATE EXTRACTION
# ==========================================================

def find_date(text, labels):
    """
    Find a date after one of the supplied labels.

    Supports:
    12/04/2002
    12-04-2002
    12.04.2002

    Also supports:
    17 OCT 1988
    23 Dec 2027
    """

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    # ------------------------------------------------------
    # FORMAT 1: Numeric dates
    # Example:
    # Date of Birth: 12/04/2002
    # ------------------------------------------------------

    numeric_pattern = (
        rf"(?:{label_pattern})"
        rf"\s*[:\-]?\s*"
        rf"([0-9]{{1,2}}[-/.][0-9]{{1,2}}[-/.][0-9]{{4}})"
    )

    match = re.search(
        numeric_pattern,
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1).strip()


    # ------------------------------------------------------
    # FORMAT 2: Text month
    #
    # Example:
    # 17 OCT 1988
    # 23 Dec 2027
    # ------------------------------------------------------

    month_pattern = (
        r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
    )

    text_date_pattern = (
        rf"(?:{label_pattern})"
        rf"\s*[:\-]?\s*"
        rf"([0-9]{{1,2}}\s+"
        rf"{month_pattern}"
        rf"\s+[0-9]{{4}})"
    )

    match = re.search(
        text_date_pattern,
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1).strip()


    return None
# ==========================================================
# PASSPORT NUMBER EXTRACTION
# ==========================================================

def find_passport_number(text):
    """
    Find passport/document number from OCR text.

    Examples:
    Passport Number: P1234567
    Passport No: P1234567
    Document Number: P1234567
    Document No: P1234567
    """

    patterns = [

        r"(?:Passport\s*Number|Passport\s*No\.?)"
        r"\s*[:\-]?\s*([A-Z0-9]{6,12})",

        r"(?:Document\s*Number|Document\s*No\.?)"
        r"\s*[:\-]?\s*([A-Z0-9]{6,12})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(1).strip().upper()

    return None

# ==========================================================
# NAME
# ==========================================================

def find_name(text):
    """
    Find the person's name from normal OCR text.

    Examples:

    Name: Rahul Kumar
    Full Name: Rahul Kumar
    Given Names: Rahul Kumar

    Also handles passport-style OCR where
    labels such as "Prenoms" may appear.
    """

    patterns = [

        # ----------------------------------------------
        # Normal format
        # Name: Rahul Kumar
        # ----------------------------------------------

        r"(?:Full\s+Name|Name)"
        r"\s*[:\-]\s*"
        r"([A-Za-z][A-Za-z .'-]{1,50})",


        # ----------------------------------------------
        # Given Names: CALLIE
        # Given Names
        # Prenoms
        # CALLIE
        #
        # This allows the value to appear on the
        # following line.
        # ----------------------------------------------

        r"(?:Given\s+Names|Given\s+Name|Forenames|Prenoms)"
        r"\s*[:\-]?\s*"
        r"(?:\n|\s)+"
        r"([A-Za-z][A-Za-z .'-]{1,50})"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            name = clean_text(
                match.group(1)
            )

            name = name.split("\n")[0].strip()

            # ------------------------------------------
            # Don't return a field label as a name
            # ------------------------------------------

            invalid_names = {
                "name",
                "full name",
                "given name",
                "given names",
                "forenames",
                "prenoms",
                "surname",
                "nationality",
                "sex",
                "passport",
                "passport number"
            }

            if name.lower() in invalid_names:
                continue

            return name


    return None


# ==========================================================
# NATIONALITY
# ==========================================================

def find_nationality(text):
    """
    Extract nationality from the normal OCR text.

    The function first looks for an explicitly labelled
    nationality field.

    Examples:

        Nationality: Indian
        Nationality
        UNITED STATES OF AMERICA

    It also handles passport-style OCR where the label
    and value are on separate lines.
    """

    # --------------------------------------------------
    # 1. Look for nationality on the same line
    # --------------------------------------------------

    same_line_pattern = (
        r"(?:Nationality|Nationality\s*/\s*Nationalité)"
        r"\s*[:\-]\s*"
        r"([A-Za-z][A-Za-z .'-]{1,80})"
    )

    match = re.search(
        same_line_pattern,
        text,
        re.IGNORECASE
    )

    if match:

        value = clean_text(
            match.group(1)
        ).strip()

        if value:
            return value


    # --------------------------------------------------
    # 2. Look for nationality on the next line
    #
    # Example:
    #
    # Nationality
    # UNITED STATES OF AMERICA
    # --------------------------------------------------

    next_line_pattern = (
        r"(?:Nationality|Nationality\s*/\s*Nationalité)"
        r"\s*(?:[:\-])?\s*\n\s*"
        r"([A-Za-z][A-Za-z .'-]{1,80})"
    )

    match = re.search(
        next_line_pattern,
        text,
        re.IGNORECASE
    )

    if match:

        value = clean_text(
            match.group(1)
        ).strip()

        # ----------------------------------------------
        # Don't accidentally return another field label
        # ----------------------------------------------

        invalid_values = {
            "name",
            "surname",
            "given names",
            "given name",
            "prenoms",
            "sex",
            "date of birth",
            "date of issue",
            "date of expiry",
            "passport number",
            "document number",
            "authority"
        }

        if value.lower() not in invalid_values:
            return value


    # --------------------------------------------------
    # 3. Nothing reliable found in normal OCR
    # --------------------------------------------------

    return None

# ==========================================================
# SEX
# ==========================================================

def find_sex(text):
    """
    Find sex/gender from normal OCR text.

    Expected values:

    M = Male
    F = Female
    X = Other/unspecified
    """

    match = re.search(
        r"(?:Sex|Gender)\s*[:\-]?\s*([MFX])\b",
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1).upper()

    return None


# ==========================================================
# MRZ EXTRACTION
# ==========================================================

def find_mrz(text):
    """
    Find probable two-line passport MRZ.

    MRZ lines normally:
    - are long
    - contain '<'
    - contain letters/numbers
    """

    possible_lines = []

    for line in text.splitlines():

        clean_line = line.strip()

        # Remove spaces.
        clean_line = clean_line.replace(
            " ",
            ""
        )

        # Convert to uppercase.
        clean_line = clean_line.upper()

        # Keep only valid MRZ characters.
        clean_line = re.sub(
            r"[^A-Z0-9<]",
            "",
            clean_line
        )

        # Passport MRZ lines are normally
        # around 44 characters long.
        if (
            len(clean_line) >= 30
            and "<" in clean_line
        ):

            possible_lines.append(
                clean_line
            )


    # We need at least two lines.
    if len(possible_lines) < 2:

        return None


    # Look for the first MRZ line.
    first_line_index = None

    for i, line in enumerate(possible_lines):

        if line.startswith("P<"):

            first_line_index = i

            break


    # If a P< line was found,
    # use it as the first line.
    if first_line_index is not None:

        line1 = possible_lines[
            first_line_index
        ]

        remaining_lines = possible_lines[
            first_line_index + 1:
        ]

        if remaining_lines:

            line2 = remaining_lines[0]

            return (
                line1
                + "\n"
                + line2
            )


    # Fallback:
    # use the first two probable MRZ lines.
    return (
        possible_lines[0]
        + "\n"
        + possible_lines[1]
    )


# ==========================================================
# NAME NORMALIZATION
# ==========================================================

def normalize_name(name):
    """
    Normalize a person's name before comparison.

    Example:

    Rahul Kumar

    and

    KUMAR RAHUL

    should be treated as the same name.
    """

    if not name:

        return None

    # Convert to uppercase.
    name = name.upper()

    # Remove non-letter characters.
    name = re.sub(
        r"[^A-Z ]",
        " ",
        name
    )

    # Split into individual words.
    words = name.split()

    # Sort the words.
    #
    # This means:
    #
    # Rahul Kumar
    #
    # becomes:
    #
    # KUMAR RAHUL
    #
    # after sorting.

    words.sort()

    return " ".join(words)


# ==========================================================
# OCR + MRZ CROSS-CHECK
# ==========================================================

def cross_check_fields(
    ocr_name,
    ocr_passport_number,
    ocr_date_of_birth,
    ocr_date_of_expiry,
    ocr_nationality,
    ocr_sex,
    mrz_data
):
    """
    Compare normal OCR information
    with information extracted from MRZ.
    """

    comparisons = {}


    # ======================================================
    # NAME
    # ======================================================

    if (
        ocr_name
        and mrz_data.get("name")
    ):

        comparisons["name"] = (
            normalize_name(ocr_name)
            ==
            normalize_name(
                mrz_data["name"]
            )
        )

    else:

        comparisons["name"] = None


    # ======================================================
    # PASSPORT NUMBER
    # ======================================================

    if (
        ocr_passport_number
        and mrz_data.get("passport_number")
    ):

        comparisons["passport_number"] = (
            ocr_passport_number.upper()
            ==
            mrz_data[
                "passport_number"
            ].upper()
        )

    else:

        comparisons["passport_number"] = None


    # ======================================================
    # DATE OF BIRTH
    # ======================================================

    if (
        ocr_date_of_birth
        and mrz_data.get("date_of_birth")
    ):

        match = re.search(
            r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})",
            ocr_date_of_birth
        )

        if match:

            day = match.group(1).zfill(2)

            month = match.group(2).zfill(2)

            year = match.group(3)

            mrz_date = mrz_data[
                "date_of_birth"
            ]

            comparisons["date_of_birth"] = (
                mrz_date
                ==
                year[-2:]
                + month
                + day
            )

        else:

            comparisons["date_of_birth"] = None

    else:

        comparisons["date_of_birth"] = None


    # ======================================================
    # DATE OF EXPIRY
    # ======================================================

    if (
        ocr_date_of_expiry
        and mrz_data.get("date_of_expiry")
    ):

        match = re.search(
            r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})",
            ocr_date_of_expiry
        )

        if match:

            day = match.group(1).zfill(2)

            month = match.group(2).zfill(2)

            year = match.group(3)

            mrz_date = mrz_data[
                "date_of_expiry"
            ]

            comparisons["date_of_expiry"] = (
                mrz_date
                ==
                year[-2:]
                + month
                + day
            )

        else:

            comparisons["date_of_expiry"] = None

    else:

        comparisons["date_of_expiry"] = None


    # ======================================================
    # NATIONALITY
    # ======================================================

    if (
        ocr_nationality
        and mrz_data.get("nationality")
    ):

        # Normal passport OCR might say:
        #
        # Indian
        #
        # while MRZ uses:
        #
        # IND

        nationality_codes = {

            "INDIAN": "IND",

            "INDIA": "IND",

            "AMERICAN": "USA",

            "UNITED STATES": "USA",

            "BRITISH": "GBR",

            "UNITED KINGDOM": "GBR",

            "CANADIAN": "CAN",

            "AUSTRALIAN": "AUS",

            "FRENCH": "FRA",

            "GERMAN": "DEU",

            "JAPANESE": "JPN",

            "CHINESE": "CHN"
        }


        ocr_value = (
            ocr_nationality
            .strip()
            .upper()
        )

        mrz_value = (
            mrz_data[
                "nationality"
            ]
            .strip()
            .upper()
        )


        # Convert nationality to
        # three-letter MRZ code.
        ocr_value = nationality_codes.get(
            ocr_value,
            ocr_value
        )


        comparisons["nationality"] = (
            ocr_value
            ==
            mrz_value
        )

    else:

        comparisons["nationality"] = None


    # ======================================================
    # SEX
    # ======================================================

    if (
        ocr_sex
        and mrz_data.get("sex")
    ):

        comparisons["sex"] = (
            ocr_sex.upper()
            ==
            mrz_data[
                "sex"
            ].upper()
        )

    else:

        comparisons["sex"] = None


    # ======================================================
    # CALCULATE CROSS-CHECK SCORE
    # ======================================================

    # Remove fields that could not be compared.

    actual_comparisons = [

        value

        for value in comparisons.values()

        if value is not None
    ]


    if actual_comparisons:

        matches = sum(
            actual_comparisons
        )

        total = len(
            actual_comparisons
        )

        match_percentage = (
            matches / total
        ) * 100

    else:

        matches = 0

        total = 0

        match_percentage = 0


    # ======================================================
    # RETURN CROSS-CHECK RESULT
    # ======================================================

    return {

        "fields_checked": total,

        "fields_matching": matches,

        "match_percentage": round(
            match_percentage,
            2
        ),

        "field_results": comparisons
    }


# ==========================================================
# MAIN EXTRACTION FUNCTION
# ==========================================================

def extract_information(text):
    """
    Extract structured passport information
    from OCR text and MRZ.
    """


    # ======================================================
    # NORMAL OCR EXTRACTION
    # ======================================================

    name = find_name(
        text
    )


    passport_number = find_passport_number(
        text
    )


    date_of_birth = find_date(
        text,
        [
            "Date of Birth",
            "DOB",
            "Birth Date"
        ]
    )


    date_of_issue = find_date(
        text,
        [
            "Date of Issue",
            "Issue Date",
            "Date Issued"
        ]
    )


    date_of_expiry = find_date(
        text,
        [
            "Date of Expiry",
            "Expiry Date",
            "Expiration Date",
            "Expires"
        ]
    )


    nationality = find_nationality(
        text
    )


    sex = find_sex(
        text
    )


    # ======================================================
    # MRZ
    # ======================================================

    mrz = find_mrz(
        text
    )


    mrz_validation = parse_mrz(
        mrz
    )


    # ======================================================
    # MRZ FALLBACKS
    # ======================================================

    # If normal OCR failed to find something,
    # use the MRZ value.

    if not passport_number:

        passport_number = (
            mrz_validation.get(
                "passport_number"
            )
        )


    if not date_of_birth:

        date_of_birth = (
            mrz_validation.get(
                "date_of_birth"
            )
        )


    if not date_of_expiry:

        date_of_expiry = (
            mrz_validation.get(
                "date_of_expiry"
            )
        )


    if not nationality:

        nationality = (
            mrz_validation.get(
                "nationality"
            )
        )


    if not sex:

        sex = (
            mrz_validation.get(
                "sex"
            )
        )


    if not name:

        name = (
            mrz_validation.get(
                "name"
            )
        )


    # ======================================================
    # CROSS-CHECK OCR AGAINST MRZ
    # ======================================================

    cross_check = cross_check_fields(

        name,

        passport_number,

        date_of_birth,

        date_of_expiry,

        nationality,

        sex,

        mrz_validation
    )


    # ======================================================
    # FINAL STRUCTURED INFORMATION
    # ======================================================

    information = {

        "name": name,

        "passport_number": passport_number,

        # Kept for compatibility with
        # your previous project code.
        "document_number": passport_number,

        "date_of_birth": date_of_birth,

        "date_of_issue": date_of_issue,

        "date_of_expiry": date_of_expiry,

        "nationality": nationality,

        "sex": sex,

        "mrz": mrz,

        "mrz_validation": mrz_validation,

        "cross_check": cross_check
    }


    return information


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    sample_text = """
    SAMPLE PASSPORT

    Name: Rahul Kumar
    Passport No: P1234567
    Date of Birth: 12/04/2002
    Date of Issue: 10/05/2022
    Date of Expiry: 09/05/2032
    Nationality: Indian
    Sex: M

    P<INDKUMAR<<RAHUL<<<<<<<<<<<<<<<<<<<<
    P1234567<1IND0204129M3205091<<<<<<<<
    """


    result = extract_information(
        sample_text
    )


    print()

    print(
        "========== STRUCTURED PASSPORT INFORMATION =========="
    )

    print()


    for key, value in result.items():

        print(
            key,
            ":",
            value
        )

    print()