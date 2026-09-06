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
# DATE NORMALIZATION
# ==========================================================

def normalize_date(value):
    """
    Normalize OCR/French month names into English month names.
    """

    if not value:
        return None

    value = clean_text(value).upper()

    replacements = {

        # January
        "JANVIER": "JANUARY",

        # February
        "FEVRIER": "FEBRUARY",
        "FÉVRIER": "FEBRUARY",

        # March
        "MARS": "MARCH",

        # April
        "AVRIL": "APRIL",

        # May
        "MAI": "MAY",
        "KAI": "MAY",

        # June
        "JUIN": "JUNE",

        # July
        "JUILLET": "JULY",

        # August
        "AOUT": "AUGUST",
        "AOÛT": "AUGUST",

        # September
        "SEPTEMBRE": "SEPTEMBER",

        # October
        "OCTOBRE": "OCTOBER",

        # November
        "NOVEMBRE": "NOVEMBER",

        # December + OCR errors
        "DECEMBRE": "DECEMBER",
        "DÉCEMBRE": "DECEMBER",
        "DECENBRE": "DECEMBER",
        "DECENIBRE": "DECEMBER",
        "DECELBRE": "DECEMBER",
        "DECEYPRE": "DECEMBER"
    }

    for wrong, correct in replacements.items():

        value = value.replace(
            wrong,
            correct
        )


    # Add missing spaces between day, month and year
    value = re.sub(
        r"^([0-9]{1,2})([A-Z]+)([0-9]{4})$",
        r"\1 \2 \3",
        value
    )

    return value

# ==========================================================
# DATE EXTRACTION
# ==========================================================
def find_date(text, labels):
    """
    Extract passport dates from OCR text.

    Handles:
    - 12/04/2002
    - 12-04-2002
    - 12.04.2002
    - 17 OCT 1988
    - 23 Dec 2027
    - 17DECELBRE1992
    - 16 DECENIBRE 1997
    - OCR punctuation/noise in dates
    """

    # ------------------------------------------------------
    # Normalize OCR spacing
    # ------------------------------------------------------

    text = re.sub(r"[ \t]+", " ", text)

    # ------------------------------------------------------
    # Month pattern
    # ------------------------------------------------------

    month_pattern = (
        r"(?:"
        r"JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|"
        r"MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|"
        r"SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|"
        r"DEC(?:EMBER)?|"
        r"JANVIER|F[ÉE]VRIER|MARS|AVRIL|MAI|JUIN|"
        r"JUILLET|AO[ÛU]T|SEPTEMBRE|OCTOBRE|"
        r"NOVEMBRE|D[ÉE]CEMBRE|"
        r"DECELBRE|DECENBRE|DECEMBRE|DECEYPRE|"
        r"DECENIBRE"
        r")"
    )

    # ------------------------------------------------------
    # 1. Explicitly labelled numeric date
    # ------------------------------------------------------

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    match = re.search(
        rf"(?:{label_pattern})"
        rf"\s*[:\-]?\s*"
        rf"([0-9]{{1,2}}[-/.][0-9]{{1,2}}[-/.][0-9]{{4}})",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    # ------------------------------------------------------
    # 2. Explicitly labelled text date
    # ------------------------------------------------------

    match = re.search(
        rf"(?:{label_pattern})"
        rf"\s*[:\-]?\s*"
        rf"([0-9]{{1,2}}\s*{month_pattern}"
        rf"\s*[0-9]{{4}})",
        text,
        re.IGNORECASE
    )

    if match:
        return re.sub(
            r"\s+",
            " ",
            match.group(1).strip()
        )

    # ------------------------------------------------------
    # 3. Find all normal OCR date candidates
    # ------------------------------------------------------

    candidates = []

    # Example:
    # 6 MAI 1962
    # 16 DECENIBRE 1997
    normal_pattern = (
        rf"\b"
        rf"([0-9]{{1,2}}\s*"
        rf"{month_pattern}"
        rf"\s*[0-9]{{4}})"
        rf"\b"
    )

    for match in re.finditer(
        normal_pattern,
        text,
        re.IGNORECASE
    ):
        value = re.sub(
            r"\s+",
            " ",
            match.group(1).strip()
        )

        if value not in candidates:
            candidates.append(value)

    # ------------------------------------------------------
    # 4. OCR date without spaces
    #
    # Example:
    # 17DECELBRE1992
    # ------------------------------------------------------

    compact_pattern = (
        rf"\b"
        rf"([0-9]{{1,2}}{month_pattern}[0-9]{{4}})"
        rf"\b"
    )

    for match in re.finditer(
        compact_pattern,
        text,
        re.IGNORECASE
    ):
        value = match.group(1).strip()

        if value not in candidates:
            candidates.append(value)

    # ------------------------------------------------------
    # 5. OCR date with punctuation/noise
    #
    # Example:
    # 17 DECEYPRE;.4992
    #
    # The OCR may insert punctuation between the
    # month and year.
    # ------------------------------------------------------

    noisy_pattern = (
        rf"\b"
        rf"([0-9]{{1,2}}\s*"
        rf"{month_pattern}"
        rf"[^0-9A-Za-z]{{0,8}}"
        rf"[14][0-9]{{3}})"
        rf"\b"
    )

    for match in re.finditer(
        noisy_pattern,
        text,
        re.IGNORECASE
    ):
        value = match.group(1).strip()

        # Normalize punctuation between month/year
        value = re.sub(
            rf"({month_pattern})[^0-9A-Za-z]+([14][0-9]{{3}})",
            r"\1 \2",
            value,
            flags=re.IGNORECASE
        )

        # OCR commonly reads 1992 as 4992.
        value = re.sub(
            r"\b4(9\d{2})\b",
            r"1\1",
            value
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        ).strip()

        if value not in candidates:
            candidates.append(value)

    # ------------------------------------------------------
    # 6. Split date across OCR lines
    #
    # Example:
    # 16 DECENIBRE
    # 1997
    # ------------------------------------------------------

    split_pattern = (
        rf"\b([0-9]{{1,2}}\s*{month_pattern})"
        rf"\s*\n\s*"
        rf"([0-9]{{4}})\b"
    )

    for match in re.finditer(
        split_pattern,
        text,
        re.IGNORECASE
    ):
        value = f"{match.group(1)} {match.group(2)}"

        value = re.sub(
            r"\s+",
            " ",
            value
        ).strip()

        if value not in candidates:
            candidates.append(value)

    # ------------------------------------------------------
    # 7. Assign based on passport field requested
    # ------------------------------------------------------

    if candidates:

        label_text = " ".join(labels).lower()

        if "birth" in label_text or "dob" in label_text:
            return candidates[0]

        if "issue" in label_text or "issued" in label_text:
            if len(candidates) >= 2:
                return candidates[1]
            return candidates[-1]

        if (
            "expiry" in label_text
            or "expiration" in label_text
            or "expires" in label_text
        ):
            if len(candidates) >= 3:
                return candidates[2]
            return candidates[-1]

        return candidates[0]

    # ------------------------------------------------------
    # 8. Numeric date fallback
    # ------------------------------------------------------

    match = re.search(
        r"\b[0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4}\b",
        text
    )

    if match:
        return match.group(0).strip()

    return None

def find_passport_number(text):
    """
    Find passport/document number from OCR text.
    """

    patterns = [

        r"(?:Passport\s*Number|Passport\s*No\.?|No\.?\s*Passeport)"
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

    # Fallback:
    # Look for a standalone passport-like numeric identifier.
    candidates = re.findall(
        r"\b\d{8,12}\b",
        text
    )

    if candidates:
        return candidates[0]

    return None

# ==========================================================
# NAME
# ==========================================================

def find_name(text):
    """
    Find person's name from normal OCR or passport-style OCR.
    """

    # ------------------------------------------------------
    # 1. Normal labelled name
    # ------------------------------------------------------

    patterns = [
        r"(?:Full\s+Name|Name)\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{1,50})",
        r"(?:Given\s+Names|Given\s+Name|Forenames|Prenoms)"
        r"\s*[:\-]?\s*(?:\n|\s)+"
        r"([A-Za-z][A-Za-z .'-]{1,50})"
    ]

    invalid_names = {
        "name",
        "full name",
        "given name",
        "given names",
        "forenames",
        "prenoms",
        "nationality",
        "sex",
        "passport",
        "passport number",
        "document",
        "document number"
    }

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

            if name.lower() not in invalid_names:
                return name

    # ------------------------------------------------------
    # 2. Passport-style OCR fallback
    #
    # Look for uppercase name words after the
    # passport/document number and before nationality.
    # ------------------------------------------------------

    passport_match = re.search(
        r"\b\d{7,10}\b",
        text
    )

    nationality_match = re.search(
        r"\b(?:HAITIENNE|HAITIEN|INDIAN|INDIEN|"
        r"FRENCH|FRANCAIS|AMERICAN|CANADIAN|BRITISH)\b",
        text,
        re.IGNORECASE
    )

    if passport_match:

        start = passport_match.end()

        if nationality_match and nationality_match.start() > start:
            section = text[start:nationality_match.start()]
        else:
            section = text[start:start + 200]

        # Find uppercase alphabetic words.
        words = re.findall(
            r"\b[A-ZÀ-ÖØ-Ý]{3,}\b",
            section
        )

        excluded = {
            "NO",
            "N0",
            "NOM",
            "NAME",
            "SEX",
            "SEXE",
            "DATE",
            "PORT",
            "PORT-AU-PRINCE",
            "PASSPORT"
        }

        words = [
            word for word in words
            if word.upper() not in excluded
        ]

        if words:
            return " ".join(words[:3])

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
    # 3. Common nationality words without a clear label
    # --------------------------------------------------

    nationality_map = {

        "HAITIEN": "HAITIAN",
        "HAITIENNE": "HAITIAN",

        "INDIAN": "INDIAN",
        "INDIEN": "INDIAN",
        "INDIENNE": "INDIAN",

        "FRENCH": "FRENCH",
        "FRANCAIS": "FRENCH",
        "FRANÇAISE": "FRENCH",

        "AMERICAN": "AMERICAN",
        "CANADIAN": "CANADIAN",

        "BRITISH": "BRITISH"
    }

    text_upper = text.upper()

    for keyword, nationality in nationality_map.items():

        if keyword in text_upper:
            return nationality


    return None

# ==========================================================
# SEX
# ==========================================================


def find_sex(text):
    """
    Find sex/gender from normal OCR text.

    Supports:
    Sex: M
    Sex: F
    Gender: M
    FEMININ
    FEMININE
    FEMALE
    MASCULIN
    MASCULINE
    MALE
    """

    text_upper = text.upper()

    # Explicit labelled M/F/X
    match = re.search(
        r"(?:SEX|GENDER|SEXE)\s*[:\-]?\s*([MFX])\b",
        text_upper
    )

    if match:
        return match.group(1)

    # Female variants
    if re.search(
        r"\b(FEMININ|FEMININE|FEMALE)\b",
        text_upper
    ):
        return "F"

    # Male variants
    if re.search(
        r"\b(MASCULIN|MASCULINE|MALE)\b",
        text_upper
    ):
        return "M"

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
# ======================================================
    # NORMALIZE COMMON OCR DATE ERRORS
    # ======================================================

    date_text = re.sub(
        r"([A-Za-z]+)[;,.]+([0-9]{4})",
        r"\1 \2",
        text
    )

    date_text = re.sub(
        r"\b([A-Za-z]+)\s+4([0-9]{3})\b",
        r"\1 1\2",
        date_text
    )


    # ======================================================
    # FIND ALL DATES
    # ======================================================

    date_matches = re.findall(
        r"\b[0-9]{1,2}\s*(?:"
        r"JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|"
        r"MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|"
        r"SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?|"
        r"JANVIER|F[ÉE]VRIER|MARS|AVRIL|MAI|JUIN|"
        r"JUILLET|AO[ÛU]T|SEPTEMBRE|OCTOBRE|"
        r"NOVEMBRE|D[ÉE]CEMBRE|"
        r"KAI|DECELBRE|DECENBRE|DECENIBRE|DECEMBRE|DECEYPRE"
        r")\s*[0-9]{4}\b",
        date_text,
        re.IGNORECASE
    )


    # ======================================================
    # ASSIGN DATES
    # ======================================================
    if len(date_matches) >= 3:

        date_of_birth = date_matches[0].strip()

        date_of_issue = date_matches[1].strip()

        date_of_expiry = date_matches[2].strip()

    else:

        date_of_birth = find_date(
        date_text,
        [
            "Date of Birth",
            "DOB",
            "Birth Date"
        ]
    )

    date_of_issue = find_date(
        date_text,
        [
            "Date of Issue",
            "Issue Date",
            "Date Issued"
        ]
    )

    date_of_expiry = find_date(
        date_text,
        [
            "Date of Expiry",
            "Expiry Date",
            "Expiration Date",
            "Expires"
        ]
    )


    # ======================================================
    # NORMALIZE EXTRACTED DATES
    # ======================================================

    date_of_birth = normalize_date(
        date_of_birth
    )

    date_of_issue = normalize_date(
        date_of_issue
    )

    date_of_expiry = normalize_date(
        date_of_expiry
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
