#!/usr/bin/python           # This is server.py file
import socket   # Import socket module
import numpy as np
import time
from multiprocessing.pool import ThreadPool
import os


def receive(socket):
    msg = ''.encode()   # type: str

    try:
        data = socket.recv(1024)    # type: object
        msg += data
    except:
        pass
    return msg.decode()


def send(socket, msg):
    socket.sendall(msg.encode())


def gameended(boardstate):
    if sum(boardstate[:6]) == 0 or sum(boardstate[7:13]) == 0:
        return True
    return False


def cutofftest(depth):
    """ Function handels the limit of the search depth """

    if depth == 3:
        return True
    return False


def actions(boardstate,player1):
    """ Function handels the check of the legal moves in current state of the Mancala game and return it in a list """
    legalmoves = []

    if player1:
        for i in range(0, 6):
            if boardstate[i] > 0:
                legalmoves.append(i)
    else:
        for i in range(7, 13):
            if boardstate[i] > 0:
                legalmoves.append(i)
    return legalmoves


def result(boardstate, action, player1):
    """ Function handels Mancala game rules that lets the Minmax algorithm to explore diffrent simulated game states
    and pick the best legal move according to evaluation function """

    # Get a virtual copy of current games state to simulate a new move for current player
    boardstate = boardstate.copy()

    # Take the marbles from the chosen hole to move (action)
    marbels = boardstate[action]
    boardstate[action] = 0
    currenthole = action

    # While having marbels in hand move to next hole and place on in each
    while marbels > 0:
        # keep counting to keep track where we are
        currenthole = (currenthole + 1) % len(boardstate)

        # If at the opponents Mancala hole jump over it dont give him my precious marbels and move to next hole
        if player1 and currenthole == 13:
            continue

        elif not player1 and currenthole == 6:
            continue

        # Put a marble in currenthole
        boardstate[currenthole] += 1
        marbels -= 1

    # Check if current player placed his last marbel in a empty hole on his side
    if boardstate[currenthole] == 1 and (player1 and currenthole in range(6) or not player1 and currenthole in range(7,13)):

        # Get the other players opposite hole number
        oppositehole = 12 - currenthole

        # And if there is any marbels in the other players hole for current boardstate
        if boardstate[oppositehole] > 0:
            # Grab the marbels from the opposite hole from the other player
            capturedmarbels = boardstate[oppositehole]
            # Empty the other players hole and current players hole
            boardstate[currenthole] = 0
            boardstate[oppositehole] = 0
            # Place the captured marbels and the last played marble secure in current players Mancala
            if player1:
                boardstate[6] += capturedmarbels + 1
            else:
                boardstate[13] += capturedmarbels + 1

    # Check if current player got a extra turn and landed in there own Mancala
    if player1 and currenthole == 6:
        # Return the current board state and let the player playagain
        return boardstate, True

    if not player1 and currenthole == 13:
        # Return the current board state and let the player playagain
        return boardstate, True

    # Returns current games state and switch player turn current player didnt get a extra turn
    return boardstate, False


def alphabeta(boardstate, alpha, beta, depth, player1):
    """ Function handels the Min & Max Alpha Beta search algorithm using heuristic evaluation function """

    # The base case that handels the terminaltest "reached allowed turns or if any player have no marbels on there side"
    if cutofftest(depth) or gameended(boardstate):
        return evaluate(boardstate), None

    if player1:
        # It is max turn
        value = -np.inf
        for action in actions(boardstate, player1):
            newboardstate, playagain = result(boardstate, action, player1)
            # Did maxi get to play again from the result of last move
            if playagain:
                v = alphabeta(newboardstate, alpha, beta, depth + 1, True)[0]
            # If not its minimizers turn
            else:
                v = alphabeta(newboardstate, alpha, beta, depth + 1, False)[0]
            # Was it a beather move than earlier if sow keep track of it
            if v > value:
                value = v
                bestaction = action+1
            if value >= beta:
                break
            alpha = max(alpha, value)

    else:
        # Is it minimizers turn
        value = np.inf
        for action in actions(boardstate, player1):
            newboardstate, playagain = result(boardstate, action, player1)
            # Did mini get to playagin from the result of last move
            if playagain:
                v = alphabeta(newboardstate, alpha, beta, depth + 1, False)[0]
            # If not its max turn
            else:
                v = alphabeta(newboardstate, alpha, beta, depth + 1, True)[0]
            # Was it a beather move than earlier if sow keep track of it
            if v < value:
                value = v
                bestaction = action+1
            if value <= alpha:
                break
            beta = min(beta, value)

    return value, bestaction


def evaluate(boardstate):
    """ Function handels the Heuristic evaluation of the current state of the Mancala game to guide tha algorithm
     using diffrent game domain tactics that is calculated using weighted linear functions """

    # Nr 1 - Calculate the score differens in players Mancala , Only needed to beat player 3 but most important weight!
    scoreweight = 1             # (1 <=> )
    # Get the amount of marbels in player1 mancala
    playermancala = boardstate[6]
    # Get the amount of marbels in opponents mancala
    opponentmancala = boardstate[13]
    scorediffrens = scoreweight * (playermancala - opponentmancala)

    # Need to use more game domain knowlege to win over 4 and 5 loses every time
    # Player 4 playstyle looks like he steals when he can sow need to take that in to account

    # Nr 2 Check for empty holes on each player side it open ups for stealing but also losing stones
    emptyholesweight = 0.5      # (0.5 <=> 0,7 )
    playeremptyholes = 0
    for i in range(6):
        if boardstate[i] == 0:
            playeremptyholes += 1

    opponentemptyholes = 0
    for i in range(7, 13):
        if boardstate[i] == 0:
            opponentemptyholes += 1

    # Calculate emptyholesdiff higher playeremptyholes value gives positive else negative.
    emptyholesdiff = emptyholesweight * (playeremptyholes - opponentemptyholes)

    # Nr 3 Gain score by stealing should be prioritezed as well importent to prevent get stolen from that move
    stealweight = 0.45  # (0.45 <=> 0.65 )
    playersteal = 0
    # Check amount of empty holes player1 has and where opposit hole that bellongs to opponent is not empty
    for i in range(6):
        if boardstate[i] == 0 and boardstate[12-i] > 0:
            playersteal += 1

    # Check amount of empty holes opponent has where opposit hole bellongs to player1 and is not empty
    opponentsteal = 0
    for i in range(7, 13):
        if boardstate[i] == 0 and boardstate[12-i] > 0:
            # Player1 will feel double as mutch pain "negativ opponentsteal" as opponent if they have same amount
            # of empty hole! I really need to watch my back for 4 and 5 sow i prevent them from stealling from me.
            opponentsteal += 2

    # Calculate scoresteal value higher playersteal gives positive value else negative to "punish" that move
    stealpotential = stealweight * (playersteal - opponentsteal)

    # Nr 4 - Try to starw 4 & 5 have hard to beat them count the amount of stones each player has during game.
    # Give small positive score for more marbels on player1 side then opponent else negative if less marbels.
    # At the end it will be counted also to the players score and during the game it will be less for opponent to play
    # with and gain score. Maybe try later make the weight dynamic during game play if about to lose to tweak more!
    marbelsweight = 0.1  # (0.05 <=> 0.1)
    # Count amount of marbels each plater has on there side
    playermarbels = sum(boardstate[:6])
    opponentmarbels = sum(boardstate[7:13])
    # Calculate the marbel diffrens more marbels on player1 "max" side will give positive value else negative.
    marbelsdiffrens = marbelsweight * (playermarbels-opponentmarbels)
    # Calculate the sum of total evaluation value based on the diffrent mancala game domain tactics
    # using weighted linear functions of current state!
    # "Max" will try get high positive evaluationvalue and "Min" wants as large negativ evaluation value as possible
    evaluationvalue = scorediffrens + stealpotential + emptyholesdiff + marbelsdiffrens

    return evaluationvalue

# VARIABLES
playerName = 'Rickard_Sörlin'
host = '127.0.0.1'
port = 30000  # Reserve a port for your service.
clientsocket = socket.socket()  # Create a socket object
pool = ThreadPool(processes=1)
gameEnd = False
MAX_RESPONSE_TIME = 5

print('The player: ' + playerName + ' starts!')
print("The Mancala server is starting up ")
os.startfile(r"Mancala.exe")

while True:
    try:
        clientsocket.connect((host, port))
        print('The player: ' + playerName + ' connected and ready!')

        os.startfile(r"getA3player.exe")

        break
    except:
        continue

data = []
board_state = []

while not gameEnd:

    async_result = pool.apply_async(receive, (clientsocket,))
    start_time = time.time()
    current_time = 0
    received = 0
    data = []

    while received == 0 and current_time < MAX_RESPONSE_TIME:
        if async_result.ready():
            data = async_result.get()
            received = 1
        current_time = time.time() - start_time

    if received == 0:
        print('No response in ' + str(MAX_RESPONSE_TIME) + ' sec')
        gameEnd = 1

    if data == 'N':
        send(clientsocket, playerName)

    if data == 'E':
        gameEnd = 1

    if len(data) > 1:

        # Read the board and player turn
        boardstate = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        playerturn = int(data[0])
        i = 0
        j = 1
        while i <= 13:
            boardstate[i] = int(data[j]) * 10 + int(data[j + 1])
            i += 1
            j += 2

        evaluationvalue, bestaction = alphabeta(boardstate, -np.inf, np.inf, 0, True)

        print("Moved marbels from hole:", bestaction)
        print("Evaluation value for current action:", evaluationvalue)
        send(clientsocket, str(bestaction))


