from flask import *
from fido2.server import Fido2Server
from fido2.webauthn import *
import os
import json
from jose import jws
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)

rp=PublicKeyCredentialRpEntity(name = "Authority", id="localhost")
server = Fido2Server(rp)

private_key=None

try:
	with open('private_key.der', 'rb') as f:
		priv_der=f.read()
		private_key=serialization.load_der_private_key(priv_der, password=None)
except:
	private_key=None
	
if private_key is None:
	private_key = ec.generate_private_key(ec.SECP256R1())
	private_der = private_key.private_bytes( encoding=serialization.Encoding.DER, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
	with open('private_key.der', 'wb') as f:
		f.write(private_der)


public_key = private_key.public_key()

public_numbers = public_key.public_numbers()
x = base64.urlsafe_b64encode(public_numbers.x.to_bytes(32, 'big')).decode('utf-8').rstrip('=')
y = base64.urlsafe_b64encode(public_numbers.y.to_bytes(32, 'big')).decode('utf-8').rstrip('=')
public_key_jwk = {
    "kty": "EC",
    "crv": "P-256",
    "x": x,
    "y": y
}

with open('public_key.json', 'w') as f:
	f.write(json.dumps(public_key_jwk, indent=4))

ISSUER_DID = "did:authority"


@app.route("/api/register/begin", methods=["POST"])
def register_begin():
	json_content = request.json
	ship_id = request.json["ship"]
	options, state = server.register_begin(
		PublicKeyCredentialUserEntity(
			id = ship_id.encode(),
			name = ship_id,
			display_name = ship_id,
		),
		resident_key_requirement="required",
		user_verification = "preferred",
		authenticator_attachment="cross-platform",
	)
	session["state"] = state
	session["ship"] = ship_id
	return jsonify(dict(options))
	
@app.route("/api/register/complete", methods=["POST"])
def register_complete():
	response = request.json
	ship_id = session.pop("ship")
	auth_data = server.register_complete(session.pop("state"), response)
	credential = auth_data.credential_data
	serialized_cred = base64.urlsafe_b64encode(credential).decode()
	data_content = {"ship": ship_id, "credential": serialized_cred}
	vcredential = {
		"@context": ["https://www.w3.org/2018/credentials/v1"],
		"id": "http://example.org/credentials/3732",
		"type": ["CyberCityShip"],
		"issuer": ISSUER_DID,
		"issuanceDate": datetime.utcnow().isoformat(),
		"credentialSubject": data_content
	}
	jws_token = jws.sign(vcredential, private_key, algorithm='ES256')
	presentation = {
		"@context": ["https://www.w3.org/2018/credentials/v1"],
		"type": ["VerifiablePresentation"],
		"issuer": ISSUER_DID,
		"verifiableCredential": jws_token
	}
	
	# TODO: Save to DB: vcredential
	
	resp = jsonify(presentation)
	return resp
	
@app.route("/")
def index():
	return redirect("register.html")
	
if __name__=='__main__':
	app.run(host="0.0.0.0", port=5000)
	



	
	
	
			