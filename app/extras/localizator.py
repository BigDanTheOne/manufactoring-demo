import os
import csv
from typing import Any


class Localizator:
    def __init__(self, filepath) -> None:
        self.__filepath = filepath
        if not os.path.exists(self.__filepath):
            raise Exception("Locales file not found!")
        self.__langs: dict = self.__get_lags_keys()
        with open(self.__filepath, encoding="utf-8") as csvfile:
            langs_reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            locales = list(langs_reader)
            lang_keys = [x.lower() for x in locales[0]]
            lang_keys.pop(0)
            for lang_key in lang_keys:
                for locale in locales:
                    self.__langs[lang_key][locale[0]] = locale[
                        lang_keys.index(lang_key) + 1
                    ]

    def __get_lags_keys(self) -> dict:
        with open(self.__filepath, encoding="utf-8") as csvfile:
            langs_reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            locales = list(langs_reader)
            locales[0].pop(0)
            langs = {}
            for lang_key in locales[0]:
                langs[lang_key.lower()] = {}
            return langs

    def get_text(self, key: str, lang: str, *params: Any) -> str:
        lang = lang.lower()
        if key in self.__langs[lang]:
            return str(self.__langs[lang][key]).format(*params)
        else:
            return key
