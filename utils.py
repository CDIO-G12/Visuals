import select


def send(s, package, add_new_line = True):
    try:
        if add_new_line:
            package += "\n"

        try:
            encoded = package.encode()
        except AttributeError:
            encoded = package

        s.sendall(encoded)
    except ValueError:
        s.close()
        return False
    except ConnectionResetError:
        return False
    return True


def check_data(s):
    try:
        readable = [s]
        r, w, e = select.select(readable, [], [], 0)
        for rs in r:  # iterate through readable sockets
            # read from a client
            data = rs.recv(1024)
            if not data:
                readable.remove(rs)
                rs.close()
            else:
                return data
    except ValueError:
        return None
    except ConnectionResetError:
        return None
    return None


def check_for_ball(hsv):
    if (hsv[1] <= 40 and hsv[2] >= 65) or (50 >= hsv[0] >= 20 and hsv[1] >= 60 and hsv[2] >= 80):
        return True
    else:
        return False


def is_close(old, new, threshold=2):
    return old + threshold > new > old - threshold
