=====
pysiaalarm
=====


Python package for creating a client that talks with SIA-based alarm systems.


Description
===========

This package was created to talk with alarm systems using the SIA protocal, it was tested using a Ajax system, but should support all defined SIA codes.


Config 
==========

The client takes these arguments:

- host: if there is a specific host to talk to, otherwise use "" for any IP.
- port: the tcp port your alarm system listens to.
- account_id: the account id as 3-16 ASCII hex characters.
- function: a function that will be called for every event that is handles, takes only a SIAEvent as parameter and does not pass back anything.
- [optional] key: encryption key specified in your alarm system 16 ASCII characters
