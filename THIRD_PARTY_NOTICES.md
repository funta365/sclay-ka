# Sclayka v1.1.0 third-party notices

Sclayka is distributed under the GNU Affero General Public License, version 3.
The matching application source and build scripts are available at
<https://github.com/funta365/sclay-ka/tree/v1.1.0>.
Third-party components retain their own licenses. The installer copies
[`THIRD_PARTY_LICENSES.txt`](THIRD_PARTY_LICENSES.txt) to the installation directory.

| Component and version | License and source |
| --- | --- |
| PyMuPDF 1.28.2 and MuPDF 1.28.2 | GNU AGPL version 3. See [PyMuPDF source distribution](https://pypi.org/project/PyMuPDF/1.28.2/#files) and the [MuPDF source release](https://github.com/ArtifexSoftware/mupdf-downloads/releases/tag/1.28.2). |
| Qt 6.11.2, PySide6 6.11.2, and Shiboken6 6.11.2 | The Qt libraries are distributed under the applicable open-source licenses in their sources, including the GNU LGPL version 3 and GNU GPL version 3. See [Qt source and module notices](https://download.qt.io/archive/qt/6.11/6.11.2/single/) and [Qt for Python source](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/). |
| Pillow 12.3.0 | Python Imaging Library license. See [source distribution](https://pypi.org/project/pillow/12.3.0/#files) and the included Pillow license. |
| CPython 3.14.7 | Python Software Foundation license and accompanying third-party notices. See [source release](https://www.python.org/downloads/release/python-3147/). |
| PyInstaller 6.22.3 | GNU GPL with PyInstaller’s distribution exception. See [source distribution](https://pypi.org/project/pyinstaller/6.22.3/#files) and the included PyInstaller license. |

The installed Qt and Qt for Python libraries are separate, dynamically loaded
files. You can replace them with compatible modified builds in the installation’s
`_internal` directory. The Qt and Python source packages include notices and
source information for their third-party components.
