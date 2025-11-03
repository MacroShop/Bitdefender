from __future__ import annotations

import os
import random
import string
import time
from typing import Final

import requests
from requests import Response
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Konfigürasyon Değerleri
TELEGRAM_BOT_TOKEN: Final[str] = "8201625011:AAE-VZuG35zPjBQl1QtH6zmdQ-WFMkH9Lrg"
TELEGRAM_CHAT_ID: Final[str] = "8299177286"

BITDEFENDER_SIGNUP_URL: Final[str] = (
    "https://login.bitdefender.com/central/signup.html?lang=tr_TR&redirect_url=https:%2F%2Fcentral.bitdefender.com%2Fdashboard%3Fservice%3Dadd_trial%26code%3D34291885-79d4-4ba6-bf01-30b0d6bdd0a1%26adobe_mc%3DMCMID%2525253D03619315198037007030084397437691590274%2525257CMCORGID%2525253D0E920C0F53DA9E9B0A490D45%2525252540AdobeOrg%2525257CTS%2525253D1698145840%26final_url%3D%2Fdevices"
)
BITDEFENDER_VPN_URL: Final[str] = "https://central.bitdefender.com/vpn"

FULL_NAME_VALUE: Final[str] = "MacroShop"
EMAIL_DOMAIN: Final[str] = "macroshoptr.com.tr"

PAGE_WAIT_TIMEOUT: Final[int] = 15
ACCOUNT_CREATION_WAIT_SECONDS: Final[int] = 3
VPN_URL_KEYWORD: Final[str] = "/vpn"

CREDENTIALS_FILE_PATH: Final[str] = os.getenv(
    "BITDEFENDER_CREDENTIALS_PATH", r"C:\Users\EREN\Desktop\Bitdefender Hesap.txt"
)

XPATHS: Final[dict[str, str]] = {
    "reject_cookies_button": "/html/body/div[6]//div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div/button[2]",
    "full_name": "/html/body/div/div/main/div/div/div[1]/form/div[3]/div[1]/input",
    "email": "/html/body/div/div/main/div/div/div[1]/form/div[3]/div[2]/input",
    "password": "/html/body/div/div/main/div/div/div[1]/form/div[3]/div[3]/div[2]/input",
    "terms_checkbox": "/html/body/div/div/main/div/div/div[1]/form/div[3]/div[5]/div/input",
    "create_account_button": "/html/body/div/div/main/div/div/div[1]/form/div[4]/div/div[1]/button",
}


def send_telegram_message(message: str) -> None:
    """Telegram kanalına mesaj gönderir."""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        response: Response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Telegram mesajı gönderilemedi: {exc}")


def create_webdriver() -> WebDriver:
    """Chrome WebDriver örneği oluşturur."""

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def wait_for_element(driver: WebDriver, xpath: str) -> None:
    """Belirtilen XPath'e sahip öğenin yüklenmesini bekler."""

    WebDriverWait(driver, PAGE_WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )


def wait_and_send_keys(driver: WebDriver, xpath: str, value: str) -> None:
    """Belirtilen alana değer yazar."""

    element = WebDriverWait(driver, PAGE_WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    element.clear()
    element.send_keys(value)


def click_element(driver: WebDriver, xpath: str) -> None:
    """Belirtilen öğeye tıklar."""

    element = WebDriverWait(driver, PAGE_WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    element.click()


def click_with_script(driver: WebDriver, xpath: str) -> None:
    """JavaScript kullanarak öğeye tıklar."""

    element = WebDriverWait(driver, PAGE_WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    driver.execute_script("arguments[0].click();", element)


def reject_cookies(driver: WebDriver) -> None:
    """Çerez reddetme penceresini kapatır."""

    try:
        click_element(driver, XPATHS["reject_cookies_button"])
    except TimeoutException:
        print("Çerez reddetme butonu bulunamadı!")


def fill_signup_form(driver: WebDriver, email: str, password: str) -> None:
    """Üyelik formunu doldurur."""

    wait_and_send_keys(driver, XPATHS["full_name"], FULL_NAME_VALUE)
    wait_and_send_keys(driver, XPATHS["email"], email)
    wait_and_send_keys(driver, XPATHS["password"], password)
    try:
        click_with_script(driver, XPATHS["terms_checkbox"])
    except TimeoutException:
        print("Kullanım koşulları kutucuğu bulunamadı!")


def submit_signup_form(driver: WebDriver) -> None:
    """Kayıt formunu gönderir."""

    try:
        click_with_script(driver, XPATHS["create_account_button"])
    except TimeoutException:
        print("'Hesap Oluştur' butonu bulunamadı!")


def random_email(length: int = 9) -> str:
    """Rastgele e-posta adresi üretir."""

    random_part = "".join(random.choices(string.ascii_lowercase, k=length))
    return f"{random_part}@{EMAIL_DOMAIN}"


def random_password(length: int = 9) -> str:
    """Rastgele, güvenlik gereksinimlerini karşılayan şifre üretir."""

    if length < 3:
        raise ValueError("Şifre uzunluğu en az 3 olmalıdır.")

    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    remaining_chars = random.choices(string.ascii_letters + string.digits, k=length - 3)

    password_chars = [uppercase, lowercase, digit, *remaining_chars]
    random.shuffle(password_chars)
    return "".join(password_chars)


def save_credentials(email: str, password: str, file_path: str) -> None:
    """Oluşturulan bilgileri dosyaya kaydeder."""

    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(f"{email} - {password}\n")
    except OSError as exc:
        print(f"Hesap bilgileri dosyaya kaydedilemedi: {exc}")
    else:
        print(f"Hesap bilgileri '{file_path}' dosyasına kaydedildi.")


def notify_credentials(email: str, password: str) -> None:
    """E-posta ve parolayı çıktı olarak verir ve Telegram üzerinden iletir."""

    print(f"Hesap oluşturuldu! E-posta: {email} | Şifre: {password}")

    current_date = time.strftime("%d/%m/%Y")
    telegram_message = (
        f"Bitdefender Hesap - [{current_date}]\n\nE-posta: {email} | Şifre: {password}"
    )
    send_telegram_message(telegram_message)
    print("Hesap bilgileri Telegram'a gönderildi.")


def main() -> None:
    """Ana çalışma akışını yönetir."""

    email = random_email()
    password = random_password()

    driver = create_webdriver()
    try:
        driver.get(BITDEFENDER_SIGNUP_URL)
        wait_for_element(driver, XPATHS["full_name"])

        reject_cookies(driver)
        fill_signup_form(driver, email, password)
        submit_signup_form(driver)
        time.sleep(ACCOUNT_CREATION_WAIT_SECONDS)

        driver.get(BITDEFENDER_VPN_URL)
        WebDriverWait(driver, PAGE_WAIT_TIMEOUT).until(EC.url_contains(VPN_URL_KEYWORD))
    finally:
        driver.quit()

    save_credentials(email, password, CREDENTIALS_FILE_PATH)
    notify_credentials(email, password)


if __name__ == "__main__":
    main()
