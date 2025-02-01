import bisect
import threading
import time
from enum import Enum

class State(Enum):
    UNINITIALIZED = 1
    OPERATIONAL = 2
    ERROR = 3
    UNKNOWN = 4

class Actuator:
    def __init__(self):
        self.current_table = [
            (0.081472, 1.28e-05),
            (0.190579, 0.034193),
            (0.212699, 0.086083),
            (0.391338, 0.135331),
            (0.463236, 0.226361),
            (0.509754, 0.329836),
            (0.62785, 0.408606),
            (0.754688, 0.586063),
            (0.895751,0.667683),
            (0.996489,0.942073),
            (1.015761,1.006377),
            (1.197059,1.27169),
            (1.295717,1.451102),
            (1.348538,1.715349),
            (1.480028,2.197349),
            (1.514189,2.463276),
            (1.642176,2.662477),
            (1.791574,3.222105),
            (1.879221,3.252412),
            (1.995949,3.778648),
            (2.065574,4.154079),            
        ]
        self.current_table.sort(key=lambda x: x[0])
        self.currents = [c[0] for c in self.current_table]
        self.positions = [p[1] for p in self.current_table]
        self.max_current = self.currents[-1]
        self._lock = threading.Lock()
        self.state = State.UNINITIALIZED
        self.current = None
        self.shutdown_timer = None                                  

    def prepare(self):
        with self._lock:
            self.current = 0.0
            self.state = State.OPERATIONAL
            if self.shutdown_timer:
                self.shutdown_timer.cancel()                                   

    def set_current(self, current):
        with self._lock:
            if self.state != State.OPERATIONAL:
                return
            if current < 0 or current > self.max_current:
                self.state = State.ERROR
                # Schedule automatic shutdown after 3 seconds
                self.shutdown_timer = threading.Timer(3.0, self.shutdown)
                self.shutdown_timer.start()
            else:
                self.current = current

    def get_position(self):
        with self._lock:
            if self.state != State.OPERATIONAL or self.current is None:
                return None
            current = self.current
        
        index = bisect.bisect_left(self.currents, current)
        if index == 0:
            nearest_index = 0
        elif index == len(self.currents):
            nearest_index = index - 1
        else:
            before = self.currents[index - 1]
            after = self.currents[index]
            if (current - before) <= (after - current):
                nearest_index = index - 1
            else:
                nearest_index = index
        return self.positions[nearest_index]

    def get_state(self):
        with self._lock:
            return self.state

    def shutdown(self):
        with self._lock:
            print("[Control] Attempting shutdown and reinitialization")
            self.current = 0.0

def real_time_monitor(actuator):
    """Continuously monitor position in real-time"""
    while True:
        pos = actuator.get_position()
        state = actuator.get_state()
        if state == State.OPERATIONAL:
            print(f"[Monitor] Current Position: {pos:.6f}")
        elif state == State.ERROR:
            print("[Monitor] Actuator in Error state!")
        time.sleep(0.1)

def control_actuator(actuator):
    """Simulate control commands from another thread"""
    time.sleep(0.5)  # Let monitor start first
    
    # Test case #1
    # currents = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2]
    # Test case #2
    # currents = [0.5, -0.5, 1.0]
    # Test case #3
    currents = [1.2, 0.5, 2.8]

    for current in currents:
        print(f"[Control] Setting current to {current:.2f}")
        actuator.set_current(current)
        time.sleep(0.3)
    
    # Attempt recovery
    print("[Control] Attempting shutdown and reinitialization")
    actuator.shutdown()
    actuator.prepare()

    time.sleep(0.5)

def main():
    actuator = Actuator()
    
    print("Starting actuator...")
    actuator.prepare()
    
    # Start monitoring thread
    monitor_thread = threading.Thread(
        target=real_time_monitor, 
        args=(actuator,),
        daemon=True
    )
    monitor_thread.start()
    
    # Start control thread
    control_thread = threading.Thread(
        target=control_actuator,
        args=(actuator,)
    )
    control_thread.start()
    
    control_thread.join()
    print("\nMain program completed")

if __name__ == "__main__":
    main()