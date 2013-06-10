import zmq
import math
import sys
import json

name = raw_input("name: ")

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.IDENTITY, name)
socket.connect("tcp://localhost:5555")
socket.send("register")

botId = socket.recv()

if botId == '0':
    sys.exit("Duplicate bot name?")

socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.IDENTITY, botId)
socket.connect("tcp://localhost:5555")
socket.send("start")

while True:
    res = json.loads(socket.recv())
    print res
    if res['game_complete']:
        sys.exit("Game over, %s won" % res["winner"])
    if res['winner']:
      socket.send("next")
      continue

    move = raw_input("your move: ")
    socket.send(move)
