

def clamp(value: float, min_value: float, max_value: float) -> float:
    # Keeps a value inside an expected range.
    if value < min_value:
        return min_value

    if value > max_value:
        return max_value

    return value


def min_max_scale(values: list[float]) -> list[float]:
    # Scales numbers to a 0-1 range.
    # Min-max normalization is used because the MVP ticker list is small.
    # Z-scores can become unstable with only 6-8 tickers.
    if not values:
        return []

    min_value = min(values)
    max_value = max(values)

    # If every value is the same, give a neutral score.
    if max_value == min_value:
        return [0.5 for _ in values]

    scaled = []

    for value in values:
        scaled_value = (value - min_value) / (max_value - min_value)
        scaled.append(scaled_value)

    return scaled


def scale_optional_values(values: list[float | None], default: float = 0.5) -> list[float]:
    # Scales only values that exist.
    # Missing values get a neutral score here.
    # Missing data is penalized later through the confidence flag.
    result = [default] * len(values)

    valid_indexes = []
    valid_values = []

    for index, value in enumerate(values):
        if value is not None:
            valid_indexes.append(index)
            valid_values.append(value)

    if not valid_values:
        return result

    scaled_values = min_max_scale(valid_values)

    for index, scaled_value in zip(valid_indexes, scaled_values):
        result[index] = scaled_value

    return result


def normalize_sentiment(sentiment: float | None) -> float:
    # Converts sentiment from [-1, 1] to [0, 1].
    # -1 becomes 0.
    # 0 becomes 0.5.
    # 1 becomes 1.
    if sentiment is None:
        return 0.5

    normalized = (sentiment + 1.0) / 2.0
    return clamp(normalized, 0.0, 1.0)


def invert(values: list[float]) -> list[float]:
    # Flips a score so a lower input becomes a higher output.
    # This is useful for P/E because lower P/E is usually better.
    inverted = []

    for value in values:
        inverted.append(1.0 - value)

    return inverted


def median(values: list[float]) -> float | None:
    # Finds the middle value.
    # Median is more stable than average when one ticker has an extreme value.
    if not values:
        return None

    ordered = sorted(values)
    length = len(ordered)
    middle = length // 2

    if length % 2 == 0:
        return (ordered[middle - 1] + ordered[middle]) / 2.0

    return ordered[middle]