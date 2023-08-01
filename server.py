import os

import asyncio
import aiofiles
from aiohttp import web


async def archive(request):
    hash = request.match_info.get('archive_hash', "Anonymous")
    files_path = os.path.join('test_photos', hash)
    response = web.StreamResponse()
    proc = await asyncio.create_subprocess_exec(
        "zip", "-r", "-", ".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=files_path)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)
    while not proc.stdout.at_eof():
        x = await proc.stdout.read(100)
        await response.write(x)
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
