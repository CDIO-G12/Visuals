import select


def send(s, package):
    try:
        package += "\n"
        # print(package)
        s.sendall(package.encode())
    except ValueError:
        s.close()
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
    except ValueError or ConnectionResetError:
        return None
    return None


def is_close(old, new, threshold=2):
    return new < old + threshold and new > old - threshold