
# Path configs
SRC_DIR := src/photobooth/native
BUILD_DIR := $(SRC_DIR)
FRAMEWORK_DIR := Framework
HEADER_DIR := Header

# File names
CPP_SRC := $(SRC_DIR)/edsdk_bridge.cpp
DYLIB := $(BUILD_DIR)/libedsdk.dylib

# Compiler flags
CXX := g++
CXXFLAGS := -std=c++11 -D__MACOS__ -I$(HEADER_DIR) -F$(FRAMEWORK_DIR) -framework EDSDK -framework CoreFoundation -dynamiclib

.PHONY: all clean

# Default target
all: $(DYLIB)

# Build rule
$(DYLIB): $(CPP_SRC)
	$(CXX) $(CXXFLAGS) -o $@ $^

# Clean built dylib
clean:
	rm -f $(DYLIB)
