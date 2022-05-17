import binascii


def key_to_bin(filename):

    with open(filename, 'r') as f:
        blob = binascii.hexlify("".join(f.read().split('\n')[1:-2]).encode())

    return blob


def format_bin(blob):
    return [blob[ch: ch+72] for ch in range(0, len(blob), 72)]


def write_bin(blob, filename):
    with open(filename, 'w') as f:
        for line in format_bin(blob):
            f.write("b'" + line.decode() + "'\n")

