langs("C", "Python")

cpp_header (
  name = "include",
  srcs = pattern("*.h"),
)

cc_binary (
  name = "avrdude",
  includes = [
    ":include",
  ],
  srcs = pattern("*.c"),
  compiler = "gcc",
  std="gnu11",
  flags = [
    '-DPATH_MAX=256',
    '-lusb-1.0',
    '-lelf',
    '-lm',
    '-lreadline',
  ],
)

py_library (
  name = "autoflash",
  srcs = [
    "autoflash.py",
    "avrdude.py",
  ],
  deps = [
    ":avrdude",
    "//impulse:impulse_libs",
    "//impulse/args:args",
    "//impulse/util:bintools",
    "//impulse/util:buildvars",
  ],
  data = [
    "avrdude.conf",
  ],
)