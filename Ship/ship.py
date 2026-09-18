from flask import *
import os
from fido2.server import *
from fido2.webauthn import *
import base64
from pathlib import Path
import json

app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)

rp=PublicKeyCredentialRpEntity(name = "Port", id="localhost")
server = Fido2Server(rp)

license_file="license.json"

@app.route("/getlicense")
def get_license():
	try:
		with open(license_file, "r") as f:
			return json.loads(f.read())
	except Exception as e:
		return {}

@app.route("/savelicense", methods=["POST"])
def save_license():
	req = request.json
	license = req
	with open(license_file, "w") as f:
		f.write(json.dumps(license, indent=4))
	return jsonify({"status": True})
		
@app.route("/deletelicense", methods=["POST"])
def delete_license():
	file_path = Path(license_file)
	file_path.unlink(missing_ok=True)
	return jsonify({"status": "success"})
	
@app.route("/haslicense")
def haslicense():
	if get_license():
		return jsonify({"status": True})
		
	return jsonify({"status": False}), 404	
		
@app.route("/api/authenticate/begin", methods=["POST"])
def authenticate_begin():
	if not get_license():
		raise ValueError("License not saved")
	req = request.json
	print(req)
	challenge_b64 = req["data"]
	challenge=base64.urlsafe_b64decode(challenge_b64)
	options, state = server.authenticate_begin(challenge = challenge)
	return jsonify(dict(options))
	
@app.route("/api/authenticate/complete", methods=["POST"])
def authenticate_complete():
	response = request.json
	license = get_license()
	return jsonify({"presentation": license, "authresp": response})
	
@app.route("/")
def index():
	return redirect("license.html")
		
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5002)