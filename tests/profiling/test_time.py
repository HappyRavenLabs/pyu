import sys
import time
from unittest.mock import patch

import pytest

from pyu.profiling.time import ltimer, timer


def _assert_report_printed(output):
    assert "Timing Report" in output
    assert "Total elapsed time" in output
    assert "Average time per run" in output
    assert "Standard deviation" in output
    assert "Median time" in output
    assert "Interquartile range (IQR)" in output
    assert "Minimum time" in output
    assert "Maximum time" in output


TIME_MEASUREMENT_ATOL = 0.01  # 10 ms


class TestTimeProfiling:

    def test_ordinary_use_as_context_manager(self, capsys):
        with timer.run():
            time.sleep(0.1)

        captured = capsys.readouterr()
        assert "Elapsed time:" in captured.err

    def test_ordinary_use_as_context_manager_stdout(self, capsys):
        with timer.run(sys.stdout):
            time.sleep(0.1)

        captured = capsys.readouterr()
        assert "Elapsed time:" in captured.out

    def test_ordinary_use_as_context_manager_file(self, tmp_path):
        output_file = tmp_path / "timing_report.txt"
        with timer.run(output_file):
            time.sleep(0.1)

        assert output_file.exists()
        with open(output_file, "r") as f:
            content = f.read()
            assert "Elapsed time:" in content

    def test_decorator_single_run(self, capsys):
        @timer
        def sample_function():
            time.sleep(0.1)

        sample_function()
        captured = capsys.readouterr()
        assert "Elapsed time:" in captured.err

    def test_decorator_multiple_runs(self, capsys):
        @timer(repeat=5)
        def sample_function():
            time.sleep(0.1)

        sample_function()
        captured = capsys.readouterr()
        _assert_report_printed(captured.err)

    def test_decorator_single_run_stdout(self, capsys):
        @timer(out=sys.stdout)
        def sample_function():
            time.sleep(0.1)

        sample_function()
        captured = capsys.readouterr()
        assert "Elapsed time:" in captured.out

    def test_decorator_multiple_runs_stdout(self, capsys):
        @timer(repeat=5, out=sys.stdout)
        def sample_function():
            time.sleep(0.1)

        sample_function()
        captured = capsys.readouterr()
        _assert_report_printed(captured.out)

    def test_decorator_single_run_file(self, tmp_path):
        output_file = tmp_path / "timing_report.txt"

        @timer(out=output_file)
        def sample_function():
            time.sleep(0.1)

        sample_function()
        assert output_file.exists()
        with open(output_file, "r") as f:
            content = f.read()
            assert "Elapsed time:" in content

    def test_decorator_multiple_runs_file(self, tmp_path):
        output_file = tmp_path / "timing_report.txt"

        @timer(repeat=5, out=output_file)
        def sample_function():
            time.sleep(0.1)

        sample_function()
        assert output_file.exists()
        with open(output_file, "r") as f:
            content = f.read()
            _assert_report_printed(content)

    def test_raise_on_zero_repeats(self):
        with pytest.raises(ValueError, match="Repeat must be at least 1."):

            @timer(repeat=0)
            def sample_function():
                time.sleep(0.1)

            sample_function()

    def test_raise_on_negative_repeats(self):
        with pytest.raises(ValueError, match="Repeat must be at least 1."):

            @timer(repeat=-3)
            def sample_function():
                time.sleep(0.1)

            sample_function()

    def test_measure_quick_function(self, capsys):
        @timer(repeat=10)
        def quick_function():
            return None

        quick_function()
        captured = capsys.readouterr()
        _assert_report_printed(captured.err)

    def test_measure_function_with_args(self, capsys):
        @timer(repeat=3)
        def function_with_args(x, y):
            time.sleep(0.05)
            return x + y

        result = function_with_args(5, 10)
        assert result == 15
        captured = capsys.readouterr()
        _assert_report_printed(captured.err)

    @patch("pyu.profiling.writing.TimeWriter.write")
    def test_recursive_function_decorator(self, mock_time_writer_write):
        @timer
        def recursive_function(n):
            if n <= 1:
                return 1
            else:

                return n * recursive_function(n - 1)

        assert mock_time_writer_write.call_count == 0
        result = recursive_function(5)
        mock_time_writer_write.assert_called_once()

    @patch("pyu.profiling.writing.TimeWriter.write")
    def test_recursive_function_context_manager(self, mock_time_writer_write):

        def recursive_function(n):
            if n <= 1:
                return 1
            else:

                return n * recursive_function(n - 1)

        assert mock_time_writer_write.call_count == 0
        with timer.run():
            result = recursive_function(5)

        mock_time_writer_write.assert_called_once()

    def test_time_is_measured_on_error(self, mock_time_writer_write):
        @timer
        def buggy_function():
            time.sleep(1)
            return 1 / 0  # ZeroDivisionError is propagated, timing still recorded

        with pytest.raises(ZeroDivisionError):
            buggy_function()
        mock_time_writer_write.assert_called_once()


class TestLineTimeProfiling:

    def test_ordinary_use_as_context_manager_file(self, tmp_path):
        output_file = tmp_path / "line_timing_report.txt"

        with ltimer.run(out=output_file):
            total = 0
            for i in range(5):
                total += i
            time.sleep(0.1)
            total *= 2

        with open(output_file, "r") as f:
            content = f.read()
            assert "Timing Report" in content
            assert "Line No." in content
            assert "Code" in content
            assert "Total" in content
            assert "Avg" in content
            assert "Count" in content

    def test_ordinary_use_as_context_manager_stdout(self, capsys):
        with ltimer.run(out=sys.stdout):
            total = 0
            for i in range(5):
                total += i
            time.sleep(0.1)
            total *= 2

        captured = capsys.readouterr()
        assert "Timing Report" in captured.out
        assert "Line No." in captured.out
        assert "Code" in captured.out
        assert "Total" in captured.out
        assert "Avg" in captured.out
        assert "Count" in captured.out

    def test_ordinary_use_as_context_manager_default_output(self, capsys):
        with ltimer.run():
            total = 0
            for i in range(5):
                total += i
            time.sleep(0.1)
            total *= 2

        captured = capsys.readouterr()
        assert "Timing Report" in captured.err
        assert "Line No." in captured.err
        assert "Code" in captured.err
        assert "Total" in captured.err
        assert "Avg" in captured.err
        assert "Count" in captured.err

    @patch("pyu.profiling.writing.TimeWriter.write")
    def test_correct_code_in_rows(self, mock_time_writer_write):
        import linecache

        with ltimer.run():
            total = 0
            for i in range(5):
                total += i
            time.sleep(0.1)
            total *= 2

        line_times = mock_time_writer_write.call_args.args[0]
        codes = set(
            [
                linecache.getline(fname, lineno).strip()
                for (fname, lineno) in line_times.keys()
            ]
        )
        assert "total = 0" in codes
        assert "for i in range(5):" in codes
        assert "total += i" in codes
        assert "time.sleep(0.1)" in codes
        assert "total *= 2" in codes
        assert len(codes) == 5

    @patch("pyu.profiling.writing.TimeWriter.write")
    @pytest.mark.skipif(
        sys.platform == "darwin", reason="Timing on macOS is less reliable"
    )
    def test_correct_time_in_rows(self, mock_time_writer_write):
        import linecache

        with ltimer.run():
            time.sleep(0.1)
            time.sleep(0.2)
            time.sleep(0.3)

        line_times = mock_time_writer_write.call_args.args[0]
        codes_times = {
            linecache.getline(fname, lineno).strip(): sum(times)
            for (fname, lineno), times in line_times.items()
        }
        assert (
            abs(codes_times["time.sleep(0.1)"] - 0.1) < TIME_MEASUREMENT_ATOL
        )
        assert (
            abs(codes_times["time.sleep(0.2)"] - 0.2) < TIME_MEASUREMENT_ATOL
        )
        assert (
            abs(codes_times["time.sleep(0.3)"] - 0.3) < TIME_MEASUREMENT_ATOL
        )

    @patch("pyu.profiling.writing.TimeWriter.write")
    def test_recursive_function_decorator(self, mock_time_writer_write):
        @ltimer
        def recursive_function(n):
            if n <= 1:
                return 1
            else:

                return n * recursive_function(n - 1)

        assert mock_time_writer_write.call_count == 0
        result = recursive_function(5)
        mock_time_writer_write.assert_called_once()

    @patch("pyu.profiling.writing.TimeWriter.write")
    def test_recursive_function_context_manager(self, mock_time_writer_write):

        def recursive_function(n):
            if n <= 1:
                return 1
            else:

                return n * recursive_function(n - 1)

        assert mock_time_writer_write.call_count == 0
        with ltimer.run():
            result = recursive_function(5)

        mock_time_writer_write.assert_called_once()
