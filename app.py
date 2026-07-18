from app import App
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES
from typing import Any, Callable, Coroutine

import ubinascii
import network
import espnow
import asyncio
import time

PEER_MAC = "64e83371f428"

class PancakeOrderApp(App):
  baconText: str
  cheeseText: str
  baconAndCheeseText: str
  plainText: str
  comms: Comms
  color: int = 0
  textColor: int = 1
  hasSent: bool = False
  
  def __init__(self):
    self.button_states = Buttons(self)
    self.comms = Comms()

  def update(self, delta):
      if not self.hasSent:
        if self.button_states.get(BUTTON_TYPES["UP"]):
            send_task = self.comms.send(
                message="bacon",
                mac=PEER_MAC,
            )
            self.baconText = "bacon"
            asyncio.create_task(send_task)
            self.hasSent = True
        elif self.button_states.get(BUTTON_TYPES["CONFIRM"]):
            send_task = self.comms.send(
                message="cheese",
                mac=PEER_MAC,
            )
            self.baconText = "cheese"
            asyncio.create_task(send_task)
            self.hasSent = True
        elif self.button_states.get(BUTTON_TYPES["RIGHT"]):
            send_task = self.comms.send(
                message="bandc",
                mac=PEER_MAC,
            )
            self.baconText = "bacon & cheese"
            asyncio.create_task(send_task)
            self.hasSent = True
        elif self.button_states.get(BUTTON_TYPES["DOWN"]):
            send_task = self.comms.send(
                message="plain",
                mac=PEER_MAC,
            )
            self.baconText = "plain"
            asyncio.create_task(send_task)
            self.hasSent = True
        if not self.hasSent:
            self.baconText = "A for bacon"
            self.cheeseText = "B for bcn&chs"
            self.baconAndCheeseText = "C for cheese"
            self.plainText = "D for plain" 
      else:
          self.baconAndCheeseText = "orders"
          self.cheeseText = "No double"
          self.plainText = "allowed"
          self.baconText = "Order sent."

         
  def draw(self, ctx):
    clear_background(ctx)
    ctx.text_align = ctx.LEFT
    ctx.text_baseline = ctx.TOP
    ctx.move_to(-100, -50).gray(1).text(self.baconText)
    ctx.move_to(-100, -25).gray(1).text(self.cheeseText)
    ctx.move_to(-100, 0).gray(1).text(self.baconAndCheeseText)
    ctx.move_to(-100, 25).gray(1).text(self.plainText)
    

__app_export__ = PancakeOrderApp

class Comms:
    def __init__(self):
        # A WLAN interface must be active to send()/recv()
        self.sta = wifi_reset()  # Reset wifi to AP off, STA on and disconnected

        self.e = espnow.ESPNow()
        self.e.active(True)

    def reset(self) -> None:
        self.__init__()

    def get_mac(self) -> str:
        wlan_sta = network.WLAN(network.STA_IF)
        wlan_sta.active(True)

        wlan_mac = wlan_sta.config("mac")
        mac_str = ubinascii.hexlify(wlan_mac).decode()
        print(f"MAC address: {mac_str}")
        return mac_str

    async def advertise(self):
        print("Advertising")

    async def scan(self):
        print("Scanning")

    async def send(
        self,
        message: str,
        mac: str | bytes | None = None,  # Send to broadcast by default
    ):
        peer_mac: bytes = b""

        if mac is None:
            peer_mac = b"\xFF\xFF\xFF\xFF\xFF\xFF"
        else:
            if isinstance(mac, str):
                peer_mac = bytes.fromhex(mac)
            else:
                peer_mac = mac

        try:
            self.e.add_peer(peer_mac)  # Must add_peer() before send()
            print("Peer added")
        except OSError as e:
            if "ESP_ERR_ESPNOW_EXIST" in str(e):
                print("Peer already added")
                raise e
            else:
                raise e

        print(f"Sending to {peer_mac}")
        try:
            self.e.send(peer_mac, message)
            self.e.send(peer_mac, b"end")
        except OSError as e:
            if "ETIMEDOUT" in str(e):
                print("Timeout")

        print("Sent message")

    async def receive(self, on_receive: Callable[[bytes, str], None]):
        while True:
            host, msg = self.e.recv()
            if msg:  # msg == None if timeout in recv()
                # convert message to string
                msg_str = msg.decode()
                # print(host, msg_str)
                if msg == b"end":
                    break
                on_receive(host, msg_str)

def wifi_reset():  # Reset wifi to AP_IF off, STA_IF on and disconnected
    sta = network.WLAN(network.STA_IF)
    sta.active(False)
    # ap = network.WLAN(network.AP_IF)
    # ap.active(False)
    sta.active(True)
    while not sta.active():
        time.sleep(0.1)
    sta.disconnect()  # For ESP8266, because it auto-connects to last Access Point
    while sta.isconnected():
        time.sleep(0.1)
    # return sta, ap
    return sta
