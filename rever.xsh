# ********************************************************************
#  This file is part of metadata-schema.
#
#        Copyright (C) 2022-2025 Albert Engstfeld
#        Copyright (C) 2022      Johannes Hermann
#        Copyright (C) 2022      Julian Rüth
#        Copyright (C) 2022      Nicolas Hörmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ********************************************************************

import re

# Check that we are on the main branch
branch=$(git branch --show-current)
if branch.strip() != "main":
  raise Exception("You must be on the main branch to release.")
# and that it is up to date with origin/main
git fetch https://github.com/echemdb/metadata-schema.git
git reset FETCH_HEAD
git diff --exit-code
git diff --cached --exit-code

$PROJECT = 'metadata-schema'

from rever.activities.command import command

command('pixi', 'pixi install --manifest-path "$PWD/pyproject.toml"')
command('regenerate_schemas', 'pixi run generate-all && pixi run update-expected-schemas')

$ACTIVITIES = [
    'version_bump',
    'pixi',
    'regenerate_schemas',
    'changelog',
    'tag',
    'push_tag',
]

$VERSION_BUMP_PATTERNS = [
    ('pyproject.toml', r'version =', 'version = "$VERSION"'),
    ('mdstools/__init__.py', r'__version__', '__version__ = "$VERSION"'),
    ('doc/conf.py', r'release =', 'release = "$VERSION"'),
    ('doc/index.md', r'JSON Schemas \(v', 'JSON Schemas (v$VERSION)'),
    ('doc/index.md', r'metadata-schema/\d+\.\d+\.\d+/schemas/', 'metadata-schema/$VERSION/schemas/'),
    # echemdbSchemaVersion in LinkML schemas (example values)
    ('linkml/minimum_echemdb.yaml', r'- value: "\d+\.\d+\.\d+"', '- value: "$VERSION"'),
    ('linkml/autotag.yaml', r'- value: "\d+\.\d+\.\d+"', '- value: "$VERSION"'),
    ('linkml/source_data.yaml', r'- value: "\d+\.\d+\.\d+"', '- value: "$VERSION"'),
    ('linkml/svgdigitizer.yaml', r'- value: "\d+\.\d+\.\d+"', '- value: "$VERSION"'),
    ('linkml/echemdb_package.yaml', r'- value: "\d+\.\d+\.\d+"', '- value: "$VERSION"'),
    ('linkml/svgdigitizer_package.yaml', r'- value: "\d+\.\d+\.\d+"', '- value: "$VERSION"'),
    # echemdbSchemaVersion in example files
    ('examples/file_schemas/minimum_echemdb.yaml', r'echemdbSchemaVersion:', 'echemdbSchemaVersion: $VERSION'),
    ('examples/file_schemas/autotag.yaml', r'echemdbSchemaVersion:', 'echemdbSchemaVersion: $VERSION'),
    ('examples/file_schemas/source_data.yaml', r'echemdbSchemaVersion:', 'echemdbSchemaVersion: $VERSION'),
    ('examples/file_schemas/svgdigitizer.yaml', r'echemdbSchemaVersion:', 'echemdbSchemaVersion: $VERSION'),
    ('examples/file_schemas/echemdb_package.json', r'"echemdbSchemaVersion":', '"echemdbSchemaVersion": "$VERSION",'),
    ('examples/file_schemas/svgdigitizer_package.json', r'"echemdbSchemaVersion":', '"echemdbSchemaVersion": "$VERSION",'),
]

$CHANGELOG_FILENAME = 'ChangeLog'
$CHANGELOG_TEMPLATE = 'TEMPLATE.rst'
$CHANGELOG_NEWS = 'doc/news'
$PUSH_TAG_REMOTE = 'git@github.com:echemdb/metadata-schema.git'

$GITHUB_ORG = 'echemdb'
$GITHUB_REPO = 'metadata-schema'

$CHANGELOG_CATEGORIES = ('Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Performance')
