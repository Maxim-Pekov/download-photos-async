import os
import logging
import asyncio
import aiofiles

from aiohttp import web

SIZE = 100_000
logger = logging.getLogger(__name__)


async def archive(request):
    hash = request.match_info.get('archive_hash', "Anonymous")
    files_path = os.path.join('test_photos', hash)
    response = web.StreamResponse()
    if not os.path.exists(files_path):
        logger.info(f'There are no photos in the directory "{files_path}"')
        return web.HTTPNotFound(reason=404, text='Ошибка 404, папка с фотографиями удалена')
    proc = await asyncio.create_subprocess_exec(
        "zip", "-r", "-", ".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=files_path)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)
    chunk_count = 1
    try:
        while not proc.stdout.at_eof():
            x = await proc.stdout.read(SIZE)
            await response.write(x)
            logger.info(f'Sending archive chunk №{chunk_count} ({SIZE} bytes)')
            chunk_count += 1
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info(f'Download was interrupted')
        raise
    finally:
        proc.communicate()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%d-%m-%Y %I:%M:%S %p',
                        level=logging.INFO)
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}', archive),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app, port=8000)
