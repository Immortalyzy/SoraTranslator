""" nscmake will create a nscript.dat from a nscript/0.txt (tradition), it take a list of files as input and combine them into a single file """

from typing import List


def encode_and_combine_files(in_files: List[str], out_file: str = "nscript.dat"):
    """Encode and combine files into a single file."""
    try:
        with open(out_file, "wb") as out_fp:
            for in_file in in_files:
                with open(in_file, "rb") as in_fp:
                    last_ch = b"\n"
                    last_was_newline = True

                    while True:
                        ch = in_fp.read(1)
                        if not ch:
                            break

                        # Write a single '\n' for newline sequences '\r\n', '\r', '\n'
                        if ch == b"\r":
                            out_fp.write(b"\n" ^ b"\x84")
                        elif not (ch == b"\n" and last_ch == b"\r"):
                            out_fp.write(ch ^ b"\x84")

                        last_was_newline = ch in (b"\n", b"\r")
                        last_ch = ch

                    # Add an ending newline if there wasn't one
                    if not last_was_newline:
                        out_fp.write(b"\n" ^ b"\x84")

    except IOError as e:
        print(f"Error: {e}")


# Example usage:
# encode_and_combine_files(["input1.txt", "input2.txt"])
