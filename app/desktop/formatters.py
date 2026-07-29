from datetime import datetime
from pathlib import Path


def format_phone(value: str) -> str:
    number = value.split("@", 1)[0]
    digits = "".join(character for character in number if character.isdigit())
    if len(digits) == 13 and digits.startswith("55"):
        return f"+55 {digits[2:4]} {digits[4:9]}-{digits[9:]}"
    if len(digits) == 12 and digits.startswith("55"):
        return f"+55 {digits[2:4]} {digits[4:8]}-{digits[8:]}"
    if digits:
        return f"+{digits}" if digits.startswith("55") else digits
    return value or "-"


def format_datetime(value: str) -> str:
    if not value:
        return "-"

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value

    return parsed.strftime("%d/%m/%Y %H:%M")


def media_kind_from_name(file_name: str, origin: str = "") -> str:
    suffix = Path(file_name).suffix.lower()
    if origin.lower() == "youtube":
        return "YouTube"
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return "Imagem"
    if suffix in {".mp3", ".ogg", ".wav", ".m4a", ".aac", ".opus"}:
        return "Audio"
    if suffix in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
        return "Video"
    if suffix in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}:
        return "Documento"
    return "Arquivo"


def initials_from_sender(sender: str) -> str:
    formatted = format_phone(sender)
    digits = "".join(character for character in formatted if character.isdigit())
    if len(digits) >= 2:
        return digits[-2:]
    return "YK"
