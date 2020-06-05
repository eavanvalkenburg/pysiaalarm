![CI](https://github.com/eavanvalkenburg/pysiaalarm/workflows/CI/badge.svg?branch=master)
![Build](https://github.com/eavanvalkenburg/pysiaalarm/workflows/Build/badge.svg)
[![PyPI version](https://badge.fury.io/py/pysiaalarm.svg)](https://badge.fury.io/py/pysiaalarm)

<H1>pySIAAlarm</H1>

Python package for creating a client that talks with SIA-based alarm systems. Currently tested using a Ajax Systems alarm system. If you have other systems please reach out.


<H2>Description</H2>

This package was created to talk with alarm systems using the SIA protocol, it was tested using a Ajax system, but should support all defined SIA codes. 
It either creates a new thread with a TCP Server or a asyncio coroutine running bound to the host and port, the alarm system acts a client that sends messages to that server and the server acknowledges the messages and call the supplied function.

The asyncio version seems to be faster but that depends on your system.

<H2>Config</H2>

Choose to use the Threaded approach or a Asyncio approach

<H3>SIAClient</H3>

Threaded version:
```python 
from pysiaalarm import SIAClient, SIAAccount
``` 
Asyncio version:
```python 
from pysiaalarm.aio import SIAClient, SIAAccount
``` 


The SIAClient takes these arguments:

- host: if there is a specific host to talk to, usually has '' for localhost.
- port: the TCP port your alarm system communicates with.
- accounts: list of type SIAAccount that are to be allowed to send messages to this server
- function: a function that will be called for every event that it handles, takes only a SIAEvent as parameter and does not pass back anything.

<H3>SIAAccount</H3>
SIAAccount takes these arguments:

- account_id: the account id as 3-16 ASCII hex characters.
- [optional] key: encryption key specified in your alarm system 16, 24, or 32 ASCII characters
- [optional] allowed_timeband: encrypted messages have a timestamp and those are checked against this timeband, by default the timestamp is allowed between -40 and +20 seconds comparing the timestamp in the message and the current timestamp of the system running the server.

See [`tests/run.py`](tests/run.py) or [`tests/run_aio.py`](tests/run_aio.py) for a complete sample.
