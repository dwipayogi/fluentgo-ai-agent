import sys
from livekit.agents import cli, WorkerOptions
from agent import entrypoint, prewarm

if __name__ == "__main__":
    room_name = sys.argv[1] if len(sys.argv) > 1 else "default-room"
    cli.run_app(
        WorkerOptions(
            auto_join={"room_name": room_name},
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="translator-bot",
        )
    )
