import re
from typing import Optional, Tuple

NUMBER_RE = re.compile(r"(\d+(?:[.,]\d+)?)([kKкК])?(?![а-яА-Яa-zA-Z])")


def parse_line(line: str) -> Optional[Tuple[float, str]]:
    """"50 такси" / "плов 35" / "1.5к аренда" / "кофе 12,5" -> (amount, note)"""
    match = NUMBER_RE.search(line)
    if not match:
        return None

    raw_amount, suffix = match.groups()
    amount = float(raw_amount.replace(",", "."))
    if suffix and suffix.lower() in ("к", "k"):
        amount *= 1000

    remainder = line[: match.start()] + line[match.end() :]
    note = " ".join(remainder.strip(" \t\n-:,./|").split())
    if not note or amount <= 0:
        return None

    return amount, note


def parse_amount(text: str) -> Optional[float]:
    """"45" / "1.5к" -> число. Заметка не нужна — для редактирования суммы записи."""
    match = NUMBER_RE.search(text)
    if not match:
        return None

    raw_amount, suffix = match.groups()
    amount = float(raw_amount.replace(",", "."))
    if suffix and suffix.lower() in ("к", "k"):
        amount *= 1000

    return amount if amount > 0 else None


def fmt(x: float) -> str:
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", " ")
    s = f"{x:,.2f}".replace(",", " ")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s
