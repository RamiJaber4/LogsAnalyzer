from processing_logs import MetricsCalculator,  Log, LogParser
from database import DatabaseManager
from queue_manager import log_queue
from fastapi import FastAPI, HTTPException, Body
from dotenv import load_dotenv
import asyncio
from worker import calc
from threading import Thread
from worker import start_work
import logging
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(), 
        ]
    )
logger= logging.getLogger(__name__)
load_dotenv()
app= FastAPI()

@app.get('/')
def welcome():
    return {'msg' : 'welcome'}


parse= LogParser()

dbManager= DatabaseManager()


@app.post('/recieve-log')
async def recieve_logs(log_data: str = Body(..., media_type="text/plain")):
    logger.info("Log recieved ..")

    logs= log_data.strip().split('\n')
    for log in logs:        
        await log_queue.put(log)
    return {
            "count" : len(logs)
            }    


@app.on_event("startup")
async def start_background_worker():
    asyncio.create_task(start_work())

@app.get('/show-stats')
def show_metrics():
    metrics= dbManager.get_metric()
    return {
        "total_requests= " : metrics[0],
        "errors_count= " : metrics[1],
        "avg_response_time= ": metrics[2]
    }

@app.get('/show-comp-stats')
def show_comps():
    result= dbManager.get_components_stats()
    components= []
    for row in result:
        components.append({
            "component: " : row[0],
            "requests": row[1],
            "errors": row[2],
            "avg_response": row[3]
        })
    return {
        "components:": components
    }
@app.post('/reset-metrics')
def reset():
    dbManager.reset_metrics(calc)

    return {
        "status" : "Done"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }