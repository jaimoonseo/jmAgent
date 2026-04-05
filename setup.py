from setuptools import setup, find_packages

setup(
    name="jmAgent",
    version="1.0.0",
    description="Personal Claude coding assistant using AWS Bedrock with enterprise features",
    author="jmAgent Contributors",
    author_email="contact@jmagent.local",
    url="https://github.com/yourusername/jmAgent",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "boto3>=1.28.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "PyGithub>=2.0.0",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "jm=src.cli:main",
        ],
    },
    keywords=[
        "claude",
        "bedrock",
        "code-generation",
        "ai-assistant",
        "aws",
        "developer-tools",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description_content_type="text/markdown",
)
