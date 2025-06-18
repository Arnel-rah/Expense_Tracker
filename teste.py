import requests
import re
from bs4 import BeautifulSoup
import os
import time
from colorama import init, Fore, Style

init(autoreset=True)

def slowprint(text, delay=0.005):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    green = Fore.GREEN + Style.BRIGHT
    print(green + r"""
██╗    ██╗███████╗██████╗ ███████╗██╗  ██╗███████╗██████╗  █████╗ ██████╗ ███████╗
██║    ██║██╔════╝██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝
██║ █╗ ██║█████╗  ██████╔╝█████╗  █████╔╝ █████╗  ██████╔╝███████║██║  ██║█████╗  
██║███╗██║██╔══╝  ██╔═══╝ ██╔══╝  ██╔═██╗ ██╔══╝  ██╔═══╝ ██╔══██║██║  ██║██╔══╝  
╚███╔███╔╝███████╗██║     ███████╗██║  ██╗███████╗██║     ██║  ██║██████╔╝███████╗
 ╚══╝╚══╝ ╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═════╝ ╚══════╝

🌐 Dark Web Scraper - Hacker Theme
💻 Created by Arnel | github.com/Arnel-rah
""")

def get_website_content(url):
    print(Fore.YELLOW + "\n[~] Connexion au site...")
    try:
        response = requests.get(url)
        return response.text
    except:
        print(Fore.RED + "❌ Erreur de connexion.")
        return None

def scrape_emails(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def scrape_phones(text):
    return re.findall(r"\+?\d[\d\s\-]{8,}", text)

def scrape_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('/'):
            href = base_url + href
        elif not href.startswith('http'):
            continue
        links.add(href)
    return links

def scrape_social_links(links):
    social_sites = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'tiktok.com']
    return [link for link in links if any(site in link for site in social_sites)]

def main():
    banner()
    url = input(Fore.CYAN + "\n[+] Entrer l'URL à scanner (avec https://) : ").strip()
    if not url.startswith("http"):
        print(Fore.RED + "❌ L'URL doit commencer par http:// ou https://")
        return

    html = get_website_content(url)
    if not html:
        return

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()

    slowprint(Fore.GREEN + "\n[!] Lancement du scraping...")

    emails = list(set(scrape_emails(text)))
    phones = list(set(scrape_phones(text)))
    links = list(scrape_links(html, url))
    socials = list(scrape_social_links(links))

    print(Fore.GREEN + "\n📧 Emails trouvés :")
    if emails:
        for email in emails:
            print(Fore.LIGHTGREEN_EX + " -", email)
    else:
        print(Fore.RED + " - Aucun email trouvé.")

    print(Fore.GREEN + "\n📱 Numéros de téléphone :")
    if phones:
        for phone in phones:
            print(Fore.LIGHTGREEN_EX + " -", phone)
    else:
        print(Fore.RED + " - Aucun numéro trouvé.")

    print(Fore.GREEN + f"\n🔗 Liens trouvés ({len(links)}):")
    if links:
        print(Fore.LIGHTBLACK_EX + f" - {len(links)} liens collectés.")
    else:
        print(Fore.RED + " - Aucun lien trouvé.")

    print(Fore.GREEN + "\n🌐 Réseaux sociaux :")
    if socials:
        for social in socials:
            print(Fore.LIGHTCYAN_EX + " -", social)
    else:
        print(Fore.RED + " - Aucun réseau social trouvé.")

    save = input(Fore.YELLOW + "\n💾 Sauvegarder les résultats ? (y/n): ").lower()
    if save == 'y':
        with open("🕶️_resultats_arnel_hacker.txt", "w", encoding="utf-8") as f:
            f.write("Emails:\n" + '\n'.join(emails) + "\n\n")
            f.write("Phones:\n" + '\n'.join(phones) + "\n\n")
            f.write("Socials:\n" + '\n'.join(socials) + "\n\n")
            f.write("Links:\n" + '\n'.join(links) + "\n\n")
        print(Fore.GREEN + "✅ Fichier enregistré dans '🕶️_resultats_arnel_hacker.txt'")

if __name__ == "__main__":
    main()
