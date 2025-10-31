"""
Setup configuration for Global Insight Explorer
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="global-insight-explorer",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="글로벌 인사이트 탐색기 - 미디어 콘텐츠 분석 도구",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/global-insight-explorer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "global-insight-explorer=app.main:main",
        ],
    },
)
