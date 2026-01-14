import argparse, os

parser = argparse.ArgumentParser(prog="Tribes Keyserver", description="Tribes KeyServer")
parser.add_argument("--start-prod", action='store_true')
parser.add_argument("--start-debug", action='store_true')

args = parser.parse_args()

if args.start_prod is True:
  from waitress import serve
  from server import app
  os.environ['MODE'] = 'PROD'
  print(f"Running production server on port {os.environ['PORT']}")
  serve(app, host='0.0.0.0', port=os.environ['PORT'])

if args.start_debug is True:
  os.environ['MODE'] = 'DEBUG'
  subprocess.call(f"flask --app server --debug run --port {os.environ['PORT']}", shell=True)


