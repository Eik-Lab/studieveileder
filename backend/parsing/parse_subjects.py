from bs4 import BeautifulSoup
import requests
import os

def fetch_subjects(filename="subjects.txt", output_dir="subject_contents"):
    """
    Fetch and save plain text content for each subject from NMBU website.
    Tries {code} and {code}-0 if the first fails.
    """
    base_url = "https://www.nmbu.no/emne/"
    os.makedirs(output_dir, exist_ok=True)
    failed_subjects = []

    with open(filename, "r") as file:
        next(file)
        subject_codes = [line.strip() for line in file.readlines()[::4]]

    for code in subject_codes:
        urls = [f"{base_url}{code}", f"{base_url}{code}-0"]
        success = False

        for url in urls:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for s in soup(["script", "style"]):
                    s.extract()
                text = soup.get_text(separator="\n", strip=True)

                filepath = os.path.join(output_dir, f"{code}.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)

                print(f"Saved: {code} ({url})")
                success = True
                break

        if not success:
            print(f"Failed: {code}")
            failed_subjects.append(code)

    with open(os.path.join(output_dir, "failed_subjects.txt"), "w") as f:
        for failed_code in failed_subjects:
            f.write(f"{failed_code}\n")

if __name__ == "__main__":
    fetch_subjects()
