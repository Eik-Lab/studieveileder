from bs4 import BeautifulSoup
import requests
import os

def fetch_single_subject(subject_code, output_dir="subject_contents"):
    """
    fetch data from url and save to a text file
    """
    url = f"https://www.nmbu.no/studenter/velkommen-som-nettstudent"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        for s in soup(["script", "style"]):
            s.extract()

        text = soup.get_text(separator="\n", strip=True)

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{subject_code}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Saved: {subject_code}")
    else:
        print(f"Failed: {subject_code} (status {response.status_code})")

if __name__ == "__main__":
    test_subject_code = "velkommen-som-nettstudent"
    fetch_single_subject(test_subject_code, output_dir="new_doc")