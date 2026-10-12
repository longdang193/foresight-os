from dataclasses import dataclass
from enum import StrEnum


class Profile(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    XHIGH = "xhigh"


@dataclass(frozen=True)
class ProfilePreset:
    profile: Profile
    max_agent_steps: int


PRESETS = {
    Profile.LOW: ProfilePreset(Profile.LOW, 3),
    Profile.NORMAL: ProfilePreset(Profile.NORMAL, 5),
    Profile.HIGH: ProfilePreset(Profile.HIGH, 5),
    Profile.XHIGH: ProfilePreset(Profile.XHIGH, 5),
}
