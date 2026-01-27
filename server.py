import argparse, os
import subprocess
from datetime import datetime
import pytz, json
from dotenv import load_dotenv
import garden


parser = argparse.ArgumentParser(prog="Tribes Keyserver", description="Tribes KeyServer")
parser.add_argument("--start-prod", action='store_true')
parser.add_argument("--start-debug", action='store_true')

args = parser.parse_args()
load_dotenv()

key1 = """
-----BEGIN PGP PUBLIC KEY BLOCK-----

xsFNBGipw00BEACpqIEoqbvT3YsUzqOXpWVPgZFT77tOXC8tVm75JbUpJJzzUUcw
dYFoB5fqHDK9Q40aHdKjl2DQutWl5ONRRGQLiqkHcxFYZpqJdphrE6/Sq9+sbP9B
Yoy7P3I822RLG+dtnl56WNdwk29klQpN5Qev4r+UDRZbUxGkSAJdoDbFajbdZyPv
uyGfYBOtu3ze6iuOUeQZwg/sVMvaSuhQVXcfKPPhXspT3n0+EEoA9WABpCxi9jX8
thpKM1INPzgrHZm6evyjL+NO76mGHeda1V1HOMUI4IQgXWT+64rL9/9U0L6MLfeV
1yeaCpatozLBfYs/NKmN9FUBGytunWJdtagriYV4/yIWKOnxmfvur1AzMEmDnFm9
5NBgpoQLYlDCusx2JJIhnlyd/3WGJBIFj6yxbz+bkP10f6GP4pfMXWeLEs0SGr07
v2vpqZTJqdUn03qE84p4p7qHeV+hIO+i5PMqSBnKFH44a0kmTMNNExALhld2wqr8
6wGukP+UtpArBD1h9lxxcY0g/kdq7DxaN+I3MH010gelPSdNEde+0afqbr6vKhCK
MOuMKCthUHxMW4bdO/6QPhYNrMkDOxBrGZCNztzz6t1U6/tz/2Ipza6LG327FqzJ
emvNqvhFTSuOF/DQRgEJnP/+OauHfuDfq0QKGqtyIC+GuvOOjCNButh+6wARAQAB
zRd1c2VyMSA8dXNlcjFAdXNlcjEuY29tPsLBigQTAQgANAUCaKnDTwIbDgQLCQgH
BRUICQoLBRYCAwEAAh4BFiEErjc4YtOWaJVQ5GnZ5twbzChn0lQACgkQ5twbzChn
0lQiXRAAhiWcIh72OnsILYiN5YUA3aihq+G3Vqi79H28z+xqabGeIACfg5sC/v0+
/GLQX3WopOiWtgUp8JEE05yTim7mOyBnptjsri523PzREvypJMpCNLuRl+Kr22J3
jIKnPBYItIVO9Hg6f1AbJq7FhiQsEXUY6Ugqh8m5BXmZ/TYsAS+qu4v5F2dj2W/r
pUenIs0VzgZxL6s89o0cVbmuJCa9yGzfXIMpk5bCOxjWtE6SjqWEVEeApw+gxzeR
5UPc/PrH0ld2I1dU4f+RPfX3/21sUWfsMD9wELO4XCu3VU0U0mUfY62bpeIRG4PL
9MKxEXxuu4iZh0ySXDLqTYRoe9+lKQWFb/GVpCRSO5RiP1nkfZwIm08L5ARvin+h
h36ATUZeW/SS9sDetxDfTj89HIJnk9Gy8SeGA+9GkUCgtPi97SFVqS3pd1eAejht
7nJmFIPfIIcVhH2DmJLTuYU+C6LkrfRNwLvxcCro50P0SxlxeQ0yc3gjAwrLBAWC
4H89I2Fw4vBIHRjVhF0Fr5z7tk7UTcQNHNbVM6pw2PGXu97Vt4MDn6Hg0CE6CvGz
qaw+n/czqa4IzBozaaauh18ZoY+c2gybkPufSD8vlzbKnK2gxEKvxKuRoURHKd7b
lWhl5Du6QuecTgFTpdwhdvw59XPDXV2566uJ1MTC/6LVQ9LKASs=
=vchn
-----END PGP PUBLIC KEY BLOCK-----
"""


key2="""
-----BEGIN PGP PUBLIC KEY BLOCK-----

xsFNBGl11UUBEACu03efkNqm1AeNFBMlzTLhQO6GRp0KPxjW7EfHrESZuEvfo8UH
m16u7L+01zGBtF0Md8yMWH/Bz0GsuN7WGqWnkw5rG6ygUFV9+XTJ5es2j7bNykzI
IScUcIxiDjfpW6WU7PSp9kCZsJCEo4N4Q0WT0osu1myz2RmbSh1q4ymEwI/NTMkh
yBb62nKO+KxDAZXIF+uLZZUPFrUiQ2bqv2mVNAPJUocGAxPvJhxxQDGnHO1wpMiw
9s4SrP6etXyQdyUaHhBO/N1d5E8ao8X2mJkNTTQzzb6uCYgHORsckUJ0RrNA/Tjd
ZnbTJ2cXgrK0IW9mDkcgvG5RUekWfgkGAQ7a9h+9yN/fI0G9EDXuSiWGuolJfR+E
q7Itf/FCYncxtFkqvsX6qNomZJvqU0ktP6yvYTuafYEmbrhqr2tOikYm01R54Jr5
MjPqC9R71z3LM4ula3jK6k5UmOrkB4QZ/ofxjUGIzU/UwEWzyopaTT3deJW5Nnh7
lMgkTTlV2IevkUPPI0Sn3/fQuVLgK0QoaDCt2Cv7nx3Bsd6nXGp5RwkeskupkRbH
2HNIs2fCLOBWpU1wJF3cfM/GXSxxOgH2neJWqBF5lLD/fFFq/moXphGNbExjf4G3
/HLtvbzqj63sTmjbQk5XGJMIIhWuOy8GSWMEeYU0/wWktT+/OCg7pPhOQQARAQAB
zRpnb29kbmUgPGdvb2RuZUB0cmliZXMubHRkPsLBigQTAQgANAUCaXXVRQIbDgQL
CQgHBRUICQoLBRYCAwEAAh4BFiEE1XFWzcVbKZkckufvuucMrdz3zIMACgkQuucM
rdz3zIMWkg//WclU3A1eBvOgPnRzovkrvFH0p7sX84oO7HYG5c729ssLQ6Mharuv
dXNMAiOt63PYysgHkZ6Q1Yt8Gmpt5qQGyKwn62cHh++GWE0TcwWoVSffbORhHh7P
oXMlsZc+lGifzBq6mLojBTyET3RGBu8bIYWJCBSPQq+w8HVicS5mtjKxMrJDTWSy
EqBj4GKPdL3IvJ6c6kHRl2Xo2HWdYz6lwMyIxG4WMi8jp6DE89fUL3O1AZhGW1PS
aSKx/vOxWaoEiysZMWuZcmeedFLVLrD22t8nxc04anbdetaqkqjjDfpvc47GAqmF
A6yCPOAuALae0fodoML69AZdq9/EfQRJjN/Zw5Py/TIXgW6Vx2TtFtyhkFFeiFiW
1nblWfVqvyWpNpycTT2brNABvpp5V/Fl/VmCWs5J9i9UoMA4Crh9u7rkpCyABwUX
8SuJ+0rWR6jBlqBVdnKFvmpamMO87b3ecJYxkGcGHbOUdHH9JF8fVNswTCxptx9i
XrT3PiLtTm5Zu1qC2Vhe2ev4H4AClx5sjuMWMVXuUBxrBgYheswP52nml/6Qh8UM
2TcYSzrYKuBu+FNh35uTmAUa8ojlROwAp/dcaGQ0ENI4Xu14xo3kIUide6z+Q5vW
OZkMOVmrugdORl1FXW9eceY37WU0sAS4/4xT28wF34oj68RGwQcqF4A=
=NL/d
-----END PGP PUBLIC KEY BLOCK-----
"""

pubkey = garden.create_key_from_text(key2)
print(pubkey.fingerprint)
message = garden.encrypt_message("hello", pubkey)
print(json.dumps({
  "message": str(message),
  "to": pubkey.fingerprint,
  "from": "test",
  "createdAt": str(datetime.now(pytz.UTC))
}))
if args.start_prod is True:
  from waitress import serve
  from server.app import app
  os.environ['MODE'] = 'PROD'
  print(f"Running production server on port {os.environ['PORT']}")
  serve(app, host='0.0.0.0', port=os.environ['PORT'])

if args.start_debug is True:
  os.environ['MODE'] = 'DEBUG'
  subprocess.call(f"flask --app server.app --debug run --port {os.environ['PORT']}", shell=True)


