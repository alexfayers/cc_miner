# cc_miner

An epic projected called cc_miner, by alexfayers!

## Installation

To install the project you only need to clone the repo and run pip install:

```bash
git clone https://github.com/alexfayers/cc_miner
cd cc_miner
pip install .
```

If you like using virtual environments, you can easily install the project within one using [pipx](https://pypa.github.io/pipx/):

```bash
pipx install .
```

## Usage

You can use cc_miner as an importable module:

```py
from cc_miner import BaseClass

app = BaseClass("config.yml")

# start the socket server listener
app.start_socketserver()
```

Or as a command line interface:

```bash
$ python3 -m cc_miner
# or
$ cc_miner
```

## Documentation

API documentation for cc_miner can be found at [https://alexfayers.github.io/cc_miner](https://alexfayers.github.io/cc_miner).
