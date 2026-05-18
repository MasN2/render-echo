#!/usr/bin/env python

import asyncio
import http
import signal
import os

from websockets.asyncio.server import serve

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


async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

def health_check(connection, request):
    if request.path == "/healthz":
        return connection.respond(http.HTTPStatus.OK, "OK\n")


async def main():
    port = int(os.environ["PORT"])
    async with serve(relay, "", port, process_request=health_check) as server:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, server.close)
        await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())

