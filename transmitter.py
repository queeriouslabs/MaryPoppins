import socket
import time
import sys
import threading


def run_transmitter(port, delay):

    delay = max(10, delay)

    def transmitter_thread():
        while True:
            transmitter = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            transmitter.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = ('sel-transmitter %s' % port).encode('utf-8')

            transmitter.sendto(message, ('<broadcast>', 1337))
            time.sleep(delay)

    threading.Thread(target=transmitter_thread).start()
