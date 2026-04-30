import sys
import os
import shutil

from config import PUBLIC_HOLIDAYS_ICS_DIR, SCHOOL_HOLIDAYS_ICS_DIR

# Check if ICS dirs exists
if (
    not os.path.exists(PUBLIC_HOLIDAYS_ICS_DIR)
    or not os.path.isdir(PUBLIC_HOLIDAYS_ICS_DIR)
    or not os.path.exists(SCHOOL_HOLIDAYS_ICS_DIR)
    or not os.path.isdir(SCHOOL_HOLIDAYS_ICS_DIR)
):
    print("Error ics dirs are not ready!")
    sys.exit(1)


os.makedirs("website/", exist_ok=True)

shutil.copy("CNAME", "website/")
shutil.copytree(SCHOOL_HOLIDAYS_ICS_DIR, "website/Ferien/", dirs_exist_ok=True)
shutil.copytree(PUBLIC_HOLIDAYS_ICS_DIR, "website/Feiertage/", dirs_exist_ok=True)


def markdown_links_from_dir(directory: str, http_path: str) -> str:
    files = os.listdir(directory)
    files.sort()

    links = ""
    for filename in files:
        full_path = os.path.join(directory, filename)
        if os.path.isfile(full_path):
            links += f"- [{filename}]({http_path}{filename})\n"

    return links


template_path = "website/index_template.md"
output_path = "website/index.md"

public_links = markdown_links_from_dir("website/Feiertage", "Feiertage/")
school_links = markdown_links_from_dir("website/Ferien", "Ferien/")

with open(template_path, "r", encoding="utf-8") as file1:
    content = file1.read()

content = content.replace("[[feiertage-tree]]", public_links)
content = content.replace("[[ferien-tree]]", school_links)

with open(output_path, "w", encoding="utf-8") as file:
    file.write(content)
