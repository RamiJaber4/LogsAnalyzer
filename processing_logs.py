import pandas as pd
import numpy as np
#from cassandra.cluster import Cluster
from time import sleep
import logging
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(), 
        ]
    )
logger= logging.getLogger(__name__)
class Log:
    
    def __init__(self, timestamp, level: str, component: str, response_time : int, msg: str):
        self.timestamp= timestamp
        self.level = level.strip().lower()
        self.component = component.strip().lower()
        self.response_time= int(response_time)
        self.msg= msg
        pass

class LogParser:
    def __init__(self):
        pass
    def interpretLog(self, line: str):
        log_data = line.strip().split(",", 4)
        if len(log_data) < 5:
            return Log("0", "info", "Unknown","0","Empty or invalid log")
        LogObj= Log(log_data[0], log_data[1], log_data[2], log_data[3], log_data[4])
        return LogObj
    
class ComponentManager:
    def __init__(self, comp: str):
        self.component= comp
        self.errors= 0
        self.requests =0 
        self.avg_response = 0.0
        self.total_response = 0
    

class MetricsCalculator:

    def __init__(self):
        self.errors = 0
        self.total_requests = 0
        self.total_response = 0        
        self.response_avg =0

        self.components = {
            "auth": ComponentManager("auth"),
            "payment": ComponentManager("payment"),
            "database": ComponentManager("database"),
            "rate-limiter": ComponentManager("rate-limiter"),
            }
        # self.auth_obj= ComponentManager("auth")
        # self.rate_limiter_obj= ComponentManager("rate-limiter")
        # self.payment_obj= ComponentManager("payment")
        # self.database_obj= ComponentManager("database")

    def reset_metrics_obj(self):
        self.errors=0
        self.total_requests= 0
        self.total_response= 0
        self.response_avg=0
        for comp in self.components.values():
            comp.errors = 0
            comp.requests = 0
            comp.avg_response = 0.0
            comp.total_response = 0
            
    def process_log(self, obj_log: Log):
        logger.info("processing log .. ")

        self.total_response += obj_log.response_time        
        self.total_requests += 1
        if obj_log.level == 'error':
            self.errors += 1

        component = self.components.get(obj_log.component)

        if component is None:
            logger.warning("The component wasn't recognized.")
            return

        component.requests += 1
        component.total_response += obj_log.response_time
        component.avg_response = component.total_response / component.requests

        if obj_log.level == "error":
            component.errors += 1
        
    

