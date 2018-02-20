import time

class ExpirationThread:
    def __init__(self, frequency=1, start=True):
        # Run every ..
        self.frequency = frequency*10
        self.run_flag = start

    def run(self, func, *args):
        while self.run_flag:
            print("Expiration cleanup start")
            func(*args)
            print("Expiration cleanup finish")
            time.sleep(self.frequency)

    def stop(self):
        self.run_flag = False