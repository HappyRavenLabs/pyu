
def compute_statistics(data: list[float]) -> dict[str, float]:
    """Compute basic statistics (mean, median, stddev) for a list of numbers."""
    sorted_data = sorted(data)
    if not data:
        return {}
    mean = sum(data) / len(data)
    return {
        'mean': mean,
        'median': sorted_data[len(sorted_data) // 2],
        'stdev': (sum((x - mean) ** 2 for x in sorted_data) / (len(sorted_data) - 1)) ** 0.5 if len(data) > 1 else 0.0,
        "iqr": sorted_data[int(0.75 * len(sorted_data))] - sorted_data[int(0.25 * len(sorted_data))],
        'min': min(data),
        'max': max(data),
        'count': len(data),
        "sum": sum(data),
    }