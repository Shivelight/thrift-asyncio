#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#
#
# Contains some contributions under the Thrift Software License.
# Please see doc/old-thrift-license.txt in the Thrift distribution for
# details.

AUTOMAKE_OPTIONS = subdir-objects nostdinc

SUBDIRS = src .
if WITH_TESTS
SUBDIRS += test
endif

bin_PROGRAMS = thrift

thrift_OBJDIR = obj

thrift_SOURCES = src/thrift/audit/t_audit.cpp \
                 src/thrift/audit/t_audit.h \
                 src/thrift/common.cc \
                 src/thrift/common.h \
                 src/thrift/generate/t_generator.cc \
                 src/thrift/generate/t_generator.h \
                 src/thrift/generate/t_generator_registry.h \
                 src/thrift/globals.h \
                 src/thrift/logging.h \
                 src/thrift/main.cc \
                 src/thrift/main.h \
                 src/thrift/version.h \
                 src/thrift/parse/parse.cc \
                 src/thrift/parse/t_base_type.h \
                 src/thrift/parse/t_const.h \
                 src/thrift/parse/t_const_value.h \
                 src/thrift/parse/t_container.h \
                 src/thrift/parse/t_doc.h \
                 src/thrift/parse/t_enum.h \
                 src/thrift/parse/t_enum_value.h \
                 src/thrift/parse/t_field.h \
                 src/thrift/parse/t_function.h \
                 src/thrift/parse/t_list.h \
                 src/thrift/parse/t_map.h \
                 src/thrift/parse/t_program.h \
                 src/thrift/parse/t_scope.h \
                 src/thrift/parse/t_service.h \
                 src/thrift/parse/t_set.h \
                 src/thrift/parse/t_struct.h \
                 src/thrift/parse/t_type.h \
                 src/thrift/parse/t_typedef.cc \
                 src/thrift/parse/t_typedef.h \
                 src/thrift/platform.h

# Specific client generator source
thrift_SOURCES += src/thrift/generate/t_py_generator.cc

thrift_CPPFLAGS = -I$(srcdir)/src
thrift_CXXFLAGS = -Wall -Wextra -pedantic -Werror
thrift_LDADD = @LEXLIB@ src/thrift/libparse.a

WINDOWS_DIST = \
             compiler.sln \
             compiler.vcxproj \
             compiler.vcxproj.filters

EXTRA_DIST = \
             coding_standards.md \
             README.md \
             CMakeLists.txt \
             test \
             $(WINDOWS_DIST)

#clean-local:
#	$(RM) version.h   -- do not delete, we need it

src/thrift/main.cc: src/thrift/version.h

style-local:
	$(CPPSTYLE_CMD)
