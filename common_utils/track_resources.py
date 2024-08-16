## For debug and track the compute resouces
import psutil
import time
from functools import wraps # decorator factory
from contextlib import contextmanager
from typing import Callable


def track_usage(_interval: float = 0.5):
    def track_usage_wrapper(
            func: Callable, 
        )-> Callable:    
        """
        ### Decorator
        
        To track the CPU and Memory usage of the function
        

        Args:
            func (Callable): Function to be decorated

        Returns:
            Callable: Function to be decorated
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()        
            whole_cpu = psutil.cpu_percent(interval=_interval, percpu=True)
            print(f"Whole CPU: {whole_cpu}")
            process_id = process.pid
            process_name = process.name()
            before_process_cpu = process.cpu_percent(interval=_interval)
            before_process_memory = process.memory_info().rss / 1024 / 1024 # in MB
            print(f"After Process ID: {process_id}, Process Name: {process_name}, CPU: {before_process_cpu}, Memory: {before_process_memory}MB")
            print(f"Function name: {func.__name__}")
            result = func(*args, **kwargs)
            
            end_time = time.time()
            after_process_cpu = process.cpu_percent(interval=_interval)
            after_process_memory = process.memory_info().rss / 1024 / 1024 # in MB
            whole_cpu = psutil.cpu_percent(interval=_interval, percpu=True)
            print(f"Whole CPU: {whole_cpu}")
            print(f"After Process ID: {process_id}, Process Name: {process_name}, CPU: {after_process_cpu}, Memory: {after_process_memory}MB")
            print(f"Execution time: {end_time - start_time}")
            print(f"Difference in CPU: {after_process_cpu - before_process_cpu}, Difference in Memory: {after_process_memory - before_process_memory}MB")
            
            return result
        
        return wrapper
    
    return track_usage_wrapper


@contextmanager
def track_usage_context(interval: float = 0.5):
    """
    ### Context Manager
    
    To track the CPU and Memory usage of the code block
    
    args:
        interval (float): Interval to check the CPU and Memory usage    

    Yields:
        None: None
    """

    start_time = time.time()
    process = psutil.Process()        
    whole_cpu = psutil.cpu_percent(interval=interval, percpu=True)
    print(f"Whole CPU: {whole_cpu}")
    process_id = process.pid
    process_name = process.name()
    before_process_cpu = process.cpu_percent(interval=interval)
    before_process_memory = int(process.memory_info().rss / 1024 / 1024 )# in MB
    print(f"After Process ID: {process_id}, Process Name: {process_name}, CPU: {before_process_cpu}, Memory: {before_process_memory}MB")
    try:
        yield 
    finally:   
        end_time = time.time()
        after_process_cpu = process.cpu_percent(interval=interval)
        after_process_memory = int(process.memory_info().rss / 1024 / 1024) # in MB
        whole_cpu = psutil.cpu_percent(interval=interval, percpu=True)
        print(f"Whole CPU: {whole_cpu}")
        print(f"After Process ID: {process_id}, Process Name: {process_name}, CPU: {after_process_cpu}, Memory: {after_process_memory}MB")
        print(f"Execution time: {end_time - start_time}")
        print(f"Difference in CPU: {after_process_cpu - before_process_cpu}, Difference in Memory: {after_process_memory - before_process_memory}MB")


@track_usage(_interval=0.5)
def test():
    lst = []
    for i in range(10**8):
        lst.append(i)
        
if __name__ == "__main__":
    # test()
    
    with track_usage_context(interval=0.5):
        lst = []
        for i in range(10**8):
            lst.append(1)    
        
