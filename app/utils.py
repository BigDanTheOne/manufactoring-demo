import os
import shutil
import subprocess
import config
from datetime import datetime

from aiogram.types import (
    FSInputFile,
    InputMediaDocument,
)
from loaders import bot, mongo_client


def make_db_dump() -> None:
    dump_dir_path = "../storage/dump"
    db_name = mongo_client.get_database().name
    if not os.path.exists(dump_dir_path):
        os.makedirs(dump_dir_path)

    subprocess.run(
        [
            "mongodump",
            f"--db={db_name}",
            f"--out={dump_dir_path}",
            f"--uri={config.MONGODB_CONN}",
        ]
    )


def zip_folder(folder_path: str) -> str:
    db_zip_file_path = f"temp/archive_{datetime.now()}.zip"
    shutil.make_archive(
        db_zip_file_path.replace(".zip", ""), "zip", folder_path
    )
    return db_zip_file_path


async def send_dump(receiver_ids: list[int], zip_file: str) -> None:
    media_group = [
        InputMediaDocument(type="document", media=FSInputFile(path=zip_file))
    ]
    for tg_id in receiver_ids:
        try:
            await bot.send_media_group(chat_id=tg_id, media=media_group)
        except Exception as e:
            print(e)
