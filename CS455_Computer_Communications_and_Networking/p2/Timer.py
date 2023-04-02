import time

class Timer:
    # The constructor method initializes the instance variables of the Timer object. 
    # The duration parameter sets the duration of the timer in seconds. 
    # The optional callback parameter sets the function to be executed 
    #   when the timer completes.
    def __init__(self, duration, callback == None):
        self.start_time = 0
        self.duration = duration
        self.callback = callback
    
    # This method starts the timer by setting the start_time instance variable 
    #   to the current time.    
    def start(self):
        self.start_time = time.time()
    
    # This method stops the timer by resetting the start_time instance variable to 0.    
    def stop(self):
        self.start_time = 0
    
    # This method returns True if the timer is currently running 
    #   otherwise it returns False.
    def is_running(self):
        return self.start_time != 0
    
    # This method checks if the timer has completed 
    #   by comparing the current time with the start_time plus the duration. 
    # If the timer has completed and a callback function is provided, 
    #   it executes the function. 
    # The method returns True if the timer has completed and False otherwise.
    def timeout(self):
        flag = self.is_running() and (time.time()-self.start_time) >= self.duration
        if flag and self.callback is not None:
            self.callback()
        return flag    