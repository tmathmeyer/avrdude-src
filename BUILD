load (
    "//rules/core/C/build_defs.py",
)

c_header (
  name = "avrdude_headers",
  srcs = pattern("*.h")
)

c_files = ["serbb_win32", "pgm_type", "ft245r", "update", "lists",
           "pgm", "ser_win32", "ppiwin", "lexer", "par", "pindefs", "flip2",
           "usbasp", "butterfly", "ser_posix", "arduino", "pickit2", "ppi",
           "avrftdi", "crc16", "term", "safemode", "jtagmkI", "buspirate",
           "dfu", "avr910", "stk500", "stk500generic", "confwin", "avrftdi_tpi",
            "ser_avrdoper", "jtagmkII", "avrpart", "stk500v2", "usbtiny",
            "fileio", "flip1", "linuxgpio", "usb_hidapi", "usb_libusb",
            "wiring", "bitbang", "serbb_posix", "config", "jtag3",
            "config_gram", "avr"]

for sourcefile in c_files:
  cpp_object (
    name = "obj_"+sourcefile,
    srcs = [ sourcefile + ".c" ],
    deps = [":avrdude_headers"],
    compiler = "gcc",
    std="gnu11",
    flags = [
      '-DCONFIG_DIR="$(sysconfigdir)"',
      '-DPATH_MAX=256'
    ]
  )

cpp_library (
  name = "avrdude_lib",
  deps = [':obj_' + x for x in c_files],
  compiler = "gcc",
)

cpp_binary (
  name = "avrdude",
  deps = [
    ":avrdude_headers",
    ":avrdude_lib"
  ],
  srcs = [ "main.c" ],
  compiler = "gcc",
  std="gnu11",
  flags = [
    '-DCONFIG_DIR=\\"$(sysconfigdir)\\"',
    '-lusb-1.0',
    '-lelf',
    '-lm',
    '-lreadline'
  ]
)