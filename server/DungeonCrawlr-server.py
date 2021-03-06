import socket
import socketserver
import json
import time
import sys
import argparse
import configparser
from enum import Enum
import mysql.connector

class serverInfo(Enum):
	VERSION = 0.1

class logLevel(Enum):
	INFO = "INFO"
	WARN = "WARN"
	FATAL = "FATAL"

def log(str, loglevel):
	output = "[{}] [{}]: {}".format(time.strftime("%H:%M:%S"), loglevel, str)
	sys.stdout.write(output)
	with open("server.log", "a") as logfile:
		logfile.write(output)

class ConnectError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
		
class OutdatedClientError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class OutdatedServerError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class ConnectionHandler(socketserver.BaseRequestHandler):
	def handle(self):
		self.dataRaw = self.request.recv(1024).strip()
		try:
			self.data = json.loads(self.dataRaw.decode())
			if self.data["connectType"] != "request_connect":
				raise ConnectError
			if self.data["data"]["clientVersion"] != serverInfo.version:
				raise OutdatedClientError
			log("Incoming connection from {} with username {}".format(self.client_address[0], self.data["data"]["username"]), logLevel.INFO)
			while True:
				self.dataStreamRaw = self.request.recv(1024).strip()
				self.dataStream = json.loads(self.dataStreamRaw.decode())
				self.connectType = self.dataStream["connectType"]
				if self.connectType[0] == "request":
					if self.connectType[1] == "disconnect":
						break
					elif self.connectType[1] == "chat":
						pass
				elif self.connectType[0] == "put":
					if self.connectType[1] == "movement":
						pass
					elif self.connectType[1] == "chat":
						pass
		except ValueError:
			log("{} lost connection: Invalid JSON".format(self.client_address[0]), logLevel.INFO)
		except ConnectError:
			log("{} lost connection: Invalid request".format(self.client_address[0]), logLevel.WARN)
		except OutdatedClientError:
			log("{} lost connection: Outdated client (client version {f})".format(self.client_address[0],self.data["data"]["clientVersion"]), logLevel.INFO)
		except OutdatedServerError:
			log("{} lost connection: Outdated server (client version {f})".format(self.client_address[0],self.data["data"]["clientVersion"]), logLevel.INFO)

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description="Hosts a server for DungeonCrawlr.")
	argparser.add_argument("--server", "-s", action="store", default="localhost", required=False, dest="mysqlServerAddr", help="Address of the MySQL or MariaDB server to store data at. Default: localhost")
	argparser.add_argument("--username", "-u", action="store", default="dungeoncrawlr", required=False, dest="mysqlUsername", help="Username to use to log into the MySQL / MariaDB server with. Default: dungeoncrawlr")
	argparser.add_argument("--password", "-p", action="store", required=False, dest="mysqlPassword", help="Password of the account used to log into the MySQL / MariaDB server.")
	