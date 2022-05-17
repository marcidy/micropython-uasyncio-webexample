import os

dirs = [
    "./websockets",
    "./scripts",
    "./www",
    "./certs",
    "./http",
    "./examples",
    "./examples/ws_client_dupterm",
    "./test",
]

for d in dirs:
    try:
        os.mkdir(d)
    except Exception:
        pass
