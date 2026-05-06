import asyncio
import uvicorn

async def main():
    # Run on port 8005 to satisfy the new docker-compose and EasyPanel default expose
    config1 = uvicorn.Config("app.main:app", host="0.0.0.0", port=8005)
    server1 = uvicorn.Server(config1)

    # Run on port 8000 to satisfy the old custom domain configuration in EasyPanel
    config2 = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000)
    server2 = uvicorn.Server(config2)

    # Start both servers concurrently
    await asyncio.gather(server1.serve(), server2.serve())

if __name__ == "__main__":
    asyncio.run(main())
