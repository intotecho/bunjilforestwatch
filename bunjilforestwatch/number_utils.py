def clamp(n, lower, upper):
    """
    :param n: The number to limit
    :param lower: The lower boundary
    :param upper: The upper boundary
    :return: Returns a number within the inclusive lower and upper bounds
    """
    # TODO: Fix import issues with numpy replace usages of this with numpy.clip.
    return max(min(upper, n), lower)
