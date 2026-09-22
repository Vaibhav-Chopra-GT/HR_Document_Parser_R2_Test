"""
Document Validator - Validates PAN and Aadhaar formats
"""
import re


class PANValidator:
    """
    PAN Card Validator

    Format: AAAAA9999A
    - First 5: Letters (A-Z)
    - Next 4: Digits (0-9)
    - Last 1: Letter (A-Z)
    - 4th character indicates holder type:
      C=Company, P=Person, H=HUF, F=Firm, A=AOP, T=Trust, B=BOI, L=Local Authority, J=AJP, G=Government
    """

    PATTERN = r'^[A-Z]{5}[0-9]{4}[A-Z]$'

    HOLDER_TYPES = {
        'A': 'Association of Persons (AOP)',
        'B': 'Body of Individuals (BOI)',
        'C': 'Company',
        'F': 'Firm',
        'G': 'Government',
        'H': 'Hindu Undivided Family (HUF)',
        'J': 'Artificial Juridical Person',
        'L': 'Local Authority',
        'P': 'Individual/Person',
        'T': 'Trust'
    }

    @classmethod
    def validate(cls, pan: str) -> dict:
        """
        Validate PAN number format

        Args:
            pan: PAN number string

        Returns:
            dict with valid status, formatted PAN, holder type, or error
        """
        if not pan:
            return {"valid": False, "error": "PAN number is required"}

        # Clean and uppercase
        pan = pan.upper().strip().replace(' ', '')

        if len(pan) != 10:
            return {"valid": False, "error": "PAN must be exactly 10 characters"}

        if not re.match(cls.PATTERN, pan):
            return {"valid": False, "error": "Invalid PAN format. Expected: AAAAA9999A"}

        # Get holder type from 4th character
        holder_code = pan[3]
        holder_type = cls.HOLDER_TYPES.get(holder_code, 'Unknown')

        return {
            "valid": True,
            "pan": pan,
            "holder_type": holder_type,
            "holder_code": holder_code
        }

    @classmethod
    def mask(cls, pan: str) -> str:
        """Mask PAN for display (show first 2 and last 2)"""
        if not pan or len(pan) != 10:
            return pan
        return f"{pan[:2]}XXXXXX{pan[-2:]}"


class AadhaarValidator:
    """
    Aadhaar Card Validator

    Format: 12 digits with Verhoeff checksum
    - Cannot start with 0 or 1
    - Last digit is checksum
    """

    # Verhoeff algorithm tables
    MULTIPLICATION_TABLE = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]

    PERMUTATION_TABLE = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
    ]

    @classmethod
    def validate(cls, aadhaar: str) -> dict:
        """
        Validate Aadhaar number format and checksum

        Args:
            aadhaar: Aadhaar number string (may contain spaces/hyphens)

        Returns:
            dict with valid status, masked Aadhaar, or error
        """
        if not aadhaar:
            return {"valid": False, "error": "Aadhaar number is required"}

        # Remove spaces, hyphens, and other non-digits
        aadhaar_clean = re.sub(r'[\s\-]', '', aadhaar)

        if not aadhaar_clean.isdigit():
            return {"valid": False, "error": "Aadhaar must contain only digits"}

        if len(aadhaar_clean) != 12:
            return {"valid": False, "error": "Aadhaar must be exactly 12 digits"}

        # Cannot start with 0 or 1
        if aadhaar_clean[0] in ('0', '1'):
            return {"valid": False, "error": "Aadhaar cannot start with 0 or 1"}

        # Verhoeff checksum validation
        if not cls._verhoeff_check(aadhaar_clean):
            return {"valid": False, "error": "Invalid Aadhaar checksum"}

        # Format with spaces for readability
        formatted = f"{aadhaar_clean[:4]} {aadhaar_clean[4:8]} {aadhaar_clean[8:]}"

        return {
            "valid": True,
            "aadhaar": aadhaar_clean,
            "formatted": formatted,
            "masked": cls.mask(aadhaar_clean)
        }

    @classmethod
    def _verhoeff_check(cls, num: str) -> bool:
        """Verify Verhoeff checksum"""
        c = 0
        for i, digit in enumerate(reversed(num)):
            c = cls.MULTIPLICATION_TABLE[c][
                cls.PERMUTATION_TABLE[i % 8][int(digit)]
            ]
        return c == 0

    @classmethod
    def mask(cls, aadhaar: str) -> str:
        """Mask Aadhaar for display (show only last 4 digits)"""
        aadhaar_clean = re.sub(r'[\s\-]', '', aadhaar)
        if len(aadhaar_clean) != 12:
            return aadhaar
        return f"XXXX XXXX {aadhaar_clean[-4:]}"


# Utility function to validate document image files
def validate_document_image(file_path: str) -> dict:
    """
    Basic validation for document images

    Args:
        file_path: Path to the image file

    Returns:
        dict with valid status and image info
    """
    from PIL import Image
    import os

    try:
        # Check file exists
        if not os.path.exists(file_path):
            return {"valid": False, "error": "File not found"}

        # Check file size (max 5MB)
        size = os.path.getsize(file_path)
        if size > 5 * 1024 * 1024:
            return {"valid": False, "error": "File too large (max 5MB)"}

        # For PDFs, we just check the extension
        if file_path.lower().endswith('.pdf'):
            return {
                "valid": True,
                "format": "PDF",
                "size": size
            }

        # For images, use PIL to validate
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format

            # Check minimum dimensions (document should be readable)
            if width < 200 or height < 200:
                return {"valid": False, "error": "Image too small (min 200x200)"}

            # Check maximum dimensions
            if width > 10000 or height > 10000:
                return {"valid": False, "error": "Image too large (max 10000x10000)"}

            return {
                "valid": True,
                "format": format_name,
                "width": width,
                "height": height,
                "size": size
            }

    except Exception as e:
        return {"valid": False, "error": f"Invalid image file: {str(e)}"}
