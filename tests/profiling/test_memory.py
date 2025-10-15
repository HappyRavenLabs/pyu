import sys
from unittest.mock import patch

import pytest

from pyu.profiling.memory import mem


def _allocate(size_in_bytes):
    return bytearray(size_in_bytes)


MEM_MEASUREMENT_ATOL = 1000  # bytes


class TestMemoryTracer:

    def test_decorator_single_run(self, capsys):

        @mem
        def sample_function():
            dummy_var = _allocate(1024)
            return dummy_var

        sample_function()
        captured = capsys.readouterr()
        assert "Total Memory Used" in captured.err

    @pytest.mark.parametrize(
        "exp_mem",
        [10, 1024, 10 * 1024, 100 * 1024, 500 * 1024, 1024 * 1024, 1024**3],
    )
    @patch("pyu.profiling.writing.MemoryWriter.write")
    def test_mem_usage_computed_correctly(
        self, mock_memory_writer_write, capsys, exp_mem
    ):
        @mem
        def sample_function():
            dummy_var = _allocate(exp_mem)
            return dummy_var

        sample_function()
        mem_usage = sum(mock_memory_writer_write.call_args[0][0])
        assert abs(mem_usage - exp_mem) < MEM_MEASUREMENT_ATOL

    def test_decorator_multiple_runs(self, capsys):

        @mem(repeat=5)
        def sample_function():
            dummy_var = _allocate(2048)
            return dummy_var

        sample_function()
        captured = capsys.readouterr()
        assert "Memory Usage Report" in captured.err

    @pytest.mark.parametrize(
        "exp_mem",
        [1024, 10 * 1024, 100 * 1024, 500 * 1024, 1024 * 1024, 1024**3],
    )
    @patch("pyu.profiling.writing.MemoryWriter.write")
    def test_mem_usage_computed_correctly_over_multiple_runs(
        self, mock_memory_writer_write, capsys, exp_mem
    ):

        @mem(repeat=3)
        def sample_function():
            dummy_var = _allocate(exp_mem)
            return dummy_var

        sample_function()
        for mem_usage in mock_memory_writer_write.call_args[0][0]:
            assert abs(mem_usage - exp_mem) < MEM_MEASUREMENT_ATOL

    def test_ordinary_use_as_context_manager(self, capsys):
        with mem.run():
            dummy_var = _allocate(4096)

        captured = capsys.readouterr()
        assert "Total Memory Used" in captured.err

    def test_ordinary_use_as_context_manager_stdout(self, capsys):
        with mem.run(sys.stdout):
            dummy_var = _allocate(4096)

        captured = capsys.readouterr()
        assert "Total Memory Used" in captured.out

    def test_ordinary_use_as_context_manager_file(self, tmp_path):
        output_file = tmp_path / "memory_report.txt"
        with mem.run(output_file):
            dummy_var = _allocate(4096)

        assert output_file.exists()
        with open(output_file, "r") as f:
            content = f.read()
            assert "Total Memory Used" in content

    @patch("pyu.profiling.memory.MemoryWriter.write")
    def test_mem_usage_computed_correctly_context_manager(
        self, mock_memory_writer_write
    ):
        EXPECTED_USAGE = 1024 * 1024 + 678
        with mem.run():
            dummy_var = _allocate(EXPECTED_USAGE)

        assert (
            abs(mock_memory_writer_write.call_args[0][0][0] - EXPECTED_USAGE)
            < MEM_MEASUREMENT_ATOL
        )

    @patch("pyu.profiling.memory.MemoryWriter.write")
    def test_recursive_function_decorator(self, mock_memory_writer_write):
        @mem
        def recursive_function(n):
            if n <= 1:
                return 1
            return n * recursive_function(n - 1)

        result = recursive_function(5)

        mock_memory_writer_write.assert_called_once()

    @patch("pyu.profiling.memory.MemoryWriter.write")
    def test_recursive_function_context_manager(
        self, mock_memory_writer_write
    ):

        def recursive_function(n):
            if n <= 1:
                return 1
            return n * recursive_function(n - 1)

        with mem.run():
            result = recursive_function(5)

        mock_memory_writer_write.assert_called_once()
