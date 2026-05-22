# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys
import os
import shutil

from config import (
    WEBSITE_TEMPLATE_DIR,
    WEBSITE_RESULT_DIR,
    WEBSITE_TEMPLATE_FILE,
    WEBSITE_OUTPUT_FILE,
    WEBSITE_ICS_SOURCE_DIRS,
    WEBSITE_PLACEHOLDERS,
)

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

if not os.path.exists(WEBSITE_TEMPLATE_DIR):
    print(
        "::error::Missing website template directory: "
        f"'{WEBSITE_TEMPLATE_DIR}'. Current working directory: '{os.getcwd()}'."
    )
    sys.exit(3)

if not os.path.isdir(WEBSITE_TEMPLATE_DIR):
    print(
        "::error::Invalid website template path (expected directory): "
        f"'{WEBSITE_TEMPLATE_DIR}'. Current working directory: '{os.getcwd()}'."
    )
    sys.exit(4)


if os.path.exists(WEBSITE_RESULT_DIR):
    shutil.rmtree(WEBSITE_RESULT_DIR)

shutil.copytree(WEBSITE_TEMPLATE_DIR, WEBSITE_RESULT_DIR)

for source_dir in WEBSITE_ICS_SOURCE_DIRS:
    target_dir = os.path.join(WEBSITE_RESULT_DIR, os.path.basename(os.path.normpath(source_dir)))
    shutil.copytree(source_dir, target_dir)


def markdown_links_from_dir(directory: str, http_path: str) -> str:
    files = os.listdir(directory)
    files.sort()

    links = ""
    for filename in files:
        full_path = os.path.join(directory, filename)
        if os.path.isfile(full_path):
            links += f"- [{filename}]({http_path}{filename})\n"

    return links


template_path = os.path.join(WEBSITE_RESULT_DIR, WEBSITE_TEMPLATE_FILE)
output_path = os.path.join(WEBSITE_RESULT_DIR, WEBSITE_OUTPUT_FILE)

with open(template_path, "r", encoding="utf-8") as file1:
    content = file1.read()

for source_dir in WEBSITE_ICS_SOURCE_DIRS:
    dir_name = os.path.basename(os.path.normpath(source_dir))
    placeholder = WEBSITE_PLACEHOLDERS.get(source_dir)
    if not placeholder:
        continue

    website_dir_path = os.path.join(WEBSITE_RESULT_DIR, dir_name)
    links = markdown_links_from_dir(website_dir_path, f"{dir_name}/")
    content = content.replace(placeholder, links)

with open(output_path, "w", encoding="utf-8") as file:
    file.write(content)

if os.path.exists(template_path):
    os.remove(template_path)
