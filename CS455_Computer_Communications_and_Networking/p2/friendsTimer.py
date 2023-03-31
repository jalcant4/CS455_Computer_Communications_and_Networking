import time 

class Timer : 
    def __init__ (self, duration, callback = None) :
        self.start_time = 0
        self.duration = duration
        self.callback = callback
        
    def start(self): 
        self.start_time = time.time()
    
    def stop(self):
        self.start_time = 0

    def is_running(self) :
        return self.start_time != 0

    def timeout(self) :
        flag = self.is_running() and (time.time()-self.start_time) >= self.duration
        if flag and self.callback is not None:
            self.callback()
        return flag 

