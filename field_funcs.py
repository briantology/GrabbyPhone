import re

port_counters = [
    'RxalignErr',
    'RxcrcErr',
    'RxlongErr',
    'RxshortErr',
    'RxtokenDrop',
    'Txcollisions',
    'TxexcessDefer',
    'TxexcessLength',
    'TxlateCollision',
]

# 78/88 debug display:
# [8:54:12am 08/20/19] DeviceTLInfo ... ReasonForOutOfServiceText=...
# 8821 has space after seconds
# [5:48:09 AM 10/11/19]  DeviceName=SEP007686CF681A ... ReasonForOutOfServiceText=...
debug_rgx_default = re.compile(
        r'\d{1,2}:\d{1,2}:\d{1,2}\s*\w{2},?\s*'
        r'(?P<STAMP>\d{2}/\d{2}/\d{2}).+'
        r'ReasonForOutOfServiceText=(?P<TEXT>\w+)',
        re.I,
)

# 79xx debug display (does not include date:
# 12:02:55a 25: Name=SEPB8BEBF227D79 Load= 9.4(2SR3.1S) Last=Initialized
debug_rgx_79xx = re.compile(
        r'(?P<STAMP>\d{1,2}:\d{1,2}:\d{1,2}\w).+'
        r'Last=(?P<TEXT>.+)$',
        re.I,
    )

# 78/88 status messages:
# [8:52:30am 10/01/19] ITL installed
status_rgx_default = re.compile(
    r'\d{1,2}:\d{1,2}:\d{1,2}\s*\w{2},?\s*'
    r'(?P<STAMP>\d{2}/\d{2}/\d{2})\]\s*'
    r'(?P<TEXT>.+)',
    re.I,
)

# 79xx debug display (does not include date:
# 1:33:26a TFTP Error : SEPB8BEBF9D2061.cnf.xml.sgn
status_rgx_79xx = re.compile(
        r'(?P<STAMP>\d{1,2}:\d{1,2}:\d{1,2}\w)\s*'
        r'(?P<TEXT>.+)$',
        re.I,
    )

debug_display_rgx = [debug_rgx_default, debug_rgx_79xx]
status_messages_rgx = [status_rgx_default, status_rgx_79xx]


def multi_match(text_list, rgx_list, cnt):
    """
    Collected lines that match regex's in the rgx_list until the # of collected
    lines equals cnt.

    Args:
        text_list (list): List of strings to match
        rgx_list (list): One or more regex's
        cnt (int): Number of matches to collect before returning

    Returns:
        (str): The matched lines joined by linefeed/CR
    """
    matches = []
    for line in text_list:
        line = re.sub(r'\n', ' ', line)
        for rgx in rgx_list:
            m = rgx.search(line)
            if m:
                matches.append(' '.join(m.groups()))
                break

        if len(matches) >= cnt:
            break
    return '\n\r'.join(matches)


def prep_xml(func):
   
    def wrapper(xml_dict, count=1):
        """
       Take the OrderedDict returned from the Status message or Debug display web page
       and strip out the status messages for further processing.

       These pages both return the following data structures:
       If multiple messages exist:
             {'DeviceLog': { 'status' [ 'msg1', 'msg2']}}
       If a single (or no) message exists:
             {'DeviceLog': { 'status' 'msg'}}

       The value of the inner 'status' key is taken and, if necessary converted to a list. 
       The list is then reversed so the most recent entries are first. 

       Args:
           xml_dict (OrderedDict): Converted XML from IP phone web page
           count (int): Number of results to return 
            
       Returns:
            status_messages (list): Reversed list of status message entries
       """
        device_log = xml_dict.get('DeviceLog') or {}
        status_messages = device_log.get('status') or []

        # status_messages will be a list unless only one status message exists on the page
        # in which case it will be a string
        if isinstance(status_messages, str):
            status_messages = [status_messages]

        status_messages.reverse()
        return func(status_messages, count)
    return wrapper


@prep_xml
def parse_status_error(status_messages, count):
    """
    Parse Status message web page for the most recent error messages.

    Lines are matched based on the err_rgx.

    The most recent X matches are returned where X is the value of count.

    Args:
        status_messages (list): Lines from the Status message web page
        count (int): Number of matches to return

    Returns:
        (str): One or more matched lines joined by CR/LF
    """
    err_rgx = re.compile(r'(no trust list|error|configmismatch|tftp timeout)', re.I)
    matched = []
    for msg in status_messages:
        if err_rgx.search(msg):
            matched.append(msg)

    return multi_match(matched, status_messages_rgx, count)


@prep_xml
def parse_status_itl(status_messages, count):
    """
    Parse Status message web page for the most recent ITL-related entries.

    Matched lines contain "ITL" or "Trust". These may be errors or informational.

    The most recent X matches are returned where X is the value of count.

    Args:
        status_messages (list): Lines from the Status message web page
        count (int): Number of matches to return

    Returns:
        (str): One or more matched lines joined by CR/LF
    """
    itl_rgx = re.compile(r'(ITL|Trust)')
    matched = []
    for msg in status_messages:
        if itl_rgx.search(msg, re.I):
            matched.append(msg)

    return multi_match(matched, status_messages_rgx, count)


@prep_xml
def parse_debug_reason(debug_messages, count=1):
    """
    Parse Debug display page content for the most recent out of service reasons.

    Values are pulled from "ReasonForOutOfServiceText=TEXT" lines. The date and TEXT
    are extracted from the line and returned.

    The most recent X matches are returned where X is the value of count.

    Args:
        debug_messages (list): Lines from the Debug display web page
        count (int): Number of matches to return

    Returns:
        (str): One or more matched lines joined by CR/LF
    """
    return multi_match(debug_messages, debug_display_rgx, count)


def parse_port_errors(port_dict):
    """
    Parse PortInformation web pages and sum all the error counters into a single value.

    Args:
        port_dict (OrderedDict): Converted XML from IP phone web page

    Returns:
        val: (int): Sum of error counters
    """
    port_info = port_dict.get('PortInformation') or {}
    val = 0
    for k in port_counters:
        try:
            val += int(port_info.get(k, 0))
        except (TypeError, KeyError):
            pass
    return val


def parse_pc_port_speed(port_dict):
    """
    Parse Access network page content for PC port speed/duplex.

    Return 'N/A' if PortSpeed key is not present under the assumption that
    the source device does not have a PC port.

    Args:
        port_dict (OrderedDict): Converted XML from IP phone web page

    Returns:
        (str): PortSpeed value or 'N/A
    """
    port_info = port_dict.get('PortInformation') or {}
    return port_info.get('PortSpeed', 'N/A')
