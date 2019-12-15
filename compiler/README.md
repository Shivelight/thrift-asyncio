# thrift-asyncio compiler

Stripped Thrift compiler with Python 3.6+ asyncio generator and custom options.

<!-- TOC -->

- [Python Generator Options](#python-generator-options)
- [Build on Unix-like System](#build-on-unix-like-system)
- [Build on Windows](#build-on-windows)

<!-- /TOC -->

## Python Generator Options

New options in addition to the original compiler:

| Option       | description                                          |
|--------------|------------------------------------------------------|
| asyncio      | Generate code for use with asyncio.                  | 
| no_docstring | Do not generate docstring in the generated code.     | 
| client_only  | Generate code without interface, server, and remote. |


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

### Building the Thrift IDL compiler in Windows without CMake

If you don't want to use CMake you can use the already available Visual Studio 2010 solution.

The Visual Studio project contains pre-build commands to generate the thriftl.cc, thrifty.cc and thrifty.hh files which are necessary to build the compiler. 

These depend on bison, flex and their dependencies to work properly.

Download flex & bison as described above. 

Place these binaries somewhere in the path and rename win_flex.exe and win_bison.exe to flex.exe and bison.exe respectively.

If this doesn't work on a system, try these manual pre-build steps.

Open compiler.sln and remove the Pre-build commands under the project's: Properties -> Build Events -> Pre-Build Events.

From a command prompt:
```
cd thrift/compiler/cpp
flex -o src\thrift\thriftl.cc src\thrift\thriftl.ll
```
In the generated thriftl.cc, comment out #include <unistd.h>

Place a copy of bison.simple in thrift/compiler/cpp
```
bison -y -o "src/thrift/thrifty.cc" --defines src/thrift/thrifty.yy
move src\thrift\thrifty.cc.hh  src\thrift\thrifty.hh
```

Bison might generate the yacc header file "thrifty.cc.h" with just one h ".h" extension; in this case you'll have to rename to "thrifty.h".

```
move src\thrift\version.h.in src\thrift\version.h
```

Download inttypes.h from the interwebs and place it in an include path
location (e.g. thrift/compiler/cpp/src).

Build the compiler in Visual Studio.