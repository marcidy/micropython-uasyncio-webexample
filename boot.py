import webrepl
from controllers import net


net.active(1)
net.connect("titopuente", "testmatt")
webrepl.start(password="test")
