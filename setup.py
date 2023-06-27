from setuptools import find_packages
from setuptools import setup

long_description = open("README.md", encoding="utf-8").read()
description = "WPP_Whatsapp aim of exporting functions from WhatsApp Web to the python, which can be used to support the creation of any interaction, such as customer service, media sending, intelligence recognition based on phrases artificial and many other things, use your imagination"

version = "0.0.1"

setup(
    name="WPP_Whatsapp",
    version=version,
    license="MIT License",
    author="Ammar Alkotb",
    author_email="ammar.alkotb@gmail.com",
    description=description,
    packages=find_packages("WPP_Whatsapp"),
    package_dir={"": "WPP_Whatsapp"},
    url="https://github.com/3mora2/WPP_Whatsapp",
    project_urls={"Bug Report": "https://github.com/3mora2/WPP_Whatsapp/issues/new"},
    install_requires=[
        "event-emitter-js",
        "greenlet",
        "playwright",
        "Pillow",
        "psutil",
        "pye",
        "pyee",
        'PyQRCode',
        'typing_extensions',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["WPP_Whatsapp"],
    classifiers=[
        # "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
