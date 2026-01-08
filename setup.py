"""
Activator 安装脚本

使用 pip install -e . 进行开发模式安装
"""

from pathlib import Path
from setuptools import setup, find_packages

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="activator",
    version="1.0.0",
    author="Activator Team",
    author_email="your-email@example.com",
    description="AI订阅套餐激活器工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/activator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "activator=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai activation openai anthropic api scheduler",
    project_urls={
        "Bug Reports": "https://github.com/your-username/activator/issues",
        "Source": "https://github.com/your-username/activator",
    },
)
