import setuptools
import proof_of_weights

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="proof-of-weights",
    version=proof_of_weights.__version__,
    python_requires=">3.6",
    description=(
        "SDK for validators from various subnets to publish their "
        "reward function inputs to validators within the omron subnet."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/inference-labs-inc/proof-of-weights-sdk",
    packages=["proof_of_weights"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 1 - Planning",
    ],
    requires=["requests", "bittensor", "yarl"],
    test_suite="tests",
)
