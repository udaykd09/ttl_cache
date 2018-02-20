import time
import threading


class ExpirationThread(threading.Thread):
    def __init__(self, target=None, name=None, freq=1, args=()):
        self.__target = target
        self.__args = args
        self.exc = None
        super(ExpirationThread, self).__init__(name=name)
        self.frequency = freq*10
        self.stop_req = threading.Event()

    def run(self):
        while not self.stop_req.isSet():
            print("Start cleanup")
            if self.__target:
                self.__target(*self.__args)
            print("Finish cleanup")
            time.sleep(self.frequency)