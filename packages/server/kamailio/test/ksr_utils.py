import re
from typing import Union

pvar_vals = {}
hdr_vals = {}
hdr_iterators = {}

registrations = {"kamailio_location": {}}

pending_changes = []

def ksr_utils_init(_mock_data):
    global registrations
    global pvar_vals
    global hdr_vals
    global pending_changes

    pending_changes = []

    pvar_vals = {}
    hdr_vals = {}

    registrations["kamailio_location"] = {}

    _mock_data[''] = {}
    _mock_data['tm'] = {}
    _mock_data['dispatcher'] = {}
    _mock_data['permissions'] = {}

    _mock_data['pv']['get'] = pvar_get
    _mock_data['pv']['getw'] = pvar_getw
    _mock_data['pv']['gete'] = pvar_gete
    _mock_data['pv']['sets'] = pvar_set
    _mock_data['pv']['seti'] = pvar_seti
    _mock_data['htable']['sht_get'] = sht_get
    _mock_data['htable']['sht_getw'] = sht_getw
    _mock_data['htable']['sht_gete'] = sht_gete
    _mock_data['htable']['sht_inc'] = sht_inc
    _mock_data['htable']['sht_sets'] = sht_set
    _mock_data['htable']['sht_seti'] = sht_seti
    _mock_data['']['is_INVITE'] = is_invite
    _mock_data['']['is_KDMQ'] = is_kdmq
    _mock_data['']['is_ACK'] = is_ack
    _mock_data['']['is_BYE'] = is_bye
    _mock_data['']['is_CANCEL'] = is_cancel
    _mock_data['']['is_REGISTER'] = is_register
    _mock_data['']['is_OPTIONS'] = is_options
    _mock_data['']['is_WS'] = is_WS
    _mock_data['']['is_TCP'] = is_TCP
    _mock_data['']['is_UDP'] = is_UDP
    _mock_data['']['is_TLS'] = is_TLS
    _mock_data['']['is_method_in'] = is_method_in
    _mock_data['']['info'] = print
    _mock_data['']['warn'] = print
    _mock_data['']['err'] = print
    _mock_data['registrar']['save'] = location_save
    _mock_data['registrar']['lookup'] = location_lookup
    _mock_data['registrar']['unregister'] = location_unregister
    _mock_data['registrar']['registered'] = location_registered
    _mock_data['siputils']['has_totag'] = siputils_has_to_tag
    _mock_data['tmx']['t_precheck_trans'] = -1
    _mock_data['tm']['t_check_trans'] = -1
    _mock_data['hdr']['append'] = hdr_append
    _mock_data['hdr']['remove'] = hdr_remove
    _mock_data['hdr']['get'] = hdr_get
    _mock_data['hdr']['is_present'] = hdr_present
    _mock_data['dispatcher']['ds_select_dst'] = dispatcher_select_dst
    _mock_data['dispatcher']['ds_select_domain'] = ds_select_domain
    _mock_data['textopsx']['hf_iterator_start'] = hf_iterator_start
    _mock_data['textopsx']['hf_iterator_next'] = hf_iterator_next
    _mock_data['textopsx']['hf_iterator_end'] = hf_iterator_end
    _mock_data['textopsx']['msg_apply_changes'] = textopsx_msg_apply_changes
    if 'nathelper' in _mock_data:
        _mock_data['nathelper']['fix_nated_register'] = fix_nated_register

def hf_iterator_start(name: str):
    global hdr_vals
    global hdr_iterators
    hdr_iterators[name] = {"list": list(hdr_vals.keys()), "index": -1}
    return 1

def hf_iterator_next(name: str):
    global hdr_iterators
    if name not in hdr_iterators:
        print("Iterator not started!")
        assert False
    hdr_iterators[name]["index"] += 1
    print("Comparing index %d to length %d" % (hdr_iterators[name]["index"], len(hdr_iterators[name]["list"])) )
    if hdr_iterators[name]["index"] >= len(hdr_iterators[name]["list"]):
        return -1
    return 1

def hf_iterator_end(name: str):
    global hdr_iterators
    if name not in hdr_iterators:
        print("Iterator not started!")
        assert False
    del hdr_iterators[name]
    return 1

def dispatcher_select_dst(group: int, algo: int):
    pvar_set("$du", "sip:dispatcher_group_" + str(group) + ";transport=TCP")
    return 1

def ds_select_domain(group: int, algo: int):
    print("ds_select_domain called!\n")
    pvar_set("$ru", "sip:" + pvar_get("$rU") + "@dispatcher_group_" + str(group) + ";transport=TCP")
    return 1

def hdr_present(hdr_key: str):
    if hdr_key in hdr_vals and len(hdr_vals[hdr_key]) > 0:
        return 1
    return -1

def hdr_get(hdr_key: str):
    if hdr_key in hdr_vals and len(hdr_vals[hdr_key]) > 0:
        return hdr_vals[hdr_key][0]
    return None

def hdr_remove(hdr_key: str):
    global hdr_vals
    if hdr_key in hdr_vals and len(hdr_vals[hdr_key]) > 0:
        hdr_vals[hdr_key].pop(0)

def hdr_append(hdr: str):
    global hdr_vals
    if not hdr.endswith("\r\n"):
        print("missing end newline! (%s)\n" % str)
        assert False
    result = re.match("^([^:]+):[ ]*(.*)$", hdr.rstrip())
    if result is None:
        print ("Invalid Hdr Format! (%s)" % hdr.rstrip())
        assert False

    print ("Setting hdr! (%s => %s)" % (result.group(1), result.group(2)))

    hdr_key = result.group(1)
    if hdr_key not in hdr_vals:
        hdr_vals[hdr_key] = []
    hdr_vals[hdr_key].append(result.group(2))
    return 1

def location_unregister(table: str, uri: str):
    global registrations
    registrations[table][uri] = None
    return 1


def location_save(table: str, flags: int):
    global registrations
    registrations[table][pvar_get("$fu")] = pvar_get("$ct")
    return 1


def location_lookup(table: str):
    global registrations
    if table not in registrations or pvar_get("$ru") not in registrations[table]:
        return -1

    pvar_set("$ru", registrations[table][pvar_get("$ru")])
    pvar_set("$xavp(ulrcd[0]=>received)", "sip:10.0.0.1;transport=ws;home=127.0.0.1")
    return 1

def location_registered(table: str):
    global registrations
    if table not in registrations or pvar_get("$ru") not in registrations[table]:
        return -1
    return 1

def pvar_gete(key):
    val = pvar_get(key)
    if val is None:
        return ""
    return val

def pvar_getw(key):
    val = pvar_get(key)
    if val is None:
        return "<null>"
    return val

def resolve_xval(key):
    if key.startswith("$"):
        return pvar_get(key)
    return key

SIPURI_REGEX = "^sip:(([^@:]+)@)?([^;?]+)(.*)$"
def get_domain(uri: str):
    result = re.search(SIPURI_REGEX, uri)
    if result is not None:
        return result.group(3)
    print("Parse error for uri (%s)\n" % (uri))
    assert(False)


def get_param(uri: str, param: str):
    print("Looking for param %s in uri %s\n" % (param, uri))
    result = re.search(SIPURI_REGEX, uri)
    if result is None:
        print("Parse error for uri (%s)\n" % (uri))
        assert (False)
    param_list = result.group(4)
    print("Param list of %s\n" % param_list)
    result = re.search(";%s=([^;]+)" % param, param_list)
    if result is None:
        print("parameter (%s) not found\n" % (param))
        return ""
    return result[1]

def get_header_param(header: str, param: str):
    print("Looking for param %s in header %s\n" % (param, header))
    result = re.search("((;[^;<>]+)=([^;<>])+)*$", header)
    if result is None:
        print("Parse error for header (%s)\n" % (header))
        assert (False)
    param_list = result.group(1)
    print("Param list of %s\n" % param_list)
    result = re.search(";%s=([^;]+)" % param, param_list)
    if result is None:
        print("parameter (%s) not found\n" % (param))
        return ""
    return result[1]

def get_user(uri: str):
    result = re.search(SIPURI_REGEX, uri)
    if result is not None:
        return result.group(2)
    print("Parse error for uri (%s)\n" % (uri))
    assert(False)

def set_domain(uri: str, domain: str):
    result = re.search(SIPURI_REGEX, uri)
    if result is not None:
        if result.group(1) is None:
            return "sip:" + domain + result.group(4)
        else:
            return "sip:" + result.group(1) + domain + result.group(4)
    print("Parse error for uri (%s)\n" % (uri))
    assert(False)

def set_user(uri: str, user: str):
    result = re.search(SIPURI_REGEX, uri)
    if result is not None:
        if result.group(1) is None:
            return "sip:" + user + "@" + result.group(3) + result.group(4)
        else:
            return "sip:" + user + "@" + result.group(3) + result.group(4)

    print("Parse error for uri (%s)\n" % (uri))
    assert(False)

def get_user(uri: str):
    result = re.search(SIPURI_REGEX, uri)
    if result is not None:
        return result.group(2)
    print("Parse error for uri (%s)\n" % (uri))
    assert(False)

def get_special_pvar(key):
    global hdr_vals
    global hdr_iterators

    if key == "$fU":
        return get_user(pvar_get("$fu"))
    elif key == "$fd":
        return get_domain(pvar_get("$fu"))
    elif key == "$tU":
        return get_user(pvar_get("$tu"))
    elif key == "$td":
        return get_domain(pvar_get("$tu"))
    elif key == "$rU":
        return get_user(pvar_get("$ru"))
    elif key == "$rd":
        return get_domain(pvar_get("$ru"))

    result = re.search("^\$\((.*)\)$", key)
    if result is not None:
        text_op = result.group(1)

        if text_op.endswith("{uri.user}"):
            key = pvar_get("$(%s)"% text_op[:-len("{uri.user}")])
            return get_user(key)
        if text_op.endswith("{uri.host}"):
            key = pvar_get("$(%s)"% text_op[:-len("{uri.host}")])
            return get_domain(key)
        if text_op.endswith("{nameaddr.uri}"):
            key = pvar_get("$(%s)"% text_op[:-len("{nameaddr.uri}")])
            result = re.search("<(.*)>", key)
            if result is not None:
                return result.group(1)
            else:
                return key
        if re.search("{uri.param,([^}]+)}$", text_op) is not None:
            result = re.search("{uri.param,([^}]+)}$", text_op)
            uri = pvar_get("$(%s)"% text_op[:-len(result.group(0))])
            return get_param(uri, result.group(1))
        if re.search("{param.value,([^}]+)}$", text_op) is not None:
            result = re.search("{param.value,([^}]+)}$", text_op)
            header = pvar_get("$(%s)" % text_op[:-len(result.group(0))])
            return get_header_param(header, result.group(1))
        else:
            key = pvar_get("$%s"% text_op)
            return key



    result = re.search("^\$hdr\((.*)\)$", key)
    if result is not None:
        hdr_key = result.group(1)
        print("Header function found %s!\n" % hdr_key)
        resolved_hdr_key  = resolve_xval(hdr_key)
        if resolved_hdr_key not in hdr_vals or hdr_vals[resolved_hdr_key] is None:
            return None

        if len(hdr_vals[resolved_hdr_key]) > 0:
            print("Header %s has value of %s\n" % (resolved_hdr_key, hdr_vals[resolved_hdr_key]))
            return hdr_vals[resolved_hdr_key][0]

    result = re.search("^\$hfitbody\((.*)\)$", key)
    if result is not None:
        iterator_key = result.group(1)
        print("Header function iterator name found %s!\n" % iterator_key)
        resolved_iterator_key = resolve_xval(iterator_key)
        if resolved_iterator_key not in hdr_iterators:
            return None
        hdr_key = hdr_iterators[resolved_iterator_key]["list"][hdr_iterators[resolved_iterator_key]["index"]]
        if hdr_vals[hdr_key] is None:
            return None
        if len(hdr_vals[hdr_key]) > 0:
            return hdr_vals[hdr_key][0]

    result = re.search("^\$hfitname\((.*)\)$", key)
    if result is not None:
        iterator_key = result.group(1)
        print("Header function iterator name found %s!\n" % iterator_key)
        resolved_iterator_key = resolve_xval(iterator_key)
        if resolved_iterator_key not in hdr_iterators:
            return None
        hdr_index = hdr_iterators[resolved_iterator_key]["index"]
        print("Header function iterator index found %s!\n" % hdr_index)
        hdr_key = hdr_iterators[resolved_iterator_key]["list"][hdr_index]
        return hdr_key

    return None
def pvar_get(key):
    global pvar_vals
    val = get_special_pvar(key)
    if val is not None:
        print("%s => %s\n" % (key, val))
        return val
    if key not in pvar_vals or pvar_vals[key] is None:
        return None
    print("%s => %s\n" % (key, pvar_vals[key]))
    return pvar_vals[key]


# setting vars that modify the message, doesn't impact the value of get
# until the changes are applied
def pvar_set_special(key: str, value: str):
    if key == "$fU":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$fd":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$fu":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$tU":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$td":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$tu":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$rU":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$rd":
        pending_changes.append({"key": key, "value": value})
        return True
    elif key == "$ru":
        pending_changes.append({"key": key, "value": value})
        return True

    return False

def pvar_set(key, value):
    global pvar_vals

    if pvar_set_special(key, value):
        return 1
    pvar_vals[key] = value
    return 1

def pvar_seti(key, value):
    global pvar_vals
    print("Value is of type %s\n" % type(value))
    assert(isinstance(value, int))

    if pvar_set_special(key, value):
        return 1
    pvar_vals[key] = value
    return 1


def pvar_apply_special(key: str, value: str):
    if key == "$fU":
        return pvar_apply("$fu", set_user(pvar_get("$fu"), value))
    elif key == "$fd":
        return pvar_apply("$fu", set_domain(pvar_get("$fu"), value))
    if key == "$tU":
        return pvar_apply("$tu", set_user(pvar_get("$tu"), value))
    elif key == "$td":
        return pvar_apply("$tu", set_domain(pvar_get("$tu"), value))
    elif key == "$rU":
        return pvar_apply("$ru", set_user(pvar_get("$ru"), value))
    elif key == "$rd":
        return pvar_apply("$ru", set_domain(pvar_get("$ru"), value))
    else:
        pvar_apply(key, value)

    return False

def pvar_apply(key: str, value: str):
    pvar_vals[key] = value
    return 1

def textopsx_msg_apply_changes():
    global pending_changes
    for change in pending_changes:
        pvar_apply_special(change["key"], change["value"])
    pending_changes = []

def sht_set(table: str, key: str, value: Union[str,int]):
    global pvar_vals

    pvar_vals["$sht(%s=>%s)" % (table, key)] = value
    return 1


def sht_seti(table: str, key: int, value: Union[str,int]):
    global pvar_vals
    assert(isinstance(value, int))
    pvar_vals["$sht(%s=>%s)" % (table, key)] = value
    return 1


def sht_get(table: str, key: str) -> Union[str,int]:
    val = pvar_get("$sht(%s=>%s)" % (table, key))
    if val is None:
        if table in ["apbanctl", "blocklist", "preblockblocklist"]:
            return 0
    return val


def sht_gete(table: str, key: str) -> Union[str,int]:
    val =  sht_get(table, key)
    if val is None:
        return ""
    return val


def sht_getw(table: str, key: str) -> Union[str,int]:
    val =  sht_get(table, key)
    if val is None:
        return "<null>"
    return val


def sht_inc(table: str, key: str) -> int:
    val = sht_get(table, key)
    if val is None:
        return -255
    val = val + 1
    sht_set(table, key, val)
    return val


def siputils_has_to_tag():
    if pvar_gete("$tt") == "":
        return -1
    return 1


def is_invite():
    if pvar_get("$rm") == "INVITE":
        return True
    return False

def is_kdmq():
    if pvar_get("$rm") == "KDMQ":
        return True
    return False

def is_ack():
    if pvar_get("$rm") == "ACK":
        return True
    return False


def is_bye():
    if pvar_get("$rm") == "BYE":
        return True
    return False


def is_cancel():
    if pvar_get("$rm") == "CANCEL":
        return True
    return False


def is_register():
    if pvar_get("$rm") == "REGISTER":
        return True
    return False


def is_options():
    if pvar_get("$rm") == "OPTIONS":
        return True
    return False

def is_method_in(vmethod: str):
    method = pvar_get("$rm")

    if method == "INVITE" and vmethod.__contains__("I"):
        return True
    elif method == "ACK" and vmethod.__contains__("A"):
        return True
    elif method == "CANCEL" and vmethod.__contains__("C"):
        return True
    elif method == "BYE" and vmethod.__contains__("B"):
        return True
    elif method == "OPTIONS" and vmethod.__contains__("O"):
        return True
    elif method == "REGISTER" and vmethod.__contains__("R"):
        return True
    else:
        return True


def fix_nated_register() -> int:
    pvar_set("$avp(RECEIVED)", "sip:10.0.0.1;transport=ws")
    return 1

def is_WS() -> bool:
    if pvar_get("$Rp") == 8080:
        return True
    return False

def is_TCP() -> bool:
    return pvar_get("$pr") == "TCP"

def is_UDP() -> bool:
    return pvar_get("$pr") == "UDP"

def is_TLS() -> bool:
    return pvar_get("$pr") == "TLS"