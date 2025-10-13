# PyU Profiling Module

A comprehensive profiling toolkit for measuring execution time and memory usage in Python applications. This module provides both decorators and context managers for easy integration into your code.

## Overview

The profiling module offers four main tools, each available both as **decorators** and **context managers**:

- **`timer`** - Time profiling (decorator: `@timer` or context manager: `timer.run()`)
- **`ltimer`** - Line-by-line time profiling (context manager: `ltimer.run()`)  
- **`mem`** - Memory profiling (decorator: `@mem` or context manager: `mem.run()`)
- **`lmem`** - Line-by-line memory profiling (*coming soon*)

All tools support outputting results to stderr (default), stdout, or files, and provide detailed statistical reports with beautiful formatting.


> [!IMPORTANT]
> 🚨 **Do not combine time and memory profiling simultaneously!** Memory profiling introduces significant timing overhead, and time profiling introduces memory overhead. Running both together will produce inaccurate results for both metrics. Profile time and memory separately for reliable measurements.
>
> Always profile these metrics **separately** for reliable results.

## Installation & Import

To install use:

```bash
pip install raven-pyu
```

To import, use:

```python
from pyu.profiling import timer, ltimer
from pyu.profiling import mem, lmem
```

---

## ⏱️ Time Profiling

### `timer` - Time Profiling (Decorator & Context Manager)

The `timer` tool can be used both as a decorator (`@timer`) for functions and as a context manager (`timer.run()`) for code blocks. It measures execution time with detailed statistical analysis.

#### Basic Usage as Decorator

```python
from pyu.profiling import timer
import time

# Simple decorator usage
@timer
def slow_function():
    time.sleep(0.1)
    return "completed"

result = slow_function()
```

Output:

```
Elapsed time: 0.100104 seconds
```

#### Advanced Usage with Parameters

```python
# Multiple runs for statistical analysis
@timer(repeat=10)
def variable_function():
    import random
    time.sleep(random.uniform(0.05, 0.15))
    return "variable timing"

result = variable_function()
```

Output:

```
                          Timing Report for function       
                            'variable_function'                                                                                                                                          
           ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓                                                                                                                                                          
           ┃ Metric                    ┃ Value                         ┃                                                                                                                                                          
           ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩                                                                                                                                                          
           │ Total elapsed time        │ 1.109157 seconds over 10 runs │                                                                                                                                                          
           │ Average time per run      │ 0.110916 seconds              │                                                                                                                                                          
           │ Standard deviation        │ 0.031046 seconds              │                                                                                                                                                          
           │ Median time               │ 0.123785 seconds              │                                                                                                                                                          
           │ Interquartile range (IQR) │ 0.041723 seconds              │                                                                                                                                                          
           │ Minimum time              │ 0.052458 seconds              │                                                                                                                                                          
           │ Maximum time              │ 0.148912 seconds              │                                                                                                                                                          
           └───────────────────────────┴───────────────────────────────┘                                                                                                                                                          
             Timing report for function variable_function called with 
                                 arguments {}    
```                                   

#### Output Redirection

```python
import sys

# Output to stdout instead of stderr
@timer(repeat=5, out=sys.stdout)
def stdout_function():
    time.sleep(0.05)

# Output to file
@timer(repeat=3, out="timing_results.txt")
def file_output_function():
    time.sleep(0.02)

# The file will contain the complete timing report
```

#### Working with Function Arguments

```python
@timer(repeat=5)
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# The report will include function name and arguments
result = calculate_fibonacci(10)
# Report shows: "Timing Report for function 'calculate_fibonacci' called with arguments {'n': 10}"
```

### `timer.run()` - Context Manager for Code Blocks

Profile specific code blocks without decorating entire functions.

#### Basic Context Manager Usage

```python
from pyu.profiling.time import timer
import time

# Time a specific code block
with timer.run():
    data = []
    for i in range(1000):
        data.append(i ** 2)
    time.sleep(0.1)
# Output: Elapsed time: 0.101234 seconds
```

#### Context Manager with Output Control

```python
import sys

# Output to stdout
with timer.run(out=sys.stdout):
    expensive_computation = sum(i**2 for i in range(100000))

# Output to file
with timer.run(out="block_timing.txt"):
    with open("large_file.txt", "w") as f:
        for i in range(10000):
            f.write(f"Line {i}\n")
```

### `@ltimer` - Line-by-Line Time Profiling

The `ltimer` provides detailed line-by-line execution timing, perfect for identifying performance bottlenecks within code blocks.

#### Line Timer Context Manager

```python
from pyu.profiling.time import ltimer
import time

with ltimer.run():
    total = 0                    # This line will be timed
    for i in range(5):           # This line will be timed
        total += i               # This line will be timed (multiple executions)
        time.sleep(0.01)         # This line will be timed (multiple executions)
    result = total * 2           # This line will be timed
```

Output:

```
                                        Line Timing Report for '/home/jakub/happy_raven_labs/repos/pyu/t1. py'                                                                                                   
           ┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━┓                                                                                
           ┃ Line No. ┃ Code                                                                             ┃ Total Time (s) ┃ Avg Time (s) ┃ Count ┃                                                                                
           ┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━┩                                                                                
           │ 5        │     total = 0                    # This line will be timed                       │ 0.000002       │ 0.000002     │ 1     │                                                                                
           │ 6        │     for i in range(5):           # This line will be timed                       │ 0.000074       │ 0.000012     │ 6     │                                                                                
           │ 7        │         total += i               # This line will be timed (multiple executions) │ 0.000013       │ 0.000003     │ 5     │                                                                                
           │ 8        │         time.sleep(0.01)         # This line will be timed (multiple executions) │ 0.050601       │ 0.010120     │ 5     │                                                                                
           │ 9        │     result = total * 2           # This line will be timed                       │ 0.000002       │ 0.000002     │ 1     │                                                                                
           └──────────┴──────────────────────────────────────────────────────────────────────────────────┴────────────────┴──────────────┴───────┘                                                                                
                                      Timing report for lines executed in /.../pyu/t1.py         
```                                      

#### Line Timer with Different Outputs

```python
import sys

# Output to stdout
with ltimer.run(out=sys.stdout):
    numbers = [1, 2, 3, 4, 5]
    squared = [x**2 for x in numbers]
    cubed = [x**3 for x in numbers]

# Output to file for detailed analysis
with ltimer.run(out="line_analysis.txt"):
    def bubble_sort(arr):
        n = len(arr)
        for i in range(n):
            for j in range(0, n-i-1):
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
    
    test_array = [64, 34, 25, 12, 22, 11, 90]
    bubble_sort(test_array)
```

---

## 💾 Memory Profiling

### `mem` - Memory Profiling (Decorator & Context Manager)

The `mem` tool can be used both as a decorator (`@mem`) for functions and as a context manager (`mem.run()`) for code blocks. It tracks memory allocation during execution.

#### Basic Usage as Decorator

```python
from pyu.profiling.memory import mem

@mem
def memory_intensive_function():
    # Allocate a large list
    big_list = [i for i in range(100000)]
    # Allocate a large string
    big_string = "x" * 50000
    return len(big_list) + len(big_string)

result = memory_intensive_function()
```


Output:
```
Total Memory Used: 32.00 bytes 
```

#### Multiple Runs for Memory Analysis

```python
@mem(repeat=5)
def variable_memory_function():
    import random
    size = random.randint(1000, 10000)
    data = bytearray(size)
    return len(data)

result = variable_memory_function()
```

Output:

```
                      Memory Usage Report for function 
                          'variable_memory_function'                                                                                                                                                                              
           ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓                                                                                                                                                               
           ┃ Metric                    ┃ Value                    ┃                                                                                                                                                               
           ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩                                                                                                                                                               
           │ Total Memory Used         │ 140.00 bytes over 5 runs │                                                                                                                                                               
           │ Average Memory per run    │ 28.00 bytes              │                                                                                                                                                               
           │ Standard deviation        │ 0.00 bytes               │                                                                                                                                                               
           │ Median Memory             │ 28.00 bytes              │                                                                                                                                                               
           │ Interquartile range (IQR) │ 0.00 bytes               │                                                                                                                                                               
           │ Minimum Memory            │ 28.00 bytes              │                                                                                                                                                               
           │ Maximum Memory            │ 28.00 bytes              │                                                                                                                                                               
           └───────────────────────────┴──────────────────────────┘                                                                                                                                                               
                       Memory usage report for function  
                 variable_memory_function called with arguments {}  
```              

#### Memory Profiling with Output Control

```python
import sys

# Output to stdout
@mem(repeat=3, output=sys.stdout)
def stdout_memory_function():
    large_dict = {i: str(i) * 100 for i in range(1000)}
    return len(large_dict)

# Output to file
@mem(repeat=5, output="memory_analysis.txt")
def file_memory_function():
    matrix = [[j for j in range(100)] for i in range(100)]
    return len(matrix)

stdout_memory_function()
file_memory_function()
```

#### Memory Profiling with Arguments

```python
@mem(repeat=3)
def create_matrix(rows, cols, fill_value=0):
    return [[fill_value for _ in range(cols)] for _ in range(rows)]

# The report will show function name and arguments
matrix = create_matrix(100, 50, fill_value=42)
```

### `mem.run()` - Context Manager for Memory Profiling

Profile memory usage of specific code blocks.

#### Basic Memory Context Manager

```python
from pyu.profiling.memory import mem

with mem.run():
    # Create some memory-intensive objects
    big_list = list(range(50000))
    big_dict = {i: str(i) * 10 for i in range(10000)}
    big_tuple = tuple(range(25000))

# Output: Total Memory Used: 3.24 MB
```

#### Memory Context Manager with Output Control

```python
import sys

# Output to stdout
with mem.run(out=sys.stdout):
    data_structure = {}
    for i in range(5000):
        data_structure[f"key_{i}"] = [j for j in range(10)]

# Output to file
with mem.run(out="memory_profile.txt"):
    # Simulate data processing
    raw_data = [random.random() for _ in range(100000)]
    processed_data = [x * 2 + 1 for x in raw_data if x > 0.5]
    final_result = sum(processed_data)
```

### `@lmem` - Line-by-Line Memory Profiling

*Note: Line-by-line memory profiling is currently under development and will be available in future versions.*

---

## 📃 Specifying Output

All profiling tools support flexible output options to suit different analysis needs. You can direct output to standard streams or files for further processing.

### Output Options

#### 1. **Standard Error (Default)**
By default, all profiling output goes to `stderr` to avoid interfering with your program's main output:

```python
from pyu.profiling import timer, mem

@timer  # Outputs to stderr by default
def default_output():
    return sum(range(1000))

with mem.run():  # Also outputs to stderr by default
    data = [i**2 for i in range(1000)]
```

#### 2. **Standard Output**
Redirect output to `stdout` using `sys.stdout`:

```python
import sys
from pyu.profiling import timer, ltimer, mem

# Timer decorator to stdout
@timer(repeat=5, out=sys.stdout)
def stdout_timer():
    return sum(range(1000))

# Memory context manager to stdout  
with mem.run(out=sys.stdout):
    large_list = list(range(10000))

# Line timer to stdout
with ltimer.run(out=sys.stdout):
    total = sum(i**2 for i in range(100))
```

#### 3. **File Output**

##### Rich Formatted Reports (Default)
When you specify a file path, profiling tools generate beautifully formatted reports:

```python
from pyu.profiling import timer, ltimer, mem

# Timer results to file
@timer(repeat=10, out="timing_report.txt")
def file_timer():
    return sum(range(5000))

# Memory results to file
@mem(repeat=5, output="memory_report.txt")  # Note: 'output' parameter for mem
def file_memory():
    return [i**3 for i in range(1000)]

# Line-by-line timing to file
with ltimer.run(out="line_timing.txt"):
    numbers = []
    for i in range(100):
        numbers.append(i**2)
    result = sum(numbers)

file_timer()
file_memory()
```

##### CSV Output for Data Analysis
For data analysis and processing, you can generate comma-separated values by appending `.csv` to your filename:

```python
from pyu.profiling import timer, mem

# Generate CSV timing data
@timer(repeat=20, out="timing_data.csv")
def csv_timer():
    import random
    return sum(random.random() for _ in range(1000))

# Generate CSV memory data  
@mem(repeat=15, output="memory_data.csv")
def csv_memory():
    import random
    size = random.randint(100, 1000)
    return bytearray(size)

csv_timer()
csv_memory()
```

**CSV Format for Timing Data:**
```csv
run,execution_time_seconds,function_name,arguments
1,0.000123,csv_timer,{}
2,0.000145,csv_timer,{}
3,0.000134,csv_timer,{}
...
```

**CSV Format for Memory Data:**
```csv
run,memory_bytes,memory_mb,function_name,arguments
1,1024,0.001,csv_memory,{}
2,2048,0.002,csv_memory,{}
3,1536,0.0015,csv_memory,{}
...
```

**CSV Format for Line Timing Data:**
```csv
filename,line_number,code,total_time_seconds,avg_time_seconds,execution_count
/path/to/file.py,45,total = 0,0.000001,0.000001,1
/path/to/file.py,46,for i in range(5):,0.000003,0.000003,1
/path/to/file.py,47,total += i,0.000010,0.000002,5
...
```

### Advanced Output Examples

#### Conditional Output Based on Environment

```python
import os
import sys
from pyu.profiling import timer, mem

# Determine output based on environment
output_target = sys.stdout if os.getenv('DEBUG') else "production_profile.csv"

@mem(repeat=10, output=f"memory_{output_target}")
def environment_aware_function():
    return [i**2 for i in range(1000)]

# Run with: DEBUG=1 python script.py (outputs to stdout)
# Run with: python script.py (outputs to CSV files)
```

#### Multiple Output Formats

```python
from pyu.profiling import timer
import sys

def profile_multiple_outputs():
    """Generate both human-readable and CSV reports"""
    
    @timer(repeat=10, out="human_readable.txt")
    def human_report():
        return sum(range(1000))
    
    @timer(repeat=10, out="data_analysis.csv") 
    def csv_report():
        return sum(range(1000))
    
    @timer(repeat=10, out=sys.stdout)
    def console_report():
        return sum(range(1000))
    
    human_report()    # Rich formatted report
    csv_report()      # CSV for analysis
    console_report()  # Console output

profile_multiple_outputs()
```

### Output File Management

#### Automatic Directory Creation
The profiling tools automatically create directories if they don't exist:

```python
from pyu.profiling import timer, ltimer, mem

# Creates 'reports/timing/' directory if it doesn't exist
@timer(repeat=5, out="reports/timing/detailed_analysis.txt")
def auto_directory():
    return sum(range(1000))

# Creates nested directory structure
with ltimer.run(out="data/profiling/2024/line_analysis.csv"):
    for i in range(100):
        result = i**2

auto_directory()
```

#### Timestamp-based Output Files

```python
from datetime import datetime
from pyu.profiling import timer, mem

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

@timer(repeat=10, out=f"timing_report_{timestamp}.csv")
def timestamped_timer():
    return sum(range(1000))

@mem(repeat=5, output=f"memory_report_{timestamp}.csv")
def timestamped_memory():
    return [i**2 for i in range(1000)]

timestamped_timer()
timestamped_memory()
```


## 📊 Understanding the Output

### Time Profiling Output

#### Single Run Output
```
Elapsed time: 0.123456 seconds
```

#### Multiple Runs Statistical Report
```
╭─────────────────── Timing Report for function 'my_function' ──────────────────╮
│                     Timing report for function my_function                    │
│                        called with arguments {'x': 10}                        │
├────────────────────────────┬───────────────────────────────────────────────────┤
│ Metric                     │ Value                                             │
├────────────────────────────┼───────────────────────────────────────────────────┤
│ Total elapsed time         │ 0.501234 seconds over 5 runs                     │
│ Average time per run       │ 0.100247 seconds                                 │
│ Standard deviation         │ 0.002143 seconds                                 │
│ Median time                │ 0.100123 seconds                                 │
│ Interquartile range (IQR)  │ 0.001876 seconds                                 │
│ Minimum time               │ 0.098765 seconds                                 │
│ Maximum time               │ 0.103456 seconds                                 │
╰────────────────────────────┴───────────────────────────────────────────────────╯
```

#### Line-by-Line Timing Report
```
╭──────────────── Line Timing Report for '/path/to/file.py' ─────────────────╮
│                 Timing report for lines executed in /path/to/file.py       │
├─────────┬─────────────────────────────┬──────────────┬─────────────┬───────┤
│ Line No.│ Code                        │ Total Time(s)│ Avg Time(s) │ Count │
├─────────┼─────────────────────────────┼──────────────┼─────────────┼───────┤
│ 45      │ total = 0                   │ 0.000001     │ 0.000001    │ 1     │
│ 46      │ for i in range(5):          │ 0.000003     │ 0.000003    │ 1     │
│ 47      │     total += i              │ 0.000010     │ 0.000002    │ 5     │
│ 48      │     time.sleep(0.01)        │ 0.050234     │ 0.010047    │ 5     │
│ 49      │     result = total * 2      │ 0.000001     │ 0.000001    │ 1     │
╰─────────┴─────────────────────────────┴──────────────┴─────────────┴───────╯
```

### Memory Profiling Output

#### Single Run Output
```
Total Memory Used: 2.45 MB
```

#### Multiple Runs Statistical Report
```
╭────────────────── Memory Usage Report for function 'my_function' ──────────────────╮
│                     Memory usage report for function my_function                    │
│                        called with arguments {'size': 1000}                         │
├──────────────────────────────┬───────────────────────────────────────────────────────┤
│ Metric                       │ Value                                                 │
├──────────────────────────────┼───────────────────────────────────────────────────────┤
│ Average Memory per run       │ 2.49 MB                                              │
│ Standard deviation           │ 0.15 MB                                              │
│ Median Memory                │ 2.47 MB                                              │
│ Interquartile range (IQR)    │ 0.23 MB                                              │
│ Minimum Memory               │ 2.31 MB                                              │
│ Maximum Memory               │ 2.68 MB                                              │
╰──────────────────────────────┴───────────────────────────────────────────────────────╯
```

---

## 🔧 Advanced Usage Patterns

### Separate Time and Memory Profiling


```python
import time

from pyu.profiling import timer, ltimer, mem

def complex_function(n):
    # Create some data structures
    data = [i**2 for i in range(n)]
    time.sleep(0.01)  # Simulate some work
    return sum(data)

# ✅ CORRECT: Profile time first
@timer(repeat=3, out="timing_results.txt")
def time_profiled_function(n):
    return complex_function(n)

# ✅ CORRECT: Profile memory separately  
@mem(repeat=3, output="memory_results.txt")
def memory_profiled_function(n):
    return complex_function(n)

# Run profiling separately
time_result = time_profiled_function(10000)
memory_result = memory_profiled_function(10000)

# ❌ INCORRECT: Don't do this!
# @timer(repeat=3)
# @mem(repeat=3)  # This will give inaccurate results for both!
# def bad_example(n):
#     return complex_function(n)
```

---

## 📁 File Output Examples

All profiling tools can output to files for later analysis:

```python
from pyu.profiling import timer, ltimer
from pyu.profiling import mem

# Generate comprehensive profiling reports
@mem(repeat=10, output="function_memory.txt")
def comprehensive_test():
    data = [i**3 for i in range(5000)]
    return sum(data)

# Generate line-by-line analysis
with ltimer.run(out="line_analysis.txt"):
    total = 0
    for i in range(1000):
        if i % 2 == 0:
            total += i**2
        else:
            total += i**3
    
    final_result = total / 1000

comprehensive_test()
```

The generated files will contain beautifully formatted reports that you can review, share, or integrate into your performance analysis workflow.

---

## 🚀 Best Practices

1. **Use `repeat` parameter for statistical significance** when measuring variable-duration operations
2. **Profile time and memory separately** - never combine them as they interfere with each other's accuracy
3. **Use `ltimer.run()`** to identify specific performance bottlenecks within functions
4. **Output to files** for comprehensive analysis and record-keeping
5. **Consider conditional profiling** in production environments
6. **Profile representative workloads** that match your real-world usage patterns
7. **Use context managers** for profiling specific code blocks within larger functions

The PyU profiling module makes performance analysis straightforward and comprehensive, helping you build faster and more efficient Python applications.
