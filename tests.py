import importlib
import os
import signal
import shutil
import subprocess
import time
import unittest

import proof_of_weights

import bittensor
import requests


class Test_Proof_of_Weights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree("omron-validator-api", True)
        os.mkdir("omron-validator-api")
        # get latest api
        with open("omron-validator-api/main.py", "w") as f:
            f.write(
                requests.get(
                    "https://raw.githubusercontent.com/inference-labs-inc/omron-validator-api/main/main.py"
                ).text
            )
        # get requirements for api
        requirements = requests.get(
            "https://raw.githubusercontent.com/inference-labs-inc/omron-validator-api/main/requirements.txt"
        ).text
        # check if the requirements are installed
        for requirement in requirements.split("\n"):
            if requirement:
                try:
                    importlib.import_module(requirement)
                except ImportError:
                    subprocess.run(["pip", "install", requirement])
        # run the api and get the pid to kill it later
        env = os.environ
        env["VALIDATOR_PATH"] = "."
        env["LAZY_RUN"] = "true"
        os.chdir("omron-validator-api")
        cls.api_process = subprocess.Popen(
            ["uvicorn", "main:app", "--host", "localhost", "--port", "8000"], env=env
        )
        os.chdir("..")
        time.sleep(1)
        # create test wallet
        cls.wallet = bittensor.wallet(name="test_wallet", hotkey="test_wallet_hotkey")
        cls.wallet.create_new_coldkey(use_password=False, overwrite=True)
        cls.wallet.create_new_hotkey(use_password=False, overwrite=True)
        # replace methods that can't be tested
        proof_of_weights.main.get_omron_validator_ip = lambda x, y: "localhost"

    @classmethod
    def tearDownClass(cls):
        cls.api_process.send_signal(signal.SIGINT)
        shutil.rmtree("omron-validator-api", True)

    def test_send(self):
        pow = proof_of_weights.Proof_Of_Weights(
            "test_wallet", "test_wallet_hotkey", "null", 1
        )
        transaction_hash = pow.submit_inputs(
            {
                "max_score": [0.0042553190141916275, 0.0042553190141916275],
                "previous_score": [0.0, 0.0],
                "verification_result": [False, False],
                "proof_size": [5000, 5000],
                "response_time": [600.0, 600.0],
                "median_max_response_time": [600.0, 600.0],
                "min_response_time": [0.0, 0.0],
                "block_number": [0, 0],
                "validator_uid": [0, 0],
                "uid": [0, 0],
            }
        )
        print("Transaction hash:", transaction_hash)


if __name__ == "__main__":
    unittest.main()
