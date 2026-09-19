from flask import *
import os
from fido2.server import *
from fido2.webauthn import *
import base64
import json
from jose import jws
from datetime import datetime
from db import *

app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)

rp=PublicKeyCredentialRpEntity(name = "Port", id="localhost")
server = Fido2Server(rp)


pubkey_name = "public_key.json"

with open("public_key.json", "r") as f:
	public_key = json.loads(f.read())
	
def verify_credential(presentation):
	jws_token = presentation['verifiableCredential']
	verified_credential = jws.verify(jws_token, public_key, algorithms=['ES256'])
	credential = json.loads(verified_credential.decode('utf-8'))
	if not all(key in credential for key in ['@context', 'id', 'type', 'issuer', 'issuanceDate', 'credentialSubject']):
		raise ValueError("Invalid credential structure")
	issuance_date = datetime.fromisoformat(credential['issuanceDate'].replace("Z", "+00:00"))
	if issuance_date > datetime.utcnow():
		raise ValueError("Credential issued in the future")
	return credential
	
@app.route("/api/authenticate/begin", methods=["POST"])
def authenticate_begin():
	options, state = server.authenticate_begin()
	session["state"]=state
	challenge = options.public_key.challenge
	challenge_b64 = base64.urlsafe_b64encode(challenge).decode()
	return jsonify({"challenge": challenge_b64})
	
@app.route("/api/authenticate/complete", methods=["POST"])
def authenticate_complete():
	response = request.json
	print(json.dumps(response, indent=4))
	presentation = response["presentation"]
	authresp = response["assertion"]
	verified_credential = verify_credential(presentation)
	serialized_cred = verified_credential["credentialSubject"]["credential"]
	ship_id = verified_credential["credentialSubject"]["ship"]
	credential = AttestedCredentialData(base64.urlsafe_b64decode(serialized_cred))
	server.authenticate_complete(session.pop("state"), [credential], authresp)
	
	resp = {"status": "success", "ship": ship_id}
	
	# TODO: Add to DB resp
	add_to_db(resp)
	
	return jsonify(resp)
	
@app.route("/")
def index():
	return redirect("index.html")
	
@app.route("/api/ships")
def api_ships():
	return show_all()
	
@app.route("/db")
def db_page():
	return redirect("db.html")

	
		
if __name__=='__main__':
	app.run(host='0.0.0.0', port=5001)