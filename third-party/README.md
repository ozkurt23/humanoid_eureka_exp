# Third-party components and source access

This directory accompanies the full experimental archive. Copyright and license notices for third-party components apply to their respective files. The project's permissive license applies to the project authors' contributions. The third-party license texts remain part of this distribution.

## Qwen model

The archive includes Qwen2.5-Coder-1.5B-Instruct weights and tokenizer files in `work/qwen`. The original model is distributed under Apache License 2.0. A copy is supplied as `QWEN-LICENSE.txt`, alongside the upstream model card, `QWEN-MODEL-CARD.md`. The saved model files were used for the historical reward experiments.

Original model and licensing information are available from [Qwen's model repository](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct).

## Blender and its libraries

The archived binary distribution is Blender 4.5.16 LTS for Linux x86-64, build hash `3f6797307da5`, built on 2026-11-10. Its original notices are reproduced in `Blender-copyright.txt`, `Blender-license.md`, and `Blender-licenses.json`. The complete original notices also remain inside the archived Blender directory.

The corresponding Blender source release, including build scripts and patches, is available at [blender-4.5.16.tar.xz](https://download.blender.org/source/blender-4.5.16.tar.xz). Its [publisher-provided checksum](https://download.blender.org/source/blender-4.5.16.tar.xz.md5sum) accompanies the source. A downloaded and checked copy of this source release is supplied with the public release as `blender-4.5.16.tar.xz`.

The complete dependency version and download recipe from that source version is supplied as `Blender-4.5.16-dependency-versions.cmake`. The machine-readable `blender-dependency-sources.json` expands those recipe variables into source download URLs, source archive hashes, versions and license identifiers. Build patches and dependency build scripts are in `build_files/build_environment` in the Blender source archive. These files provide access to the library sources used by the supplied build.

The dependency source archives are hosted by their respective upstreams. Blender also hosts the [4.5.0 source bundle with libraries](https://download.blender.org/source/blender-with-libraries-4.5.0.tar.xz). Updated dependencies should be retrieved at the versions pinned in the 4.5.16 recipe above.

Blender's GPL terms apply to Blender. Rendered images and project models have their own copyright and license terms.

## Archived Python environments and geometry libraries

The full archive contains the experiment's CAD environment and formatting environment. `python-components.json` records their installed versions, original package metadata and license locations. The `python-notices/` directory reproduces installed license texts and package metadata. `python-sources.json` links to upstream project pages and version-specific source distributions provided by PyPI.

The CAD environment includes cadquery-ocp-novtk and cadquery-ocp-proxy 8.0.1.1.0. The OCP wrapper is Apache-2.0, with a copy in `OCP-8.0.1.1-LICENSE.txt`. Open CASCADE Technology 8.0.1 uses LGPL-2.1 with the Open CASCADE exception, supplied in `OCCT-8.0.1-LICENSE.txt` and `OCCT-8.0.1-EXCEPTION.txt`.

The matching Linux wrapper source is supplied as OCP-8.0.1.1-Linux-source.zip. The wrapper source and build instructions are available from [OCP 8.0.1.1](https://github.com/CadQuery/OCP/releases/tag/8.0.1.1) and [the official OCP build system](https://github.com/CadQuery/ocp-build-system). The underlying library source is available from [OCCT V8_0_1](https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V8_0_1.tar.gz). The build system's saved revision, no-VTK workflow and source pointers are in `OCP-source-access.json`, `OCP-build-workflow.yml`, and `OCP-build-README.md`. Native libraries retained inside the wheel follow their own licenses and software bill of materials. Relevant installed SBOM and notice data accompany the package metadata in `python-notices/`.

The geometry binaries are dynamically linked. The archive includes the native library files in their original package directories. The original license terms govern modification and replacement of those libraries.
