import time

def process_job(project_id: str, job_id: str):
    print(f"Processing job {job_id} for project {project_id}...")
    time.sleep(2)  # Simulate processing delay
    print(f"Processing complete!")
