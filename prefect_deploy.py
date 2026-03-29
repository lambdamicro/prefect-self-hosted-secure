from prefect import flow as prefect_flow
from prefect.flows import load_flow_from_entrypoint
import os
import sys
from pathlib import Path

ENVIRONMENT = os.getenv("ENVIRONMENT", "NOT_SET")

DEPLOYMENTS = [
    ("jobs/test-env-vars.py:start_test", "start-test-env-vars-flow"),
]

GIT_REPO_URL = "https://github.com/seansss/lambda-tutorials-test.git"

WORK_POOL = "local-pool"
IMAGE = "getting-started-flow:v1"

JOB_VARS = {
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
            # Retrieve from github or directory
            flow_obj = prefect_flow.from_source(
                #source=str(script_dir),
                source=GIT_REPO_URL,
                entrypoint=entrypoint,
            )

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
