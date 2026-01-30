import argparse, os
import subprocess
from datetime import datetime
import pytz, json
from dotenv import load_dotenv
import utils


parser = argparse.ArgumentParser(prog="Tribes Keyserver", description="Tribes KeyServer")
parser.add_argument("--start-prod", action='store_true')
parser.add_argument("--start-debug", action='store_true')

args = parser.parse_args()
load_dotenv()

  

if args.start_prod is True:
  from waitress import serve
  from server.app import app
  os.environ['MODE'] = 'PROD'
  print(f"Running production server on port {os.environ['PORT']}")
  serve(app, host='0.0.0.0', port=os.environ['PORT'])

if args.start_debug is True:
  os.environ['MODE'] = 'DEBUG'
  if len(os.listdir(utils.get_keyfile_directory())) == 0:
    utils.generate_keys(os.getenv('USERNAME'), os.getenv('EMAIL'), utils.get_keyfile_directory())
  subprocess.call(f"flask --app server.app --debug run --port {os.environ['PORT']}", shell=True)


