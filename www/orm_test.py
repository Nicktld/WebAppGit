import orm
from models import User, Blog, Comment
import asyncio

async def test():
    await orm.create_pool(user='webapp', password='tangledong1994', db='awesome', loop=loop)

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    await u.save()
    await orm.close_pool()

loop = asyncio.get_event_loop()

loop.run_until_complete(test())
