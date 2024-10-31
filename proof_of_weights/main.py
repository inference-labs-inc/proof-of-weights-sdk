import base64
import hashlib
import json
import typing
import logging
from yarl import URL

import bittensor
import requests

__version__: typing.Final[str] = "0.0.4"
OMRON_NETUID_FINNEY: typing.Final[int] = 2
OMRON_NETUID_TESTNET: typing.Final[int] = 118

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# logger.addHandler(logging.StreamHandler())
# file_handler = logging.FileHandler(
#     os.path.join(os.path.dirname(__file__), "proof_of_weights.log")
# )
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger.addHandler(file_handler)


def get_omron_validator_axon(
    omron_validator_ss58: str, network: str = "finney"
) -> bittensor.AxonInfo:
    """
    Get the axon of a validator on the omron subnet.
    """
    btnetwork = bittensor.subtensor(network=network)
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
    ):
        """
        Initialize the Proof of Weights class with your wallet and a validator's hotkey from the omron subnet.
        """
        self._wallet = bittensor.wallet(wallet_name, wallet_hotkey)
        self._omron_validator_axon = get_omron_validator_axon(
            omron_validator_ss58, network
        )
        self._netuid = netuid
        self._last_transaction_hash = ""
        self._base_url = URL.build(
            scheme="http",
            host=self._omron_validator_axon.ip,
            port=self._omron_validator_axon.port,
        )

    def submit_inputs(self, reward_function_inputs: dict | list) -> str:
        """
        Submit reward function inputs from network with netuid to a validator on the omron subnet.
        """
        # serialize the reward function inputs as json bytes
        input_bytes = json.dumps(reward_function_inputs).encode()
        # sign the inputs with your hotkey
        signature = self._wallet.hotkey.sign(input_bytes)
        # encode the inputs and signature as base64
        input_str = base64.b64encode(input_bytes).decode("utf-8")
        signature_str = base64.b64encode(signature).decode("utf-8")
        self._last_transaction_hash = _hash_inputs(reward_function_inputs)

        # send the reward function inputs and signature to the omron subnet on port API_PORT
        response = requests.post(
            self._base_url.with_path("submit-inputs"),
            json={
                "inputs": input_str,
                "signature": signature_str,
                "sender": self._wallet.hotkey.ss58_address,
                "netuid": self._netuid,
            },
        )
        if response.status_code != 200:
            logger.error(
                f"Failed to submit inputs. Status code: {response.status_code}, "
                f"Content: {response.content}"
            )
            return ""

        data = response.json()
        if data.get("hash") != self._last_transaction_hash:
            logger.error(
                f"Transaction hash mismatch. Local: {self._last_transaction_hash}, "
                f"Remote: {data.get('hash')}"
            )
            return ""

        return self._last_transaction_hash

    def get_proof(self) -> dict:
        """
        Get the proof of weights from the omron subnet validator.
        """
        response = requests.get(
            self._base_url.with_path(
                f"get-proof-of-weights/{self._last_transaction_hash}"
            )
        )
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
