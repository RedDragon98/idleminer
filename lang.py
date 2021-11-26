"""defines the text messages for idleminer"""


ERRMSG: str
COSTMSG: str
UPMSG: str
NOTINTMSG: str
MINEUPMSG: str
CATCHFISHMSG: str
CATCHTREASUREMSG: str
CATCHPETMSG: str
NOCATCHPETMSG: str
FISHINGUPMSG: str
CORRECTANSWERMSG: str
WRONGANSWERMSG: str
INCOMPATDATAMSG: str
COOLDOWNMSG: str
UPBIOMEMSG: str
GROWMSG: str
HELPMSG: str
HELPMSGC: str
MOBHITMSG: str
MOBHURTMSG: str
WINMSG: str
DEADMSG: str
BATTLEUPMSG: str
WOULDLIKETOEATMSG: str
ATEMSG: str
NOFOODMSG: str
LASTMINELEVELMSG: str
NOLAPISMSG: str
BADPROFILEMSG: str
INVALIDTOOLMSG: str
BADDIFFICULTYMSG: str


def load(langpack: dict):
    """loads the text messages out of a file"""
    for key in langpack.keys():
        globals()[key] = langpack[key]
