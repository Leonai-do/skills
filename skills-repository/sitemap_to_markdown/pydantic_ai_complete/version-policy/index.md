---
url: https://ai.pydantic.dev/version-policy/
date: 2026-01-03T23:40:25.459200
---

# Version policy

## Version Policy

We will not intentionally make breaking changes in minor releases of V1. V2 will be released in April 2026 at the earliest, 6 months after the release of V1 in September 2025.

Once we release V2, we'll continue to provide security fixes for V1 for another 6 months minimum, so you have time to upgrade your applications.

Functionality marked as deprecated will not be removed until V2.

Of course, some apparently safe changes and bug fixes will inevitably break some users' code — obligatory link to [xkcd](https://xkcd.com/1172/).

The following changes will **NOT** be considered breaking changes, and may occur in minor releases:

In all cases we will aim to minimize churn and do so only when justified by the increase of quality of Pydantic AI for users.

## Beta Features

At Pydantic, we like to move quickly and innovate! To that end, minor releases may introduce beta features (indicated by a `beta` module) that are active works in progress. While in its beta phase, a feature's API and behaviors may not be stable, and it's very possible that changes made to the feature will not be backward-compatible. We aim to move beta features out of beta within a few months after initial release, once users have had a chance to provide feedback and test the feature in production.

## Support for Python versions

Pydantic will drop support for a Python version when the following conditions are met:

  - The Python version has reached its [expected end of life](https://devguide.python.org/versions/).
  - less than 5% of downloads of the most recent minor release are using that version.

