import os
from distutils.sysconfig import get_python_inc
from setuptools import find_packages
from setuptools import setup
from setuptools.extension import Extension

long_description = open("README.md", encoding="utf-8").read()
description = "WPP_Whatsapp aim of exporting functions from WhatsApp Web to the python, which can be used to support the creation of any interaction, such as customer service, media sending, intelligence recognition based on phrases artificial and many other things, use your imagination"

incdir = os.path.join('Numerical')
version = "0.1.3"


setup(
    name="WPP_Whatsapp",
    version=version,
    license="MIT License",
    author="Ammar Alkotb",
    author_email="ammar.alkotb@gmail.com",
    description=description,
    packages=find_packages(),
    url="https://github.com/3mora2/WPP_Whatsapp",
    project_urls={"Bug Report": "https://github.com/3mora2/WPP_Whatsapp/issues/new"},
    install_requires=[
        "event-emitter-js",
        "greenlet",
        "playwright",
        "Pillow",
        "psutil",
        "pyee",
        'segno',
        'typing_extensions',
        "playwright-stealth"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    # py_modules=["WPP_Whatsapp"],
    package_dir={"": "."},
    package_data={"WPP_Whatsapp": ["*/*.js", "*.md"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",

    ],

)
