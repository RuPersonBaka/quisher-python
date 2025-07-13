from setuptools import setup, find_packages

setup(
    name="guisher",
    version="0.1.0",
    description="A lightweight GUI library without external dependencies",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    package_data={
        'guisher': ['*.dll', '*.exe'],  # если будут дополнительные файлы
    },
    install_requires=[],  # намеренно пустой, так как библиотека должна работать без зависимостей
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
    ],
    keywords="gui lightweight windows native",
)
