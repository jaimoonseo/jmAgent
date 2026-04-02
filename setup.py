from setuptools import setup, find_packages

setup(
    name="jmAgent",
    version="0.1.0",
    description="Personal Claude coding assistant using AWS Bedrock",
    author="jmAgent",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "boto3>=1.28.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "jm=src.cli:main",
        ],
    },
)
