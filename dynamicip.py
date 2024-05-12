import minqlx
import requests
import json

MYIP_KEY = "minqlx:myip"

class dynamicip(minqlx.Plugin):
	def __init__(self):
		super().__init__()
		self.add_hook("game_countdown", self.handle_game_countdown)
		
		self.set_cvar_once("qlx_qlStatsAdminPanel", "qlstats.net/panel3")

		self.api_url = "http://{}/api/".format(self.get_cvar("qlx_qlStatsAdminPanel"))
		self.zmq_password = self.get_cvar("zmq_stats_password")
		self.zmq_port = self.get_cvar("zmq_stats_port")
		if not self.zmq_port:
			self.zmq_port = self.get_cvar("net_port")
			if not self.zmq_port:
				self.zmq_port = "27960"
		self.server_owner = self.get_cvar("qlx_owner")

		servers = self.run_api("servers")
		old_ip = self.db[MYIP_KEY] if MYIP_KEY in self.db else ""
		current_ip = self.get_current_ip()
		for server in servers:
			if ( server['ip'], server['port'] ) == ( old_ip, int(self.zmq_port) ):
				if current_ip != old_ip:
					self.set_current_ip( current_ip )
				self.server_owner = server['owner']
				break
			elif ( server['ip'], server['port'] ) == ( current_ip, int(self.zmq_port) ):
				self.server_owner = server['owner']
				self.db[MYIP_KEY] = current_ip
				break

		self.logger.info("zmq_password: " + self.zmq_password)
		self.logger.info("zmq_port: " + self.zmq_port)
		self.logger.info("server_owner: " + self.server_owner)
		self.logger.info("current_ip: " + current_ip)

	def handle_game_countdown(self):
		@minqlx.thread
		def f():
			self.set_current_ip( self.get_current_ip() )
		f()

	def set_current_ip(self, current_ip):
		if MYIP_KEY in self.db:
			if current_ip != self.db[MYIP_KEY]:
				r = self.run_api("editserver", {
					"action": "update",
					"newAddr": current_ip,
					"newGamePort": "",
					"newPwd1": "",
					"newPwd2": "",
					"oldPwd": self.zmq_password,
					"owner": None,
					"server": self.db[MYIP_KEY]
				})
				if r["ok"] == False:
					self.logger.warning(r["msg"])
				else:
					self.logger.info(r["msg"])
					self.db[MYIP_KEY] = current_ip
			else:
				self.logger.info("same ip. nothing changed")
		else:
			r = self.run_api("addserver", {
				"newAddr": current_ip + ":" + self.zmq_port,
				"newPwd1": self.zmq_password,
				"newPwd2": self.zmq_password,
				"owner": self.server_owner
			})
			self.logger.info(r["msg"])
			self.db[MYIP_KEY] = current_ip
	
	def get_current_ip(self):
		return requests.get("http://ifconfig.me/ip").text
		
	def run_api(self, method, params=None):
		if params == None:
			r = requests.get(self.api_url + method)
		else:
			r = requests.post(self.api_url + method, json=params)
		return json.loads(r.text)
	

