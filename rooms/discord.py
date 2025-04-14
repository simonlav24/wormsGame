from pypresence import Presence
import time

CLIENT_ID = 1340765041544400989

def update_presence():
    rpc = Presence(CLIENT_ID)
    rpc.connect()

    rpc.update(
        state="In Game",
        details="Is beeing awesome",
        # large_image="game_icon",
        start=time.time()
    )

