import asyncio

async def task(number):
    print('task', number)
    await asyncio.sleep(5)
    print('task_end', number)

async def main():
    await task(1)
    await asyncio.gather( task(2) ) # รอจนเสร็จ
    asyncio.gather( task(3) ) # ไม่รอจนเสร็จ
    await task(4)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())