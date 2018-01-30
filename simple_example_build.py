from cffi import FFI

ffibuilder = FFI()
ffibuilder.set_source("_simple_example", None)
ffibuilder.cdef("""
    int printf(const char *format, ...);
""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
