import logging
import re

logging.basicConfig(level=logging.DEBUG)
from pysiaalarm import SIAAccount, SIAEvent
from pysiaalarm.utils.regexes import (
    MAIN_MATCHER,
    ENCR_ADM_CONTENT_MATCHER,
    ENCR_SIA_CONTENT_MATCHER,
    SIA_CONTENT_MATCHER,
    ADM_CONTENT_MATCHER,
    OH_MATCHER,
)

# # matcher = re.compile(regex, re.X)
# # print(matcher.pattern)
# main_regex = r"""
# (?P<crc>[A-F0-9]{4})
# (?P<length>[A-F0-9]{4})\"
# (?P<encrypted_flag>[*])?
# (?P<message_type>SIA-DCS|NULL)\"
# (?P<sequence>[0-9]{4})
# (?P<receiver>R[A-F0-9]{1,6})?
# (?P<prefix>L[A-F0-9]{1,6})
# [#]?(?P<account>[A-F0-9]{3,16})?
# [\[]
# (?P<rest>.*)
# """
# MAIN_MATCHER = re.compile(main_regex, re.X)

# # “ti”hh:mm/ time (e.g. ti10:23/).
# # “id”nnn/ user number, if applicable; otherwise not sent (e.g.
# # “ri”nn/ partition no. (e.g. ri12/ or ri3).
# content_regex = r"""
# [#]?(?P<account>[A-F0-9]{3,16})?
# [|]?
# [N]?
# (?:ti)?(?:(?<=ti)(?P<ti>\d{2}:\d{2}))?\/?
# (?:id)?(?:(?<=id)(?P<id>\d*))?\/?
# (?:ri)?(?:(?<=ri)(?P<ri>\d*))?\/?
# (?P<code>[a-zA-z]{2})?
# (?P<message>\w*)
# [\]]
# (?:\[(?:(?<=\[)(?P<extendeddata>\w*)(?=\]))\])?
# [_]?
# (?P<timestamp>[0-9:,-]*)?
# """
# CONTENT_MATCHER = re.compile(content_regex, re.X)

# encr_content_regex = r"""(?:[^\|\[\]]*)[|]?"""
# ENCR_CONTENT_MATCHER = re.compile(encr_content_regex + content_regex, re.X)

# heartbeat_regex = r"""
# ^S
# (?:R)(?:(?<=R)(?P<receiver>\d{4}))
# (?:L)(?:(?<=L)(?P<prefix>\d{4}))
# \s+\w{8}\s+
# \[(?P<id>\w+)\]$
# """

# HEARTBEAT_MATCHER = re.compile(heartbeat_regex, re.X)

sia_lines = [
    r'2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501]_14:12:04,09-25-2019',
    r'76D80055"*NULL"0000R0L0#AAAB[B4BC8B40D0E6D959D6BEA78E88CC0B2155741A3C44FBB96D476A3E557CAD64D9',
    r'01010051"SIA-DCS"4738R0001L0001[#006969|Nri04/OP001*’NM]DDA2FBB313169D87|#006969',
    r'C4160279"SIA-DCS"5268L0#AAA[.Rr\x1d PaG\'5"�\n\x03��|Nri1/WA000]_08:40:47,07-08-2020',
    r'68370130"*NULL"6327L0#AAA[9F719719F36B05547CD730D4615FE0A4B5BB7A27A9F500741A07C3F7328FC7A1',
    r'43580023"SIA-DCS"0084L0#AAA[#AAA|Nri1/XC12]'
    r'85DF0078"*SIA-DCS"4480L0#EA1984[83F153789366885D5F83DD5A8D19F691DE6602D5D71342E244C040C5D10D89040444068312750F38DF7E63AD3DE8AD5A',
    r'1908002B"SIA-DCS"0000L0#3080[#3080|Nti19:44/id1/ri4/RP]',
    r'43580023"*SIA-DCS"0084L0#AAA[P$WwA!#|#EA1984|Nri1/NL4]_08:38:13,01-07-2021',
    r'2E680078"SIA-DCS"6002L0#AAA[|Nri1/CL501][A38475345]_14:12:04,09-25-2019',
    r"SR0001L0001    006969XX    [ID00000000]",
]

adm_lines = [
    r'87CD0037"ADM-CID"9876R579BDFL789ABC#12345A[#12345A|1110 00 129]_14:12:04,09-25-201'
]

encr_content = [
    r"v V|#EA1984|Nri0/RP0000]_16:57:20,08-11-2020",
    r" HM|#EA1984|Nri0/RP0000]_19:52:37,08-11-2020",
    r"T,o |#EA1984|Nri0/RP0000]_20:44:12,08-11-2020",
    r"_ |#EA1984|Nri0/RP0000]_22:27:02,08-11-2020",
    r"&* |#EA1984|Nri0/RP0000]_05:19:49,08-12-2020",
    r"P$WwA!#|#EA1984|Nri1/NL4]_08:38:13,01-07-2021",
]
unen_content = [
    r"#006969|Nri04/OP001NM]",
]

# for content in unen_content:
#     content_match = SIA_CONTENT_MATCHER.match(content)
#     print("unen_content_match groups", content_match.groupdict())

# for content in encr_content:
#     en_content_match = ENCR_SIA_CONTENT_MATCHER.match(content)
#     print("en_content_match groups", en_content_match.groupdict())

# for line in sia_lines:
#     print("Line ", line)
#     # print(SIAEvent(line))
#     prefix = MAIN_MATCHER.match(line)
#     # re.match(prefix_regex, line, re.X)
#     if prefix:
#         print("Groups", prefix.groupdict())
#         if prefix.group("encrypted_flag"):
#             # if re.search(r"(\*SIA-DCS|\*NULL)", line):
#             encrypted_content = prefix.group("rest")
#             print(encrypted_content)
#             content = ENCR_SIA_CONTENT_MATCHER.match(encrypted_content)
#             if content:
#                 print("Groups ", content.groupdict())
#             # print(
#             #     "Groups ", re.match(regex_encrypted, prefix.group("rest"), re.X).groupdict()
#             # )
#         else:
#             content = SIA_CONTENT_MATCHER.match(prefix.group("rest"))
#             if content:
#                 print("Groups ", content.groupdict())
#     else:
#         heartbeat = OH_MATCHER.match(line)
#         if heartbeat:
#             print("Groups ", heartbeat.groupdict())

for line in adm_lines:
    print("Line ", line)
    # print(SIAEvent(line))
    prefix = MAIN_MATCHER.match(line)
    # re.match(prefix_regex, line, re.X)
    if prefix:
        print("Groups", prefix.groupdict())
        if prefix.group("encrypted_flag"):
            # if re.search(r"(\*SIA-DCS|\*NULL)", line):
            encrypted_content = prefix.group("rest")
            print(encrypted_content)
            content = ENCR_ADM_CONTENT_MATCHER.match(encrypted_content)
            if content:
                print("Groups ", content.groupdict())
            # print(
            #     "Groups ", re.match(regex_encrypted, prefix.group("rest"), re.X).groupdict()
            # )
        else:
            content = ADM_CONTENT_MATCHER.match(prefix.group("rest"))
            if content:
                print("Groups ", content.groupdict())
    else:
        heartbeat = OH_MATCHER.match(line)
        if heartbeat:
            print("Groups ", heartbeat.groupdict())
