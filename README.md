# Django Subforms

[![Coverage Status][coverage-badge]][coverage]
[![GitHub Workflow Status][status-badge]][status]
[![PyPI][pypi-badge]][pypi]
[![GitHub][licence-badge]][licence]
[![GitHub Last Commit][repo-badge]][repo]
[![GitHub Issues][issues-badge]][issues]
[![Downloads][downloads-badge]][pypi]
[![Python Version][version-badge]][pypi]

```shell
pip install django-subforms
```

---

**Documentation**: [https://mrthearman.github.io/django-subforms/](https://mrthearman.github.io/django-subforms/)

**Source Code**: [https://github.com/MrThearMan/django-subforms/](https://github.com/MrThearMan/django-subforms/)

**Contributing**: [https://github.com/MrThearMan/django-subforms/blob/main/CONTRIBUTING.md](https://github.com/MrThearMan/django-subforms/blob/main/CONTRIBUTING.md)

---

This library adds two new fields: `NestedFormField`, which can wrap forms as fields on another form
and thus provide validation for, e.g., a JSON field, and `DynamicArrayField`, which can wrap
fields, including `NestedFormField`, as dynamically expandable lists of fields.

![Example image](https://github.com/MrThearMan/django-subforms/raw/main/docs/img/example.png)

[coverage-badge]: https://coveralls.io/repos/github/MrThearMan/django-subforms/badge.svg?branch=main
[status-badge]: https://img.shields.io/github/actions/workflow/status/MrThearMan/django-subforms/test.yml?branch=main
[pypi-badge]: https://img.shields.io/pypi/v/django-subforms
[licence-badge]: https://img.shields.io/github/license/MrThearMan/django-subforms
[repo-badge]: https://img.shields.io/github/last-commit/MrThearMan/django-subforms
[issues-badge]: https://img.shields.io/github/issues-raw/MrThearMan/django-subforms
[version-badge]: https://img.shields.io/pypi/pyversions/django-subforms
[downloads-badge]: https://img.shields.io/pypi/dm/django-subforms

[coverage]: https://coveralls.io/github/MrThearMan/django-subforms?branch=main
[status]: https://github.com/MrThearMan/django-subforms/actions/workflows/test.yml
[pypi]: https://pypi.org/project/django-subforms
[licence]: https://github.com/MrThearMan/django-subforms/blob/main/LICENSE
[repo]: https://github.com/MrThearMan/django-subforms/commits/main
[issues]: https://github.com/MrThearMan/django-subforms/issues
