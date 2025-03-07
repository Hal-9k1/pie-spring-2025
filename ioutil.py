from struct import pack

def write_flexible_string(buf, string):
    if string == None:
        buf.append(0)
    else:
        buf.append(min(255, len(string)))
        buf.extend(string.encode('ascii'))
        if len(string) > 255:
            buf.append(0)

def write_double(buf, double):
    buf.extend(pack('!d', double))
