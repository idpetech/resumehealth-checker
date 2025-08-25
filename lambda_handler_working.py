import json
from mangum import Mangum
from main_working import app

# Create the Lambda handler using the working version
lambda_handler = Mangum(app, lifespan="off")