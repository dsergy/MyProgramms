"""
PingStats model
Handles statistics for ping monitoring
"""
from datetime import datetime
from typing import Optional


class PingStats:
    def __init__(self):
        self.total_pings: int = 0
        self.failed_pings: int = 0
        self.start_time: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None
        self.current_status: str = "Not Running"

    def reset(self) -> None:
        """Reset all statistics to initial values"""
        self.__init__()

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_pings == 0:
            return 0.0
        return ((self.total_pings - self.failed_pings) / self.total_pings) * 100

    @property
    def uptime(self) -> str:
        """Calculate uptime in human readable format"""
        if not self.start_time:
            return "0h 0m"

        delta = datetime.now() - self.start_time
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"
