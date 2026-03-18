from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ParsedMessage:
    seq: int
    timestamp: str              # ISO-8601 "YYYY-MM-DD HH:MM:SS"
    sender: str
    body: str
    is_media: bool = False
    is_voice_note: bool = False
    attached_filename: Optional[str] = None   # e.g. "00000004-AUDIO-....opus"


@dataclass
class ParsedChat:
    filename: str               # source path (file or folder)
    chat_name: str
    platform: str               # 'ios' | 'android' | 'unknown'
    messages: List[ParsedMessage] = field(default_factory=list)
    raw_text: str = ""

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def date_first_msg(self) -> Optional[str]:
        return self.messages[0].timestamp if self.messages else None

    @property
    def date_last_msg(self) -> Optional[str]:
        return self.messages[-1].timestamp if self.messages else None
