"""Pure GS1 SSCC-18 helpers (no ORM, so they can be tested in isolation)."""

SSCC_LENGTH = 18
PAYLOAD_LENGTH = SSCC_LENGTH - 1  # everything except the check digit
EXTENSION_DIGIT = "0"
MIN_PREFIX_LENGTH = 6
MAX_PREFIX_LENGTH = 12


def is_valid_prefix(prefix: str) -> bool:
    """ASCII digits only (``str.isdigit`` would accept e.g. superscripts)."""
    return (
        prefix.isascii()
        and prefix.isdigit()
        and MIN_PREFIX_LENGTH <= len(prefix) <= MAX_PREFIX_LENGTH
    )


def serial_length(prefix: str) -> int:
    """Digits left for the serial reference: payload - extension digit - prefix."""
    return PAYLOAD_LENGTH - 1 - len(prefix)


def compute_check_digit(payload: str) -> int:
    """GS1 mod-10: weights 3,1,3,... starting from the rightmost payload digit."""
    total = sum(
        int(digit) * (3 if position % 2 == 0 else 1)
        for position, digit in enumerate(reversed(payload))
    )
    return (10 - total % 10) % 10


def build_sscc(extension: str, prefix: str, serial: int) -> str:
    """Return the 18-digit SSCC. Raises ValueError if the parts do not fit."""
    if len(extension) != 1 or not (extension.isascii() and extension.isdigit()):
        raise ValueError("The extension digit must be a single digit.")
    if not is_valid_prefix(prefix):
        raise ValueError("Invalid GS1 company prefix.")
    width = serial_length(prefix)
    if serial < 0 or len(str(serial)) > width:
        raise ValueError(f"The serial reference does not fit in {width} digits.")
    payload = f"{extension}{prefix}{serial:0{width}d}"
    return f"{payload}{compute_check_digit(payload)}"
