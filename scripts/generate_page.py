import sys
import os
import shutil

from config import (
    WEBSITE_DIR,
    WEBSITE_TEMPLATE_FILE,
    WEBSITE_OUTPUT_FILE,
    WEBSITE_ROOT_FILES,
    WEBSITE_ICS_SOURCE_DIRS,
    WEBSITE_PLACEHOLDERS,
)

# Check if ICS dirs exist
for source_dir in WEBSITE_ICS_SOURCE_DIRS:
    if not os.path.exists(source_dir):
        print(
            "::error::Missing ICS source directory: "
            f"'{source_dir}'. Current working directory: '{os.getcwd()}'. "
            "Run the ICS generation step before generate_page.py."
        )
        sys.exit(1)

    if not os.path.isdir(source_dir):
        print(
            "::error::Invalid ICS source path (expected directory): "
            f"'{source_dir}'. Current working directory: '{os.getcwd()}'."
        )
        sys.exit(2)


os.makedirs(WEBSITE_DIR, exist_ok=True)

for root_file in WEBSITE_ROOT_FILES:
    shutil.copy(root_file, os.path.join(WEBSITE_DIR, root_file))

for source_dir in WEBSITE_ICS_SOURCE_DIRS:
    dir_name = os.path.basename(os.path.normpath(source_dir))
    target_dir = os.path.join(WEBSITE_DIR, dir_name)
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)


def markdown_links_from_dir(directory: str, http_path: str) -> str:
    files = os.listdir(directory)
    files.sort()

    links = ""
    for filename in files:
        full_path = os.path.join(directory, filename)
        if os.path.isfile(full_path):
            links += f"- [{filename}]({http_path}{filename})\n"

    return links


template_path = os.path.join(WEBSITE_DIR, WEBSITE_TEMPLATE_FILE)
output_path = os.path.join(WEBSITE_DIR, WEBSITE_OUTPUT_FILE)

with open(template_path, "r", encoding="utf-8") as file1:
    content = file1.read()

for source_dir in WEBSITE_ICS_SOURCE_DIRS:
    dir_name = os.path.basename(os.path.normpath(source_dir))
    placeholder = WEBSITE_PLACEHOLDERS.get(source_dir)
    if not placeholder:
        continue

    website_dir_path = os.path.join(WEBSITE_DIR, dir_name)
    links = markdown_links_from_dir(website_dir_path, f"{dir_name}/")
    content = content.replace(placeholder, links)

with open(output_path, "w", encoding="utf-8") as file:
    file.write(content)

if os.path.exists(template_path):
    os.remove(template_path)
