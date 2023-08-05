import os
import logging
import asyncio
import aiofiles
import argparse

from aiohttp import web


DOWNLOAD_DELAY = 0
CHUNK_SIZE = 100_000
logger = logging.getLogger(__name__)


async def get_photo_archive(request):
    archive_hash = request.match_info.get('archive_hash')
    files_path = os.path.join(app.args.photo_folder, archive_hash)
    response = web.StreamResponse()
    if not os.path.exists(files_path):
        logger.info(f'There are no photos in the directory "{files_path}"')
        return web.HTTPNotFound(
            reason=404,
            text='Ошибка 404, папка с фотографиями удалена')
    process = await asyncio.create_subprocess_exec(
        "zip", "-r", "-", ".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=files_path)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = ('attachment; '
                                               'filename="photos.zip"')
    await response.prepare(request)
    chunk_count = 1
    try:
        while not process.stdout.at_eof():
            archive_chunk = await process.stdout.read(CHUNK_SIZE)
            await response.write(archive_chunk)
            logger.info(f'Sending archive chunk №{chunk_count} ({CHUNK_SIZE} bytes)')
            chunk_count += 1
            await asyncio.sleep(DOWNLOAD_DELAY)
    except asyncio.CancelledError:
        logger.info('Download was interrupted')
        raise
    finally:
        if not process.stdout.at_eof():
            process.kill()
            process.communicate()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    def create_parser():
        parser = argparse.ArgumentParser(
            description='скачивает фотографии одним архивом ')
        parser.add_argument(
            '-l', '--is_logging',
            action='store_true',
            help='Что бы включить логирование, укажите этот параметр')
        parser.add_argument(
            '-d', '--download_delay',
            action='store_true',
            help='Укажите флаг, чтобы включить задержку скачивания в 1 сек.')
        parser.add_argument(
            '-f', '--photo_folder',
            help='путь к каталогу с фотографиями',
            default='test_photos', type=str, nargs='?')
        return parser
    parser = create_parser()

    app = web.Application()
    app.args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d-%m-%Y %I:%M:%S %p',
        level=logging.INFO)
    if not app.args.is_logging:
        logging.disable('INFO')

    if app.args.download_delay:
        DOWNLOAD_DELAY = 1

    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}', get_photo_archive),
        web.get('/archive/{archive_hash}/', get_photo_archive),
    ])
    web.run_app(app)
