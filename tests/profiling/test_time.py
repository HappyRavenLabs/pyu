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


TIME_MEASUREMENT_RTOL = 0.05  # 5%


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

    @pytest.mark.parametrize("repeat", [1, 3, 5])
    @pytest.mark.parametrize("duration", [0.01, 0.05, 0.1])
    @pytest.mark.skip
    @patch("pyu.profiling.time.print_report")
    def test_accuracy_of_timing(
        self, mock_print_report, capsys, repeat, duration
    ):
        @timer(repeat=repeat)
        def timed_function():
            time.sleep(duration)

        timed_function()
        exec_times = mock_print_report.call_args.args[1]
        mean_time = sum(exec_times) / len(exec_times)
        assert abs(mean_time - duration) / duration < TIME_MEASUREMENT_RTOL
        for t in exec_times:
            assert abs(t - duration) / duration < TIME_MEASUREMENT_RTOL


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
            assert "Line Timing Report" in content
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
        assert "Line Timing Report" in captured.out
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
        assert "Line Timing Report" in captured.err
        assert "Line No." in captured.err
        assert "Code" in captured.err
        assert "Total" in captured.err
        assert "Avg" in captured.err
        assert "Count" in captured.err

    @patch("pyu.profiling.time.print_line_report")
    def test_correct_code_in_rows(self, mock_print_line_report):
        import linecache

        with ltimer.run():
            total = 0
            for i in range(5):
                total += i
            time.sleep(0.1)
            total *= 2

        line_times = mock_print_line_report.call_args.args[1]
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

    @patch("pyu.profiling.time.print_line_report")
    def test_correct_time_in_rows(self, mock_print_line_report):
        import linecache

        with ltimer.run():
            time.sleep(0.1)
            time.sleep(0.2)
            time.sleep(0.3)

        line_times = mock_print_line_report.call_args.args[1]
        codes_times = {
            linecache.getline(fname, lineno).strip(): sum(times)
            for (fname, lineno), times in line_times.items()
        }
        assert (
            codes_times["time.sleep(0.1)"] - 0.1
        ) / 0.1 < TIME_MEASUREMENT_RTOL
        assert (
            codes_times["time.sleep(0.2)"] - 0.2
        ) / 0.2 < TIME_MEASUREMENT_RTOL
        assert (
            codes_times["time.sleep(0.3)"] - 0.3
        ) / 0.3 < TIME_MEASUREMENT_RTOL
