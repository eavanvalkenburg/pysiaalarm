==========
pysiaalarm
==========


Python package for creating a client that talks with SIA-based alarm systems.


Description
===========

This package was created to talk with alarm systems using the SIA protocal, it was tested using a Ajax system, but should support all defined SIA codes. 
It creates a new thread with a TCP Server running binded to a host and port, the alarm system acts a client that sends messages to that server and the server acknowledges the messages and call the supplied function.


Config 
==========

The client takes these arguments:

- host: if there is a specific host to talk to, should use '' for localhost.
- port: the tcp port your alarm system listens to.
- account_id: the account id as 3-16 ASCII hex characters.
- function: a function that will be called for every event that is handles, takes only a SIAEvent as parameter and does not pass back anything.
- [optional] key: encryption key specified in your alarm system 16, 24, or 32 ASCII characters
