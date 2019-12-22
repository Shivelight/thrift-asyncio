# thrift-asyncio compiler

Stripped Thrift compiler with Python 3.6+ asyncio generator and custom options.

<!-- TOC -->

- [Python Generator Options](#python-generator-options)
- [CMake Options](#cmake-options)
- [Latest Build Artifacts](#latest-build-artifacts)
- [Build on Unix-like System](#build-on-unix-like-system)
- [Build on Windows](#build-on-windows)

<!-- /TOC -->

## Python Generator Options

New options in addition to the original compiler:

| Option       | Description                                          |
|--------------|------------------------------------------------------|
| asyncio      | Generate code for use with asyncio.                  | 
| no_docstring | Do not generate docstring in the generated code.     | 
| client_only  | Generate code without interface, server, and remote. |

## CMake Options

To use these options, you can use the `-D` argument. For example to build static executable:

```
cmake -DBUILD_STATIC_EXECUTABLE=ON
```

| Option                  | Description                                 | Default |
|-------------------------|---------------------------------------------|---------|
| BUILD_STATIC_EXECUTABLE | Build static executable instead of dynamic. | OFF     |


## Latest Build Artifacts

You can download latest build artifacts from [actions](https://github.com/Shivelight/thrift-asyncio/actions). The workflow runs everytime there is a change to the compiler.

## Build on Unix-like System

### Prerequisites
- Install CMake
- Install flex and bison

### Build using CMake

- Go to **thrift\compiler\cpp**
- Use the following steps to build using cmake:

```
mkdir cmake-build && cd cmake-build
cmake ..
make
```

#### Build with Eclipse IDE

- Go to **thrift\compiler\cpp**
- Use the following steps to build using cmake:

```
mkdir cmake-ec && cd cmake-ec
cmake -G "Eclipse CDT4 - Unix Makefiles" ..
make
```

Now open the folder cmake-ec using eclipse.

#### Build with XCode IDE in MacOS

- Install/update flex, bison and cmake with brew

```
brew install cmake
brew install bison
```

- Go to **thrift\compiler\cpp**
- Run commands in command line:

```
mkdir cmake-build && cd cmake-build
cmake -G "Xcode" ..
cmake --build .
```

#### Usage of other IDEs

Please check list of supported IDE 

```
cmake --help
```

## Build on Windows

### Prerequisites
- Install CMake - https://cmake.org/download/
- In case if you want to build without Git Bash - install winflexbison - https://sourceforge.net/projects/winflexbison/
- In case if you want to build with Visual Studio - install Visual Studio 
  - Better to use the latest stable Visual Studio Community Edition - https://www.visualstudio.com/vs/whatsnew/ (ensure that you installed workload "Desktop Development with C++" for VS2017) - Microsoft added some support for CMake and improving it in Visual Studio

### Build using Git Bash

Git Bash provides flex and bison

- Go to **thrift\compiler\cpp**
- Use the following steps to build using cmake:

```
mkdir cmake-vs && cd cmake-vs
cmake -DWITH_SHARED_LIB=off ..
cmake --build .
```

### Using Visual Studio and Win flex-bison

- Generate a Visual Studio project for version of Visual Studio which you have (**cmake --help** can show list of supportable VS versions):
- Run commands in command line:
```
mkdir cmake-vs
cd cmake-vs
cmake -G "Visual Studio 15 2017" ..
```
- Now open the folder cmake-vs using Visual Studio.

### Cross compile using mingw32 and generate a Windows Installer with CPack

```
mkdir cmake-mingw32 && cd cmake-mingw32
cmake -DCMAKE_TOOLCHAIN_FILE=../build/cmake/mingw32-toolchain.cmake -DBUILD_COMPILER=ON -DBUILD_LIBRARIES=OFF -DBUILD_TESTING=OFF ..
cpack
```