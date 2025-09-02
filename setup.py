from setuptools import setup, find_packages

setup(
    name="anubis_discord_adapters",
    version="0.0.3",
    author="Jose Manuel Herera Saenz",
    author_email="incubadoradepollos@gmail.com",
    description="Core for Anubis System",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AnubisSystems/AnubisDiscordAdapters",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "Topic :: Education",
    ],
    python_requires=">=3.13.0",
    install_requires=[
         "anubis_core @ git+https://github.com/AnubisSystems/AnubisCore.git",
         "discord.py"
    ],
)
