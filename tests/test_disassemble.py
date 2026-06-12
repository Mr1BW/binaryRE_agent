import os
import pytest
import src.utils as utils


def test_disassemble_function():
    # Test with ch2.bin for disassembling a function
    binary_path = os.path.join("binaries", "ch2.bin")
    function_name = "check_one_fd"

    # Ensure the binary exists before testing
    assert os.path.exists(binary_path), f"Binary file not found: {binary_path}"

    # Attempt to extract the assembly for the function
    asm = utils.disassemble_function(binary_path, function_name)

    # Verify that the returned assembly is not an error message and is non-empty
    assert "Function check_one_fd not found." not in asm, "The function was not found in the binary."
    assert asm.strip() != "", "The disassembled output is empty."
    assert function_name in asm, f"Expected function name '{function_name}' not found in the output."

    # Optionally, check that the output contains expected instructions
    function_label = "080485f0 <check_one_fd>:"
    first_line = "80485f0:	55                   	push   %ebp"
    last_line = "80486b9:	8d bc 27 00 00 00 00 	lea    0x0(%edi,%eiz,1),%edi"
    assert function_label in asm, f"Expected label '{function_label}' not found in the output."
    assert first_line in asm, f"Expected instruction '{first_line}' not found in the output."
    assert last_line in asm, f"Expected instruction '{last_line}' not found in the output."


def test_disassemble_binary():
    # Test with ch1.bin for disassembling the entire binary
    binary_path = os.path.join("binaries", "ch1.bin")

    # Ensure the binary exists before testing
    assert os.path.exists(binary_path), f"Binary file not found: {binary_path}"

    # Attempt to disassemble the binary
    asm = utils.disassemble_binary(binary_path)
    normalized_asm = " ".join(asm.split())

    # Verify that the disassembled output contains expected markers
    assert "ch1.bin:     file format elf32-i386" in asm, "The binary was not disassembled."
    expected = "80487f3:       e8 00 00 00 00          call   80487f8 <_fini+0xc>"
    normalized_expected = " ".join(expected.split())
    assert normalized_expected in normalized_asm, "Expected call instruction not found."


def test_summarize_assembly():
    binary_path = os.path.join("binaries", "ch2.bin")

    # Ensure the binary exists before testing
    assert os.path.exists(binary_path), f"Binary file not found: {binary_path}"

    # Attempt to summarize the assembly code
    summary = utils.summarize_assembly(binary_path=binary_path)

    # Verify that the summary is a non-empty dictionary
    assert isinstance(
        summary, dict), "summarize_assembly did not return a dict."
    assert len(summary) > 0, "The summary dictionary is empty."

    # Verify that the summary contains expected keys
    assert summary["architecture"] == "i386", "Architecture should be 'i386'."
    assert summary["start_address"] == "0x08048150", "Start address should be '0x08048150'."
    assert isinstance(summary["program_headers"],
                      list), "Program headers should be a list."
    assert len(summary["program_headers"]
               ) > 0, "Program headers list is empty."


def test_dump_memory():
    # Test dump_memory using ch1.bin
    binary_path = os.path.join("binaries", "ch1.bin")

    # Ensure the binary exists before testing
    assert os.path.exists(binary_path), f"Binary file not found: {binary_path}"

    # Read 16 bytes from an offset; here we pick 0x8048808 (start of .rodata section)
    data = utils.dump_memory(binary_path, 0x804883a, 16)

    # Verify that data is bytes and has the expected length
    assert isinstance(data, bytes), "dump_memory did not return bytes."
    assert len(
        data) == 16, "dump_memory did not return the expected length of bytes."

    # Verify that the data contains expected bytes
    assert data == b'memory\x00123456789'


def test_get_string_at_address():
    # Test get_string_at_address using ch1.bin
    binary_path = os.path.join("binaries", "ch1.bin")
    # Use an address in .rodata that contains a known string.
    # According to the provided asm, address 0x8048908 contains part of a string like "Veuillez ent" or "Bien jou"
    s = utils.get_string_at_address(binary_path, 0x804888c)

    # Verify that a non-empty string is returned
    assert isinstance(s, str), "get_string_at_address did not return a string."
    assert len(s) > 0, "get_string_at_address returned an empty string."
    # Check if expected substrings are present
    assert s == "##        Bienvennue dans ce challenge de cracking        ##", "The expected string content was not found."


if __name__ == "__main__":
    pytest.main()
