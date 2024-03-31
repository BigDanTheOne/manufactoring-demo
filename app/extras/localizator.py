import csv
from pathlib import Path
from typing import Any, Iterable

LOCALES_KEY = "locale"


class Localizator:
    def __init__(self, filepath: Path, default_lang: str = "ru") -> None:
        self.__filepath = filepath
        self.__default_lang = default_lang.lower()
        if not self.__filepath.exists():
            raise Exception("Locales file not found!")
        self.reload_locales()

    def reload_locales(self) -> None:
        self.__texts, self.__locales = self.__read_locales()

    def available_locales(self) -> tuple[str, ...]:
        return tuple(self.__locales.keys())

    def available_keys(self) -> tuple[str, ...]:
        return tuple(self.__texts.keys())

    def get_text(self, key: str, *args: Any, lang: str | None = None) -> str:
        _lang = lang.lower() if lang else self.__default_lang
        if (
            (locale_id := self.__locales.get(_lang)) is None
            or (text := self.__texts.get(key)) is None
        ):
            return key
        return text[locale_id].format(*args) if args else text[locale_id]

    def __read_locales(self) -> tuple[dict[str, tuple[str, ...]], dict[str, int]]:
        __texts: dict[str, tuple[str, ...]] = {}
        with self.__filepath.open(encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",", quotechar='"')
            for row in csv_reader:
                key, *texts = row
                __texts[key] = tuple(texts)
        if LOCALES_KEY not in __texts:
            raise Exception("Locales names not found.")
        return __texts, self.__available_locales(__texts[LOCALES_KEY])

    def __available_locales(self, locales: Iterable[str]) -> dict[str, int]:
        return {locale.lower(): i for i, locale in enumerate(locales)}
