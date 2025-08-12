import time

MAX_U32 = 0xFFFFFFFF


class Timer:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.overflow_count = 0x00
        self.last_value = 0

    def get_ms_ts(self) -> int:
        current_ms = int((time.perf_counter() - self.start_time) * 1000)

        if current_ms > MAX_U32:
            delta = current_ms - self.last_value
            overflow_cycles = delta // (MAX_U32 + 1)

            self.overflow_count += overflow_cycles
            self.last_value = current_ms % (MAX_U32 + 1)
        else:
            self.last_value = current_ms

        return self.last_value

    def get_full_ts(self) -> tuple:
        return (self.overflow_count, self.last_value)


