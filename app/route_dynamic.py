from flask import Flask, request, jsonify
import fmt

app = Flask(__name__)

@app.route('/token', methods=["POST"])
def token():

    #Fills data with the parameters from the xxx urlencoded content which posts to
    #our endpoint
    data = request.form

    #Gets and sets the parts of the url encoded content.
    grant_type = data.get('grant_type')
    pre_authorized_code = data.get('pre-authorized_code')
    tx_code = data.get('tx_code')

    #If the pre autorized code is the same as the one set earlier.
    if pre_authorized_code == "abkifewowo":
        response = {
        "accessToken": "EYinsertIT",
        "token_type": "bearer",
        "expires_in": 86400,
        "c_nonce": "tZignsnFbp",
        "c_nonce_expires_in": 86400,
        "authorization_details": [
                                     {
                                         "type": "openid_credential",
                                         "credential_configuration_id": "UniversityDegreeCredential",
                                         "credential_identifiers": [
                                             "CivilEngineeringDegree-2023",
                                             "ElectricalEngineeringDegree-2023"
                                         ]
                                     }
                                 ]
        }


        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        }

    #Post to wallet ;)
        response = request.post("HardCoded.com.uk.test.yolo", json=response, headers=headers)
    else : fmt.printf("Erra erra")
