import logging
import re

logging.basicConfig(level=logging.DEBUG)
from pysiaalarm import SIAAccount, SIAEvent

# matcher = re.compile(regex, re.X)
# print(matcher.pattern)
main_regex = r"""
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
MAIN_MATCHER = re.compile(main_regex, re.X)

content_regex = r"""
[#]?(?P<account>[A-F0-9]{3,16})?
[|]?
(?:Nri)?
(?P<zone>\d*)?
\/?
(?P<code>[a-zA-z]{2})?
(?P<message>.*)
[\]]
[_]?
(?P<timestamp>[0-9:,-]*)?
"""
CONTENT_MATCHER = re.compile(content_regex, re.X)

encr_content_regex = r"""
(?:[^\|\[\]]*)
[|]?
[#]?(?P<account>[A-F0-9]{3,16})?
[|]?
(?:.*Nri)?
(?P<zone>\d*)?
\/?
(?P<code>[a-zA-z]{2})?
(?P<message>.*)
[\]][_]?
(?P<timestamp>[0-9:,-]*)?
"""
ENCR_CONTENT_MATCHER = re.compile(encr_content_regex, re.X)

lines = [
    # r'2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
    # r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
    # r'01010051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001*’NM]DDA2FBB313169D87|#006969',
    # r'C4160279"SIA-DCS"5268L0#AAA[.Rr\x1d PaG\'5"�\n\x03��|Nri1/WA000]_08:40:47,07-08-2020',
    # r'68370130"*NULL"6327L0#AAA[9F719719F36B05547CD730D4615FE0A4B5BB7A27A9F500741A07C3F7328FC7A1',
    # r'43580023"SIA-DCS"0084L0#AAA[#AAA|Nri1/XC12]'
    r'85DF0078"*SIA-DCS"4480L0#EA1984[83F153789366885D5F83DD5A8D19F691DE6602D5D71342E244C040C5D10D89040444068312750F38DF7E63AD3DE8AD5A'
]

encr_content = [
    r"v V|#EA1984|Nri0/RP0000]_16:57:20,08-11-2020",
    r" HM|#EA1984|Nri0/RP0000]_19:52:37,08-11-2020",
    r"T,o |#EA1984|Nri0/RP0000]_20:44:12,08-11-2020",
    r"_ |#EA1984|Nri0/RP0000]_22:27:02,08-11-2020",
    r"&* |#EA1984|Nri0/RP0000]_05:19:49,08-12-2020",
]

# for content in encr_content:
#     en_content_match = CONTENT_MATCHER.match(content)
#     print("en_content_match groups", en_content_match.groupdict())

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
    print(ev.encrypted)
    # print(ev.valid_message)
    print(acc.decrypt(ev))
    # print(acc.decrypt(ev))
