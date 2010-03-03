'''
Quick and dirty code for locking down access to specific IP addresses.
Add items to APROVED_IPS, import ip_in_whitelist to views.py, and add
a check to each view to control access. I.e.:

if not ip_in_whitelist(request.META['REMOTE_ADDR']):
    return Http404

'''
from kindle.utils.ipaddr import IPv4

APPROVED_IPS = (
    '127.0.0.1',
)

def ip_in_whitelist(request_ip):
    # the long int version of the ip address
    user_ip = IPv4(request_ip).ip

    for whitelist_ip in APPROVED_IPS:
        w_ip = IPv4(whitelist_ip)

        # if ip == the network's base IP (which is the case if we're giving it a straight IP with
        # no range suffix) OR if ip is within the subnet for the given range
        # (a machine's address in a subnet can't ever be the broadcast address so it's < not <=)
        if (user_ip == w_ip.network) or ((user_ip >= w_ip.network) and (user_ip < w_ip.broadcast)):
            # if match, return true (short circuits the rest of the function)
            return True
    return False
