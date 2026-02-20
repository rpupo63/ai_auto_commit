from setuptools import setup, find_packages

setup(
    name="ai_auto_commit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain_core",
        "langchain_openai",
        "langchain_anthropic",
        "langchain_google_genai",
        "langchain_mistralai",
        "langchain_cohere",
        "ai_model_picker",
        "InquirerPy",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "autocommit = ai_auto_commit.cli:main",
        ],
    },
)