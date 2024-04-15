import asyncio

from WPP_Whatsapp import Create

path = r"C:\Users\ammar\Whatsapp Pro\123.txt"

Number = {}

with open(path, 'r') as re:
    for i in re.readlines():
        Number[Number.__len__() + 1] = {
            "number": str(i).replace("+", "").strip(),
            "state": None
        }


async def checker(client, index):
    num = Number[index]["number"]
    return await client.checkNumberStatus_(num.rstrip())
    # Number[index]["state"] = data.get("numberExists")


async def main():
    # start client with your session name
    your_session_name = "test"
    creator = Create(session=your_session_name, browser="chrome")

    client = await creator.start_()
    # Now scan Whatsapp Qrcode in browser

    # check state of login
    if creator.state != 'CONNECTED':
        raise Exception(creator.state)
    print("- Start")
    tasks = []
    for index in Number:
        print(index)
        task = asyncio.create_task(checker(client, index))
        tasks.append(task)
    print("- Wait All Finish")
    # Wait All Finish
    results = await asyncio.gather(*tasks)
    print(results)


asyncio.run(main())
