from database import DatabaseManager
from processing_logs import LogParser, MetricsCalculator
from queue_manager import log_queue
import asyncio

parser= LogParser()
calc= MetricsCalculator()
db= DatabaseManager()

async def start_work():
    counter =0 
    while True:
        line= await log_queue.get()
        log= parser.interpretLog(line)

        calc.process_log(log)
        counter += 1

        
        if counter >= 5:
            await asyncio.to_thread(db.update_component, calc)
            await asyncio.to_thread(db.update_metric,calc)
            calc.reset_metrics_obj()
            counter =0
        log_queue.task_done()