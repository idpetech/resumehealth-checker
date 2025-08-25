import json
from mangum import Mangum
from main_original_monolith import app

# Create the Lambda handler using the original monolithic version
lambda_handler = Mangum(app, lifespan="off")