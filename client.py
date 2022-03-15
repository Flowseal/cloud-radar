import socketio
import time
import struct
import pymem, requests, pymem.process

sio = socketio.Client()
url = 'https://raw.githubusercontent.com/frk1/hazedumper/master/csgo.json'
response = requests.get(url).json()
dwClientState = int(response['signatures']['dwClientState'])
dwClientState_Map = int(response['signatures']['dwClientState_Map'])
dwClientState_PlayerInfo = int(response["signatures"]["dwClientState_PlayerInfo"])
dwEntityList = int(response["signatures"]["dwEntityList"])
m_iTeamNum = int(response["netvars"]["m_iTeamNum"])
m_iHealth = int(response["netvars"]["m_iHealth"])
m_vecOrigin = int(response["netvars"]["m_vecOrigin"])
m_angEyeAnglesY = int(response["netvars"]["m_angEyeAnglesY"])
m_bDormant = int(response["signatures"]["m_bDormant"])
dwGameRulesProxy = int(response["signatures"]["dwGameRulesProxy"])
dwLocalPlayer = int(response["signatures"]["dwLocalPlayer"])
dwRadarBase = int(response["signatures"]["dwRadarBase"])

pm = pymem.Pymem("csgo.exe")
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
engine = pymem.process.module_from_name(pm.process_handle, "engine.dll").lpBaseOfDll

def read_vec3(handle, address):
    bytes = handle.read_bytes(address, struct.calcsize("3f"))
    bytes = struct.unpack("3f", bytes)
    return bytes[0], bytes[1]


def background_thread():
    dormant_time = {}
    while not sio.connected:
        sio.sleep(0.5)

    while True:
        data = {}
        data['map'] = ''
        data['players'] = []
        data['smokes'] = []
        data['bomb'] = {}

        #  Get local palyer instance
        local_player = pm.read_int(client + dwLocalPlayer)
        if not local_player:
            sio.sleep(1.0)
            continue

        #  Get client state
        client_state = pm.read_uint(engine + dwClientState)
        if not client_state:
            sio.sleep(1.0)
            continue

        #  Read map name from client state
        data['map'] = pm.read_string(client_state + dwClientState_Map)

        #  Get player info table from client state
        userinfo = pm.read_uint(client_state + dwClientState_PlayerInfo)
        if not userinfo:
            sio.sleep(1.0)
            continue

        #  Read items from player info table
        items = pm.read_int(pm.read_int(userinfo + 0x40) + 0xC)
        if not items:
            sio.sleep(1.0)
            continue

        for i in range(65):
            try:
                #  Create entity instance
                entity = pm.read_int(client + dwEntityList + i * 0x10)

                if entity:
                    #  Lifestate check
                    alive = pm.read_int(entity + m_iHealth) > 0
                    if not alive:
                        continue

                    #  Team check
                    team = pm.read_int(entity + m_iTeamNum)
                    local_team = pm.read_int(local_player + m_iTeamNum)
                    if team == local_team:
                        continue

                    #  Collect player info data
                    struct_info = pm.read_int(items + 0x28 + (i * 0x34))
                    nickname = pm.read_string(struct_info + 0x0010)
                    steam_id = pm.read_string(struct_info + 0x0094)

                    #  Record player for dormant checks
                    if (nickname+steam_id) not in dormant_time:
                        dormant_time[nickname + steam_id] = 0

                    #  Dormant checks
                    dormant = pm.read_bool(entity + m_bDormant)
                    if not dormant:
                        dormant_time[nickname + steam_id] = time.time()
                    else:
                        if time.time() - dormant_time[nickname+steam_id] >= 3.0:
                            continue

                    #  Dormant alpha, angle and origin
                    dormant_alpha = int((3.0 - (time.time() - dormant_time[nickname+steam_id])) * 85)
                    angle = pm.read_float(entity + m_angEyeAnglesY)
                    x, y = read_vec3(pm, entity + m_vecOrigin)

                    player_data = {"nickname": nickname, "team": team, "x": x, "y": y, "angle": angle, "dormant": dormant_alpha}
                    data['players'].append(player_data)
            except Exception as e:
                continue
    
        sio.emit('data_client', data)
        sio.sleep(0.01)


if __name__ == '__main__':
    # threading.Thread(target=background_thread).start()
    sio.connect('http://127.0.0.1:2121/')
    sio.start_background_task(background_thread)
    # sio.wait()