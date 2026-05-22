from pyqtgraph import DateAxisItem
from datetime import datetime, timezone

class TimeAxisItem(DateAxisItem):
    def tickStrings(self, values, scale, spacing):
        if not values:
            return []
        rng = max(values) - min(values)
        if rng < 1:  # миллисекунды
            return [
                datetime.fromtimestamp(v, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
                for v in values
            ]
        elif rng < 60:
            return [
                datetime.fromtimestamp(v, tz=timezone.utc).strftime("%H:%M:%S")
                for v in values
            ]
        elif rng < 3600:
            return [
                datetime.fromtimestamp(v, tz=timezone.utc).strftime("%M:%S")
                for v in values
            ]
        else:
            return [
                datetime.fromtimestamp(v, tz=timezone.utc).strftime("%H:%M")
                for v in values
            ]
