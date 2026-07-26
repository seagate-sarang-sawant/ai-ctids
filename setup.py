"""
AI-CTIDS Package Setup
Install the project as a package for easier imports and distribution.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements from requirements.txt
def read_requirements(filename):
    """Read requirements from file, excluding comments and options."""
    requirements_file = Path(__file__).parent / filename
    if not requirements_file.exists():
        return []
    
    requirements = []
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments, empty lines, and pip options
            if line and not line.startswith("#") and not line.startswith("-"):
                requirements.append(line)
    return requirements


setup(
    name="ai-ctids",
    version="0.1.0",
    author="AI-CTIDS Team",
    author_email="your-email@example.com",
    description="AI-Driven Cyber Threat Detection and Intrusion Detection System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-ctids",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/ai-ctids/issues",
        "Documentation": "https://github.com/yourusername/ai-ctids/docs",
        "Source Code": "https://github.com/yourusername/ai-ctids",
    },
    packages=find_packages(
        exclude=["tests", "tests.*", "docs", "examples", "jupyter_notebooks"]
    ),
    python_requires=">=3.9,<4.0",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "minimal": read_requirements("requirements-minimal.txt"),
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "cybersecurity",
        "intrusion-detection",
        "machine-learning",
        "deep-learning",
        "threat-detection",
        "network-security",
        "xgboost",
        "tensorflow",
        "fastapi",
        "kafka",
    ],
    entry_points={
        "console_scripts": [
            "ai-ctids-train=batch_trainer.train:main",
            "ai-ctids-api=inference_api.main:run",
            "ai-ctids-consumer=streaming_consumer.consumer:main",
            "ai-ctids-ingest=data_ingestion.generate:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.pkl"],
    },
    zip_safe=False,
)
