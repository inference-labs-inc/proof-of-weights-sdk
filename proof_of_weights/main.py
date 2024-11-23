import base64
import hashlib
import json
import typing
import logging
import random
import string
from yarl import URL
from typing import Optional

import bittensor
import requests

__version__: typing.Final[str] = "0.0.5"
OMRON_NETUID_FINNEY: typing.Final[int] = 2
OMRON_NETUID_TESTNET: typing.Final[int] = 118

logger = logging.getLogger(__name__)


def get_omron_validator_axon(
    omron_validator_ss58: str,
    network: str = "finney",
    chain_endpoint: str = "",
) -> bittensor.AxonInfo:
    """
    Get the axon of a validator on the omron subnet.
    """
    config = bittensor.config()
    config.subtensor = bittensor.config()
    if chain_endpoint:
        config.subtensor.chain_endpoint = chain_endpoint
        config.subtensor.network = network
    else:
        config.subtensor.network, config.subtensor.chain_endpoint = (
            bittensor.subtensor.determine_chain_endpoint_and_network(network)
        )

    btnetwork = bittensor.subtensor(config)
    omron_validator_axon = btnetwork.get_axon_info(
        netuid=(OMRON_NETUID_FINNEY if network == "finney" else OMRON_NETUID_TESTNET),
        hotkey_ss58=omron_validator_ss58,
    )
    return omron_validator_axon


class Proof_Of_Weights:
    def __init__(
        self,
        wallet_name: str,
        wallet_hotkey: str,
        omron_validator_ss58: str,
        netuid: int,
        network: str = "finney",
        chain_endpoint: str = "",
    ):
        """
        Initialize the Proof of Weights class with your wallet and a validator's hotkey from the omron subnet.
        """
        self._wallet = bittensor.wallet(wallet_name, wallet_hotkey)
        self._omron_validator_axon = get_omron_validator_axon(
            omron_validator_ss58, network, chain_endpoint
        )
        self._netuid = netuid
        self._last_input_hash = ""
        self._base_url = URL.build(
            scheme="http",
            host=self._omron_validator_axon.ip,
            port=self._omron_validator_axon.port,
        )

    def get_signature_headers(
        self,
        url: str,
        data: str = "",
        salt: Optional[str] = "",
    ) -> dict[str, str]:
        """
        Sign the request with the wallet's hotkey and return proper headers with the signature.
        """
        if salt is None:
            salt = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        payload = f"{url}{salt}{data}".encode()
        signature = self._wallet.hotkey.sign(payload)
        return {
            "X-Salt": salt,
            "X-Request-Signature": base64.b64encode(signature).decode("utf-8"),
            "X-ss58-Address": self._wallet.hotkey.ss58_address,
        }

    def submit_inputs(self, reward_function_inputs: dict | list) -> str:
        """
        Submit reward function inputs from network with netuid to a validator on the omron subnet.
        """
        self._last_input_hash = _hash_inputs(reward_function_inputs)
        # serialize the reward function inputs as json bytes
        input_str = json.dumps(
            {
                "inputs": reward_function_inputs,
                "netuid": self._netuid,
            }
        )
        url = self._base_url.with_path("submit-inputs")

        # send the reward function inputs and signature to the omron subnet on port API_PORT
        response = requests.post(
            url=url,
            data=input_str.encode(),
            headers={
                "Content-Type": "application/json",
                **self.get_signature_headers(url=url, data=input_str),
            },
        )
        if response.status_code != 200:
            logger.error(
                f"Failed to submit inputs. Status code: {response.status_code}, "
                f"Content: {response.content}"
            )
            return ""

        data = response.json()
        if data.get("hash") != self._last_input_hash:
            logger.error(
                f"Transaction hash mismatch. Local: {self._last_input_hash}, "
                f"Remote: {data.get('hash')}"
            )
            return ""

        return self._last_input_hash

    def get_proof(self) -> dict:
        """
        Get the proof of weights from the omron subnet validator.
        """
        url = self._base_url.with_path(f"get-proof-of-weights").with_query(
            {"input_hash": self._last_input_hash}
        )
        response = requests.get(
            url=url,
            headers=self.get_signature_headers(url=str(url)),
        )
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            return {}
        return response.json()


def _hash_inputs(inputs: dict) -> str:
    """
    Hashes inputs to proof of weights, excluding dynamic fields.

    Args:
        inputs (dict): The inputs to hash.

    Returns:
        str: The hashed inputs.
    """
    filtered_inputs = {
        k: v
        for k, v in inputs.items()
        if k not in ["validator_uid", "nonce", "uid_responsible_for_proof"]
    }
    return hashlib.sha256(str(filtered_inputs).encode()).hexdigest()
