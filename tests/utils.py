from typing import Iterable


def assert_sorting_of_items_list(items: list[dict], sort_fields: list[str]) -> None:
    sorted_items = items.copy()

    for field in reversed(sort_fields):
        reverse = field.startswith("-")
        key = field[1:] if reverse else field
        sorted_items.sort(key=lambda x: x[key], reverse=reverse)
    assert items == sorted_items


def assert_filtering_of_items_list(
    items: list, filter_data: Iterable[tuple[str, list, str]]
) -> None:
    op_checks = {
        "eq": lambda field_val, vals: field_val == vals[0],
        "neq": lambda field_val, vals: field_val != vals[0],
        "lt": lambda field_val, vals: all(field_val < v for v in vals),
        "lte": lambda field_val, vals: all(field_val <= v for v in vals),
        "gt": lambda field_val, vals: all(field_val > v for v in vals),
        "gte": lambda field_val, vals: all(field_val >= v for v in vals),
        "co": lambda field_val, vals: all(v in field_val for v in vals),
        "ico": lambda field_val, vals: all(
            v.casefold() in field_val.casefold() for v in vals
        ),
        "nco": lambda field_val, vals: all(v not in field_val for v in vals),
        "nico": lambda field_val, vals: all(
            v.casefold() not in field_val.casefold() for v in vals
        ),
        "in": lambda field_val, vals: field_val in vals,
        "nin": lambda field_val, vals: field_val not in vals,
        "between": lambda field_val, vals: vals[0] <= field_val <= vals[1],
    }

    for item in items:
        for field, value, op in filter_data:
            assert op in op_checks, f"Unsupported operation '{op}'"
            field_val = item[field]
            assert op_checks[op](field_val, value), (
                f"Assertion failed for item {item}, "
                f"field '{field}' with operation '{op}' and value(s) {value}"
            )


def assert_pagination(
    rs: dict, page_number: int, page_size: int, page_total: int, total: int
) -> None:
    assert len(rs["items"]) == page_total
    assert rs["page_number"] == page_number
    assert rs["page_size"] == page_size
    assert rs["total"] == total
