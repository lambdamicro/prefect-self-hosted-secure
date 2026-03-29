from prefect import flow as prefect_flow
from prefect.flows import load_flow_from_entrypoint
import os
import sys
from pathlib import Path

ENVIRONMENT = os.getenv("ENVIRONMENT", "NOT_SET")

DEPLOYMENTS = [
    # ("jobs/test-env-vars.py:start_test", "start-test-env-vars-flow"),
    ("jobs/test-env-vars.py:start_test", "start-test-env-vars-flow"),
]

GIT_REPO_URL = "https://github.com/seansss/lambda-tutorials-test.git"

WORK_POOL = "docker-pool-lambda"
IMAGE = "getting-started-flow:lambda"

JOB_VARS = {
    #"extra_hosts": {"host.docker.internal": "host-gateway"},
    "image_pull_policy": "Never",
    "env": {
        "ENVIRONMENT": ENVIRONMENT,
    },  # or your network approach
    "stream_output": True,
    "auto_remove": False,
}

if __name__ == "__main__":
    # Ensure we're in the correct directory (backend directory)
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    for entrypoint, name in DEPLOYMENTS:
        try:
            print(f"Loading flow from entrypoint: {entrypoint}")
            # Use from_source for proper deployment with source location
            #flow_obj = prefect_flow.from_source(
            #    source=str(script_dir),
            #    entrypoint=entrypoint,
            #)
            
            flow_obj = prefect_flow.from_source(
                source=GIT_REPO_URL,
                entrypoint=entrypoint,
            )

            if flow_obj is None:
                print(f"ERROR: Failed to load flow from {entrypoint}")
                continue
                
            print(f"Deploying {entrypoint} as '{name}'...")
            flow_obj.deploy(
                name=name,
                work_pool_name=WORK_POOL,
                image=IMAGE,
                build=False,
                push=False,
                job_variables=JOB_VARS,
            )
            print(f"Successfully deployed {entrypoint} as '{name}'")
        except Exception as e:
            print(f"ERROR: Failed to deploy {entrypoint} as '{name}': {e}")
            import traceback
            traceback.print_exc()
            # Continue with next deployment instead of exiting
            continue
