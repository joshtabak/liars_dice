import zmq
import math
import sys
import json
import pdb

class Game:
    def __init__(self):
        self.bidPips = None
        self.bidSize = None
        self.myHand  = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
        self.oppDice = 0
        self.onesOn  = True

    @staticmethod
    def choose(n, k):
        return math.factorial(n) / (math.factorial(k) * math.factorial(n-k))

    def handSize(self):
        size = 0
        #pdb.set_trace()

        for pips in self.myHand.keys():
            size += self.myHand[pips]

        return size

    def totalDice(self):
        return self.handSize() + self.oppDice

    def pMatch(self):
        return (1.0/3.0) if self.onesOn else (1.0/6.0)

    def success(self):
        target = self.bidSize - self.myHand[self.bidPips]

        if self.onesOn:
            target -= self.myHand[1]

        if target <= 0:
            return 1.0

        pSuccess = 0.0

        for i in xrange(target, self.oppDice + 1):
            inc = Game.choose(self.oppDice, i) * self.pMatch() ** i * (1 - self.pMatch()) ** (self.oppDice - i) 
            pSuccess += inc
        
        return pSuccess

    def initialBid(self):
        count = self.myHand[self.mode()]

        if self.onesOn:
            count += self.myHand[1]

        count += int(self.oppDice * self.pMatch())

        return [count, self.mode()]

    def mode(self):
        count = 0
        mode  = 0

        # TODO: handles the hand of all 1s badly
        for i in xrange(2 if self.onesOn else 1, 7):
            if self.myHand[i] >= count:
                count = self.myHand[i]
                mode  = i

        return mode

    def nextBid(self):
        if self.bidPips != 6:
            newSize = self.bidSize
            newPips = self.bidPips + 1
        else:
            newSize = self.bidSize + 1
            if self.onesOn:
                newPips = 2
            else:
                newPips = 1

        return [newSize, newPips]


    def setState(self, res):
        self.myHand = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0}

        if res["history"]:
            self.bidSize = int(res["history"][-1][0])
            self.bidPips = int(res["history"][-1][-1])
        else:
            self.bidSize = None
            self.bidPips = None

        if res["game_complete"]:
            sys.exit("Game over, %s won" % res["winner"])

        self.oppDice = int(res["oppenent_dice_num"])
        self.onesOn = res["ones_valid"]

        for pips in res["dice"]:
            self.myHand[pips] += 1

        if res["winner"] and not len(res["history"]):
            print("Round over, %s wins. Opponent's dice: %s" % (res["winner"], res["opponent_dice"]))
            return -1

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

game = Game()

def handleTurn():
    res = json.loads(socket.recv())

    if 'error' in res:
        print("Error: %s" % res['error'])
        pdb.set_trace()

    print(res)

    if game.setState(res) == -1:
        socket.send('next')
        return

    if game.bidSize != None:
        pSuccess = game.success()
        print(pSuccess)
        if pSuccess < 0.5:
            socket.send("0,0")
        else:
            size, pips = game.nextBid()
            socket.send("%s,%s" % (size, pips))
    else:
        size, pips = game.initialBid()
        socket.send("%s,%s" % (size, pips))


while True:
    handleTurn()
