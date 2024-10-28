import random
import time

import pytest
import requests


class YaUploader:
    def __init__(self):
        pass

    def create_folder(self, path, token):
        """Создание папки YaCloud"""
        time.sleep(1)
        response = requests.put(f'{url_create}?path={path}', headers=self.get_headers(token=token))
        if response.status_code != 201:
            raise Exception("Не удалось создать папку")

    def delete_folder(self, path, token):
        """Удаление папки при наличии YaCloud"""
        response = requests.get(f'{url_create}?path={path}', headers=self.get_headers(token=token))
        if response.status_code != 404:
            response = requests.delete(f'{url_create}?path={path}', headers=self.get_headers(token=token))
            time.sleep(1)
            if response.status_code != 202:
                raise Exception("Не удалось удалить папку")

    def upload_photos_to_yd(self, token, path, url_file, name):
        """Загрузка фотографий в папку на YaCloud"""
        params = {"path": f'/{path}/{name}', 'url': url_file, "overwrite": "true"}
        """Проверка что url существует"""
        if not url_file:
            raise Exception("URL файла недоступен")
        resp = requests.post(f'{url_create}/upload', headers=self.get_headers(token=token), params=params)
        if resp.status_code != 202:
            raise Exception("Не удалось загрузить фотографию")

    def get_headers(self, token):
        """Создание headers для запроса"""
        return {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {token}'}


"""Вынесли переменные для удобства изменения принеобходимости"""
url_create = 'https://cloud-api.yandex.net/v1/disk/resources'
url_dog = 'https://dog.ceo/api/breed'


def get_sub_breeds(breed):
    """Получение списка подпород"""
    res = requests.get(f'{url_dog}/{breed}/list')
    return res.json().get('message', [])


def get_urls(breed, sub_breeds):
    """Получение ссылок для скачивания фотографий пород\подпород"""
    url_images = []
    if sub_breeds:
        for sub_breed in sub_breeds:
            res = requests.get(f'{url_dog}/{breed}/{sub_breed}/images/random')
            res.raise_for_status()
            sub_breed_urls = res.json().get('message')
            url_images.append(sub_breed_urls)
    else:
        res = requests.get(f'{url_dog}/{breed}/images/random')
        res.raise_for_status()
        breed_urls = res.json().get('message')
        url_images.append(breed_urls)
    return url_images


def download_and_upload_photos(breed, token, path):
    """Скачивание и загрузка фотографий на YaCloud"""
    sub_breeds = get_sub_breeds(breed=breed)
    urls = get_urls(breed=breed, sub_breeds=sub_breeds)
    yandex_client = YaUploader()
    yandex_client.delete_folder(path=path, token=token)
    yandex_client.create_folder(path=path, token=token)
    for url in urls:
        part_name = url.split('/')
        name = f"{part_name[-2]}_{part_name[-1]}".replace('/', '_')
        # name = '_'.join([part_name[-2], part_name[-1]])
        yandex_client.upload_photos_to_yd(token=token, path=path, url_file=url, name=name)
    time.sleep(5)


def check_breed(response, breed):
    """Проверка что в полученном ответе ссылки отвечают необходимым требованиям"""
    for item in response.json()['_embedded']['items']:
        assert item['type'] == 'file'
        assert item['name'].startswith(breed)


@pytest.mark.parametrize('breed', ['doberman', random.choice(['bulldog', 'collie'])])
def test_proverka_upload_dog(breed):
    token = 'y0_AgAAAAAAVmrtAADLWwAAAAEV4sNEAABEcqD9LBFJzp7x5vG6aALYKyupuA'
    path = 'test_folder'
    download_and_upload_photos(breed=breed, token=token, path=path)
    # проверка
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'{token}'}
    response = requests.get(f'{url_create}?path=/{path}', headers=headers)
    assert response.json()['type'] == "dir"
    assert response.json()['name'] == path
    sub_breed = get_sub_breeds(breed=breed)
    assert len(response.json()['_embedded']['items']) == 1 if not sub_breed else len(sub_breed)
    check_breed(response=response, breed=breed)
