import time

class Timer:
    # The constructor method initializes the instance variables of the Timer object. 
    # The duration parameter sets the duration of the timer in seconds. 
    # The optional callback parameter sets the function to be executed 
    #   when the timer completes.
    def __init__(self, duration, callback = None):
        self.start_time = None
        self.duration = duration
        self.callback = callback
    
    # This method starts the timer by setting the start_time instance variable 
    #   to the current time.    
    def start(self):
        self.start_time = time.monotonic()
    
    # This method stops the timer by resetting the start_time instance variable to 0.    
    def stop(self):
        self.start_time = None
    
    # This method returns True if the timer is currently running 
    #   otherwise it returns False.
    def is_running(self):
        return self.start_time is not None
     
    # The method returns True if the timer has completed and False otherwise.
    def timeout(self):
        if not self.is_running():
            return False
        
        elapsed_time = time.monotonic() - self.start_time
        if elapsed_time >= self.duration:
            if self.callback:
                self.callback()
            return True
        
        return False  