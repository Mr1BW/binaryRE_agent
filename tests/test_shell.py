import pytest
from src.tools.sandboxed_shell.dockerized_bash import DockerizedBashProcess


def test_dockerized_bash_process():
    process = DockerizedBashProcess(persistent=True)
    process.run("cd /tmp && touch test.txt")
    r = process.run("ls")
    assert "test.txt" in r

def test_gdb_disassemble():
    # Open a gdb session with the ch25.bin binary
    process = DockerizedBashProcess(persistent=True, mounted_dirs={'./binaries': '/binaries'})
    r = process.run("cd /binaries && echo 'john\nthe ripper\n' | qemu-i386-static -g 1234 ./ch2.bin & gdb -q -ex 'target remote localhost:1234' -ex 'disassemble check_one_fd' -ex 'c' -ex 'q' -ex 'y'")
    assert "Bien joue, vous pouvez valider l'epreuve" in r
    
    assert "0x8048618 <check_one_fd+40>" in r
    
def test_python_hello_world():
    process = DockerizedBashProcess(persistent=True)
    r = process.run("python3 -c 'print(\"Hello, World!\")'")
    assert "Hello, World!" in r

if __name__ == "__main__":
    pytest.main()