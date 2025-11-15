import enum


class Status(enum.Enum):
    WORKING = "Включён 🟢"
    STOPPED = "Выключён 🔴"


class MediaType(enum.Enum):
    TEXT = "Текст 💬"
    ANIMATION = "Гиф 🖼"
    AUDIO = "Песни 🎵"
    DOCUMENT = "Документ 🗂"
    PHOTO = "Фото 🌄"
    STICKER = "Стикер 🚀"
    VIDEO = "Видео 📹"
    VIDEO_NOTE = "Кружок 📀"
    VOICE = "Голосовое 🎙"

    @staticmethod
    def types():
        media_types = ""
        for i in MediaType._member_map_.values():
            media_types += f"{i.value}\n"
        return media_types

    @staticmethod
    def get_type(content_type: str):
        try:
            return getattr(MediaType, content_type.upper())
        except AttributeError:
            return None

