import os
import json
import httpx
import pathlib
from bs4 import BeautifulSoup
from typing import List, Dict


from .folder_manager import verify_dir


class NSWICACInvestigation:
    def __init__(
        self,
        title: str,
        year: int,
        status: bool,
        description: str,
        media_releases: List[Dict[str, str]],
        transcripts: List[Dict[str, str]],
        exhibits: List,
        misc_docs: List):
            self.title = title
            self.year = year
            self.status = status
            self.description = description
            self.media_releases = media_releases
            self.transcripts = transcripts
            self.exhibits = exhibits
            self.misc_docs = misc_docs


async def download(url, output_dir):
    status_dict = {
        'Current': True,
        'Currrent': True,  # There is a typo on some of the pages
        'Completed': False
    }
    async with httpx.AsyncClient() as client:
        main_page = await client.get(url)

    page_data = BeautifulSoup(main_page, 'lxml').find('article')
    title = page_data.find('h1').text

    panel = page_data.find('div', {'class': 'investigation-panel'}) \
        .find('div', {'class': 'pull-left investigation-info'})
    year = int(panel.find('span').contents[1][3:])
    status = status_dict[panel.find_all('span')[-1].contents[1][2:]]
    description = panel.findNext('p').findNext('p').text.strip()
    misc_docs = [{'title': x.text.strip(), 'url': x['href']} for x in page_data.find_all('a', {'class': 'document pdf', 'target': '_blank'})]

    content = page_data.find('section', {'id': 'investigation-content'})
    media_releases = [{'title': x.text.strip(), 'url': x['href']} for x in content.find('article', {'id': 'media'}).find_all('a')]

    transcripts = []
    for row in content.find('table', {'id': 'tableDocList'}).find_all('tr')[1:]:
        transcript_url = row.find('a')['href']
        transcript_title = f'{row.find_all("td")[-2].text.strip()} - {row.find("a").text.strip()}'
        transcripts.append({
            'title': transcript_title,
            'url': transcript_url
        })

    exhibits = [{'title': x.text.strip(), 'url': x['href']} for x in content.find('article', {'id': 'exhibits'}).find_all('a')]
    investigation = NSWICACInvestigation(
        title=title,
        year=year,
        status=status,
        description=description,
        media_releases=media_releases,
        transcripts=transcripts,
        exhibits=exhibits,
        misc_docs=misc_docs
    )
    await save_files(investigation, output_dir)


async def save_files(data: NSWICACInvestigation, output_dir):
    invs_output_dir = pathlib.PurePath(output_dir, pathlib.Path(f'{data.year} - {data.title}'))
    verify_dir(invs_output_dir)

    with open(os.path.join(invs_output_dir, 'manifest.json'), 'w') as f:
        f.write(json.dumps(data.__dict__, indent=2))


    transcripts_dir = pathlib.PurePath(invs_output_dir, pathlib.Path('transcripts'))
    verify_dir(transcripts_dir)
    for transcript in data.transcripts:
        filename = transcript['title'] + '.pdf'
        filepath = os.path.join(transcripts_dir, filename)
        if not os.path.isfile(filepath):
            with open(filepath, 'wb') as f:
                f.write(httpx.get(transcript['url']).content)
                print(f"Downloaded {filepath}")

    media_releases_dir = pathlib.PurePath(invs_output_dir, pathlib.Path('releases'))
    verify_dir(media_releases_dir)
    for index, media_release in enumerate(data.media_releases):
        release_content = BeautifulSoup(httpx.get(media_release['url']), 'lxml').find('article').text.strip()
        filename = f'{index}.txt'
        filepath = os.path.join(media_releases_dir, filename)
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                f.write(release_content)
                print(f"Downloaded {filepath}")


    exhibits_dir = pathlib.PurePath(invs_output_dir, pathlib.Path('exhibits'))
    verify_dir(exhibits_dir)
    for exhibit in data.exhibits:
        filename = exhibit['title'] + '.pdf'
        filepath = os.path.join(exhibits_dir, filename)
        if not os.path.isfile(filepath):
            with open(filepath, 'wb') as f:
                f.write(httpx.get(exhibit['url']).content)
                print(f"Downloaded {filepath}")
