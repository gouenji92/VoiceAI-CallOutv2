from dp_agent.agent import Agent
from dp_agent.channel import ZMQChannel
from agent.skill import CallbotSkill

agent = Agent(
    skills=[CallbotSkill(name="callbot_skill")],
    in_channel=ZMQChannel(port=4242),
    out_channel=ZMQChannel(port=4243),
)

print("--- DEEPPAVLOV AGENT SERVER DANG CHAY TREN CONG 4242 ---")
print("--- Nhan Ctrl+C de dung ---")
agent.run()