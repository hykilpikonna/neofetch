#!/usr/bin/env bash

FASTFETCH_VERSION="2.10.2"
FASTFETCH_DL="https://github.com/fastfetch-cli/fastfetch/releases/download/$FASTFETCH_VERSION/"

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

set -e

# Remove the old build
rm -rf dist/
rm -rf build/

# Remove git from the source code before building
rm -rf hyfetch/git/

# Build python from setup.py
python3 setup.py sdist bdist_wheel

# Check
twine check dist/*.tar.gz
twine check dist/*.whl

# =================
# Build for windows
cd dist

# Get the file name
# file="$(ls | grep .whl)" use glob instead
file=$(echo *-none-any.whl)

# Build bash pacakge
"$DIR/build_bash.sh"

# Unzip the wheel
echo "> Unzipping $file"
rm -rf wheel
unzip -qq "$file" -d wheel
# TODO: Find a way to exclude the tools folder
rm -rf wheel/tools

# Copy the git distribution to the wheel
cp -r git/ wheel/hyfetch/

# Embed fastfetch binary
echo "> Embedding fastfetch binary"
wget -q "$FASTFETCH_DL/fastfetch-windows-i686.zip" -O fastfetch-windows.zip
mkdir -p wheel/hyfetch/fastfetch
bsdtar -zxf fastfetch-windows.zip -C wheel/hyfetch/fastfetch
rm -rf fastfetch-windows.zip

# Change the file name (replace -none-any with -win_amd64)
new_name=${file/-any/-win32}

# Zip the wheel to win_amd64.whl
cd wheel && zip -qq -y -r "../$new_name" * && cd ..
cp "$new_name" "${new_name/.whl/-win_amd64.whl}"

# Check again
twine check "$new_name"

# =================
# Build for linux

# Now we're done with windows, delete the git folder
rm -rf wheel/git

function build_for_platform() {
    ff_platform=$1
    wheel_platform=$2

    echo "Building for $ff_platform"
    
    # Download the fastfetch binary
    wget -q "$FASTFETCH_DL/fastfetch-$ff_platform.zip" -O "fastfetch-$ff_platform.zip"

    # Delete the old fastfetch folder
    rm -rf wheel/hyfetch/fastfetch

    # Unzip the fastfetch binary
    # unzip -qq "fastfetch-$ff_platform.zip" -d wheel/hyfetch/fastfetch
    mkdir -p wheel/hyfetch/fastfetch
    bsdtar -zxf "fastfetch-$ff_platform.zip" -C wheel/hyfetch/fastfetch --strip-components 1
    rm -rf "fastfetch-$ff_platform.zip"

    # Change the file name
    new_name=${file/-any/-"$wheel_platform"}

    # Zip the wheel to platform.whl
    cd wheel && zip -qq -y -r "../$new_name" * && cd ..

    # Check again
    twine check "$new_name"
}

# See https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
# The official fastfetch build uses Ubuntu 20.04 with glibc 2.31
build_for_platform "linux-amd64" "manylinux_2_31_x86_64"
build_for_platform "linux-aarch64" "manylinux_2_31_aarch64"
# There doesn't seem to be tags for freebsd?
# build_for_platform "freebsd-amd64" "freebsd_x86_64"
# build_for_platform "freebsd-aarch64" "freebsd_aarch64"
build_for_platform "musl-amd64" "musllinux_1_1_x86_64"
build_for_platform "musl-aarch64" "musllinux_1_1_aarch64"
# The official fastfetch build uses macOS 12.0
build_for_platform "macos-universal" "macosx_11_0_x86_64"
build_for_platform "macos-universal" "macosx_11_0_arm64"
# TODO: linux_riscv64

# Finally, remove temporary files
rm -rf wheel git
