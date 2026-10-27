import os
import requests

def download_valid_inpho_owl():

    url = "https://www.inphoproject.org/owl/db-arch_20200103.owl"
    target_filename = "inpho.owl"
    
    print(f"Запуск скачивания онтологии InPhO...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        file_size = len(response.content)
        if file_size == 0:
            print("Ошибка: Сервер вернул пустой файл. Попробуйте позже.")
            return False

        with open(target_filename, "wb") as f:
            f.write(response.content)
            
        print(f" Успешно! Файл сохранен как: {os.path.abspath(target_filename)}")
        print(f"Размер файла: {file_size / 1024:.2f} KB (файл валиден и готов к работе)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании файла: {e}")
        return False

if __name__ == "__main__":
    download_valid_inpho_owl()
