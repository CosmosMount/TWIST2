import redis
import json
import socket
import time

# 配置
REDIS_IP = 'localhost'
PJ_IP = '127.0.0.1'
PJ_PORT = 9870
# 机器人关节名称映射 (根据 G1 的 29 个关节定义)
JOINT_NAMES = [f"joint_{i}" for i in range(29)] 

r = redis.Redis(host=REDIS_IP, port=6379, db=0)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Monitoring Redis and sending to PlotJuggler on UDP {PJ_PORT}...")

while True:
    # 1. 读取发送给机器人的指令 (Command)
    cmd_data = r.get("action_body_unitree_g1_with_hands")
    # 2. 读取机器人反馈的实际状态 (Actual) 
    actual_data = r.get("robot_state_qpos") 

    msg = {}
    
    if cmd_data:
        mimic_obs = json.loads(cmd_data)
        # mimic_obs 前 6 位是位姿/速度，第 6 位开始是 29 个关节位置
        cmd_joints = mimic_obs[6:35]
        for name, val in zip(JOINT_NAMES, cmd_joints):
            msg[f"cmd/{name}"] = val
            
    if actual_data:
        actual_joints = json.loads(actual_data)
        for name, val in zip(JOINT_NAMES, actual_joints):
            msg[f"actual/{name}"] = val

    if msg:
        # 发送 JSON 到 PlotJuggler
        packet = json.dumps(msg).encode('utf-8')
        sock.sendto(packet, (PJ_IP, PJ_PORT))

    time.sleep(0.01) # 100Hz 转发