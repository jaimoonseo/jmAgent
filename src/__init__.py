"""
jmAgent - Personal Claude Coding Assistant powered by AWS Bedrock

A production-ready coding assistant that supports code generation, refactoring,
testing, explanation, debugging, and interactive chat across multiple programming
languages and frameworks.
"""

__version__ = "1.0.0"
__author__ = "jmAgent Contributors"
__license__ = "MIT"

from src.agent import JmAgent

__all__ = ["JmAgent", "__version__", "__author__", "__license__"]
