"""Bitdefender hesabı oluşturma ve bilgileri iletme otomasyonu."""

from __future__ import annotations

import os
import random
import string
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from requests import RequestException, Response
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Bölüm: Ayarlar ve sabitler -------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "8201625011:AAE-VZuG35zPjBQl1QtH6zmdQ-WFMkH9Lrg",
)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8299177286")

BITDEFENDER_SIGNUP_URL = (
    "https://login.bitdefender.com/central/signup.html?lang=tr_TR&redirect_url="
    "https:%2F%2Fcentral.bitdefender.com%2Fdashboard%3Fservice%3Dadd_trial%26code%3D"
    "34291885-79d4-4ba6-bf01-30b0d6bdd0a1%26adobe_mc%3DMCMID%2525253D036193151980370070300843"
    "97437691590274%2525257CMCORGID%2525253D0E920C0F53DA9E9B0A490D45%2525252540AdobeOrg%2525257"
    "CTS%2525253D1698145840%26final_url%3D%2Fdevices"
)
BITDEFENDER_VPN_URL = "https://central.bitdefender.com/vpn"

FULL_NAME_VALUE = "MacroShop"
EMAIL_DOMAIN = "macroshoptr.com.tr"
PASSWORD_LENGTH = 9

WAIT_TIMEOUT = 12
HTTP_TIMEOUT = 10
FALLBACK_POST_SUBMIT_SLEEP = 3

DEFAULT_OUTPUT_FILE = r"C:\Users\EREN\Desktop\Bitdefender Hesap.txt"
OUTPUT_FILE_PATH = Path(os.getenv("BITDEFENDER_OUTPUT_FILE", DEFAULT_OUTPUT_FILE))

XPATHS = {
    "reject_cookies_button": '/html/body/div[6]//div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div/button[2]',
    "full_name_input": '/html/body/ui-view/div/main/div/div[1]/ui-view/form/div[3]/div[1]/input',
    "email_input": '/html/body/ui-view/div/main/div/div[1]/ui-view/form/div[3]/div[2]/input',
    "password_input": '/html/body/ui-view/div/main/div/div[1]/ui-view/form/div[3]/div[3]/div[1]/input',
    "terms_checkbox": '/html/body/ui-view/div/main/div/div[1]/ui-view/form/div[3]/div[5]/div/input',
    "create_account_button": '/html/body/ui-view/div/main/div/div[1]/ui-view/form/div[4]/div/div[2]/button',
}


# Bölüm: Yardımcı fonksiyonlar -----------------------------------------------
def configure_driver() -> WebDriver:
    """Chrome WebDriver örneği hazırla ve döndür."""

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def random_email() -> str:
    """Rastgele 9 harfli (küçük) e-posta adresi üret."""

    random_part = "".join(random.choices(string.ascii_lowercase, k=PASSWORD_LENGTH))
    return f"{random_part}@{EMAIL_DOMAIN}"


def random_password() -> str:
    """En az bir büyük, bir küçük harf ve bir sayı içeren 9 karakterlik şifre üret."""

    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    remaining_chars = "".join(
        random.choices(string.ascii_letters + string.digits, k=PASSWORD_LENGTH - 3)
    )
    password_chars = list(uppercase + lowercase + digit + remaining_chars)
    random.shuffle(password_chars)
    return "".join(password_chars)


def send_telegram_message(message: str) -> Optional[dict]:
    """Telegram botu aracılığıyla mesaj gönder."""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        response: Response = requests.post(url, json=payload, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
    except RequestException as exc:
        print(f"Telegram mesajı gönderilemedi: {exc}")
        return None

    return response.json()


def click_element_via_js(driver: WebDriver, element) -> None:
    """Belirtilen elementi JavaScript ile tıkla."""

    driver.execute_script("arguments[0].click();", element)


def fill_input(wait: WebDriverWait, xpath: str, value: str) -> None:
    """Metin alanını doldur."""

    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.clear()
    element.send_keys(value)


def click_checkbox(driver: WebDriver, wait: WebDriverWait, xpath: str) -> None:
    """Onay kutusunu seçili hale getir."""

    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except TimeoutException:
        print("Kullanım koşulları kutucuğu bulunamadı!")
        return

    click_element_via_js(driver, element)


def click_button(driver: WebDriver, wait: WebDriverWait, xpath: str) -> None:
    """Belirli bir butona tıkla."""

    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except TimeoutException:
        print("'Hesap Oluştur' butonu bulunamadı!")
        return

    click_element_via_js(driver, element)


def dismiss_cookies_popup(driver: WebDriver, wait: WebDriverWait) -> None:
    """Çerez reddetme penceresini kapat."""

    try:
        element = wait.until(
            EC.element_to_be_clickable((By.XPATH, XPATHS["reject_cookies_button"]))
        )
    except TimeoutException:
        print("Çerez reddetme butonu bulunamadı!")
        return

    element.click()


def wait_for_post_signup_transition(driver: WebDriver, wait: WebDriverWait) -> None:
    """Form gönderimi sonrası yönlendirmeyi bekle."""

    try:
        wait.until(EC.url_contains("central.bitdefender.com"))
    except TimeoutException:
        time.sleep(FALLBACK_POST_SUBMIT_SLEEP)


def wait_for_vpn_page(wait: WebDriverWait) -> None:
    """VPN sayfasının yüklenmesini URL üzerinden doğrula."""

    try:
        wait.until(EC.url_contains("/vpn"))
    except TimeoutException:
        print("VPN sayfası beklenen sürede yüklenmedi.")


def save_credentials(email: str, password: str, file_path: Path) -> None:
    """E-posta ve şifreyi belirtilen dosyaya kaydet."""

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as file:
            file.write(f"{email} - {password}\n")
    except OSError as exc:
        print(f"Hesap bilgileri kaydedilemedi: {exc}")
    else:
        print(f"Hesap bilgileri '{file_path}' dosyasına kaydedildi.")


def report_success(email: str, password: str) -> None:
    """Hesap oluşturma bilgilerini yazdır, dosyaya kaydet ve Telegram'a gönder."""

    print(f"Hesap oluşturuldu! E-posta: {email} | Şifre: {password}")

    save_credentials(email, password, OUTPUT_FILE_PATH)

    current_date = datetime.now().strftime("%d/%m/%Y")
    telegram_message = (
        f"Bitdefender Hesap - [{current_date}]\n\nE-posta: {email} | Şifre: {password}"
    )
    if send_telegram_message(telegram_message) is not None:
        print("Hesap bilgileri Telegram'a gönderildi.")


# Bölüm: Ana akış -------------------------------------------------------------
def main() -> None:
    """Bitdefender hesap oluşturma iş akışını çalıştır."""

    email = random_email()
    password = random_password()

    try:
        driver = configure_driver()
    except WebDriverException as exc:
        print(f"WebDriver başlatılamadı: {exc}")
        return

    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        driver.get(BITDEFENDER_SIGNUP_URL)
        dismiss_cookies_popup(driver, wait)
        fill_input(wait, XPATHS["full_name_input"], FULL_NAME_VALUE)
        fill_input(wait, XPATHS["email_input"], email)
        fill_input(wait, XPATHS["password_input"], password)
        click_checkbox(driver, wait, XPATHS["terms_checkbox"])
        click_button(driver, wait, XPATHS["create_account_button"])
        wait_for_post_signup_transition(driver, wait)
        driver.get(BITDEFENDER_VPN_URL)
        wait_for_vpn_page(wait)
        report_success(email, password)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
