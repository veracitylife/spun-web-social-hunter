import asyncio
import signal


class Worker:
    def __init__(self) -> None:
        self._running = True

    def stop(self, *_args: object) -> None:
        self._running = False

    async def run(self) -> None:
        while self._running:
            await asyncio.sleep(5)


async def main() -> None:
    worker = Worker()
    signal.signal(signal.SIGTERM, worker.stop)
    signal.signal(signal.SIGINT, worker.stop)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

