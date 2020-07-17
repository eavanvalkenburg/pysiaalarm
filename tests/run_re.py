import logging
import re

logging.basicConfig(level=logging.DEBUG)
from pysiaalarm import SIAAccount, SIAEvent

# regex = r"""(?P<crc>[A-F0-9]{4})
#     (?P<length>[A-F0-9]{4})
#     (?P<type>SIA-DCS|\*SIA-DCS|NULL|\*NULL)
#     \"
#     (?P<sequence>[0-9]{4})
#     (?P<receiver>R[A-F0-9]{1,6})?
#     (?P<prefix>L[A-F0-9]{1,6})
#     [#]?
#     (?P<account>[A-F0-9]{3,16})?
#     \[[#]?
#     (?P<encrypted>[A-F0-9]*)?
#     (?P<account2>[A-F0-9]{3,16})?
#     .*Nri
#     (?P<zone>\d*)
#     /
#     (?P<code>[a-zA-z]{2})
#     (?P<message>.*)?
#     ]_?
#     (?P<timestamp>[0-9:,-]*)?"""
prefix_regex = r"""
(?P<crc>[A-F0-9]{4})
(?P<length>[A-F0-9]{4})\"
(?P<encrypted_flag>[*])?
(?P<message_type>SIA-DCS|NULL)\"
(?P<sequence>[0-9]{4})
(?P<receiver>R[A-F0-9]{1,6})?
(?P<prefix>L[A-F0-9]{1,6})
[#]?(?P<account>[A-F0-9]{3,16})?
[\[]
(?P<rest>.*)
"""
prefix_matcher = re.compile(prefix_regex, re.X)
content_regex = r"""
[#]?(?P<account>[A-F0-9]{3,16})?
(?:.*Nri)
(?P<zone>\d*)?
\/?
(?P<code>[a-zA-z]{2})?
(?P<message>.*)
[\]][_]?
(?P<timestamp>[0-9:,-]*)?
"""
# matcher = re.compile(regex, re.X)
# print(matcher.pattern)

lines = [
    # r'2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
    # r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
    # r'01010051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001*’NM]DDA2FBB313169D87|#006969',
    # r'C4160279"SIA-DCS"5268L0#AAA[.Rr\x1d PaG\'5"�\n\x03��|Nri1/WA000]_08:40:47,07-08-2020',
    # r'68370130"*NULL"6327L0#AAA[9F719719F36B05547CD730D4615FE0A4B5BB7A27A9F500741A07C3F7328FC7A1',
    # r'43580023"SIA-DCS"0084L0#AAA[#AAA|Nri1/XC12]'
    r'021A0078"*SIA-DCS"0764L0#EA1984[E759F1FE2FDBAF5B30AED69378DF87CF9DA82AA9292D0661E3EBA6DF2AD55AEA4D91968EE8460EC206B8AEAD69B33BCB'
]


for line in lines:
    # print("Line ", line)
    # # print(SIAEvent(line))
    # prefix = prefix_matcher.match(line)
    # # re.match(prefix_regex, line, re.X)
    # print("Prefix groups", prefix.groupdict())
    # if prefix:
    #     if prefix.group("encrypted_flag"):
    #         # if re.search(r"(\*SIA-DCS|\*NULL)", line):
    #         encrypted_content = prefix.group("rest")
    #         print(encrypted_content)
    #         # print(
    #         #     "Groups ", re.match(regex_encrypted, prefix.group("rest"), re.X).groupdict()
    #         # )
    #     else:
    #         print(
    #             "Groups ",
    #             re.match(content_regex, prefix.group("rest"), re.VERBOSE).groupdict(),
    #         )
    #         # print("Groups ", matcher.match(line).groupdict())
    acc = SIAAccount("EA1984", "3BD7E66AA9E2F190")
    ev = SIAEvent(line)
    print(ev)
    # print(ev.valid_message)
    print(acc.decrypt(ev))
    print(acc.decrypt(ev))
