![CI](https://github.com/eavanvalkenburg/pysiaalarm/workflows/CI/badge.svg?branch=dev)
![Build](https://github.com/eavanvalkenburg/pysiaalarm/workflows/Build/badge.svg?event=release)

<H1> pysiaalarm</H1>
==========


Python package for creating a client that talks with SIA-based alarm systems.


<H2>Description</H2>
===========

This package was created to talk with alarm systems using the SIA protocol, it was tested using a Ajax system, but should support all defined SIA codes. 
It creates a new thread with a TCP Server running binded to a host and port, the alarm system acts a client that sends messages to that server and the server acknowledges the messages and call the supplied function.


<H2>Config </H2>
==========

<H3>SIAClient</H3>

The SIAClient takes these arguments:

- host: if there is a specific host to talk to, usually has '' for localhost.
- port: the tcp port your alarm system listens to.
- accounts: list of type SIAAccount that are to be allowed to send messages to this server
- function: a function that will be called for every event that it handles, takes only a SIAEvent as parameter and does not pass back anything.

<H3>SIAAccount</H3>
SIAAccount takes these arguments:

- account_id: the account id as 3-16 ASCII hex characters.
- [optional] key: encryption key specified in your alarm system 16, 24, or 32 ASCII characters
- [optional] allowed_timeband: encrypted messages have a timestamp and those are checked against this timeband, by default the timestamp is allowed between -40 and +20 seconds comparing the timestamp in the message and the current timestamp of the system running the server.

See [`tests/run.py`](tests/run.py) for a complete sample.