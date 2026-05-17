import websockets
from websockets.asyncio.server import serve
import asyncio

waiting_player = None

class Player:
   def __init__(self, sock):
      self.socket = sock
      self.message = None
      self.opponent = None


async def relay(ws):
   global waiting_player

   p = Player(ws)
   if not waiting_player:
      waiting_player = p
      while waiting_player is p:
         await asyncio.sleep(0.01)
   else:
      p.opponent = waiting_player
      waiting_player.opponent = p
      waiting_player = None

   while True:
      try:
         msg = await ws.recv()
         p.message = msg
      except websockets.ConnectionClosedError:
         p.message = "DC"
      if p.message and p.opponent.message:
         await p.opponent.socket.send(p.message)
         await p.socket.send(p.opponent.message)
         p.message = None
         p.opponent.message = None
      while p.message is not None:
         await asyncio.sleep(0.01)


async def main():
   async with serve(relay, "localhost", 8888):
      await asyncio.get_running_loop().create_future()  # run forever

if __name__ == "__main__":
   asyncio.run(main())
