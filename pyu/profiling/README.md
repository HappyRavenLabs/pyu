# PyU Profiling Module

A powerful and flexible Python profiling toolkit for measuring execution time and memory usage with rich reporting capabilities.

> [!IMPORTANT]
> **Do not use time and memory profilers simultaneously**. Time profiling causes memory overhead and vice-versa.

## Features

- **Time Profiling**: Measure execution time with microsecond precision
- **Memory Profiling**: Track memory usage during function execution
- **Line-by-Line Analysis**: Get detailed breakdowns for each line of code
- **Multiple Output Formats**: Console (with Rich formatting), CSV, and text files
- **Summary statistics**: Automatic computation of mean, median, standard deviation, and more
- **Recursive Function Support**: Prevents interference in recursive calls

## Table of Contents

- [Quick Start](#quick-start)
- [Time Profiling](#time-profiling)
    - [Basic Usage](#basic-usage)
        - [As a Decorator](#as-a-decorator)
        - [Multiple Runs for Better Statistics](#multiple-runs-for-better-statistics)
        - [As a Context Manager](#as-a-context-manager)
        - [Custom Output Destinations](#custom-output-destinations)
        - [Precision Control](#precision-control)
    - [Line-by-Line Time Profiling](#line-by-line-time-profiling)
- [Memory Profiling](#memory-profiling)
    - [Basic Usage](#basic-usage-1)
        - [As a Decorator](#as-a-decorator-1)
        - [Multiple Runs](#multiple-runs)
        - [As a Context Manager](#as-a-context-manager-1)
        - [Custom Output](#custom-output)
    - [Line-by-Line Memory Profiling](#line-by-line-memory-profiling)
- [Advanced Usage](#advanced-usage)
- [Output Format Examples](#output-format-examples)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [API Reference](#api-reference)
- [Accessing stats programmatically](#accessing-stats-programmatically)



## Quick Start

```python
from pyu.profiling import timer, ltimer, mem, lmem
import time

# Time profiling with decorator
@timer()
def my_function():
    time.sleep(0.1)
    return "done"

# Memory profiling with context manager
with mem():
    data = [i for i in range(10000)]

# Line-by-line time analysis
with ltimer():
    total = 0
    for i in range(1000):
        total += i * 2
    result = total / 1000
```

## Time Profiling

### Basic Usage

#### As a Decorator

```python
from pyu.profiling import timer

@timer()
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

result = calculate_fibonacci(10)
# Output: Elapsed time: 0.0123 seconds
```

#### Multiple Runs for Better Statistics

```python
@timer(repeat=5)
def network_request():
    import requests
    response = requests.get("https://api.github.com")
    return response.status_code

status = network_request()
# Output: Rich table with mean, std dev, median, min, max, etc.
```

#### As a Context Manager

```python
with timer():
    # Your code here
    result = sum(i**2 for i in range(10000))
# Output: Elapsed time: 0.0045 seconds
```

#### Custom Output Destinations

```python
import sys

# Output to stdout
@timer(out=sys.stdout)
def my_function():
    return "hello world"

# Output to file
@timer(out="timing_results.txt")
def my_function():
    return "hello world"

# Output to CSV
with timer(out="results.csv"):
    data = [i for i in range(100000)]
```

#### Precision Control

```python
@timer(precision=6)  # 6 decimal places
def precise_timing():
    time.sleep(0.001234)

precise_timing()
# Output: Elapsed time: 0.001234 seconds
```

### Line-by-Line Time Profiling

Get detailed timing for each line of your code:

```python
from pyu.profiling import ltimer

@ltimer()
def complex_function():
    data = []                    # Line timing tracked
    for i in range(1000):       # Line timing tracked  
        data.append(i * 2)      # Line timing tracked
    result = sum(data)          # Line timing tracked
    return result               # Line timing tracked

complex_function()

# Or as context manager
with ltimer:
    x = 10
    y = 20
    z = x * y
    time.sleep(0.1)
    final = z + 5
```

**Output Example:**
```
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Line No.┃ Code               ┃ Total Time (s) ┃ Avg Time (s)  ┃ Count  ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━ ━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 156     │ x = 10             │ 0.000001       │ 0.000001      │ 1      │
│ 157     │ y = 20             │ 0.000001       │ 0.000001      │ 1      │
│ 158     │ z = x * y          │ 0.000002       │ 0.000002      │ 1      │
│ 159     │ time.sleep(0.1)    │ 0.100123       │ 0.100123      │ 1      │
│ 160     │ final = z + 5      │ 0.000001       │ 0.000001      │ 1      │
└─────────┴────────────────────┴────────────────┴───────────────┴────────┘
```

## Memory Profiling

### Basic Usage

#### As a Decorator

```python
from pyu.profiling import mem

@mem()
def create_large_list():
    return [i for i in range(100000)]

data = create_large_list()
# Output: Total Memory Used: 4.58 MB
```

#### Multiple Runs

```python
@mem(repeat=3)
def allocate_memory():
    return bytearray(1024 * 1024)  # 1MB allocation

result = allocate_memory()
# Output: Rich table with memory statistics
```

#### As a Context Manager

```python
with mem:
    # Memory usage will be tracked for this block
    big_dict = {i: str(i) * 100 for i in range(10000)}
# Output: Total Memory Used: 12.45 MB
```

#### Custom Output

```python
# Save to file
with mem(out="memory_report.txt"):
    data = list(range(1000000))

# CSV output
@mem(out="memory_stats.csv")
def memory_intensive_function():
    matrix = [[i * j for j in range(100)] for i in range(100)]
    return matrix

memory_intensive_function()
```

### Line-by-Line Memory Profiling

Track memory allocation for each line:

```python
from pyu.profiling import lmem

with lmem():
    small_list = [1, 2, 3]          # Small allocation
    medium_list = list(range(1000)) # Medium allocation  
    large_dict = {i: i**2 for i in range(10000)}  # Large allocation
    del large_dict                  # Memory freed
```

**Output Example:**
```
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Line No. ┃ Code                                      ┃ Avg Memory    ┃ Count  ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 234      │ small_list = [1, 2, 3]                    │ 128 bytes     │ 1      │
│ 235      │ medium_list = list(range(1000))           │ 8.79 kB       │ 1      │
│ 236      │ large_dict = {i: i**2 for i in range...   │ 368.64 kB     │ 1      │
│ 237      │ del large_dict                            │ -360.45 kB    │ 1      │
└──────────┴───────────────────────────────────────────┴───────────────┴────────┘
```

## Advanced Usage

### Profiling Functions with Arguments

```python
@timer(repeat=3, precision=4)
def process_data(data, multiplier=2, use_cache=True):
    return [x * multiplier for x in data if x > 0]

# Function arguments are displayed in the report
result = process_data([1, -2, 3, 4], multiplier=3, use_cache=False)
# Output includes: "Timing Report for process_data(data=[1, -2, 3, 4], multiplier=3, use_cache=False)"
```

### Recursive Functions

The profilers handle recursive functions intelligently, avoiding measurement interference:

```python
@timer()
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Only the top-level call is measured
result = factorial(10)
```

### Output Format Examples

#### CSV Output Structure
```csv
Timing Report for my_function(x=10, y=20)

Metric,Value
Total elapsed time,0.5234
Number of runs,5
Average time,0.1047
Standard deviation,0.0123
Median time,0.1034
Interquartile range (IQR),0.0089
Minimum time,0.0987
Maximum time,0.1234
```

#### Rich Console Output
The console output uses the [Rich library](https://rich.readthedocs.io/) for beautiful, colorful tables with proper formatting and alignment.

<!-- ## Configuration

### Report Configuration

```python
from pyu.profiling.writing import ReportConfig

config = ReportConfig(
    precision=4,
    show_statistics=["mean", "median", "min", "max"],
    memory_units="MB",  # 'bytes', 'kb', 'mb', 'gb', 'auto'
    time_units="milliseconds"  # 'seconds', 'milliseconds', 'microseconds'
)

# Use with custom configuration (implementation may vary)
``` -->

## Best Practices

### ✅ Do's

1. **Profile one metric at a time**: Use either time OR memory profiling, not both
2. **Use multiple runs**: For timing, use `repeat > 1` for statistical significance
3. **Profile realistic workloads**: Test with representative data sizes
4. **Save results**: Use file output for batch analysis and comparison
5. **Use line profiling for optimization**: Identify bottlenecks with `ltimer` and `lmem`

### ❌ Don'ts

1. **Don't mix profilers**: Never use `timer` and `mem` simultaneously
2. **Don't profile trivial code**: Overhead may skew results for very fast operations
3. **Don't ignore statistical variance**: Single measurements can be misleading
4. **Don't profile in production**: Profiling adds overhead and should be development-only

## Common Patterns

### Before/After Optimization Comparison

```python
# Save baseline performance
@timer(repeat=10, out="baseline_performance.csv")
def slow_algorithm(data):
    return sorted(data, key=lambda x: str(x))

# Test optimized version
@timer(repeat=10, out="optimized_performance.csv") 
def fast_algorithm(data):
    return sorted(data)

# Compare CSV files to measure improvement
```

### Batch Profiling

```python
import sys
from pathlib import Path

def profile_all_algorithms():
    results_dir = Path("profiling_results")
    results_dir.mkdir(exist_ok=True)
    
    algorithms = [bubble_sort, quick_sort, merge_sort]
    
    for algo in algorithms:
        @timer(repeat=5, out=results_dir / f"{algo.__name__}_timing.csv")
        def wrapped_algo(data):
            return algo(data.copy())
        
        test_data = list(range(1000, 0, -1))  # Worst case
        wrapped_algo(test_data)
```

## Error Handling

The profilers include built-in error handling for common issues:

```python
# Invalid repeat count
@timer(repeat=0)  # Raises ValueError: Repeat must be at least 1
def my_function():
    pass

# Invalid output target  
@timer(out=123)  # Raises InvalidOutputError
def my_function():
    pass

# The profilers gracefully handle exceptions in your code
@timer()
def buggy_function():
    import time
    
    time.sleep(1)
    return 1 / 0  # ZeroDivisionError is propagated, timing still recorded
```

## Performance Considerations

- **Timing overhead**: ~1-5 microseconds per function call
- **Memory overhead**: Minimal, uses Python's built-in `tracemalloc`
- **Line profiling overhead**: Higher due to tracing, use sparingly
- **File I/O**: CSV/TXT output adds minimal overhead, Rich console output is optimized


## API Reference

### Common Parameters

- `repeat` (int): Number of times to run the function (default: 1)
- `out` (str|Path|TextIOWrapper|None): Output destination (default: stderr)
- `precision` (int): Decimal places for timing display (default: 4)

### Exceptions

- `ProfilingError`: Base exception for all profiling errors
- `InvalidOutputError`: Raised when output target is invalid  
- `DataValidationError`: Raised when measurement data is invalid

---

## Accessing stats programmatically

All profilers expose their computed summary statistics on the profiler instance after a run. The summary object is an instance of `pyu.profiling.stats.Stats` and provides cached properties you can read from code: `mean`, `median`, `mode`, `stddev`, and `sorted_values`.



> [!NOTE]
> When you use decorators, keep a reference to the decorator instance if you want to access `stats`/`usage` later. If you call the decorator directly as `@timer()` without storing it, you won't have a handle to the instance to read the property.

> [!NOTE]
> When used as a context manager (`with timer() as t:`) the context manager returns the profiler instance so you can read the values after the block.

Examples:

Time decorator (store decorator instance to read stats):

```python
from pyu.profiling import timer

t = timer(repeat=3)

@t
def work():
    # expensive operation
    sum(i*i for i in range(100000))

work()

# Access summary statistics
print("mean:", t.stats.mean)
print("median:", t.stats.median)
print("stddev:", t.stats.stddev)
```

Time context manager (use returned instance):

```python
from pyu.profiling import timer

with timer() as t:
    sum(i*i for i in range(100000))

print("elapsed (s):", t.stats.mean)
```

Line-by-line time profiler (`ltimer`) — `stats` is a mapping from
`(code_line, lineno, filename)` to `Stats`:

```python
from pyu.profiling import ltimer

with ltimer() as lt:
    total = 0
    for i in range(10000):
        total += i * 3

# lt.stats keys are tuples: (code_line_str, lineno, filename)
for (code, lineno, filename), stats in lt.stats.items():
    print(f"{filename}:{lineno}: {code!s}\n  mean={stats.mean:.6f}s stddev={stats.stddev:.6f}s")
```

Memory decorator/context manager (property name is `usage`):

```python
from pyu.profiling import mem

m = mem(repeat=2)

@m
def allocate():
    return [0] * (1024 * 1024 // 8)  # allocate ~1M elements

allocate()

# Memory stats are in bytes
print("peak mean (bytes):", m.usage.mean)
print("peak mean (MB):", m.usage.mean / (1024 * 1024))
```

Line-by-line memory profiler (`lmem`) — `usage` is a mapping similar to `ltimer`:

```python
from pyu.profiling import lmem

with lmem() as lm:
    a = [i for i in range(10000)]
    b = [i*i for i in range(10000)]

for (code, lineno, filename), stats in lm.usage.items():
    print(f"{filename}:{lineno}: {code!s}\n  mean={stats.mean / (1024*1024):.3f} MB  stddev={stats.stddev / (1024*1024):.3f} MB")
```

Programmatic tips


> [!TIP]
> Sort lines by a statistic (e.g. mean) to find the biggest consumers:
> ```python
> hot_lines = sorted(lm.usage.items(), key=lambda kv: kv[1].mean, reverse=True)
> for (code, lineno, filename), stats in hot_lines[:10]:
>     print(lineno, stats.mean)
> ```
> This approach makes it convenient to integrate profiling into automated runs or CI, save `stats` for later analysis, or convert bytes to human-friendly units when reporting memory.


**Author**: Jakub Walczak  
**Organization**: HappyRavenLabs

For more examples and advanced usage, see the test files in `tests/profiling/`.