import base64
import hashlib
import json
import os

import substrateinterface

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

BITTENSOR_NETWORK = "finney"
VERIFY_EXTERNAL_VALIDATOR_SUBNET = False


class PowInputModel(BaseModel):

    inputs: str
    signature: str
    sender: str
    netuid: int


@app.post("/submit_inputs")
async def submit_inputs(data: PowInputModel):
    # decode inputs and signature then verify signature
    try:
        inputs = base64.b64decode(data.inputs)
        signature = base64.b64decode(data.signature)
        public_key = substrateinterface.Keypair(ss58_address=data.sender)
        if not public_key.verify(data=inputs, signature=signature):
            raise Exception("Invalid signature")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Signature or input error: {e}",
            headers={"X-Error": "Signature or input error"},
        )

    transaction_hash = hashlib.sha256(inputs + signature).hexdigest()
    inputs = json.loads(inputs)
    return {"hash": transaction_hash}
