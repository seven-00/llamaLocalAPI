import subprocess


class RedisFlusher:
    def __init__(self, cmd: str = "wsl redis-cli FLUSHDB", ping_cmd: str = "wsl redis-cli ping"):
        """Initialize with the default WSL Redis flush command and ping command to check Redis status."""
        self.cmd = cmd
        self.ping_cmd = ping_cmd

    def is_redis_running(self):
        """Check if Redis is running by using the ping command."""
        try:
            process = subprocess.run(
                self.ping_cmd, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Check if the response is "PONG"
            if process.stdout.strip() == "PONG":
                return True
            return False
        except subprocess.CalledProcessError:
            return False

    def restart_redis(self):
        """Restart the Redis service if it's not active."""
        try:
            print("Redis is not running. Attempting to restart...")
            restart_process = subprocess.run(
                "wsl sudo service redis-server start", shell=True, check=True, text=True)
            print("Redis has been started.")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while starting Redis: {e}")
            raise

    def flush(self):
        """Flush the Redis database in the WSL environment."""
        if not self.is_redis_running():
            self.restart_redis()

        try:
            # Proceed to flush Redis after ensuring it is running
            process = subprocess.run(
                self.cmd, shell=True, check=True, text=True)
            print("Redis database in WSL has been flushed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running the WSL command: {e}")
