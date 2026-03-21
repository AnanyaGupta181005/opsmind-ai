import os
import time
from celery import Celery
from celery.result import AsyncResult
from fastapi import FastAPI
from pydantic import BaseModel

# -------------------------------------------------------------------------------
# 1. CONFIGURATION
# -------------------------------------------------------------------------------
# Connects to your local Redis server running on port 6379
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# -------------------------------------------------------------------------------
# 2. CELERY SETUP 
# -------------------------------------------------------------------------------
# IMPORTANT: The first argument "report_generator" must match your filename!
celery_app = Celery(
    "report_generator",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    result_expires=3600,
)

# -------------------------------------------------------------------------------
# 3. BACKGROUND TASKS 
# -------------------------------------------------------------------------------
@celery_app.task(bind=True)
def generate_report_task(self, report_type: str):
    """
    Simulates a heavy report generation task.
    """
    print(f"📄 WORKER: Starting {report_type} report generation...")
    
    total_steps = 5
    for i in range(total_steps):
        time.sleep(1)  # Simulate work
        
        # Update progress in Redis
        progress = ((i + 1) / total_steps) * 100
        self.update_state(
            state='PROGRESS',
            meta={
                'current_step': i + 1, 
                'total_steps': total_steps, 
                'percent': f"{progress}%",
                'status': 'Processing data...'
            }
        )
    
    result_message = f"{report_type} Report generated successfully."
    print(f"✅ WORKER: {result_message}")
    
    return {
        "status": "Completed", 
        "download_url": "/downloads/report_final.pdf", 
        "message": result_message
    }

# -------------------------------------------------------------------------------
# 4. FASTAPI SETUP
# -------------------------------------------------------------------------------
app = FastAPI(title="Report Generator System")

class ReportRequest(BaseModel):
    report_type: str = "monthly"

@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    # Send task to Celery
    task = generate_report_task.delay(request.report_type)
    
    return {
        "message": "Report generation started",
        "task_id": task.id,
        "check_status_url": f"/report-status/{task.id}"
    }

@app.get("/report-status/{task_id}")
async def get_report_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "state": task_result.state,
    }

    if task_result.state == 'PENDING':
        response["info"] = "Task is waiting in queue..."
    elif task_result.state == 'PROGRESS':
        response["info"] = task_result.info 
    elif task_result.state == 'SUCCESS':
        response["result"] = task_result.result
    elif task_result.state == 'FAILURE':
        response["error"] = str(task_result.result)

    return response